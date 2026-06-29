import json
import time
from pathlib import Path
from typing import Optional

import typer
from openai import OpenAI

from novel_cli.core.client import chat_stream, create_client
from novel_cli.core.config import load_config
from novel_cli.core.exceptions import APIError
from novel_cli.core.generator import MAX_RETRIES, RETRY_BASE_DELAY, require_api_key
from novel_cli.utils.display import (
    console,
    print_error,
    print_info,
    print_streaming_text,
    print_success,
    print_warning,
)

app = typer.Typer(help="逐章生成长篇小说")


def load_characters(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        print_error(f"人物表文件不存在: {path}")
        raise typer.Exit(1)
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print_error(f"人物表文件格式错误: {e}")
        raise typer.Exit(1)
    if not isinstance(data, list):
        print_error("人物表文件必须是 JSON 数组")
        raise typer.Exit(1)
    for i, ch in enumerate(data):
        if "name" not in ch:
            print_error(f"人物表第 {i + 1} 项缺少必填字段: name")
            raise typer.Exit(1)

    lines = []
    for ch in data:
        parts = [f"【{ch['name']}】"]
        if "role" in ch:
            parts.append(f"角色：{ch['role']}")
        if "age" in ch:
            parts.append(f"年龄：{ch['age']}")
        if "identity" in ch:
            parts.append(f"身份：{ch['identity']}")
        if "personality" in ch:
            parts.append(f"性格：{ch['personality']}")
        if "appearance" in ch:
            parts.append(f"外貌：{ch['appearance']}")
        if "relationships" in ch and isinstance(ch["relationships"], dict):
            rels = "，".join(f"{v}是{k}" for k, v in ch["relationships"].items())
            parts.append(f"关系：{rels}")
        if "background" in ch:
            parts.append(f"背景：{ch['background']}")
        lines.append("；".join(parts))
    return "\n".join(lines)


def generate_chapter(
    client: OpenAI,
    model: str,
    chapter_info: dict[str, object],
    prev_summary: str,
    system_prompt: str,
    words: int,
    temperature: float,
    max_tokens: int,
    max_rounds: int,
    quiet: bool,
    characters: str = "",
) -> tuple[str, int]:
    num = chapter_info["num"]
    title = chapter_info["title"]
    outline = chapter_info["outline"]
    target_chars = words

    characters_block = f"""

人物表（严格遵循，不可自行编造人物姓名、身份、关系）：
{characters}
""" if characters else ""

    if characters:
        user_msg = f"""请创作第{num}章「{title}」的完整正文。

本章大纲：{outline}

{"前文概要：" + prev_summary if prev_summary else "（这是第一章）"}
{characters_block}
要求：
1. 字数不少于{words}字（中文字符），内容丰满，细节丰富
2. 严格按照大纲内容展开
3. 注重场景描写、人物对话、内心活动
4. 保持与前文的连贯性
5. 只输出正文内容，不要输出章节标题以外的元信息
6. 以 "## 第{num}章 {title}" 作为开头
7. 所有人物的姓名、身份、关系必须严格按照人物表，不得自由发挥"""
    else:
        user_msg = f"""请创作第{num}章「{title}」的完整正文。

本章大纲：{outline}

{"前文概要：" + prev_summary if prev_summary else "（这是第一章）"}

要求：
1. 字数不少于{words}字（中文字符），内容丰满，细节丰富
2. 严格按照大纲内容展开
3. 注重场景描写、人物对话、内心活动
4. 保持与前文的连贯性
5. 只输出正文内容，不要输出章节标题以外的元信息
6. 以 "## 第{num}章 {title}" 作为开头"""

    full_content = ""

    for round_idx in range(max_rounds):
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]

        if full_content:
            messages.append({"role": "assistant", "content": full_content})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"当前内容约{len(full_content)}字，请继续创作本章后续内容，"
                        "直到本章完整结束。再写至少1500字。"
                    ),
                }
            )

        chunk_content = ""
        last_error: Optional[Exception] = None
        for attempt in range(MAX_RETRIES):
            try:
                for token in chat_stream(
                    client, model, messages, temperature=temperature, max_tokens=max_tokens
                ):
                    chunk_content += token
                    if not quiet:
                        print_streaming_text(token)
                break
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BASE_DELAY * (2 ** attempt)
                    if not quiet:
                        print_warning(f"第{num}章第{attempt + 1}次失败，{wait}s 后重试...")
                    time.sleep(wait)
                else:
                    print_error(f"第{num}章生成失败（已重试{MAX_RETRIES}次）: {last_error}")
                    print_info(f"可使用 --resume {num} 从本章恢复生成")
                    raise APIError(str(last_error)) from last_error

        full_content += chunk_content

        char_count = len(full_content.replace(" ", "").replace("\n", ""))
        if not quiet:
            console.print(f"\n[dim]  第{num}章 当前字数: {char_count}[/dim]")

        if char_count >= target_chars - 500:
            break

    char_count = len(full_content.replace(" ", "").replace("\n", ""))
    return full_content, char_count


