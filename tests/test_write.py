import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer


def _parse_outline(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"大纲文件不存在: {path}")
    try:
        chapters = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"大纲文件格式错误: {e}")
    if not isinstance(chapters, list):
        raise TypeError("大纲文件必须是 JSON 数组")
    for i, ch in enumerate(chapters):
        for field in ("num", "title", "outline"):
            if field not in ch:
                raise KeyError(f"大纲第 {i + 1} 项缺少字段: {field}")
    return chapters


def test_parse_valid_outline(tmp_path):
    outline = [
        {"num": 1, "title": "初遇", "outline": "故事开始"},
        {"num": 2, "title": "抉择", "outline": "冲突升级"},
    ]
    path = tmp_path / "outline.json"
    path.write_text(json.dumps(outline, ensure_ascii=False), encoding="utf-8")

    result = _parse_outline(path)
    assert len(result) == 2
    assert result[0]["num"] == 1
    assert result[1]["title"] == "抉择"


def test_parse_outline_file_not_found(tmp_path):
    path = tmp_path / "nonexistent.json"
    with pytest.raises(FileNotFoundError):
        _parse_outline(path)


def test_parse_outline_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="大纲文件格式错误"):
        _parse_outline(path)


def test_parse_outline_not_array(tmp_path):
    path = tmp_path / "obj.json"
    path.write_text(json.dumps({"num": 1}), encoding="utf-8")
    with pytest.raises(TypeError, match="JSON 数组"):
        _parse_outline(path)


def test_parse_outline_missing_field(tmp_path):
    outline = [{"num": 1, "title": "test"}]
    path = tmp_path / "incomplete.json"
    path.write_text(json.dumps(outline), encoding="utf-8")
    with pytest.raises(KeyError, match="缺少字段: outline"):
        _parse_outline(path)


def test_resume_skips_chapters(tmp_path):
    outline = [
        {"num": 1, "title": "A", "outline": "a"},
        {"num": 2, "title": "B", "outline": "b"},
        {"num": 3, "title": "C", "outline": "c"},
    ]
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    (output_dir / "chapter_01.txt").write_text("第一章内容", encoding="utf-8")
    (output_dir / "chapter_02.txt").write_text("第二章内容", encoding="utf-8")

    resume = 3
    chapters_to_generate = []
    for ch in outline:
        if resume > 0 and ch["num"] < resume:
            continue
        chapters_to_generate.append(ch)

    assert len(chapters_to_generate) == 1
    assert chapters_to_generate[0]["num"] == 3


