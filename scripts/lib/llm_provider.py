"""LLM Provider abstraction layer for multiple AI providers."""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Default config path
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "devflow" / "config.yml"


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    api_key: str = ""
    base_url: str = ""
    model: str = ""
    extra_headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderConfig":
        """Create config from dictionary."""
        return cls(
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url", ""),
            model=data.get("model", ""),
            extra_headers=data.get("extra_headers", {}),
        )


def load_config(config_path: Path | str | None = None) -> dict[str, ProviderConfig]:
    """Load provider configurations from YAML file.

    Args:
        config_path: Path to config file. Defaults to ~/.config/devflow/config.yml

    Returns:
        Dictionary mapping provider names to their configurations.
    """
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    if not path.exists():
        return {}

    try:
        import yaml

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        configs = {}
        providers_data = data.get("providers", {})

        for name, provider_data in providers_data.items():
            if isinstance(provider_data, dict):
                configs[name] = ProviderConfig.from_dict(provider_data)

        return configs
    except Exception:
        return {}


def get_provider_config(provider_name: str, config_path: Path | str | None = None) -> ProviderConfig:
    """Get configuration for a specific provider.

    Args:
        provider_name: Name of the provider (openai, anthropic, gemini).
        config_path: Optional path to config file.

    Returns:
        Provider configuration (may be empty if not configured).
    """
    configs = load_config(config_path)
    return configs.get(provider_name, ProviderConfig())


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMMessage:
    """A message in a conversation."""

    role: str  # system, user, assistant, tool
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str = ""  # For tool response messages
    name: str = ""  # For tool response messages

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI API format."""
        msg: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    },
                }
                for tc in self.tool_calls
            ]
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        if self.name:
            msg["name"] = self.name
        return msg

    def to_anthropic_format(self) -> dict[str, Any]:
        """Convert to Anthropic API format."""
        if self.role == "system":
            return {"role": "user", "content": f"[System]: {self.content}"}

        msg: dict[str, Any] = {"role": self.role, "content": self.content}

        if self.tool_calls:
            # Anthropic uses tool_use blocks
            content = []
            if self.content:
                content.append({"type": "text", "text": self.content})
            for tc in self.tool_calls:
                content.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                })
            msg["content"] = content

        return msg


@dataclass
class LLMRequest:
    """Request to an LLM provider."""

    messages: list[LLMMessage]
    model: str = ""
    tools: list[dict[str, Any]] = field(default_factory=list)
    max_tokens: int = 4096
    temperature: float = 0.0
    system: str = ""


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    raw_response: Any = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model for this provider."""
        pass

    @abstractmethod
    def complete(self, request: LLMRequest) -> LLMResponse:
        """Send a completion request to the provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        extra_headers: dict[str, str] | None = None,
        config_path: str | None = None,
    ):
        # Load from config file first
        config = get_provider_config("openai", config_path)

        # Priority: explicit params > config file > environment variables
        self.api_key = api_key or config.api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or config.base_url or os.environ.get("OPENAI_BASE_URL")
        self._model = model or config.model or ""
        self.extra_headers = extra_headers or config.extra_headers or {}
        self._client = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return self._model or "gpt-4o"

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI

                kwargs: dict[str, Any] = {
                    "api_key": self.api_key,
                }
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                if self.extra_headers:
                    kwargs["default_headers"] = self.extra_headers

                self._client = OpenAI(**kwargs)
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        return self._client

    def is_available(self) -> bool:
        return bool(self.api_key)

    def complete(self, request: LLMRequest) -> LLMResponse:
        client = self._get_client()
        model = request.model or self.default_model

        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        for msg in request.messages:
            messages.append(msg.to_openai_format())

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        if request.tools:
            kwargs["tools"] = request.tools

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                ))

        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "",
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            raw_response=response,
        )


class AnthropicProvider(LLMProvider):
    """Anthropic API provider."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        extra_headers: dict[str, str] | None = None,
        config_path: str | None = None,
    ):
        # Load from config file first
        config = get_provider_config("anthropic", config_path)

        # Priority: explicit params > config file > environment variables
        self.api_key = api_key or config.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.base_url = base_url or config.base_url or os.environ.get("ANTHROPIC_BASE_URL")
        self._model = model or config.model or ""
        self.extra_headers = extra_headers or config.extra_headers or {}
        self._client = None

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def default_model(self) -> str:
        return self._model or "claude-sonnet-4-20250514"

    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import Anthropic

                kwargs: dict[str, Any] = {
                    "api_key": self.api_key,
                }
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                if self.extra_headers:
                    kwargs["default_headers"] = self.extra_headers

                self._client = Anthropic(**kwargs)
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
        return self._client

    def is_available(self) -> bool:
        return bool(self.api_key)

    def complete(self, request: LLMRequest) -> LLMResponse:
        client = self._get_client()
        model = request.model or self.default_model

        messages = []
        for msg in request.messages:
            if msg.role != "system":
                messages.append(msg.to_anthropic_format())

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens,
        }

        if request.system:
            kwargs["system"] = request.system

        if request.tools:
            # Convert OpenAI tool format to Anthropic format
            anthropic_tools = []
            for tool in request.tools:
                if tool.get("type") == "function":
                    func = tool["function"]
                    anthropic_tools.append({
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "input_schema": func.get("parameters", {}),
                    })
            if anthropic_tools:
                kwargs["tools"] = anthropic_tools

        response = client.messages.create(**kwargs)

        # Extract content and tool calls
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input,
                ))

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason or "",
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
            raw_response=response,
        )


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        extra_headers: dict[str, str] | None = None,
        config_path: str | None = None,
    ):
        # Load from config file first
        config = get_provider_config("gemini", config_path)

        # Priority: explicit params > config file > environment variables
        self.api_key = api_key or config.api_key or os.environ.get("GOOGLE_API_KEY", "")
        self.base_url = base_url or config.base_url  # Gemini doesn't use base_url in standard SDK
        self._model = model or config.model or ""
        self.extra_headers = extra_headers or config.extra_headers or {}
        self._client = None

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return self._model or "gemini-2.0-flash"

    def _get_client(self):
        if self._client is None:
            try:
                import google.generativeai as genai

                # Configure with extra headers if provided
                transport_options = {}
                if self.extra_headers:
                    transport_options["headers"] = self.extra_headers

                genai.configure(
                    api_key=self.api_key,
                    transport="rest" if transport_options else None,
                )
                self._client = genai
            except ImportError:
                raise ImportError(
                    "google-generativeai package not installed. "
                    "Run: pip install google-generativeai"
                )
        return self._client

    def is_available(self) -> bool:
        return bool(self.api_key)

    def complete(self, request: LLMRequest) -> LLMResponse:
        genai = self._get_client()
        model_name = request.model or self.default_model

        # Combine system and messages
        contents = []
        if request.system:
            contents.append({"role": "user", "parts": [f"[System Instructions]: {request.system}"]})
            contents.append({"role": "model", "parts": ["Understood. I will follow these instructions."]})

        for msg in request.messages:
            role = "user" if msg.role in ("user", "system") else "model"
            contents.append({"role": role, "parts": [msg.content]})

        model = genai.GenerativeModel(model_name)

        # Configure tools if provided
        tools = None
        if request.tools:
            # Convert OpenAI format to Gemini format
            function_declarations = []
            for tool in request.tools:
                if tool.get("type") == "function":
                    func = tool["function"]
                    function_declarations.append({
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {}),
                    })
            if function_declarations:
                tools = [{"function_declarations": function_declarations}]

        generation_config = {
            "max_output_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        response = model.generate_content(
            contents,
            generation_config=generation_config,
            tools=tools,
        )

        # Extract content and tool calls
        content = ""
        tool_calls = []

        if response.candidates:
            candidate = response.candidates[0]
            for part in candidate.content.parts:
                if hasattr(part, "text"):
                    content += part.text
                elif hasattr(part, "function_call"):
                    fc = part.function_call
                    tool_calls.append(ToolCall(
                        id=f"call_{len(tool_calls)}",
                        name=fc.name,
                        arguments=dict(fc.args),
                    ))

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=str(candidate.finish_reason) if response.candidates else "",
            usage={},  # Gemini doesn't provide token counts in the same way
            raw_response=response,
        )


