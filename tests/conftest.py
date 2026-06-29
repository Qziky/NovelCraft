import os
from pathlib import Path

import pytest
from typer.testing import CliRunner


def pytest_configure(config):
    config.option.basetemp = Path(__file__).parent / ".pytest_tmp"


@pytest.fixture
def mock_chat_stream(monkeypatch):
    def fake_stream(client, model, messages, temperature=None, max_tokens=None):
        yield "这是"
        yield "模拟的"
        yield "生成内容"
    monkeypatch.setattr("novel_cli.core.client.chat_stream", fake_stream)
    return fake_stream


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def mock_config(tmp_path, monkeypatch):
    config_dir = tmp_path / "novelcraft"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    config_file.write_text(
        '{"api_key": "sk-test-key", "base_url": "https://api.test.com/v1",'
        ' "model": "test-model", "system_prompt": "测试提示"}',
        encoding="utf-8"
    )
    monkeypatch.setattr("novel_cli.core.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("novel_cli.core.config.CONFIG_FILE", config_file)
    return config_file


integration = pytest.mark.skipif(
    os.environ.get("NOVELCRAFT_INTEGRATION_TEST") != "1",
    reason="需要设置 NOVELCRAFT_INTEGRATION_TEST=1 环境变量"
)
