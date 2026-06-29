import json
import os
from unittest.mock import patch

from novel_cli.core.config import CONFIG_FIELDS, Settings, load_config, save_config


def test_save_and_load_config(tmp_path):
    config_file = tmp_path / "config.json"
    settings = Settings(api_key="test-key-123", base_url="http://localhost:8080/v1", model="test-model")

    data = {
        "api_key": settings.api_key,
        "base_url": settings.base_url,
        "model": settings.model,
        "system_prompt": settings.system_prompt,
    }
    config_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    with patch("novel_cli.core.config.CONFIG_FILE", config_file):
        loaded = load_config()
        assert loaded.api_key == "test-key-123"
        assert loaded.base_url == "http://localhost:8080/v1"
        assert loaded.model == "test-model"


def test_load_config_missing_file(tmp_path):
    nonexistent = tmp_path / "nonexistent.json"
    with patch("novel_cli.core.config.CONFIG_FILE", nonexistent):
        loaded = load_config()
        assert loaded.api_key == ""
        assert loaded.model == "gpt-4"


def test_load_config_corrupted_file(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text("not valid json {{{", encoding="utf-8")

    with patch("novel_cli.core.config.CONFIG_FILE", config_file):
        loaded = load_config()
        assert loaded.api_key == ""
        assert loaded.model == "gpt-4"


def test_env_var_overrides_config_file(tmp_path):
    config_file = tmp_path / "config.json"
    data = {"api_key": "file-key", "model": "file-model"}
    config_file.write_text(json.dumps(data), encoding="utf-8")

    with patch("novel_cli.core.config.CONFIG_FILE", config_file):
        with patch.dict(os.environ, {"NOVEL_CLI_API_KEY": "env-key", "NOVEL_CLI_MODEL": "env-model"}):
            loaded = load_config()
            assert loaded.api_key == "env-key"
            assert loaded.model == "env-model"


def test_save_config_creates_dir(tmp_path):
    config_dir = tmp_path / "new_dir"
    config_file = config_dir / "config.json"
    settings = Settings(api_key="key", model="model")

    with patch("novel_cli.core.config.CONFIG_DIR", config_dir):
        with patch("novel_cli.core.config.CONFIG_FILE", config_file):
            save_config(settings)
            assert config_file.exists()
            data = json.loads(config_file.read_text(encoding="utf-8"))
            assert data["api_key"] == "key"
            assert data["model"] == "model"


def test_save_config_writes_all_fields(tmp_path):
    config_file = tmp_path / "config.json"
    settings = Settings(api_key="k", base_url="http://test", model="m", system_prompt="中文提示")

    with patch("novel_cli.core.config.CONFIG_DIR", tmp_path):
        with patch("novel_cli.core.config.CONFIG_FILE", config_file):
            save_config(settings)
            data = json.loads(config_file.read_text(encoding="utf-8"))
            for field in CONFIG_FIELDS:
                assert field in data
            assert data["system_prompt"] == "中文提示"


def test_config_fields_constant():
    expected = {"api_key", "base_url", "model", "system_prompt"}
    assert set(CONFIG_FIELDS) == expected
