import json
from datetime import datetime
from pathlib import Path


class ChatSession:
    def __init__(self, system_prompt: str = ""):
        self.messages: list[dict] = []
        self.system_prompt = system_prompt
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def clear(self) -> None:
        self.messages.clear()
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})

    def update_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt
        if self.messages and self.messages[0]["role"] == "system":
            self.messages[0]["content"] = prompt
        else:
            self.messages.insert(0, {"role": "system", "content": prompt})

    def get_messages(self) -> list[dict]:
        return self.messages

    def to_markdown(self) -> str:
        lines = [
            "# NovelCraft 对话记录", "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "", "---", ""
        ]
        for msg in self.messages:
            if msg["role"] == "system":
                lines.append("## 📋 System Prompt")
                lines.append("")
                lines.append(msg["content"])
                lines.append("")
                lines.append("---")
                lines.append("")
            elif msg["role"] == "user":
                lines.append("## 👤 User")
                lines.append("")
                lines.append(msg["content"])
                lines.append("")
            elif msg["role"] == "assistant":
                lines.append("## 🤖 Assistant")
                lines.append("")
                lines.append(msg["content"])
                lines.append("")
                lines.append("---")
                lines.append("")
        return "\n".join(lines)

    def save(self, filepath: str) -> Path:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_markdown(), encoding="utf-8")
        return path

    def save_json(self, filepath: str) -> Path:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "system_prompt": self.system_prompt,
            "messages": self.messages,
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    @classmethod
    def load_json(cls, filepath: str) -> "ChatSession":
        path = Path(filepath)
        data = json.loads(path.read_text(encoding="utf-8"))
        session = cls(system_prompt=data.get("system_prompt", ""))
        session.messages = data.get("messages", [])
        return session

    @classmethod
    def load_markdown(cls, filepath: str) -> "ChatSession":
        path = Path(filepath)
        content = path.read_text(encoding="utf-8")
        session = cls()
        current_role = None
        current_content: list[str] = []
        for line in content.split("\n"):
            if line.startswith("## 👤 User"):
                if current_role and current_content:
                    text = "\n".join(current_content).strip()
                    if text:
                        if current_role == "system":
                            session.system_prompt = text
                            if session.messages and session.messages[0]["role"] == "system":
                                session.messages[0]["content"] = text
                            else:
                                session.messages.insert(0, {"role": "system", "content": text})
                        else:
                            session.messages.append({"role": current_role, "content": text})
                current_role = "user"
                current_content = []
            elif line.startswith("## 🤖 Assistant"):
                if current_role and current_content:
                    text = "\n".join(current_content).strip()
                    if text:
                        if current_role == "system":
                            session.system_prompt = text
                            if session.messages and session.messages[0]["role"] == "system":
                                session.messages[0]["content"] = text
                            else:
                                session.messages.insert(0, {"role": "system", "content": text})
                        else:
                            session.messages.append({"role": current_role, "content": text})
                current_role = "assistant"
                current_content = []
            elif line.startswith("## 📋 System Prompt"):
                if current_role and current_content:
                    text = "\n".join(current_content).strip()
                    if text:
                        session.messages.append({"role": current_role, "content": text})
                current_role = "system"
                current_content = []
            elif line.startswith("---"):
                continue
            elif line.startswith("# ") or line.startswith("生成时间:"):
                continue
            else:
                current_content.append(line)
        if current_role and current_content:
            text = "\n".join(current_content).strip()
            if text:
                if current_role == "system":
                    session.system_prompt = text
                    if session.messages and session.messages[0]["role"] == "system":
                        session.messages[0]["content"] = text
                    else:
                        session.messages.insert(0, {"role": "system", "content": text})
                else:
                    session.messages.append({"role": current_role, "content": text})
        return session

    @classmethod
    def load(cls, filepath: str) -> "ChatSession":
        path = Path(filepath)
        if path.suffix == ".json":
            return cls.load_json(filepath)
        return cls.load_markdown(filepath)
