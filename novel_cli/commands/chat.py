from typing import Optional

import typer

from novel_cli.core.chat_session import ChatSession
from novel_cli.core.client import chat_stream, create_client
from novel_cli.core.config import load_config
from novel_cli.utils.display import (
    console,
    print_assistant_header,
    print_error,
    print_help,
    print_info,
    print_streaming_text,
    print_success,
    print_welcome,
    prompt_input,
)

app = typer.Typer(help="进入交互式对话模式")


def _handle_slash_command(cmd: str, session: ChatSession, output_file: Optional[str]) -> Optional[str]:
    parts = cmd.strip().split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if command in ("/quit", "/exit"):
        if output_file:
            session.save(output_file)
            print_success(f"对话已自动保存到 {output_file}")
        raise typer.Exit()

    if command == "/clear":
        session.clear()
        print_success("对话历史已清空")
        return None

    if command == "/save":
        filepath = arg if arg else "novel_output.md"
        path = session.save(filepath)
        print_success(f"对话已保存到 {path}")
        return None

    if command == "/system":
        if not arg:
            print_error("用法: /system <prompt>")
            return None
        session.update_system_prompt(arg)
        print_success("系统提示词已更新")
        return None

    if command == "/help":
        print_help()
        return None

    print_error(f"未知命令: {command}，输入 /help 查看可用命令")
    return None


def _run_chat_loop(session: ChatSession, config, output_file: Optional[str]) -> None:
    print_welcome()

    while True:
        try:
            user_input = prompt_input()
        except (KeyboardInterrupt, EOFError):
            console.print("")
            if output_file:
                session.save(output_file)
                print_success(f"对话已自动保存到 {output_file}")
            print_info("再见！")
            break

        if not user_input.strip():
            continue

        if user_input.strip().startswith("/"):
            result = _handle_slash_command(user_input, session, output_file)
            if result is not None:
                return
            continue

        session.add_user_message(user_input)

        try:
            client = create_client(config)
            print_assistant_header()
            full_response = ""
            for token in chat_stream(client, config.model, session.get_messages()):
                full_response += token
                print_streaming_text(token)
            console.print("")
            session.add_assistant_message(full_response)
        except KeyboardInterrupt:
            console.print("")
            print_info("（响应已中断）")
        except Exception as e:
            print_error(f"请求失败: {e}")
            print_info("请检查网络连接和 API 配置。使用 `novelcraft config show` 查看当前配置。")


@app.callback(invoke_without_command=True)
def chat(
    system: Optional[str] = typer.Option(None, "--system", "-s", help="指定系统提示词"),
    load: Optional[str] = typer.Option(None, "--load", "-l", help="加载已有对话文件"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="自动保存对话到指定文件"),
) -> None:
    config = load_config()

    if not config.api_key:
        print_error("API 密钥未配置")
        print_info("请先配置 API 密钥: novelcraft config set --api-key <your-key>")
        raise typer.Exit(1)

    if load:
        try:
            session = ChatSession.load(load)
            print_success(f"已加载对话: {load}")
        except Exception as e:
            print_error(f"加载对话失败: {e}")
            raise typer.Exit(1)
    else:
        prompt = system or config.system_prompt
        session = ChatSession(system_prompt=prompt)

    _run_chat_loop(session, config, output)
