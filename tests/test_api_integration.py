import json
import os

import pytest
from typer.testing import CliRunner

from novel_cli.main import app

runner = CliRunner()

integration = pytest.mark.skipif(
    os.environ.get("NOVELCRAFT_INTEGRATION_TEST") != "1",
    reason="需要设置 NOVELCRAFT_INTEGRATION_TEST=1 环境变量"
)


@integration
def test_real_outline_generation():
    result = runner.invoke(app, [
        "outline",
        "--prompt", "一个发生在江南小镇的短篇故事",
        "--chapters", "2",
        "--style", "现实主义",
        "--quiet", "--json"
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert len(data["outline"]) > 100


@integration
def test_real_generate_short_story(tmp_path):
    output_file = tmp_path / "story.md"
    result = runner.invoke(app, [
        "generate",
        "--prompt", "一个程序员在雨夜加班的短篇故事",
        "--words", "500",
        "--style", "现实主义",
        "--output", str(output_file),
        "--quiet"
    ])
    assert result.exit_code == 0
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert len(content) > 200


@integration
def test_real_write_single_chapter(tmp_path):
    outline_data = [
        {"num": 1, "title": "初遇", "outline": "主角在咖啡馆遇到一个陌生人，两人展开了一段关于人生的对话。"},
    ]
    outline_file = tmp_path / "chapters.json"
    outline_file.write_text(json.dumps(outline_data, ensure_ascii=False), encoding="utf-8")
    output_dir = tmp_path / "output"

    result = runner.invoke(app, [
        "write",
        "--outline", str(outline_file),
        "--output", str(output_dir),
        "--words", "500",
        "--max-rounds", "1",
        "--quiet"
    ])
    assert result.exit_code == 0
    chapter_file = output_dir / "chapter_01.txt"
    assert chapter_file.exists()
    content = chapter_file.read_text(encoding="utf-8")
    assert len(content) > 200
