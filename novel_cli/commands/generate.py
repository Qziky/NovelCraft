from pathlib import Path
from typing import Optional

import typer

from novel_cli.core.config import load_config
from novel_cli.core.generator import handle_output, require_api_key, run_stream
from novel_cli.utils.display import console, print_error

app = typer.Typer(help="根据大纲生成小说")


@app.callback(invoke_without_command=True)
def generate(
    outline: Optional[str] = typer.Option(None, "--outline", "-O", help="大纲文件路径"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="故事提示（与 --outline 二选一）"),
    words: int = typer.Option(3000, "--words", "-w", help="目标字数"),
    style: Optional[str] = typer.Option(None, "--style", "-s", help="写作风格"),
    system: Optional[str] = typer.Option(None, "--system", help="自定义系统提示词"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    json_output: bool = typer.Option(False, "--json", help="JSON 格式输出"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="静默模式"),
) -> None:
    config = load_config()
    require_api_key(config)

    if not outline and not prompt:
        print_error("请提供大纲文件 (--outline) 或故事提示 (--prompt)")
        raise typer.Exit(1)

    system_prompt = system or config.system_prompt

    if outline:
        try:
            outline_content = Path(outline).read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            print_error(f"大纲文件不存在: {outline}")
            raise typer.Exit(1)
        except PermissionError:
            print_error(f"无权限读取文件: {outline}")
            raise typer.Exit(1)
        except UnicodeDecodeError as e:
            print_error(f"文件编码错误: {e}")
            raise typer.Exit(1)

        user_prompt = f"""请根据以下大纲生成完整的小说：

大纲：
{outline_content}

要求：
1. 目标字数：{words} 字左右
2. 分章节写作，每章有标题
3. 语言优美，情节紧凑
4. 人物形象鲜明"""
    else:
        user_prompt = f"""请根据以下概念生成一个完整的小说：

概念：{prompt}

要求：
1. 目标字数：{words} 字左右
2. 分章节写作，每章有标题
3. 语言优美，情节紧凑
4. 人物形象鲜明
5. 有完整的开头、发展、高潮、结局"""

    if style:
        user_prompt += f"\n6. 写作风格：{style}"

    if not quiet:
        console.print(f"[bold cyan]📖 正在生成小说（目标 {words} 字）...[/bold cyan]")

    full_response = run_stream(user_prompt, system_prompt, config, quiet)

    result_data = {
        "success": True,
        "content": full_response,
        "words": len(full_response),
        "target_words": words,
        "style": style,
    }
    handle_output(full_response, output, json_output, result_data, quiet)