def get_provider(name: str, config_path: str | None = None, **kwargs) -> LLMProvider:
    """Get an LLM provider by name.

    Args:
        name: Provider name (openai, anthropic, gemini).
        config_path: Optional path to config file.
        **kwargs: Provider-specific configuration (overrides config file).

    Returns:
        Configured LLM provider.
    """
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
    }

    if name not in providers:
        raise ValueError(f"Unknown provider: {name}. Available: {list(providers.keys())}")

    return providers[name](config_path=config_path, **kwargs)


def get_available_providers(config_path: str | None = None) -> list[str]:
    """Get list of available (configured) providers.

    Checks both config file and environment variables.

    Args:
        config_path: Optional path to config file.

    Returns:
        List of available provider names.
    """
    available = []

    # Check config file
    configs = load_config(config_path)

    # OpenAI
    if configs.get("openai", ProviderConfig()).api_key or os.environ.get("OPENAI_API_KEY"):
        available.append("openai")

    # Anthropic
    if configs.get("anthropic", ProviderConfig()).api_key or os.environ.get("ANTHROPIC_API_KEY"):
        available.append("anthropic")

    # Gemini
    if configs.get("gemini", ProviderConfig()).api_key or os.environ.get("GOOGLE_API_KEY"):
        available.append("gemini")

    return available
