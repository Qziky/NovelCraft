# NovelCraft

<p align="center">
  <strong>面向中文长篇创作的 AI 小说写作 CLI</strong>
</p>

<p align="center">
  <a href="https://github.com/Qziky/NovelCraft/actions/workflows/ci.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/Qziky/NovelCraft/ci.yml?branch=main&label=CI" alt="CI">
  </a>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/typed-PEP%20561-success" alt="Typed">
  <img src="https://img.shields.io/github/license/Qziky/NovelCraft" alt="License">
  <img src="https://img.shields.io/github/stars/Qziky/NovelCraft?style=social" alt="GitHub stars">
</p>

NovelCraft 是一款基于 OpenAI 兼容 API 的命令行小说创作工具，帮助作者把灵感扩展成大纲、章节、长篇正文和可继续迭代的创作会话。它适合人类作者在终端里快速试写，也适合 AI Agent 通过 JSON 输出接入自动化写作流程。

如果你想要一个轻量、可脚本化、能适配 OpenAI / Ollama / 本地兼容服务的小说写作助手，欢迎点一个 Star 关注后续更新。

## 为什么值得一试

- **长篇友好**：支持按章节逐步生成，内置断点续写，适合长篇小说而不是只生成一段短文本。
- **大纲到正文闭环**：从 `outline` 生成故事骨架，再用 `generate` 或 `write` 扩写成正文。
- **人物表约束**：`write --characters` 可传入角色设定 JSON，降低人物姓名、身份、关系前后漂移。
- **模型无绑定**：使用 OpenAI 兼容接口，可切换 OpenAI、Ollama、本地模型或其他兼容服务。
- **Agent 友好**：关键命令支持 `--json` 输出，便于工作流、脚本和自动化代理解析。
- **工程化基础**：Typer CLI、Rich 终端输出、类型标注、pytest 测试和 GitHub Actions CI。

## 功能一览

| 命令 | 用途 | 适合场景 |
| --- | --- | --- |
| `novelcraft outline` | 生成小说大纲 | 从灵感、设定或一句话梗概扩展故事结构 |
| `novelcraft generate` | 生成完整正文 | 根据提示词或大纲生成短中篇内容 |
| `novelcraft write` | 逐章生成长篇 | 长篇章节生成、断点续写、人物表约束 |
| `novelcraft continue` | 续写已有文本 | 给已有章节追加后续剧情 |
| `novelcraft edit` | 润色和改写 | polish / shorten / expand / rewrite |
| `novelcraft chat` | 交互式创作对话 | 头脑风暴、设定讨论、多轮创作 |
| `novelcraft config` | 管理配置 | API Key、模型、Base URL、系统提示词 |

## 快速开始

### 安装

```bash
git clone https://github.com/Qziky/NovelCraft.git
cd NovelCraft

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### 配置模型

```bash
novelcraft config set --api-key "your-api-key"
novelcraft config set --base-url "https://api.openai.com/v1"
novelcraft config set --model "gpt-4"
novelcraft config show
```

也可以使用环境变量：

```bash
export NOVEL_CLI_API_KEY="your-api-key"
export NOVEL_CLI_BASE_URL="https://api.openai.com/v1"
export NOVEL_CLI_MODEL="gpt-4"
```

配置优先级：环境变量 > `~/.novelcraft/config.json` > 默认值。

## 典型工作流

### 1. 从一句话生成大纲

```bash
novelcraft outline \
  --prompt "一个返乡青年守护古镇秘密的故事" \
  --chapters 16 \
  --style "现实主义悬疑" \
  --output outline.json \
  --json
```

### 2. 根据大纲生成正文

```bash
novelcraft generate \
  --outline outline.json \
  --words 5000 \
  --output novel.md
```

### 3. 逐章写长篇，并支持断点恢复

准备一个章节大纲 `chapters.json`：

```json
[
  {
    "num": 1,
    "title": "归途",
    "outline": "主角回到阔别多年的古镇，发现祖屋里留下了一封未寄出的信。"
  },
  {
    "num": 2,
    "title": "旧井",
    "outline": "主角追查信中的线索，找到被封住的旧井和一段被刻意抹去的往事。"
  }
]
```

执行逐章生成：

```bash
novelcraft write \
  --outline chapters.json \
  --words 3500 \
  --output novel_chapters/
```

中断后从第 5 章恢复：

```bash
novelcraft write \
  --outline chapters.json \
  --resume 5 \
  --output novel_chapters/
```

### 4. 使用人物表减少设定漂移

`characters.json` 示例：

```json
[
  {
    "name": "林远",
    "role": "主角",
    "age": 28,
    "identity": "返乡青年，前互联网产品经理",
    "personality": "内敛、观察力强、有责任感",
    "relationships": {
      "母亲": "李秀兰",
      "恋人": "苏晓晴"
    },
    "background": "父亲早逝，在上海工作五年后失业返乡"
  },
  {
    "name": "苏晓晴",
    "role": "女主角",
    "age": 26,
    "identity": "镇中心小学教师",
    "personality": "温柔坚定"
  }
]
```

```bash
novelcraft write \
  --outline chapters.json \
  --characters characters.json \
  --words 4000 \
  --temperature 0.85
```

### 5. 续写和改写

```bash
novelcraft continue \
  --input story.md \
  --prompt "接下来主角发现了一把没有齿痕的钥匙" \
  --words 2000 \
  --output story_continued.md
```

```bash
novelcraft edit --input story.md --action polish
novelcraft edit --input story.md --action shorten
novelcraft edit --input story.md --action expand
novelcraft edit --input story.md --action rewrite
```

## 适配不同模型服务

```bash
# OpenAI
novelcraft config set --base-url "https://api.openai.com/v1" --model "gpt-4"

# Ollama OpenAI-compatible endpoint
novelcraft config set --base-url "http://localhost:11434/v1" --model "llama3"

# 其他 OpenAI 兼容服务
novelcraft config set --base-url "https://your-service.example/v1" --model "your-model"
```

## 输出与自动化

所有生成类命令都支持常见选项：

| 选项 | 说明 |
| --- | --- |
| `--output, -o` | 输出文件或目录 |
| `--json` | JSON 格式输出，适合脚本和 AI Agent |
| `--quiet, -q` | 静默模式，减少流式文本输出 |
| `--system` | 自定义系统提示词 |

## 项目结构

```text
novel_cli/
  commands/        # Typer 命令：outline / generate / write / continue / edit / chat / config
  core/            # 配置、OpenAI 客户端、会话和生成逻辑
  utils/           # Rich 终端显示
tests/             # 单元测试和 CLI 集成测试
.github/workflows/ # CI 和发布工作流
```

## 开发

```bash
pip install -e ".[dev]"
ruff check novel_cli/ tests/
mypy novel_cli/ --ignore-missing-imports
pytest -v --tb=short
```

## Roadmap

- 更稳定的结构化大纲模板
- 更强的章节摘要和上下文压缩
- 可选的写作项目目录管理
- 更多本地模型和 OpenAI 兼容服务示例
- 更丰富的中文写作风格预设

## 贡献

欢迎提交 Issue、PR、使用反馈和写作工作流案例。好的小说工具不该只会“生成文字”，也应该帮助作者管理设定、节奏、角色一致性和长篇创作过程。

如果 NovelCraft 对你有启发，欢迎 Star，这会帮助更多写作者和开发者发现它。

## License

MIT License
