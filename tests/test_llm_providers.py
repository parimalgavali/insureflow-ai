from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from api.agent.schemas import ChatMessage, FollowupOutput
from api.llm.provider import AnthropicProvider, OllamaProvider, ProviderError, make_provider

MESSAGES = [
    ChatMessage(role="system", content="extra system"),
    ChatMessage(role="user", content="Hallo"),
]


class FakeAnthropicClient:
    def __init__(self, content):
        self.content = content
        self.kwargs = None
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            content=self.content, usage=SimpleNamespace(input_tokens=10, output_tokens=5)
        )


def test_anthropic_structured_request_forces_tool_and_merges_system():
    client = FakeAnthropicClient(
        [
            SimpleNamespace(
                type="tool_use", input={"question": "Wann?", "asked_for": ["incident_date"]}
            )
        ]
    )
    provider = AnthropicProvider(model="claude-test", client=client)
    completion = provider.complete(
        MESSAGES, system="main system", response_schema=FollowupOutput, tag="followup"
    )
    req = client.kwargs
    assert req["model"] == "claude-test" and req["temperature"] == 0
    assert req["system"] == "main system\n\nextra system"
    assert req["messages"] == [{"role": "user", "content": "Hallo"}]
    assert req["tool_choice"] == {"type": "tool", "name": "FollowupOutput"}
    assert req["tools"][0]["input_schema"]["properties"]["question"]
    assert isinstance(completion.parsed, FollowupOutput) and completion.parsed.question == "Wann?"
    assert completion.usage == {"input_tokens": 10, "output_tokens": 5}


def test_anthropic_free_text_and_missing_tool_block():
    client = FakeAnthropicClient([SimpleNamespace(type="text", text="Hi there")])
    provider = AnthropicProvider(model="m", client=client)
    assert provider.complete(MESSAGES).text == "Hi there"
    assert "tools" not in client.kwargs
    with pytest.raises(ProviderError, match="no tool_use"):
        provider.complete(MESSAGES, response_schema=FollowupOutput)


def test_anthropic_invalid_tool_payload_raises_provider_error():
    client = FakeAnthropicClient([SimpleNamespace(type="tool_use", input={"asked_for": "nope"})])
    with pytest.raises(ProviderError, match="validation"):
        AnthropicProvider(model="m", client=client).complete(
            MESSAGES, response_schema=FollowupOutput
        )


class FakeHttp:
    def __init__(self, status=200, content='{"question": "When?", "asked_for": []}'):
        self.status, self.content, self.calls = status, content, []

    def post(self, url, json=None):
        self.calls.append((url, json))
        body = {"message": {"role": "assistant", "content": self.content}}
        return SimpleNamespace(status_code=self.status, json=lambda: body, text=self.content)


def test_ollama_request_shape_and_parsing():
    http = FakeHttp()
    provider = OllamaProvider(model="qwen", base_url="http://ollama:11434/", http_client=http)
    completion = provider.complete(
        MESSAGES, system="sys", response_schema=FollowupOutput, max_tokens=99
    )
    url, body = http.calls[0]
    assert url == "http://ollama:11434/api/chat"
    assert body["messages"][0] == {"role": "system", "content": "sys"}
    assert body["messages"][1] == {"role": "system", "content": "extra system"}
    assert body["format"]["properties"]["question"] and body["options"]["num_predict"] == 99
    assert completion.parsed.question == "When?"


def test_ollama_errors():
    with pytest.raises(ProviderError, match="HTTP 500"):
        OllamaProvider(model="m", http_client=FakeHttp(status=500)).complete(MESSAGES)
    with pytest.raises(ProviderError, match="non-JSON"):
        OllamaProvider(model="m", http_client=FakeHttp(content="not json")).complete(
            MESSAGES, response_schema=FollowupOutput
        )


def test_make_provider_unknown():
    with pytest.raises(ValueError, match="unknown LLM_PROVIDER"):
        make_provider("gpt")
    assert json.dumps(
        FollowupOutput.model_json_schema()
    )  # schema is serialisable for both backends
