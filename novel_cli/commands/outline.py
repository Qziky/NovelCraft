from pathlib import Path
from typing import Optional

import typer

from novel_cli.core.config import load_config
from novel_cli.core.generator import handle_output, require_api_key, run_stream
from novel_cli.utils.display import console, print_error

app = typer.Typer(help="生成小说大纲")


@app.callback(invoke_without_command=True)
def outline(
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="故事提示"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="从文件读取提示"),
    style: Optional[str] = typer.Option(None, "--style", "-s", help="写作风格（如：科幻、武侠、言情）"),
    chapters: int = typer.Option(4, "--chapters", "-c", help="预计章节数"),
    system: Optional[str] = typer.Option(None, "--system", help="自定义系统提示词"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    json_output: bool = typer.Option(False, "--json", help="JSON 格式输出"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="静默模式"),
) -> None:
    config = load_config()
    require_api_key(config)

    if file:
        try:
            prompt = Path(file).read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            print_error(f"文件不存在: {file}")
            raise typer.Exit(1)
        except PermissionError:
            print_error(f"无权限读取文件: {file}")
            raise typer.Exit(1)
        except UnicodeDecodeError as e:
            print_error(f"文件编码错误: {e}")
            raise typer.Exit(1)

    if not prompt:
        print_error("请提供故事提示 (--prompt 或 --file)")
        raise typer.Exit(1)

    system_prompt = system or config.system_prompt
    user_prompt = f"""请根据以下概念生成一个小说大纲：

概念：{prompt}

要求：
1. 预计 {chapters} 个章节
2. 包含核心设定、人物设定、章节大纲
3. 有悬念和反转设计
4. 语言简洁明了"""

    if style:
        user_prompt += f"\n5. 写作风格：{style}"

    if not quiet:
        console.print("[bold cyan]📖 正在生成大纲...[/bold cyan]")

    full_response = run_stream(user_prompt, system_prompt, config, quiet)

    result_data = {
        "success": True,
        "outline": full_response,
        "chapters": chapters,
        "style": style,
    }
    handle_output(full_response, output, json_output, result_data, quiet)
