from pathlib import Path
from typing import Optional

import typer

from novel_cli.core.config import load_config
from novel_cli.core.generator import handle_output, require_api_key, run_stream
from novel_cli.utils.display import console, print_error

app = typer.Typer(help="编辑/改写已有内容")

ACTION_PROMPTS = {
    "polish": "请对以下内容进行润色，提升文笔和表达，保持原意不变：",
    "shorten": "请将以下内容精简，保留核心情节和关键信息：",
    "expand": "请将以下内容扩写，增加细节描写和情感表达：",
    "rewrite": "请将以下内容改写，保持故事框架但改变叙述方式：",
}


@app.callback(invoke_without_command=True)
def edit(
    input: str = typer.Option(..., "--input", "-i", help="已有内容文件路径"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="编辑指示"),
    action: Optional[str] = typer.Option(None, "--action", "-a", help="预设动作（polish/shorten/expand/rewrite）"),
    words: Optional[int] = typer.Option(None, "--words", "-w", help="目标字数"),
    system: Optional[str] = typer.Option(None, "--system", help="自定义系统提示词"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    json_output: bool = typer.Option(False, "--json", help="JSON 格式输出"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="静默模式"),
) -> None:
    config = load_config()
    require_api_key(config)

    if not prompt and not action:
        print_error("请提供编辑指示 (--prompt) 或预设动作 (--action)")
        raise typer.Exit(1)

    if action and action not in ACTION_PROMPTS:
        print_error(f"未知动作: {action}，可用动作: {', '.join(ACTION_PROMPTS.keys())}")
        raise typer.Exit(1)

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

    if action:
        action_prompt = ACTION_PROMPTS[action]
        user_prompt = f"""{action_prompt}

内容：
{existing_content}

要求：
1. 保持故事的核心框架和主题
2. 语言流畅自然
3. 适合中文读者阅读"""
    else:
        user_prompt = f"""请根据以下指示编辑内容：

指示：{prompt}

内容：
{existing_content}

要求：
1. 保持故事的核心框架和主题
2. 语言流畅自然
3. 适合中文读者阅读"""

    if words:
        user_prompt += f"\n4. 目标字数：{words} 字左右"

    if not quiet:
        action_desc = ACTION_PROMPTS.get(action, "自定义编辑") if action else "自定义编辑"
        console.print(f"[bold cyan]✏️  正在编辑（{action_desc}）...[/bold cyan]")

    full_response = run_stream(user_prompt, system_prompt, config, quiet)

    result_data = {
        "success": True,
        "edited_content": full_response,
        "original_file": input,
        "action": action,
        "words": len(full_response),
        "target_words": words,
    }
    handle_output(full_response, output, json_output, result_data, quiet)
