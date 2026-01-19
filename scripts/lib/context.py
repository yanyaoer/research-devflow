"""Context management for skill execution - variable storage and state persistence."""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .types import StepResult, StepStatus


@dataclass
class Context:
    """Execution context for a skill run.

    Manages variables, step results, and state persistence.
    """

    skill_name: str
    task_slug: str = ""
    variables: dict[str, Any] = field(default_factory=dict)
    step_results: dict[str, StepResult] = field(default_factory=dict)
    current_step_id: str = ""
    started_at: str = ""
    updated_at: str = ""
    state_file: str = ""

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def set(self, key: str, value: Any) -> None:
        """Set a context variable."""
        self.variables[key] = value
        self.updated_at = datetime.now().isoformat()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a context variable."""
        return self.variables.get(key, default)

    def interpolate(self, template: str) -> str:
        """Interpolate variables in a template string.

        Supports ${var} and {{var}} syntax.

        Args:
            template: Template string with variable placeholders.

        Returns:
            String with variables replaced by their values.
        """
        result = template

        # Replace ${var} syntax
        def replace_dollar(match: re.Match) -> str:
            var_name = match.group(1)
            value = self.get(var_name, match.group(0))
            return str(value) if value is not None else ""

        result = re.sub(r"\$\{([^}]+)\}", replace_dollar, result)

        # Replace {{var}} syntax
        def replace_braces(match: re.Match) -> str:
            var_name = match.group(1).strip()
            value = self.get(var_name, match.group(0))
            return str(value) if value is not None else ""

        result = re.sub(r"\{\{([^}]+)\}\}", replace_braces, result)

        return result

    def record_step_result(self, result: StepResult) -> None:
        """Record the result of a step execution."""
        self.step_results[result.step_id] = result
        self.updated_at = datetime.now().isoformat()

        # Also store output as a variable for interpolation
        if result.output:
            self.set(f"step_{result.step_id}_output", result.output)

    def get_step_result(self, step_id: str) -> StepResult | None:
        """Get the result of a specific step."""
        return self.step_results.get(step_id)

    def is_step_completed(self, step_id: str) -> bool:
        """Check if a step has been completed."""
        result = self.step_results.get(step_id)
        return result is not None and result.status == StepStatus.COMPLETED

    def get_completed_steps(self) -> list[str]:
        """Get list of completed step IDs."""
        return [
            step_id
            for step_id, result in self.step_results.items()
            if result.status == StepStatus.COMPLETED
        ]

    def get_pending_steps(self, all_step_ids: list[str]) -> list[str]:
        """Get list of pending step IDs."""
        completed = set(self.get_completed_steps())
        return [step_id for step_id in all_step_ids if step_id not in completed]

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "skill_name": self.skill_name,
            "task_slug": self.task_slug,
            "variables": self.variables,
            "step_results": {
                step_id: {
                    "step_id": result.step_id,
                    "status": result.status.value,
                    "output": result.output,
                    "error": result.error,
                    "duration": result.duration,
                    "metadata": result.metadata,
                }
                for step_id, result in self.step_results.items()
            },
            "current_step_id": self.current_step_id,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Context":
        """Create Context from dictionary."""
        ctx = cls(
            skill_name=data.get("skill_name", ""),
            task_slug=data.get("task_slug", ""),
            variables=data.get("variables", {}),
            current_step_id=data.get("current_step_id", ""),
            started_at=data.get("started_at", ""),
            updated_at=data.get("updated_at", ""),
        )

        # Restore step results
        for step_id, result_data in data.get("step_results", {}).items():
            ctx.step_results[step_id] = StepResult(
                step_id=result_data.get("step_id", step_id),
                status=StepStatus(result_data.get("status", "pending")),
                output=result_data.get("output", ""),
                error=result_data.get("error", ""),
                duration=result_data.get("duration", 0.0),
                metadata=result_data.get("metadata", {}),
            )

        return ctx

    def save(self, path: str | Path | None = None) -> str:
        """Save context state to a file.

        Args:
            path: Path to save the state file. If None, uses self.state_file.

        Returns:
            Path to the saved state file.
        """
        if path is None:
            if not self.state_file:
                raise ValueError("No state file path specified")
            path = self.state_file

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write atomically using temp file
        temp_path = path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        temp_path.rename(path)
        self.state_file = str(path)

        return str(path)

    @classmethod
    def load(cls, path: str | Path) -> "Context":
        """Load context state from a file.

        Args:
            path: Path to the state file.

        Returns:
            Restored Context object.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"State file not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        ctx = cls.from_dict(data)
        ctx.state_file = str(path)

        return ctx

    def get_state_summary(self) -> dict[str, Any]:
        """Get a summary of the current state."""
        completed = len([r for r in self.step_results.values() if r.status == StepStatus.COMPLETED])
        failed = len([r for r in self.step_results.values() if r.status == StepStatus.FAILED])
        total = len(self.step_results)

        return {
            "skill_name": self.skill_name,
            "task_slug": self.task_slug,
            "current_step": self.current_step_id,
            "steps_completed": completed,
            "steps_failed": failed,
            "steps_total": total,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
        }
