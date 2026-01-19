"""Tool registry - manages available tools for LLM tool calling."""

from dataclasses import dataclass, field
from typing import Any, Callable

from .context import Context


@dataclass
class ToolDefinition:
    """Definition of a tool for LLM calling."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., str]
    required_params: list[str] = field(default_factory=list)


class ToolRegistry:
    """Registry of tools available for LLM tool calling."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[..., str],
        required_params: list[str] | None = None,
    ) -> None:
        """Register a tool.

        Args:
            name: Tool name.
            description: Tool description for the LLM.
            parameters: JSON Schema for parameters.
            handler: Function to call when tool is invoked.
            required_params: List of required parameter names.
        """
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            required_params=required_params or [],
        )

    def get_tool(self, name: str) -> ToolDefinition | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get tool schemas in OpenAI function calling format."""
        schemas = []
        for tool in self._tools.values():
            schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": tool.required_params,
                    },
                },
            }
            schemas.append(schema)
        return schemas

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        context: Context | None = None,
    ) -> str:
        """Execute a tool by name.

        Args:
            name: Tool name.
            arguments: Tool arguments.
            context: Optional execution context.

        Returns:
            Tool execution result as a string.
        """
        tool = self._tools.get(name)
        if tool is None:
            return f"Error: Unknown tool '{name}'"

        try:
            # Inject context if the handler accepts it
            import inspect

            sig = inspect.signature(tool.handler)
            if "context" in sig.parameters:
                return tool.handler(**arguments, context=context)
            return tool.handler(**arguments)
        except Exception as e:
            return f"Error executing tool '{name}': {e}"


def create_default_registry(working_dir: str | None = None) -> ToolRegistry:
    """Create a registry with default local tools.

    Args:
        working_dir: Working directory for file operations.

    Returns:
        ToolRegistry with file and command tools.
    """
    from .local_executor import (
        LocalToolExecutor,
        make_bash,
        make_glob,
        make_grep,
        make_read_file,
        make_write_file,
    )

    executor = LocalToolExecutor(working_dir=working_dir)
    registry = ToolRegistry()

    # Read file tool
    registry.register(
        name="read_file",
        description="Read the contents of a file. Returns the file content with line numbers.",
        parameters={
            "file_path": {
                "type": "string",
                "description": "Path to the file to read",
            },
            "offset": {
                "type": "integer",
                "description": "Line number to start from (1-based)",
                "default": 0,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of lines to read",
                "default": 2000,
            },
        },
        handler=make_read_file(executor),
        required_params=["file_path"],
    )

    # Write file tool
    registry.register(
        name="write_file",
        description="Write content to a file. Creates parent directories if needed.",
        parameters={
            "file_path": {
                "type": "string",
                "description": "Path to the file to write",
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file",
            },
        },
        handler=make_write_file(executor),
        required_params=["file_path", "content"],
    )

    # Glob tool
    registry.register(
        name="glob",
        description="Find files matching a glob pattern. Returns matching file paths.",
        parameters={
            "pattern": {
                "type": "string",
                "description": "Glob pattern to match (e.g., '**/*.py')",
            },
            "path": {
                "type": "string",
                "description": "Directory to search in (default: current directory)",
            },
        },
        handler=make_glob(executor),
        required_params=["pattern"],
    )

    # Grep tool
    registry.register(
        name="grep",
        description="Search for a regex pattern in files. Returns matching lines with file paths and line numbers.",
        parameters={
            "pattern": {
                "type": "string",
                "description": "Regex pattern to search for",
            },
            "path": {
                "type": "string",
                "description": "File or directory to search in",
            },
            "glob": {
                "type": "string",
                "description": "Glob pattern to filter files (e.g., '*.py')",
            },
        },
        handler=make_grep(executor),
        required_params=["pattern"],
    )

    # Bash tool
    registry.register(
        name="bash",
        description="Execute a bash command and return its output.",
        parameters={
            "command": {
                "type": "string",
                "description": "The bash command to execute",
            },
            "timeout": {
                "type": "integer",
                "description": "Command timeout in seconds (default: 120)",
                "default": 120,
            },
        },
        handler=make_bash(executor),
        required_params=["command"],
    )

    return registry
