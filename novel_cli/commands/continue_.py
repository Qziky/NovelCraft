from pathlib import Path
from typing import Optional

import typer

from novel_cli.core.config import load_config
from novel_cli.core.generator import handle_output, require_api_key, run_stream
from novel_cli.utils.display import console, print_error

app = typer.Typer(help="续写已有内容")


@app.callback(invoke_without_command=True)
def continue_(
    input: str = typer.Option(..., "--input", "-i", help="已有内容文件路径"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="续写方向提示"),
    words: int = typer.Option(2000, "--words", "-w", help="续写字数"),
    system: Optional[str] = typer.Option(None, "--system", help="自定义系统提示词"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    json_output: bool = typer.Option(False, "--json", help="JSON 格式输出"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="静默模式"),
) -> None:
    config = load_config()
    require_api_key(config)

    try:
        existing_content = Path(input).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        print_error(f"文件不存在: {input}")
        raise typer.Exit(1)
    except PermissionError:
        print_error(f"无权限读取文件: {input}")
        raise typer.Exit(1)
    except UnicodeDecodeError as e:
        print_error(f"文件编码错误: {e}")
        raise typer.Exit(1)

    if not existing_content:
        print_error("输入文件为空")
        raise typer.Exit(1)

    system_prompt = system or config.system_prompt

    user_prompt = f"""请续写以下内容：

已有内容：
{existing_content}

要求：
1. 续写 {words} 字左右
2. 保持与原有内容风格一致
3. 情节自然衔接
4. 语言优美，情节紧凑"""

    if prompt:
        user_prompt += f"\n5. 续写方向：{prompt}"

    if not quiet:
        console.print(f"[bold cyan]✍️  正在续写（目标 {words} 字）...[/bold cyan]")

    full_response = run_stream(user_prompt, system_prompt, config, quiet)

    result_data = {
        "success": True,
        "continuation": full_response,
        "original_file": input,
        "words": len(full_response),
        "target_words": words,
    }
    handle_output(full_response, output, json_output, result_data, quiet)
