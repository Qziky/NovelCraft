import json
from pathlib import Path
from unittest.mock import patch

import pytest
import typer

from novel_cli.core.config import Settings
from novel_cli.core.generator import handle_output, require_api_key, run_stream


def test_require_api_key_with_key():
    config = Settings(api_key="sk-test-key")
    require_api_key(config)


def test_require_api_key_without_key():
    config = Settings(api_key="")
    with pytest.raises(typer.Exit):
        require_api_key(config)


def test_run_stream_returns_response():
    config = Settings(api_key="sk-test", model="test-model")

    def fake_stream(client, model, messages, temperature=None, max_tokens=None):
        yield "这是"
        yield "模拟的"
        yield "生成内容"

    with patch("novel_cli.core.generator.chat_stream", fake_stream):
        with patch("novel_cli.core.generator.create_client"):
            result = run_stream("测试提示", "系统提示", config, quiet=True)
            assert result == "这是模拟的生成内容"


def test_run_stream_quiet_suppresses_output(capsys):
    config = Settings(api_key="sk-test", model="test-model")

    def fake_stream(client, model, messages, temperature=None, max_tokens=None):
        yield "内容"

    with patch("novel_cli.core.generator.chat_stream", fake_stream):
        with patch("novel_cli.core.generator.create_client"):
            with patch("novel_cli.core.generator.console") as mock_console:
                result = run_stream("提示", "系统", config, quiet=True)
                assert result == "内容"
                mock_console.print.assert_not_called()


def test_handle_output_json_to_file(tmp_path):
    output_file = tmp_path / "test.json"
    result_data = {"success": True, "data": "test"}

    handle_output("内容", str(output_file), True, result_data, quiet=True)

    saved = json.loads(output_file.read_text(encoding="utf-8"))
    assert saved["success"] is True
    assert saved["data"] == "test"


def test_handle_output_json_to_stdout(capsys):
    result_data = {"success": True}

    with patch("novel_cli.core.generator.console") as mock_console:
        handle_output("内容", None, True, result_data, quiet=True)
        mock_console.print.assert_called_once()
        printed = mock_console.print.call_args[0][0]
        assert "success" in printed


def test_handle_output_markdown_to_file(tmp_path):
    output_file = tmp_path / "test.md"

    handle_output("# 标题\n\n正文", str(output_file), False, {}, quiet=True)

    saved = output_file.read_text(encoding="utf-8")
    assert "# 标题" in saved
    assert "正文" in saved


def test_handle_output_markdown_to_stdout():
    with patch("novel_cli.core.generator.console") as mock_console:
        handle_output("输出内容", None, False, {}, quiet=False)
        mock_console.print.assert_called_with("输出内容")


def test_handle_output_quiet_suppresses_success(tmp_path):
    output_file = tmp_path / "test.md"

    with patch("novel_cli.core.generator.print_success") as mock_success:
        handle_output("内容", str(output_file), False, {}, quiet=True)
        mock_success.assert_not_called()
