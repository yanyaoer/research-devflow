"""Step executor base classes and registry."""

import subprocess
import time
from abc import ABC, abstractmethod
from typing import Any

from .context import Context
from .gate_checker import GateChecker
from .types import (
    Instruction,
    OnFailure,
    SkillConfig,
    Step,
    StepResult,
    StepStatus,
    StepType,
)


class StepExecutor(ABC):
    """Abstract base class for step executors."""

    @abstractmethod
    def can_handle(self, step: Step) -> bool:
        """Check if this executor can handle the given step type."""
        pass

    @abstractmethod
    def execute(
        self,
        step: Step,
        context: Context,
        skill_config: SkillConfig,
        dry_run: bool = False,
    ) -> StepResult:
        """Execute a step and return the result."""
        pass

    def generate_instruction(
        self,
        step: Step,
        context: Context,
        skill_config: SkillConfig,
    ) -> Instruction:
        """Generate an instruction for Claude Code/CLI to execute.

        Override this for step types that need special instruction generation.
        """
        return Instruction(
            skill_id=skill_config.name,
            current_step={"id": step.id, "name": step.name},
            instruction_type=step.type.value,
            content="",
        )


class CommandExecutor(StepExecutor):
    """Executor for shell command steps."""

    def can_handle(self, step: Step) -> bool:
        return step.type == StepType.COMMAND

    def execute(
        self,
        step: Step,
        context: Context,
        skill_config: SkillConfig,
        dry_run: bool = False,
    ) -> StepResult:
        start_time = time.time()

        # Interpolate variables in the command
        command = context.interpolate(step.command)

        if dry_run:
            return StepResult(
                step_id=step.id,
                status=StepStatus.COMPLETED,
                output=f"[DRY RUN] Would execute: {command}",
                duration=time.time() - start_time,
            )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=step.timeout,
            )

            status = StepStatus.COMPLETED if result.returncode == 0 else StepStatus.FAILED
            output = result.stdout.strip()
            error = result.stderr.strip() if result.returncode != 0 else ""

            return StepResult(
                step_id=step.id,
                status=status,
                output=output,
                error=error,
                duration=time.time() - start_time,
                metadata={"return_code": result.returncode},
            )

        except subprocess.TimeoutExpired:
            return StepResult(
                step_id=step.id,
                status=StepStatus.FAILED,
                error=f"Command timed out after {step.timeout}s",
                duration=time.time() - start_time,
            )
        except Exception as e:
            return StepResult(
                step_id=step.id,
                status=StepStatus.FAILED,
                error=str(e),
                duration=time.time() - start_time,
            )

    def generate_instruction(
        self,
        step: Step,
        context: Context,
        skill_config: SkillConfig,
    ) -> Instruction:
        command = context.interpolate(step.command)
        return Instruction(
            skill_id=skill_config.name,
            current_step={"id": step.id, "name": step.name},
            instruction_type="bash",
            content=command,
        )


class GateCheckExecutor(StepExecutor):
    """Executor for gate check steps."""

    def __init__(self, gate_checker: GateChecker | None = None):
        self.gate_checker = gate_checker

    def can_handle(self, step: Step) -> bool:
        return step.type == StepType.GATE_CHECK

    def execute(
        self,
        step: Step,
        context: Context,
        skill_config: SkillConfig,
        dry_run: bool = False,
    ) -> StepResult:
        start_time = time.time()

        checker = self.gate_checker
        if checker is None:
            from .gate_checker import create_gate_checker

            checker = create_gate_checker(context, dry_run=dry_run)

        result = checker.check(step)

        if result.passed:
            return StepResult(
                step_id=step.id,
                status=StepStatus.COMPLETED,
                output=result.validation_output,
                duration=time.time() - start_time,
                metadata={"gate_passed": True},
            )

        # Handle different failure actions
        if result.action_taken == OnFailure.SKIP:
            return StepResult(
                step_id=step.id,
                status=StepStatus.SKIPPED,
                output=result.message,
                duration=time.time() - start_time,
                metadata={"gate_passed": False, "action": "skip"},
            )

        if result.action_taken == OnFailure.ASK:
            # Ask user whether to continue
            print(f"\n⚠️  {result.message}")
            print(f"Output: {result.validation_output[:200] if result.validation_output else 'none'}")
            try:
                response = input("\nContinue anyway? [y/N]: ").strip().lower()
                if response in ("y", "yes"):
                    return StepResult(
                        step_id=step.id,
                        status=StepStatus.COMPLETED,
                        output=f"User chose to continue despite gate failure",
                        duration=time.time() - start_time,
                        metadata={"gate_passed": False, "action": "ask", "user_choice": "continue"},
                    )
            except (EOFError, KeyboardInterrupt):
                pass

            return StepResult(
                step_id=step.id,
                status=StepStatus.FAILED,
                error=f"User aborted: {result.message}",
                output=result.validation_output,
                duration=time.time() - start_time,
                metadata={"gate_passed": False, "action": "ask", "user_choice": "abort"},
            )

        return StepResult(
            step_id=step.id,
            status=StepStatus.FAILED,
            error=result.message,
            output=result.validation_output,
            duration=time.time() - start_time,
            metadata={"gate_passed": False, "action": result.action_taken.value},
        )

    def generate_instruction(
        self,
        step: Step,
        context: Context,
        skill_config: SkillConfig,
    ) -> Instruction:
        command = context.interpolate(step.validation)
        return Instruction(
            skill_id=skill_config.name,
            current_step={"id": step.id, "name": step.name},
            instruction_type="bash",
            content=command,
            gate_check={
                "enabled": True,
                "validation_command": command,
                "on_failure": step.on_failure.value,
            },
        )


