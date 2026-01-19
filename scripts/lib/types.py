"""Core data types for Skill Runner."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StepType(Enum):
    """Type of step in a skill workflow."""

    PROMPT = "prompt"
    COMMAND = "command"
    GATE_CHECK = "gate_check"
    USER_INPUT = "user_input"
    TOOL_CALL = "tool_call"


class StepStatus(Enum):
    """Execution status of a step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class OnFailure(Enum):
    """Action to take when a step fails."""

    ABORT = "abort"
    RETRY = "retry"
    SKIP = "skip"
    ASK = "ask"


@dataclass
class UserInputOption:
    """Option for user input step."""

    id: str
    label: str
    description: str = ""


@dataclass
class Step:
    """A single step in a skill workflow."""

    id: str
    name: str
    type: StepType
    prompt_ref: str = ""
    command: str = ""
    validation: str = ""
    on_failure: OnFailure = OnFailure.ABORT
    options: list[UserInputOption] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    timeout: int = 120  # seconds

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Step":
        """Create Step from dictionary."""
        step_type = StepType(data.get("type", "command"))
        on_failure = OnFailure(data.get("on_failure", "abort"))

        options = []
        if "options" in data:
            for opt in data["options"]:
                options.append(
                    UserInputOption(
                        id=opt.get("id", ""),
                        label=opt.get("label", ""),
                        description=opt.get("description", ""),
                    )
                )

        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            type=step_type,
            prompt_ref=data.get("prompt_ref", ""),
            command=data.get("command", ""),
            validation=data.get("validation", ""),
            on_failure=on_failure,
            options=options,
            dependencies=data.get("dependencies", []),
            timeout=data.get("timeout", 120),
        )


@dataclass
class StepResult:
    """Result of executing a step."""

    step_id: str
    status: StepStatus
    output: str = ""
    error: str = ""
    duration: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GateResult:
    """Result of a gate check."""

    passed: bool
    message: str = ""
    validation_output: str = ""
    action_taken: OnFailure = OnFailure.ABORT


@dataclass
class Trigger:
    """Trigger conditions for a skill."""

    commands: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


@dataclass
class SkillConfig:
    """Configuration for a skill."""

    name: str
    version: str
    description: str = ""
    triggers: Trigger = field(default_factory=Trigger)
    steps: list[Step] = field(default_factory=list)
    prompts: dict[str, str] = field(default_factory=dict)
    source_file: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any], source_file: str = "") -> "SkillConfig":
        """Create SkillConfig from dictionary."""
        triggers = Trigger(
            commands=data.get("triggers", {}).get("commands", []),
            keywords=data.get("triggers", {}).get("keywords", []),
        )

        steps = []
        for step_data in data.get("steps", []):
            steps.append(Step.from_dict(step_data))

        return cls(
            name=data.get("name", ""),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            triggers=triggers,
            steps=steps,
            prompts=data.get("prompts", {}),
            source_file=source_file,
        )

    def get_step(self, step_id: str) -> Step | None:
        """Get step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None


@dataclass
class Instruction:
    """Instruction for Claude Code or CLI to execute."""

    version: str = "1.0"
    skill_id: str = ""
    current_step: dict[str, str] = field(default_factory=dict)
    instruction_type: str = ""  # bash, read, write, prompt, user_input
    content: str = ""
    gate_check: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "skill_id": self.skill_id,
            "current_step": self.current_step,
            "instruction": {
                "type": self.instruction_type,
                "content": self.content,
            },
            "gate_check": self.gate_check,
        }
