import json
import re

from typer.testing import CliRunner

from novel_cli.main import app

runner = CliRunner()

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def parse_json_output(result) -> dict:
    return json.loads(strip_ansi(result.output), strict=False)


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "novelcraft" in result.output


def test_help_command():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "NovelCraft" in result.output
    assert "outline" in result.output
    assert "generate" in result.output
    assert "write" in result.output


def test_outline_help():
    result = runner.invoke(app, ["outline", "--help"])
    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert "--prompt" in output
    assert "--chapters" in output


def test_generate_help():
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert "--outline" in output
    assert "--words" in output


def test_write_help():
    result = runner.invoke(app, ["write", "--help"])
    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert "--outline" in output
    assert "--resume" in output
    assert "--characters" in output


def test_continue_help():
    result = runner.invoke(app, ["continue", "--help"])
    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert "--input" in output


def test_edit_help():
    result = runner.invoke(app, ["edit", "--help"])
    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert "--action" in output
    assert "polish" in output


def test_chat_help():
    result = runner.invoke(app, ["chat", "--help"])
    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert "--system" in output


def test_outline_missing_prompt(mock_config):
    result = runner.invoke(app, ["outline"])
    assert result.exit_code != 0
    assert "提示" in result.output or "prompt" in strip_ansi(result.output).lower()


def test_generate_missing_args():
    result = runner.invoke(app, ["generate"])
    assert result.exit_code != 0


def test_continue_missing_input():
    result = runner.invoke(app, ["continue"])
    assert result.exit_code != 0


def test_edit_missing_args():
    result = runner.invoke(app, ["edit"])
    assert result.exit_code != 0


def test_outline_with_prompt(mock_config, monkeypatch):
    def fake_stream(client, model, messages, temperature=None, max_tokens=None):
        yield "# 大纲\n\n第一章：测试章节"

    monkeypatch.setattr("novel_cli.core.generator.chat_stream", fake_stream)
    monkeypatch.setattr("novel_cli.core.generator.create_client", lambda c: None)

    result = runner.invoke(app, ["outline", "--prompt", "一个测试故事", "--quiet", "--json"])
    assert result.exit_code == 0
    data = parse_json_output(result)
    assert data["success"] is True
    assert "outline" in data


def test_generate_from_prompt(mock_config, monkeypatch):
    def fake_stream(client, model, messages, temperature=None, max_tokens=None):
        yield "第一章 测试\n\n这是一个测试故事的开头。"

    monkeypatch.setattr("novel_cli.core.generator.chat_stream", fake_stream)
    monkeypatch.setattr("novel_cli.core.generator.create_client", lambda c: None)

    result = runner.invoke(app, ["generate", "--prompt", "一个测试故事", "--words", "100", "--quiet", "--json"])
    assert result.exit_code == 0
    data = parse_json_output(result)
    assert data["success"] is True
    assert "content" in data


def test_generate_from_outline(mock_config, tmp_path, monkeypatch):
    outline_file = tmp_path / "outline.md"
    outline_file.write_text("# 大纲\n\n第一章测试", encoding="utf-8")

    def fake_stream(client, model, messages, temperature=None, max_tokens=None):
        yield "根据大纲生成的故事内容。"

    monkeypatch.setattr("novel_cli.core.generator.chat_stream", fake_stream)
    monkeypatch.setattr("novel_cli.core.generator.create_client", lambda c: None)

    result = runner.invoke(app, ["generate", "--outline", str(outline_file), "--quiet", "--json"])
    assert result.exit_code == 0
    data = parse_json_output(result)
    assert data["success"] is True


def test_generate_output_to_file(mock_config, tmp_path, monkeypatch):
    output_file = tmp_path / "output.md"

    def fake_stream(client, model, messages, temperature=None, max_tokens=None):
        yield "输出到文件的内容"

    monkeypatch.setattr("novel_cli.core.generator.chat_stream", fake_stream)
    monkeypatch.setattr("novel_cli.core.generator.create_client", lambda c: None)

    result = runner.invoke(app, ["generate", "--prompt", "测试", "--output", str(output_file), "--quiet"])
    assert result.exit_code == 0
    assert output_file.exists()
    assert "输出到文件" in output_file.read_text(encoding="utf-8")


def test_continue_basic(mock_config, tmp_path, monkeypatch):
    input_file = tmp_path / "input.md"
    input_file.write_text("已有内容", encoding="utf-8")

    def fake_stream(client, model, messages, temperature=None, max_tokens=None):
        yield "续写的内容"

    monkeypatch.setattr("novel_cli.core.generator.chat_stream", fake_stream)
    monkeypatch.setattr("novel_cli.core.generator.create_client", lambda c: None)

    result = runner.invoke(app, ["continue", "--input", str(input_file), "--quiet", "--json"])
    assert result.exit_code == 0
    data = parse_json_output(result)
    assert data["success"] is True
    assert "continuation" in data


def test_edit_polish(mock_config, tmp_path, monkeypatch):
    input_file = tmp_path / "input.md"
    input_file.write_text("需要润色的文本", encoding="utf-8")

    def fake_stream(client, model, messages, temperature=None, max_tokens=None):
        yield "润色后的文本"

    monkeypatch.setattr("novel_cli.core.generator.chat_stream", fake_stream)
    monkeypatch.setattr("novel_cli.core.generator.create_client", lambda c: None)

    result = runner.invoke(app, ["edit", "--input", str(input_file), "--action", "polish", "--quiet", "--json"])
    assert result.exit_code == 0
    data = parse_json_output(result)
    assert data["success"] is True
    assert data["action"] == "polish"


