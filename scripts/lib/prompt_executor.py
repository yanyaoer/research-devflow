"""Prompt executor - executes prompt steps using LLM providers."""

import time
from dataclasses import dataclass, field
from typing import Any

from .context import Context
from .llm_provider import LLMMessage, LLMProvider, LLMRequest, LLMResponse, ToolCall
from .tool_registry import ToolRegistry
from .types import SkillConfig, Step, StepResult, StepStatus


@dataclass
class PromptExecutionConfig:
    """Configuration for prompt execution."""

    max_turns: int = 10  # Maximum conversation turns
    max_tool_calls_per_turn: int = 50  # Must respond to ALL tool calls from LLM
    system_prompt: str = ""
    stop_on_error: bool = True


@dataclass
class ConversationState:
    """State of an ongoing conversation."""

    messages: list[LLMMessage] = field(default_factory=list)
    turn_count: int = 0
    tool_call_count: int = 0
    finished: bool = False
    finish_reason: str = ""


class PromptRunner:
    """Runs prompts with tool calling support."""

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry | None = None,
        config: PromptExecutionConfig | None = None,
    ):
        self.provider = provider
        self.tool_registry = tool_registry
        self.config = config or PromptExecutionConfig()

    def run(
        self,
        prompt: str,
        context: Context,
        model: str = "",
    ) -> LLMResponse:
        """Run a single prompt and return the response.

        Args:
            prompt: The prompt to send to the LLM.
            context: Execution context for variable interpolation.
            model: Model to use (or provider default).

        Returns:
            LLM response.
        """
        # Interpolate variables in the prompt
        interpolated_prompt = context.interpolate(prompt)

        messages = [LLMMessage(role="user", content=interpolated_prompt)]

        request = LLMRequest(
            messages=messages,
            model=model,
            system=self.config.system_prompt,
            tools=self._get_tool_schemas() if self.tool_registry else [],
        )

        return self.provider.complete(request)

    def run_with_tools(
        self,
        prompt: str,
        context: Context,
        model: str = "",
    ) -> tuple[str, ConversationState]:
        """Run a prompt with tool calling loop.

        Continues calling tools until the LLM stops or max turns reached.

        Args:
            prompt: Initial prompt.
            context: Execution context.
            model: Model to use.

        Returns:
            Tuple of (final response text, conversation state).
        """
        state = ConversationState()
        interpolated_prompt = context.interpolate(prompt)
        state.messages.append(LLMMessage(role="user", content=interpolated_prompt))

        final_content = ""

        while not state.finished and state.turn_count < self.config.max_turns:
            state.turn_count += 1
            tools = self._get_tool_schemas() if self.tool_registry else []

            request = LLMRequest(
                messages=state.messages,
                model=model,
                system=self.config.system_prompt,
                tools=tools,
            )

            response = self.provider.complete(request)

            # Add assistant message to history
            assistant_msg = LLMMessage(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            )
            state.messages.append(assistant_msg)

            if response.content:
                final_content = response.content

            # Handle tool calls
            if response.tool_calls and self.tool_registry:
                tool_results = self._execute_tool_calls(response.tool_calls, context)

                # Add tool results to messages
                for tc, result in zip(response.tool_calls, tool_results):
                    state.messages.append(LLMMessage(
                        role="tool",
                        content=result,
                        tool_call_id=tc.id,
                        name=tc.name,
                    ))

                state.tool_call_count += len(response.tool_calls)
            else:
                # No tool calls, conversation finished
                state.finished = True
                state.finish_reason = response.finish_reason

        if state.turn_count >= self.config.max_turns:
            state.finish_reason = "max_turns_reached"
            state.finished = True

        return final_content, state

    def _get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get tool schemas in OpenAI format."""
        if not self.tool_registry:
            return []
        return self.tool_registry.get_tool_schemas()

    def _execute_tool_calls(
        self,
        tool_calls: list[ToolCall],
        context: Context,
    ) -> list[str]:
        """Execute tool calls and return results.

        Note: Must respond to ALL tool calls - API requires it.
        """
        results = []
        for tc in tool_calls:
            if self.tool_registry:
                result = self.tool_registry.execute(tc.name, tc.arguments, context)
                results.append(result)
            else:
                results.append(f"Tool not found: {tc.name}")
        return results


def execute_prompt_step(
    step: Step,
    context: Context,
    skill_config: SkillConfig,
    provider: LLMProvider,
    tool_registry: ToolRegistry | None = None,
    model: str = "",
    dry_run: bool = False,
) -> StepResult:
    """Execute a prompt step.

    Args:
        step: The prompt step to execute.
        context: Execution context.
        skill_config: Skill configuration (for prompt references).
        provider: LLM provider to use.
        tool_registry: Optional tool registry for tool calling.
        model: Model to use (or provider default).
        dry_run: If True, don't actually call the LLM.

    Returns:
        Step execution result.
    """
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
            output=f"[DRY RUN] Would execute prompt:\n{interpolated[:500]}...",
            duration=time.time() - start_time,
            metadata={
                "prompt_ref": step.prompt_ref,
                "prompt_length": len(interpolated),
            },
        )

    try:
        runner = PromptRunner(
            provider=provider,
            tool_registry=tool_registry,
        )

        if tool_registry:
            response_text, state = runner.run_with_tools(
                prompt_content,
                context,
                model=model,
            )
            return StepResult(
                step_id=step.id,
                status=StepStatus.COMPLETED,
                output=response_text,
                duration=time.time() - start_time,
                metadata={
                    "prompt_ref": step.prompt_ref,
                    "turns": state.turn_count,
                    "tool_calls": state.tool_call_count,
                    "finish_reason": state.finish_reason,
                },
            )
        else:
            response = runner.run(prompt_content, context, model=model)
            return StepResult(
                step_id=step.id,
                status=StepStatus.COMPLETED,
                output=response.content,
                duration=time.time() - start_time,
                metadata={
                    "prompt_ref": step.prompt_ref,
                    "finish_reason": response.finish_reason,
                    "usage": response.usage,
                },
            )

    except Exception as e:
        return StepResult(
            step_id=step.id,
            status=StepStatus.FAILED,
            error=str(e),
            duration=time.time() - start_time,
        )
