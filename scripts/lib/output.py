"""Output formatting for skill-runner CLI."""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.syntax import Syntax
    from rich.markdown import Markdown

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class LogLevel(Enum):
    """Log level for output."""

    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    QUIET = 4


@dataclass
class OutputConfig:
    """Configuration for output formatting."""

    level: LogLevel = LogLevel.INFO
    use_rich: bool = True
    json_output: bool = False


class OutputFormatter:
    """Formats and displays output for the CLI."""

    def __init__(self, config: OutputConfig | None = None):
        self.config = config or OutputConfig()
        self._console = Console() if RICH_AVAILABLE and self.config.use_rich else None

    def debug(self, message: str) -> None:
        """Print debug message."""
        if self.config.level.value <= LogLevel.DEBUG.value:
            self._print(f"[DEBUG] {message}", style="dim")

    def info(self, message: str) -> None:
        """Print info message."""
        if self.config.level.value <= LogLevel.INFO.value:
            self._print(message)

    def warning(self, message: str) -> None:
        """Print warning message."""
        if self.config.level.value <= LogLevel.WARNING.value:
            self._print(f"⚠️  {message}", style="yellow")

    def error(self, message: str) -> None:
        """Print error message."""
        if self.config.level.value <= LogLevel.ERROR.value:
            self._print(f"❌ {message}", style="red bold")

    def success(self, message: str) -> None:
        """Print success message."""
        if self.config.level.value <= LogLevel.INFO.value:
            self._print(f"✅ {message}", style="green")

    def _print(self, message: str, style: str | None = None) -> None:
        """Internal print method."""
        if self._console and not self.config.json_output:
            self._console.print(message, style=style)
        else:
            print(message)

    def print_json(self, data: Any) -> None:
        """Print JSON data."""
        if self._console and not self.config.json_output:
            self._console.print_json(data=data)
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False))

    def print_table(
        self,
        title: str,
        columns: list[str],
        rows: list[list[str]],
    ) -> None:
        """Print a formatted table."""
        if self._console and not self.config.json_output:
            table = Table(title=title)
            for col in columns:
                table.add_column(col)
            for row in rows:
                table.add_row(*row)
            self._console.print(table)
        else:
            # Plain text fallback
            print(f"\n{title}")
            print("-" * len(title))
            header = " | ".join(columns)
            print(header)
            print("-" * len(header))
            for row in rows:
                print(" | ".join(row))

    def print_panel(self, content: str, title: str = "") -> None:
        """Print content in a panel."""
        if self._console and not self.config.json_output:
            self._console.print(Panel(content, title=title))
        else:
            print(f"\n=== {title} ===" if title else "")
            print(content)
            print("=" * 40 if title else "")

    def print_code(self, code: str, language: str = "python") -> None:
        """Print syntax-highlighted code."""
        if self._console and not self.config.json_output:
            syntax = Syntax(code, language, theme="monokai", line_numbers=True)
            self._console.print(syntax)
        else:
            print(f"```{language}")
            print(code)
            print("```")

    def print_markdown(self, content: str) -> None:
        """Print rendered markdown."""
        if self._console and not self.config.json_output:
            md = Markdown(content)
            self._console.print(md)
        else:
            print(content)

    def print_skill_list(self, skills: list[dict[str, str]]) -> None:
        """Print a list of skills."""
        columns = ["Name", "Version", "Description"]
        rows = [
            [s.get("name", ""), s.get("version", ""), s.get("description", "")[:50]]
            for s in skills
        ]
        self.print_table("Available Skills", columns, rows)

    def print_step_result(
        self,
        step_name: str,
        status: str,
        output: str = "",
        error: str = "",
        duration: float = 0.0,
    ) -> None:
        """Print the result of a step execution."""
        status_icons = {
            "completed": "✅",
            "failed": "❌",
            "skipped": "⏭️",
            "pending": "⏳",
            "in_progress": "🔄",
        }
        icon = status_icons.get(status, "❓")

        if self.config.json_output:
            self.print_json({
                "step": step_name,
                "status": status,
                "output": output,
                "error": error,
                "duration": duration,
            })
            return

        # Header
        duration_str = f" ({duration:.2f}s)" if duration > 0 else ""
        self._print(f"\n{icon} {step_name} [{status}]{duration_str}")

        # Output
        if output and self.config.level.value <= LogLevel.DEBUG.value:
            self.print_panel(output[:500], "Output")

        # Error
        if error:
            self._print(f"   Error: {error}", style="red")

    def print_execution_summary(
        self,
        skill_name: str,
        total_steps: int,
        completed: int,
        failed: int,
        skipped: int,
        total_duration: float,
    ) -> None:
        """Print execution summary."""
        if self.config.json_output:
            self.print_json({
                "skill": skill_name,
                "total_steps": total_steps,
                "completed": completed,
                "failed": failed,
                "skipped": skipped,
                "duration": total_duration,
            })
            return

        self._print("\n" + "=" * 50)
        self._print(f"Skill: {skill_name}")
        self._print(f"Steps: {completed}/{total_steps} completed")
        if failed > 0:
            self._print(f"Failed: {failed}", style="red")
        if skipped > 0:
            self._print(f"Skipped: {skipped}", style="yellow")
        self._print(f"Duration: {total_duration:.2f}s")
        self._print("=" * 50)

    def create_progress(self) -> Any:
        """Create a progress context manager."""
        if self._console and not self.config.json_output:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self._console,
            )
        return None


def create_formatter(
    verbose: bool = False,
    quiet: bool = False,
    json_output: bool = False,
) -> OutputFormatter:
    """Create an output formatter with the specified settings.

    Args:
        verbose: Enable debug output.
        quiet: Suppress non-error output.
        json_output: Output in JSON format.

    Returns:
        Configured OutputFormatter.
    """
    if quiet:
        level = LogLevel.ERROR
    elif verbose:
        level = LogLevel.DEBUG
    else:
        level = LogLevel.INFO

    config = OutputConfig(
        level=level,
        use_rich=RICH_AVAILABLE and not json_output,
        json_output=json_output,
    )

    return OutputFormatter(config)
