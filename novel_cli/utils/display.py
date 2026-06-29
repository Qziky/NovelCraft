from typing import cast

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

custom_theme = Theme({
    "user": "bold cyan",
    "assistant": "bold green",
    "error": "bold red",
    "info": "dim white",
    "command": "bold yellow",
    "success": "bold green",
})

console = Console(theme=custom_theme)


def print_error(message: str) -> None:
    console.print(f"[error]❌ 错误: {message}[/error]")


def print_info(message: str) -> None:
    console.print(f"[info]ℹ️  {message}[/info]")


def print_success(message: str) -> None:
    console.print(f"[success]✅ {message}[/success]")


def print_streaming_text(text: str) -> None:
    console.print(text, end="")


def print_warning(message: str) -> None:
    console.print(f"[warning]⚠️  {message}[/warning]")


def print_welcome() -> None:
    welcome = Text()
    welcome.append("NovelCraft 对话模式", style="bold magenta")
    welcome.append("\n\n")
    welcome.append("输入内容开始对话，使用斜杠命令控制会话：\n")
    welcome.append("  /help    查看帮助\n", style="command")
    welcome.append("  /clear   清空对话历史\n", style="command")
    welcome.append("  /save    保存对话\n", style="command")
    welcome.append("  /system  修改系统提示词\n", style="command")
    welcome.append("  /quit    退出\n", style="command")
    welcome.append("\n按 Ctrl+C 退出", style="info")
    console.print(Panel(welcome, border_style="magenta"))


def print_assistant_header() -> None:
    console.print("\n[assistant]🤖 AI:[/assistant]")


def print_help() -> None:
    lines = Text()
    lines.append("可用命令：\n\n", style="bold")
    lines.append("  /quit, /exit", style="command")
    lines.append("  退出对话\n")
    lines.append("  /clear", style="command")
    lines.append("        清空对话历史\n")
    lines.append("  /save [文件名]", style="command")
    lines.append("  保存对话到文件（默认 novel_output.md）\n")
    lines.append("  /system <提示词>", style="command")
    lines.append("  修改系统提示词\n")
    lines.append("  /help", style="command")
    lines.append("         显示此帮助\n")
    console.print(Panel(lines, title="帮助", border_style="yellow"))


def prompt_input(prompt: str = "👤 You: ") -> str:
    return cast(str, console.input(f"[user]{prompt}[/user]"))
