import typer

from novel_cli import __version__
from novel_cli.commands.config import app as config_app
from novel_cli.commands.outline import app as outline_app
from novel_cli.commands.generate import app as generate_app
from novel_cli.commands.continue_ import app as continue_app
from novel_cli.commands.edit import app as edit_app
from novel_cli.commands.write import app as write_app
from novel_cli.commands.chat import app as chat_app
from novel_cli.core.exceptions import NovelCraftError
from novel_cli.utils.display import print_error

app = typer.Typer(
    name="novelcraft",
    help="NovelCraft — AI 驱动的长篇小说创作 CLI 工具",
    no_args_is_help=True,
)

app.add_typer(config_app, name="config", help="管理配置")
app.add_typer(outline_app, name="outline", help="生成小说大纲")
app.add_typer(generate_app, name="generate", help="根据大纲生成小说")
app.add_typer(continue_app, name="continue", help="续写已有内容")
app.add_typer(edit_app, name="edit", help="编辑/改写内容")
app.add_typer(write_app, name="write", help="逐章生成长篇小说")
app.add_typer(chat_app, name="chat", help="交互式对话模式")


@app.command()
def version() -> None:
    typer.echo(f"novelcraft v{__version__}")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    try:
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
    except NovelCraftError as e:
        print_error(str(e))
        raise typer.Exit(1) from e
    except Exception:
        print_error("发生了未预期的错误，请报告此问题")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()