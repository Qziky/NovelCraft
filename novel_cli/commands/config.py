from typing import Optional

import typer

from novel_cli.core.config import load_config, save_config, mask_key

app = typer.Typer(help="管理配置（API key、模型、URL 等）")


@app.command()
def set(
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="API 密钥"),
    base_url: Optional[str] = typer.Option(None, "--base-url", "-u", help="API 端点 URL"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="模型名称"),
    system_prompt: Optional[str] = typer.Option(None, "--system-prompt", "-s", help="系统提示词"),
) -> None:
    config = load_config()
    if api_key is not None:
        config.api_key = api_key
    if base_url is not None:
        config.base_url = base_url
    if model is not None:
        config.model = model
    if system_prompt is not None:
        config.system_prompt = system_prompt
    save_config(config)
    typer.echo("✅ 配置已保存")


@app.command()
def show() -> None:
    config = load_config()
    typer.echo(f"API Key:      {mask_key(config.api_key)}")
    typer.echo(f"Base URL:     {config.base_url}")
    typer.echo(f"Model:        {config.model}")
    typer.echo(f"System Prompt: {config.system_prompt[:50]}{'...' if len(config.system_prompt) > 50 else ''}")