def test_resume_reads_prev_summary(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    prev_content = "这是第二章的结尾内容，" * 100
    (output_dir / "chapter_02.txt").write_text(prev_content, encoding="utf-8")

    resume = 3
    chapters = [
        {"num": 1, "title": "A", "outline": "a"},
        {"num": 2, "title": "B", "outline": "b"},
        {"num": 3, "title": "C", "outline": "c"},
    ]

    total_chars = 0
    all_contents = []
    prev_summary = ""

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

    assert len(all_contents) == 2
    assert total_chars > 0
    assert len(prev_summary) == 500
    assert prev_summary.endswith("结尾内容，")


def test_resume_missing_file_fills_empty(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    (output_dir / "chapter_01.txt").write_text("第一章", encoding="utf-8")

    chapters = [
        {"num": 1, "title": "A", "outline": "a"},
        {"num": 2, "title": "B", "outline": "b"},
    ]

    all_contents = []
    for ch in chapters:
        if ch["num"] >= 3:
            break
        ch_file = output_dir / f"chapter_{ch['num']:02d}.txt"
        if ch_file.exists():
            all_contents.append(ch_file.read_text(encoding="utf-8"))
        else:
            all_contents.append("")

    assert all_contents[0] == "第一章"
    assert all_contents[1] == ""


def test_chapter_file_naming(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    for num in [1, 2, 10, 16]:
        filepath = output_dir / f"chapter_{num:02d}.txt"
        filepath.write_text(f"第{num}章", encoding="utf-8")

    assert (output_dir / "chapter_01.txt").exists()
    assert (output_dir / "chapter_02.txt").exists()
    assert (output_dir / "chapter_10.txt").exists()
    assert (output_dir / "chapter_16.txt").exists()


def test_novel_full_merge(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    contents = ["## 第1章\n\n内容一", "## 第2章\n\n内容二", "## 第3章\n\n内容三"]
    all_contents = contents[:]

    novel_path = output_dir / "novel_full.md"
    with open(novel_path, "w", encoding="utf-8") as f:
        for content in all_contents:
            if content:
                f.write(content.strip() + "\n\n---\n\n")

    merged = novel_path.read_text(encoding="utf-8")
    assert "第1章" in merged
    assert "第2章" in merged
    assert "第3章" in merged
    assert merged.count("---") == 3


def test_generate_chapter_retry_on_failure():
    from novel_cli.commands.write import generate_chapter

    call_count = 0

    def flaky_stream(client, model, messages, temperature=None, max_tokens=None):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise ConnectionError("模拟网络错误")
        yield "## 第1章 测试\n\n生成的内容足够长"
        yield "，继续添加更多内容以达到字数要求。"

    mock_client = MagicMock()
    chapter_info = {"num": 1, "title": "测试", "outline": "测试大纲"}

    with patch("novel_cli.commands.write.chat_stream", flaky_stream):
        with patch("novel_cli.commands.write.time.sleep"):
            content, chars = generate_chapter(
                client=mock_client,
                model="test-model",
                chapter_info=chapter_info,
                prev_summary="",
                system_prompt="系统提示",
                words=100,
                temperature=0.85,
                max_tokens=4096,
                max_rounds=1,
                quiet=True,
            )
            assert call_count == 3
            assert chars > 0


def test_generate_chapter_exhausts_retries():
    from novel_cli.commands.write import generate_chapter
    from novel_cli.core.exceptions import APIError

    def always_fail(client, model, messages, temperature=None, max_tokens=None):
        raise ConnectionError("持续失败")

    mock_client = MagicMock()
    chapter_info = {"num": 1, "title": "测试", "outline": "测试大纲"}

    with patch("novel_cli.commands.write.chat_stream", always_fail):
        with patch("novel_cli.commands.write.time.sleep"):
            with pytest.raises(APIError):
                generate_chapter(
                    client=mock_client,
                    model="test-model",
                    chapter_info=chapter_info,
                    prev_summary="",
                    system_prompt="系统提示",
                    words=100,
                    temperature=0.85,
                    max_tokens=4096,
                    max_rounds=1,
                    quiet=True,
                )


def test_load_characters_valid(tmp_path):
    from novel_cli.commands.write import load_characters

    chars = [
        {
            "name": "林远",
            "role": "主角",
            "age": 28,
            "identity": "产品经理",
            "personality": "内敛敏锐",
            "relationships": {"林启山": "父亲", "苏晓薇": "青梅竹马"},
        },
        {"name": "苏晓薇", "role": "女主", "age": 26, "identity": "律师"},
    ]
    path = tmp_path / "chars.json"
    path.write_text(json.dumps(chars, ensure_ascii=False), encoding="utf-8")

    result = load_characters(str(path))
    assert "【林远】" in result
    assert "角色：主角" in result
    assert "年龄：28" in result
    assert "身份：产品经理" in result
    assert "性格：内敛敏锐" in result
    assert "父亲是林启山" in result
    assert "青梅竹马是苏晓薇" in result
    assert "【苏晓薇】" in result


def test_load_characters_minimal(tmp_path):
    from novel_cli.commands.write import load_characters

    chars = [{"name": "林远"}]
    path = tmp_path / "chars.json"
    path.write_text(json.dumps(chars, ensure_ascii=False), encoding="utf-8")

    result = load_characters(str(path))
    assert result == "【林远】"


def test_load_characters_missing_name(tmp_path):
    from novel_cli.commands.write import load_characters

    chars = [{"role": "主角"}]
    path = tmp_path / "chars.json"
    path.write_text(json.dumps(chars, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(typer.Exit):
        load_characters(str(path))


def test_load_characters_not_array(tmp_path):
    from novel_cli.commands.write import load_characters

    path = tmp_path / "chars.json"
    path.write_text(json.dumps({"name": "test"}), encoding="utf-8")

    with pytest.raises(typer.Exit):
        load_characters(str(path))


def test_load_characters_file_not_found():
    from novel_cli.commands.write import load_characters

    with pytest.raises(typer.Exit):
        load_characters("/nonexistent/path.json")


def test_load_characters_invalid_json(tmp_path):
    from novel_cli.commands.write import load_characters

    path = tmp_path / "bad.json"
    path.write_text("not json", encoding="utf-8")

    with pytest.raises(typer.Exit):
        load_characters(str(path))


def test_generate_chapter_injects_characters():
    from novel_cli.commands.write import generate_chapter

    captured_messages = []

    def capture_stream(client, model, messages, temperature=None, max_tokens=None):
        captured_messages.extend(messages)
        yield "## 第1章 测试\n\n生成内容足够长，继续添加更多内容。"

    mock_client = MagicMock()
    chapter_info = {"num": 1, "title": "测试", "outline": "测试大纲"}
    characters_text = "【林远】；角色：主角；年龄：28\n【苏晓薇】；角色：女主；年龄：26"

    with patch("novel_cli.commands.write.chat_stream", capture_stream):
        generate_chapter(
            client=mock_client,
            model="test-model",
            chapter_info=chapter_info,
            prev_summary="",
            system_prompt="系统提示",
            words=100,
            temperature=0.85,
            max_tokens=4096,
            max_rounds=1,
            quiet=True,
            characters=characters_text,
        )

    user_msg = captured_messages[1]["content"]
    assert "人物表" in user_msg
    assert "【林远】" in user_msg
    assert "【苏晓薇】" in user_msg
    assert "严格按照人物表" in user_msg


def test_generate_chapter_no_characters():
    from novel_cli.commands.write import generate_chapter

    captured_messages = []

    def capture_stream(client, model, messages, temperature=None, max_tokens=None):
        captured_messages.extend(messages)
        yield "## 第1章 测试\n\n生成内容足够长，继续添加更多内容。"

    mock_client = MagicMock()
    chapter_info = {"num": 1, "title": "测试", "outline": "测试大纲"}

    with patch("novel_cli.commands.write.chat_stream", capture_stream):
        generate_chapter(
            client=mock_client,
            model="test-model",
            chapter_info=chapter_info,
            prev_summary="",
            system_prompt="系统提示",
            words=100,
            temperature=0.85,
            max_tokens=4096,
            max_rounds=1,
            quiet=True,
        )

    user_msg = captured_messages[1]["content"]
    assert "人物表" not in user_msg
    assert "严格按照人物表" not in user_msg