@app.callback(invoke_without_command=True)
def write(
    outline: str = typer.Option(..., "--outline", "-O", help="章节大纲 JSON 文件路径"),
    characters: Optional[str] = typer.Option(None, "--characters", "-C", help="人物表 JSON 文件路径"),
    words: int = typer.Option(3500, "--words", "-w", help="每章目标字数"),
    system: Optional[str] = typer.Option(None, "--system", help="自定义系统提示词"),
    temperature: float = typer.Option(0.85, "--temperature", help="生成温度"),
    max_tokens: int = typer.Option(4096, "--max-tokens", help="每轮最大 token 数"),
    max_rounds: int = typer.Option(3, "--max-rounds", help="每章最大续写轮次"),
    output: str = typer.Option("novel_chapters", "--output", "-o", help="输出目录"),
    resume: int = typer.Option(0, "--resume", help="从指定章节号恢复生成（0 表示从头开始）"),
    json_output: bool = typer.Option(False, "--json", help="JSON 格式输出"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="静默模式"),
) -> None:
    config = load_config()
    require_api_key(config)

    characters_text = ""
    if characters:
        characters_text = load_characters(characters)
        if not quiet:
            print_info(f"已加载人物表: {characters}")

    outline_path = Path(outline)
    if not outline_path.exists():
        print_error(f"大纲文件不存在: {outline}")
        raise typer.Exit(1)

    try:
        chapters = json.loads(outline_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print_error(f"大纲文件格式错误: {e}")
        raise typer.Exit(1)

    if not isinstance(chapters, list):
        print_error("大纲文件必须是 JSON 数组")
        raise typer.Exit(1)

    for i, ch in enumerate(chapters):
        for field in ("num", "title", "outline"):
            if field not in ch:
                print_error(f"大纲第 {i + 1} 项缺少字段: {field}")
                raise typer.Exit(1)

    system_prompt = system or config.system_prompt
    client = create_client(config)
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    total_chars = 0
    all_contents = []
    prev_summary = ""

    if resume > 0:
        for ch in chapters:
            if ch["num"] >= resume:
                break
            ch_file = output_dir / f"chapter_{ch['num']:02d}.txt"
            if ch_file.exists():
                ch_content = ch_file.read_text(encoding="utf-8")
                all_contents.append(ch_content)
                total_chars += len(ch_content.replace(" ", "").replace("\n", ""))
                prev_summary = ch_content[-500:] if len(ch_content) > 500 else ch_content
            else:
                all_contents.append("")

    for ch in chapters:
        if resume > 0 and ch["num"] < resume:
            continue

        if not quiet:
            console.print(
                f"\n[bold cyan]{'=' * 50}[/bold cyan]"
                f"\n[bold cyan]📖 正在生成 第{ch['num']}章「{ch['title']}」...[/bold cyan]"
                f"\n[bold cyan]{'=' * 50}[/bold cyan]"
            )

        content, chars = generate_chapter(
            client=client,
            model=config.model,
            chapter_info=ch,
            prev_summary=prev_summary,
            system_prompt=system_prompt,
            words=words,
            temperature=temperature,
            max_tokens=max_tokens,
            max_rounds=max_rounds,
            quiet=quiet,
            characters=characters_text,
        )

        all_contents.append(content)
        total_chars += chars

        ch_file = output_dir / f"chapter_{ch['num']:02d}.txt"
        ch_file.write_text(content, encoding="utf-8")

        if not quiet:
            print_success(f"第{ch['num']}章完成，共{chars}字，已保存到 {ch_file}")
            console.print(f"[dim]>>> 累计字数: {total_chars}[/dim]")

        prev_summary = content[-500:] if len(content) > 500 else content

    if json_output:
        result = {
            "success": True,
            "total_chars": total_chars,
            "chapters": [
                {
                    "num": ch["num"],
                    "title": ch["title"],
                    "chars": len(
                        all_contents[i].replace(" ", "").replace("\n", "")
                    ),
                    "file": str(output_dir / f"chapter_{ch['num']:02d}.txt").replace("\\", "/"),
                }
                for i, ch in enumerate(chapters)
            ],
        }
        console.print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        novel_path = output_dir / "novel_full.md"
        with open(novel_path, "w", encoding="utf-8") as f:
            for content in all_contents:
                if content:
                    f.write(content.strip() + "\n\n---\n\n")

        if not quiet:
            print_success(f"全部 {len(chapters)} 章生成完毕！总计约 {total_chars} 字")
            print_info(f"完整小说已保存到 {novel_path}")
