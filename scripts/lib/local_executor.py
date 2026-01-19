"""Local tool executor - provides file and command tools for standalone CLI mode."""

import fnmatch
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ToolResult:
    """Result of a tool execution."""

    success: bool
    output: str
    error: str = ""


class LocalToolExecutor:
    """Executes local file and command tools.

    Provides a subset of Claude Code's built-in tools for standalone execution.
    """

    def __init__(self, working_dir: str | None = None, timeout: int = 120):
        self.working_dir = working_dir or os.getcwd()
        self.timeout = timeout

    def read_file(self, file_path: str, offset: int = 0, limit: int = 2000) -> ToolResult:
        """Read a file's contents.

        Args:
            file_path: Path to the file (absolute or relative to working_dir).
            offset: Line number to start from (1-based).
            limit: Maximum number of lines to read.

        Returns:
            ToolResult with file contents.
        """
        try:
            path = self._resolve_path(file_path)
            if not path.exists():
                return ToolResult(success=False, output="", error=f"File not found: {file_path}")

            with open(path, encoding="utf-8") as f:
                lines = f.readlines()

            # Apply offset and limit
            start = max(0, offset - 1) if offset > 0 else 0
            end = start + limit

            selected_lines = lines[start:end]

            # Format with line numbers
            output_lines = []
            for i, line in enumerate(selected_lines, start=start + 1):
                output_lines.append(f"{i:6}\t{line.rstrip()}")

            return ToolResult(success=True, output="\n".join(output_lines))

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def write_file(self, file_path: str, content: str) -> ToolResult:
        """Write content to a file.

        Args:
            file_path: Path to the file.
            content: Content to write.

        Returns:
            ToolResult indicating success/failure.
        """
        try:
            path = self._resolve_path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return ToolResult(success=True, output=f"File written: {file_path}")

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def append_file(self, file_path: str, content: str) -> ToolResult:
        """Append content to a file.

        Args:
            file_path: Path to the file.
            content: Content to append.

        Returns:
            ToolResult indicating success/failure.
        """
        try:
            path = self._resolve_path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "a", encoding="utf-8") as f:
                f.write(content)

            return ToolResult(success=True, output=f"Content appended to: {file_path}")

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def glob_files(
        self,
        pattern: str,
        path: str | None = None,
        max_results: int = 1000,
    ) -> ToolResult:
        """Find files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "**/*.py").
            path: Directory to search in (default: working_dir).
            max_results: Maximum number of results.

        Returns:
            ToolResult with matching file paths.
        """
        try:
            search_dir = self._resolve_path(path) if path else Path(self.working_dir)

            if not search_dir.exists():
                return ToolResult(success=False, output="", error=f"Directory not found: {path}")

            matches = []
            for match in search_dir.glob(pattern):
                if match.is_file():
                    matches.append(str(match.relative_to(self.working_dir)))
                    if len(matches) >= max_results:
                        break

            return ToolResult(success=True, output="\n".join(matches))

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def grep_content(
        self,
        pattern: str,
        path: str | None = None,
        glob: str | None = None,
        case_insensitive: bool = False,
        max_results: int = 100,
    ) -> ToolResult:
        """Search for pattern in files.

        Args:
            pattern: Regex pattern to search for.
            path: File or directory to search in.
            glob: Glob pattern to filter files.
            case_insensitive: Whether to ignore case.
            max_results: Maximum number of matches.

        Returns:
            ToolResult with matching lines.
        """
        try:
            search_path = self._resolve_path(path) if path else Path(self.working_dir)
            flags = re.IGNORECASE if case_insensitive else 0
            regex = re.compile(pattern, flags)

            matches = []

            if search_path.is_file():
                files = [search_path]
            else:
                if glob:
                    files = list(search_path.glob(glob))
                else:
                    files = list(search_path.rglob("*"))

            for file_path in files:
                if not file_path.is_file():
                    continue

                # Skip binary files
                try:
                    with open(file_path, encoding="utf-8") as f:
                        for line_num, line in enumerate(f, 1):
                            if regex.search(line):
                                rel_path = file_path.relative_to(self.working_dir)
                                matches.append(f"{rel_path}:{line_num}:{line.rstrip()}")
                                if len(matches) >= max_results:
                                    break
                except (UnicodeDecodeError, PermissionError):
                    continue

                if len(matches) >= max_results:
                    break

            return ToolResult(success=True, output="\n".join(matches))

        except re.error as e:
            return ToolResult(success=False, output="", error=f"Invalid regex: {e}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def run_bash(
        self,
        command: str,
        timeout: int | None = None,
    ) -> ToolResult:
        """Run a bash command.

        Args:
            command: Command to execute.
            timeout: Command timeout in seconds.

        Returns:
            ToolResult with command output.
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                cwd=self.working_dir,
            )

            output = result.stdout.strip()
            error = result.stderr.strip() if result.returncode != 0 else ""

            return ToolResult(
                success=result.returncode == 0,
                output=output,
                error=error,
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout or self.timeout}s",
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def list_directory(self, path: str | None = None) -> ToolResult:
        """List contents of a directory.

        Args:
            path: Directory path (default: working_dir).

        Returns:
            ToolResult with directory listing.
        """
        try:
            dir_path = self._resolve_path(path) if path else Path(self.working_dir)

            if not dir_path.exists():
                return ToolResult(success=False, output="", error=f"Directory not found: {path}")

            if not dir_path.is_dir():
                return ToolResult(success=False, output="", error=f"Not a directory: {path}")

            entries = []
            for entry in sorted(dir_path.iterdir()):
                if entry.is_dir():
                    entries.append(f"{entry.name}/")
                else:
                    entries.append(entry.name)

            return ToolResult(success=True, output="\n".join(entries))

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _resolve_path(self, path: str | None) -> Path:
        """Resolve a path relative to working directory."""
        if path is None:
            return Path(self.working_dir)

        p = Path(path)
        if p.is_absolute():
            return p
        return Path(self.working_dir) / p


# Tool function wrappers for the registry
def make_read_file(executor: LocalToolExecutor):
    def read_file(file_path: str, offset: int = 0, limit: int = 2000) -> str:
        result = executor.read_file(file_path, offset, limit)
        if result.success:
            return result.output
        raise RuntimeError(result.error)

    return read_file


def make_write_file(executor: LocalToolExecutor):
    def write_file(file_path: str, content: str) -> str:
        result = executor.write_file(file_path, content)
        if result.success:
            return result.output
        raise RuntimeError(result.error)

    return write_file


def make_glob(executor: LocalToolExecutor):
    def glob_files(pattern: str, path: str | None = None) -> str:
        result = executor.glob_files(pattern, path)
        if result.success:
            return result.output
        raise RuntimeError(result.error)

    return glob_files


def make_grep(executor: LocalToolExecutor):
    def grep(pattern: str, path: str | None = None, glob: str | None = None) -> str:
        result = executor.grep_content(pattern, path, glob)
        if result.success:
            return result.output
        raise RuntimeError(result.error)

    return grep


def make_bash(executor: LocalToolExecutor):
    def bash(command: str, timeout: int = 120) -> str:
        result = executor.run_bash(command, timeout)
        if result.success:
            return result.output
        raise RuntimeError(f"{result.error}\n{result.output}")

    return bash
