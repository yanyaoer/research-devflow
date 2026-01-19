"""Gate check implementation - validates step conditions before proceeding."""

import subprocess
import sys
from dataclasses import dataclass
from typing import Callable

from .context import Context
from .types import GateResult, OnFailure, Step


@dataclass
class GateChecker:
    """Executes gate checks and handles failures.

    Gate checks are validation steps that must pass before proceeding.
    They can abort, retry, skip, or ask the user on failure.
    """

    context: Context
    notify_callback: Callable[[str, str], None] | None = None
    dry_run: bool = False

    def check(self, step: Step) -> GateResult:
        """Execute a gate check for a step.

        Args:
            step: The step with gate_check type.

        Returns:
            GateResult indicating pass/fail and action taken.
        """
        if not step.validation:
            return GateResult(
                passed=True,
                message="No validation command specified",
            )

        # Interpolate variables in the validation command
        command = self.context.interpolate(step.validation)

        if self.dry_run:
            return GateResult(
                passed=True,
                message=f"[DRY RUN] Would execute: {command}",
                validation_output="",
            )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=step.timeout,
            )

            passed = result.returncode == 0
            output = result.stdout.strip() or result.stderr.strip()

            if passed:
                return GateResult(
                    passed=True,
                    message=f"Gate check passed: {step.name}",
                    validation_output=output,
                )
            else:
                return self._handle_failure(step, output, result.stderr)

        except subprocess.TimeoutExpired:
            return self._handle_failure(
                step,
                f"Command timed out after {step.timeout}s",
                "Timeout",
            )
        except Exception as e:
            return self._handle_failure(step, str(e), str(e))

    def _handle_failure(
        self, step: Step, output: str, error: str
    ) -> GateResult:
        """Handle a gate check failure based on the on_failure policy.

        Args:
            step: The failed step.
            output: Command output.
            error: Error message.

        Returns:
            GateResult with appropriate action.
        """
        message = f"Gate check failed: {step.name}\nOutput: {output}"
        if error and error != output:
            message += f"\nError: {error}"

        # Send notification if callback is available
        if self.notify_callback:
            self.notify_callback(
                f"Gate Check Failed: {step.name}",
                message[:200],  # Truncate for notification
            )

        if step.on_failure == OnFailure.SKIP:
            return GateResult(
                passed=False,
                message=f"Gate check failed but skipping: {step.name}",
                validation_output=output,
                action_taken=OnFailure.SKIP,
            )

        if step.on_failure == OnFailure.RETRY:
            return GateResult(
                passed=False,
                message=f"Gate check failed, will retry: {step.name}",
                validation_output=output,
                action_taken=OnFailure.RETRY,
            )

        if step.on_failure == OnFailure.ASK:
            return GateResult(
                passed=False,
                message=f"Gate check failed, asking user: {step.name}",
                validation_output=output,
                action_taken=OnFailure.ASK,
            )

        # Default: ABORT
        return GateResult(
            passed=False,
            message=message,
            validation_output=output,
            action_taken=OnFailure.ABORT,
        )


def send_macos_notification(title: str, message: str) -> bool:
    """Send a macOS notification using osascript.

    Args:
        title: Notification title.
        message: Notification message.

    Returns:
        True if notification was sent successfully.
    """
    if sys.platform != "darwin":
        return False

    try:
        # Escape quotes in the message
        escaped_message = message.replace('"', '\\"').replace("'", "\\'")
        escaped_title = title.replace('"', '\\"').replace("'", "\\'")

        script = (
            f'display notification "{escaped_message}" '
            f'with title "{escaped_title}" sound name "Glass"'
        )

        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5,
        )
        return True
    except Exception:
        return False


def create_gate_checker(
    context: Context,
    dry_run: bool = False,
    enable_notifications: bool = True,
) -> GateChecker:
    """Factory function to create a GateChecker with appropriate callbacks.

    Args:
        context: Execution context.
        dry_run: If True, don't actually execute commands.
        enable_notifications: If True, send system notifications on failure.

    Returns:
        Configured GateChecker instance.
    """
    notify_callback = None
    if enable_notifications:
        notify_callback = send_macos_notification

    return GateChecker(
        context=context,
        notify_callback=notify_callback,
        dry_run=dry_run,
    )