class UserInputExecutor(StepExecutor):
    """Executor for user input steps.

    In CLI mode, prompts the user for input.
    In Claude Code mode, generates AskUserQuestion instruction.
    """

    def can_handle(self, step: Step) -> bool:
        return step.type == StepType.USER_INPUT

    def execute(
        self,
        step: Step,
        context: Context,
        skill_config: SkillConfig,
        dry_run: bool = False,
    ) -> StepResult:
        start_time = time.time()

        if dry_run:
            return StepResult(
                step_id=step.id,
                status=StepStatus.COMPLETED,
                output=f"[DRY RUN] Would ask user: {step.name}",
                duration=time.time() - start_time,
                metadata={"options": [o.id for o in step.options]},
            )

        # In CLI mode, prompt for input
        print(f"\n{step.name}")
        for i, option in enumerate(step.options, 1):
            desc = f" - {option.description}" if option.description else ""
            print(f"  {i}. {option.label}{desc}")

        try:
            choice = input("\nEnter choice (number): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(step.options):
                selected = step.options[idx]
                context.set(f"user_input_{step.id}", selected.id)
                return StepResult(
                    step_id=step.id,
                    status=StepStatus.COMPLETED,
                    output=selected.id,
                    duration=time.time() - start_time,
                    metadata={"selected": selected.id, "label": selected.label},
                )
            else:
                return StepResult(
                    step_id=step.id,
                    status=StepStatus.FAILED,
                    error="Invalid choice",
                    duration=time.time() - start_time,
                )
        except (ValueError, KeyboardInterrupt):
            return StepResult(
                step_id=step.id,
                status=StepStatus.FAILED,
                error="Input cancelled or invalid",
                duration=time.time() - start_time,
            )

    def generate_instruction(
        self,
        step: Step,
        context: Context,
        skill_config: SkillConfig,
    ) -> Instruction:
        options = [
            {"id": o.id, "label": o.label, "description": o.description}
            for o in step.options
        ]
        return Instruction(
            skill_id=skill_config.name,
            current_step={"id": step.id, "name": step.name},
            instruction_type="user_input",
            content=step.name,
            gate_check={"options": options},
        )


class PromptExecutor(StepExecutor):
    """Executor for prompt steps (LLM calls)."""

    def __init__(self, provider=None, tool_registry=None):
        """Initialize with optional LLM provider and tool registry.

        Args:
            provider: LLM provider instance (from llm_provider.py).
            tool_registry: Tool registry for tool calling (from tool_registry.py).
        """
        self.provider = provider
        self.tool_registry = tool_registry

    def can_handle(self, step: Step) -> bool:
        return step.type == StepType.PROMPT

    def execute(
        self,
        step: Step,
        context: Context,
        skill_config: SkillConfig,
        dry_run: bool = False,
    ) -> StepResult:
        start_time = time.time()

        # Get prompt content
        prompt_content = ""
        if step.prompt_ref:
            ref = step.prompt_ref.lstrip("#")
            prompt_content = skill_config.prompts.get(ref, "")

        if not prompt_content:
            return StepResult(
                step_id=step.id,
                status=StepStatus.FAILED,
                error=f"Prompt not found: {step.prompt_ref}",
                duration=time.time() - start_time,
            )

        if dry_run:
            interpolated = context.interpolate(prompt_content)
            return StepResult(
                step_id=step.id,
                status=StepStatus.COMPLETED,
                output=f"[DRY RUN] Would execute prompt: {step.name}\n\nPrompt preview:\n{interpolated[:500]}...",
                duration=time.time() - start_time,
                metadata={"prompt_ref": step.prompt_ref, "prompt_length": len(interpolated)},
            )

        # Check if provider is available
        if self.provider is None:
            return StepResult(
                step_id=step.id,
                status=StepStatus.FAILED,
                error="No LLM provider configured. Use --provider option or configure in ~/.config/devflow/config.yml",
                duration=time.time() - start_time,
                metadata={"prompt_ref": step.prompt_ref, "requires_llm": True},
            )

        # Execute prompt using LLM provider
        try:
            from .prompt_executor import execute_prompt_step

            result = execute_prompt_step(
                step=step,
                context=context,
                skill_config=skill_config,
                provider=self.provider,
                tool_registry=self.tool_registry,
            )
            return result

        except Exception as e:
            return StepResult(
                step_id=step.id,
                status=StepStatus.FAILED,
                error=f"LLM execution failed: {e}",
                duration=time.time() - start_time,
            )

    def generate_instruction(
        self,
        step: Step,
        context: Context,
        skill_config: SkillConfig,
    ) -> Instruction:
        prompt_content = ""
        if step.prompt_ref:
            ref = step.prompt_ref.lstrip("#")
            prompt_content = skill_config.prompts.get(ref, "")
            prompt_content = context.interpolate(prompt_content)

        return Instruction(
            skill_id=skill_config.name,
            current_step={"id": step.id, "name": step.name},
            instruction_type="prompt",
            content=prompt_content,
        )


class ExecutorRegistry:
    """Registry of step executors."""

    def __init__(self, provider=None, tool_registry=None):
        """Initialize registry with optional LLM provider.

        Args:
            provider: LLM provider instance for prompt execution.
            tool_registry: Tool registry for tool calling.
        """
        self.provider = provider
        self.tool_registry = tool_registry
        self._executors: list[StepExecutor] = []
        self._register_defaults()

    def _register_defaults(self):
        """Register default executors."""
        self._executors = [
            CommandExecutor(),
            GateCheckExecutor(),
            UserInputExecutor(),
            PromptExecutor(provider=self.provider, tool_registry=self.tool_registry),
        ]

    def set_provider(self, provider, tool_registry=None):
        """Set or update the LLM provider.

        Args:
            provider: LLM provider instance.
            tool_registry: Optional tool registry.
        """
        self.provider = provider
        if tool_registry:
            self.tool_registry = tool_registry
        # Re-register to update PromptExecutor
        self._register_defaults()

    def register(self, executor: StepExecutor):
        """Register a custom executor."""
        self._executors.insert(0, executor)

    def get_executor(self, step: Step) -> StepExecutor | None:
        """Get an executor that can handle the given step."""
        for executor in self._executors:
            if executor.can_handle(step):
                return executor
        return None

    def execute_step(
        self,
        step: Step,
        context: Context,
        skill_config: SkillConfig,
        dry_run: bool = False,
    ) -> StepResult:
        """Execute a step using the appropriate executor."""
        executor = self.get_executor(step)
        if executor is None:
            return StepResult(
                step_id=step.id,
                status=StepStatus.FAILED,
                error=f"No executor found for step type: {step.type}",
            )

        return executor.execute(step, context, skill_config, dry_run)

    def generate_instruction(
        self,
        step: Step,
        context: Context,
        skill_config: SkillConfig,
    ) -> Instruction:
        """Generate an instruction for a step."""
        executor = self.get_executor(step)
        if executor is None:
            return Instruction(
                skill_id=skill_config.name,
                current_step={"id": step.id, "name": step.name},
                instruction_type="unknown",
                content=f"Unknown step type: {step.type}",
            )

        return executor.generate_instruction(step, context, skill_config)
