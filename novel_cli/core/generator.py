import json
import time
from pathlib import Path
from typing import Optional

import typer

from novel_cli.core.chat_session import ChatSession
from novel_cli.core.client import chat_stream, create_client
from novel_cli.core.config import Settings
from novel_cli.core.exceptions import APIConnectionError, APIError, APIRateLimitError
from novel_cli.utils.display import (
    console,
    print_error,
    print_info,
    print_streaming_text,
    print_success,
    print_warning,
)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0


def require_api_key(config: Settings) -> None:
    if not config.api_key:
        print_error("API 密钥未配置")
        print_info("请先配置 API 密钥: novelcraft config set --api-key <your-key>")
        raise typer.Exit(1)


def _classify_api_error(exc: Exception) -> type[APIError]:
    err_str = str(exc).lower()
    if "rate" in err_str or "limit" in err_str or "429" in err_str:
        return APIRateLimitError
    if "connect" in err_str or "timeout" in err_str or "timed out" in err_str:
        return APIConnectionError
    return APIError


def run_stream(
    user_prompt: str,
    system_prompt: str,
    config: Settings,
    quiet: bool = False,
    max_retries: int = MAX_RETRIES,
    retry_base_delay: float = RETRY_BASE_DELAY,
) -> str:
    session = ChatSession(system_prompt=system_prompt)
    session.add_user_message(user_prompt)
    client = create_client(config)

    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        full_response = ""
        try:
            for token in chat_stream(client, config.model, session.get_messages()):
                full_response += token
                if not quiet:
                    print_streaming_text(token)
            if not quiet:
                console.print("")
            return full_response
        except Exception as e:
            last_error = e
            error_class = _classify_api_error(e)
            if attempt < max_retries - 1:
                delay = retry_base_delay * (2 ** attempt)
                if not quiet:
                    print_warning(f"API 调用失败，{delay}s 后重试 ({attempt + 1}/{max_retries})...")
                time.sleep(delay)
            else:
                raise APIError(f"API 调用失败（已重试 {max_retries} 次）: {last_error}") from last_error

    return ""


def handle_output(
    content: str,
    output: Optional[str],
    json_output: bool,
    result_data: dict,
    quiet: bool,
) -> None:
    if json_output:
        json_str = json.dumps(result_data, ensure_ascii=False, indent=2)
        if output:
            Path(output).write_text(json_str, encoding="utf-8")
            if not quiet:
                print_success(f"已保存到 {output}")
        else:
            console.print(json_str)
    else:
        if output:
            Path(output).write_text(content, encoding="utf-8")
            if not quiet:
                print_success(f"已保存到 {output}")
        elif not quiet:
            console.print(content)
