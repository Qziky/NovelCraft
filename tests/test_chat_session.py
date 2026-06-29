import json
import tempfile
from pathlib import Path

from novel_cli.core.chat_session import ChatSession


def test_init_without_system_prompt():
    session = ChatSession()
    assert session.messages == []
    assert session.system_prompt == ""


def test_init_with_system_prompt():
    session = ChatSession(system_prompt="test prompt")
    assert len(session.messages) == 1
    assert session.messages[0] == {"role": "system", "content": "test prompt"}
    assert session.system_prompt == "test prompt"


def test_add_user_message():
    session = ChatSession(system_prompt="sys")
    session.add_user_message("hello")
    assert len(session.messages) == 2
    assert session.messages[1] == {"role": "user", "content": "hello"}


def test_add_assistant_message():
    session = ChatSession(system_prompt="sys")
    session.add_assistant_message("hi")
    assert len(session.messages) == 2
    assert session.messages[1] == {"role": "assistant", "content": "hi"}


def test_clear_with_system_prompt():
    session = ChatSession(system_prompt="sys")
    session.add_user_message("hello")
    session.add_assistant_message("hi")
    session.clear()
    assert len(session.messages) == 1
    assert session.messages[0]["role"] == "system"


def test_clear_without_system_prompt():
    session = ChatSession()
    session.add_user_message("hello")
    session.clear()
    assert session.messages == []


def test_update_system_prompt_existing():
    session = ChatSession(system_prompt="old")
    session.update_system_prompt("new")
    assert session.system_prompt == "new"
    assert session.messages[0]["content"] == "new"


def test_update_system_prompt_insert():
    session = ChatSession()
    session.add_user_message("hello")
    session.update_system_prompt("new sys")
    assert session.messages[0] == {"role": "system", "content": "new sys"}
    assert session.system_prompt == "new sys"


def test_get_messages():
    session = ChatSession(system_prompt="sys")
    session.add_user_message("q")
    session.add_assistant_message("a")
    msgs = session.get_messages()
    assert len(msgs) == 3
    assert msgs is session.messages


def test_to_markdown_contains_roles():
    session = ChatSession(system_prompt="test sys")
    session.add_user_message("question")
    session.add_assistant_message("answer")
    md = session.to_markdown()
    assert "## 📋 System Prompt" in md
    assert "## 👤 User" in md
    assert "## 🤖 Assistant" in md
    assert "test sys" in md
    assert "question" in md
    assert "answer" in md


def test_save_and_load_json(tmp_path):
    session = ChatSession(system_prompt="sys")
    session.add_user_message("hello")
    session.add_assistant_message("world")

    filepath = str(tmp_path / "test.json")
    session.save_json(filepath)

    loaded = ChatSession.load_json(filepath)
    assert loaded.system_prompt == "sys"
    assert len(loaded.messages) == 3
    assert loaded.messages[1]["content"] == "hello"
    assert loaded.messages[2]["content"] == "world"


def test_save_and_load_markdown(tmp_path):
    session = ChatSession(system_prompt="test system")
    session.add_user_message("what?")
    session.add_assistant_message("yes.")

    filepath = str(tmp_path / "test.md")
    session.save(filepath)

    loaded = ChatSession.load(filepath)
    assert loaded.system_prompt == "test system"
    assert len(loaded.messages) == 3
    assert loaded.messages[1]["content"] == "what?"
    assert loaded.messages[2]["content"] == "yes."


def test_load_json_preserves_unicode(tmp_path):
    session = ChatSession(system_prompt="中文提示")
    session.add_user_message("你好世界")
    filepath = str(tmp_path / "unicode.json")
    session.save_json(filepath)

    loaded = ChatSession.load_json(filepath)
    assert loaded.system_prompt == "中文提示"
    assert loaded.messages[1]["content"] == "你好世界"


def test_save_creates_parent_dirs(tmp_path):
    session = ChatSession(system_prompt="sys")
    filepath = str(tmp_path / "sub" / "dir" / "test.json")
    session.save_json(filepath)
    assert Path(filepath).exists()


def test_load_dispatches_by_suffix(tmp_path):
    session = ChatSession(system_prompt="sys")
    session.add_user_message("hi")

    json_path = str(tmp_path / "test.json")
    session.save_json(json_path)
    loaded_json = ChatSession.load(json_path)
    assert loaded_json.system_prompt == "sys"

    md_path = str(tmp_path / "test.md")
    session.save(md_path)
    loaded_md = ChatSession.load(md_path)
    assert loaded_md.system_prompt == "sys"