def test_edit_invalid_action(mock_config, tmp_path):
    input_file = tmp_path / "input.md"
    input_file.write_text("内容", encoding="utf-8")

    result = runner.invoke(app, ["edit", "--input", str(input_file), "--action", "invalid"])
    assert result.exit_code != 0
    assert "未知动作" in result.output


def test_write_basic(mock_config, tmp_path, monkeypatch):
    outline_data = [
        {"num": 1, "title": "第一章", "outline": "测试大纲一"},
        {"num": 2, "title": "第二章", "outline": "测试大纲二"},
    ]
    outline_file = tmp_path / "chapters.json"
    outline_file.write_text(json.dumps(outline_data, ensure_ascii=False), encoding="utf-8")
    output_dir = tmp_path / "output"

    call_count = 0

    def fake_stream(client, model, messages, temperature=None, max_tokens=None):
        nonlocal call_count
        call_count += 1
        yield f"这是第{call_count}次生成的内容，足够长的测试文本用于验证。"

    monkeypatch.setattr("novel_cli.commands.write.chat_stream", fake_stream)
    monkeypatch.setattr("novel_cli.commands.write.create_client", lambda c: None)

    result = runner.invoke(app, [
        "write", "--outline", str(outline_file),
        "--output", str(output_dir),
        "--words", "50", "--max-rounds", "1", "--quiet", "--json"
    ])
    assert result.exit_code == 0
    data = parse_json_output(result)
    assert data["success"] is True
    assert len(data["chapters"]) == 2


def test_write_with_characters(mock_config, tmp_path, monkeypatch):
    outline_data = [{"num": 1, "title": "测试章", "outline": "测试大纲"}]
    outline_file = tmp_path / "chapters.json"
    outline_file.write_text(json.dumps(outline_data, ensure_ascii=False), encoding="utf-8")

    characters_data = [{"name": "张三", "role": "主角", "age": 25}]
    characters_file = tmp_path / "characters.json"
    characters_file.write_text(json.dumps(characters_data, ensure_ascii=False), encoding="utf-8")
    output_dir = tmp_path / "output"

    captured_messages = []

    def fake_stream(client, model, messages, temperature=None, max_tokens=None):
        captured_messages.extend(messages)
        yield "带有角色约束的生成内容。"

    monkeypatch.setattr("novel_cli.commands.write.chat_stream", fake_stream)
    monkeypatch.setattr("novel_cli.commands.write.create_client", lambda c: None)

    result = runner.invoke(app, [
        "write", "--outline", str(outline_file),
        "--characters", str(characters_file),
        "--output", str(output_dir),
        "--words", "50", "--max-rounds", "1", "--quiet"
    ])
    assert result.exit_code == 0
    user_msg = captured_messages[1]["content"]
    assert "张三" in user_msg
    assert "人物表" in user_msg


def test_write_resume(mock_config, tmp_path, monkeypatch):
    outline_data = [
        {"num": 1, "title": "第一章", "outline": "大纲一"},
        {"num": 2, "title": "第二章", "outline": "大纲二"},
    ]
    outline_file = tmp_path / "chapters.json"
    outline_file.write_text(json.dumps(outline_data, ensure_ascii=False), encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "chapter_01.txt").write_text("第一章已生成的内容", encoding="utf-8")

    def fake_stream(client, model, messages, temperature=None, max_tokens=None):
        yield "第二章新生成的内容。"

    monkeypatch.setattr("novel_cli.commands.write.chat_stream", fake_stream)
    monkeypatch.setattr("novel_cli.commands.write.create_client", lambda c: None)

    result = runner.invoke(app, [
        "write", "--outline", str(outline_file),
        "--output", str(output_dir),
        "--resume", "2", "--words", "50", "--max-rounds", "1", "--quiet", "--json"
    ])
    assert result.exit_code == 0
    data = parse_json_output(result)
    assert data["success"] is True
    assert len(data["chapters"]) == 2


def test_write_json_output(mock_config, tmp_path, monkeypatch):
    outline_data = [{"num": 1, "title": "测试", "outline": "大纲"}]
    outline_file = tmp_path / "chapters.json"
    outline_file.write_text(json.dumps(outline_data, ensure_ascii=False), encoding="utf-8")
    output_dir = tmp_path / "output"

    def fake_stream(client, model, messages, temperature=None, max_tokens=None):
        yield "JSON输出测试内容。"

    monkeypatch.setattr("novel_cli.commands.write.chat_stream", fake_stream)
    monkeypatch.setattr("novel_cli.commands.write.create_client", lambda c: None)

    result = runner.invoke(app, [
        "write", "--outline", str(outline_file),
        "--output", str(output_dir),
        "--words", "50", "--max-rounds", "1", "--quiet", "--json"
    ])
    assert result.exit_code == 0
    data = parse_json_output(result)
    assert "total_chars" in data
    assert "chapters" in data


def test_config_set_and_show(mock_config, tmp_path, monkeypatch):
    config_dir = tmp_path / "novelcraft"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    monkeypatch.setattr("novel_cli.core.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("novel_cli.core.config.CONFIG_FILE", config_file)

    result = runner.invoke(app, ["config", "set", "--api-key", "sk-new-key-1234", "--model", "new-model"])
    assert result.exit_code == 0
    assert "已保存" in result.output

    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "sk-n" in strip_ansi(result.output)
    assert "new-model" in result.output
