import json
import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


CONFIG_DIR = Path.home() / ".novelcraft"
CONFIG_FILE = CONFIG_DIR / "config.json"

CONFIG_FIELDS = ["api_key", "base_url", "model", "system_prompt"]


class Settings(BaseSettings):
    api_key: str = Field(default="", description="API 密钥")
    base_url: str = Field(default="https://api.openai.com/v1", description="API 端点 URL")
    model: str = Field(default="gpt-4", description="模型名称")
    system_prompt: str = Field(
        default="你是 NovelCraft，一个专业的小说创作助手，擅长各种体裁的小说创作。请用中文回复。",
        description="系统提示词"
    )

    model_config = {
        "env_prefix": "NOVEL_CLI_",
        "env_file": ".env",
        "extra": "ignore",
    }


def _load_file_values() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def load_config() -> Settings:
    file_values = _load_file_values()
    merged = {}
    for field in CONFIG_FIELDS:
        env_key = f"NOVEL_CLI_{field.upper()}"
        env_val = os.environ.get(env_key)
        if env_val is not None:
            merged[field] = env_val
        elif field in file_values:
            merged[field] = file_values[field]
    return Settings(**merged)


def save_config(settings: Settings) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "api_key": settings.api_key,
        "base_url": settings.base_url,
        "model": settings.model,
        "system_prompt": settings.system_prompt,
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return "****"
    return key[:4] + "*" * (len(key) - 8) + key[-4:]
