"""LLM client abstraction (Strategy + Factory).

Two concrete strategies: AnthropicClient, OpenAIClient.
Both implement the same minimal `LLMClient` protocol so callers stay agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..core.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


class LLMClient(Protocol):
    """Minimal LLM interface — single-turn completion with optional system prompt."""

    def complete(self, prompt: str, *, system: str | None = None, max_tokens: int = 1024) -> LLMResponse: ...


class AnthropicClient:
    def __init__(self, api_key: str, model: str) -> None:
        # Lazy import to keep startup light when provider is not selected.
        from anthropic import Anthropic

        self._client = Anthropic(api_key=api_key)
        self._model = model

    def complete(self, prompt: str, *, system: str | None = None, max_tokens: int = 1024) -> LLMResponse:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(getattr(b, "text", "") for b in msg.content)
        usage = getattr(msg, "usage", None)
        return LLMResponse(
            text=text,
            model=self._model,
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
        )

    def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        system: str = "",
        max_tokens: int = 4096,
    ) -> dict:
        """Run one step of the tool_use loop. Returns normalised response dict."""
        from anthropic.types import TextBlock, ToolUseBlock

        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            tools=tools,  # type: ignore[arg-type]
            messages=messages,  # type: ignore[arg-type]
        )

        text_parts = []
        tool_uses = []
        for block in response.content:
            if isinstance(block, TextBlock):
                text_parts.append(block.text)
            elif isinstance(block, ToolUseBlock):
                tool_uses.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return {
            "provider": "anthropic",
            "stop_reason": response.stop_reason,  # "end_turn" | "tool_use"
            "text": "\n".join(text_parts),
            "tool_uses": tool_uses,
            # Normalised assistant message ready to append to conversation history
            "assistant_message": {"role": "assistant", "content": response.content},
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }


class OpenAIClient:
    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(self, prompt: str, *, system: str | None = None, max_tokens: int = 1024) -> LLMResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
        )
        text = resp.choices[0].message.content or ""
        usage = resp.usage
        return LLMResponse(
            text=text,
            model=self._model,
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )

    def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        system: str = "",
        max_tokens: int = 4096,
    ) -> dict:
        import json

        oai_tools = self._to_oai_tools(tools)
        oai_messages = self._build_oai_messages(messages, system)

        resp = self._client.chat.completions.create(
            model=self._model,
            messages=oai_messages,  # type: ignore[arg-type]
            tools=oai_tools,  # type: ignore[arg-type]
            max_tokens=max_tokens,
        )
        msg = resp.choices[0].message
        finish_reason = resp.choices[0].finish_reason

        tool_uses = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_uses.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": json.loads(tc.function.arguments),
                })

        assistant_message: dict = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            assistant_message["tool_calls"] = [tc.model_dump() for tc in msg.tool_calls]

        return {
            "provider": "openai",
            "stop_reason": "end_turn" if finish_reason == "stop" else "tool_use",
            "text": msg.content or "",
            "tool_uses": tool_uses,
            "assistant_message": assistant_message,
            "input_tokens": resp.usage.prompt_tokens if resp.usage else 0,
            "output_tokens": resp.usage.completion_tokens if resp.usage else 0,
        }

    @staticmethod
    def _to_oai_tools(tools: list[dict]) -> list[dict]:
        """Convert Anthropic tool schema format to OpenAI function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
                },
            }
            for t in tools
        ]

    @staticmethod
    def _build_oai_messages(messages: list[dict], system: str) -> list[dict]:
        """Prepend system prompt and return messages for OpenAI API."""
        result = []
        if system:
            result.append({"role": "system", "content": system})
        result.extend(messages)
        return result


class NullLLMClient:
    """No-op stub used when no provider is configured (dev / CI)."""

    def complete(self, prompt: str, *, system: str | None = None, max_tokens: int = 1024) -> LLMResponse:
        log.warning(
            "llm_not_configured",
            prompt_preview=prompt[:80],
            has_system=bool(system),
            max_tokens=max_tokens,
        )
        return LLMResponse(text="", model="null")

    def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        system: str = "",
        max_tokens: int = 4096,
    ) -> dict:
        raise RuntimeError("No LLM provider configured")


class GitHubModelsClient(OpenAIClient):
    """GitHub Models endpoint — same API as OpenAI, authenticated with a GitHub PAT.

    Endpoint: https://models.inference.ai.azure.com
    Auth: GitHub Personal Access Token (no sk- prefix, standard ghp_/github_pat_ token)
    Models: gpt-4.1, gpt-4o, gpt-4o-mini, Meta-Llama, Mistral, ...
    """

    _ENDPOINT = "https://models.inference.ai.azure.com"

    def __init__(self, github_token: str, model: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(base_url=self._ENDPOINT, api_key=github_token)
        self._model = model


def build_llm_client(
    provider: str,
    anthropic_key: str,
    anthropic_model: str,
    openai_key: str,
    openai_model: str,
    github_token: str = "",
    github_model: str = "gpt-4.1",
) -> LLMClient:
    """Factory — chooses concrete LLM client based on configuration."""
    if provider == "anthropic" and anthropic_key:
        return AnthropicClient(anthropic_key, anthropic_model)
    if provider == "openai" and openai_key:
        return OpenAIClient(openai_key, openai_model)
    if provider == "github_models" and github_token:
        return GitHubModelsClient(github_token, github_model)
    log.warning("llm_provider_unavailable", provider=provider)
    return NullLLMClient()
