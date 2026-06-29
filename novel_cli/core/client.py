from typing import Iterator, Optional

from openai import OpenAI

from novel_cli.core.config import Settings


def create_client(settings: Settings) -> OpenAI:
    return OpenAI(
        api_key=settings.api_key,
        base_url=settings.base_url,
    )


def chat_stream(
    client: OpenAI,
    model: str,
    messages: list[dict],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Iterator[str]:
    kwargs = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    stream = client.chat.completions.create(**kwargs)
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
