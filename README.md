# NovelCraft

<p align="center">
  <strong>AI 驱动的长篇小说创作 CLI 工具</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/version-0.1.0-green" alt="Version 0.1.0">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License">
</p>

---

NovelCraft 是一款基于 OpenAI 兼容 API 的命令行小说创作工具，帮助作者从大纲构思到完整长篇小说的全流程创作。支持任意兼容 OpenAI API 格式的大模型（如 GPT-4、Claude、本地模型等），既适合人类作者交互使用，也适合 AI Agent 自动化调用。

## 功能特性

| 命令 | 功能 | 说明 |
|------|------|------|
| `novelcraft outline` | 生成小说大纲 | 根据提示生成包含人物设定、章节规划的完整大纲 |
| `novelcraft generate` | 生成小说正文 | 根据大纲或提示生成指定字数的小说 |
| `novelcraft write` | 逐章生成长篇小说 | 自动逐章生成，支持续写轮次、人物表约束、断点恢复 |
| `novelcraft continue` | 续写已有内容 | 在已有文本基础上续写指定字数 |
| `novelcraft edit` | 编辑/改写内容 | 润色、精简、扩写、改写已有文本 |
| `novelcraft chat` | 交互式对话 | 进入多轮对话模式，自由创作 |
| `novelcraft config` | 管理配置 | 设置 API Key、模型、端点等 |

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/Qziky/NovelCraft.git
cd NovelCraft

# 创建虚拟环境并安装
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### 配置

```bash
# 设置 API Key（必须）
novelcraft config set --api-key "your-api-key"

# 设置 API 端点（可选，默认 OpenAI）
novelcraft config set --base-url "https://api.openai.com/v1"

# 设置模型名称（可选，默认 gpt-4）
novelcraft config set --model "gpt-4"

# 查看当前配置
novelcraft config show
```

也可以通过环境变量配置：

```bash
export NOVEL_CLI_API_KEY="your-api-key"
export NOVEL_CLI_BASE_URL="https://api.openai.com/v1"
export NOVEL_CLI_MODEL="gpt-4"
```

配置优先级：环境变量 > 配置文件（`~/.novel-cli/config.json`）> 默认值

### 使用示例

#### 1. 生成大纲

```bash
# 根据提示生成 16 章大纲
novelcraft outline \
  --prompt "一个返乡青年守护古镇的故事" \
  --chapters 16 \
  --style "现实主义文学" \
  --output outline.json \
  --json
```

#### 2. 生成短篇小说

```bash
# 从提示直接生成
novelcraft generate \
  --prompt "一个发生在雨夜的悬疑故事" \
  --words 3000 \
  --style "悬疑推理" \
  --output story.md

# 从大纲生成
novelcraft generate \
  --outline outline.json \
  --words 5000 \
  --output novel.md
```

#### 3. 逐章生成长篇小说（推荐）

```bash
# 准备章节大纲 JSON 文件 chapters.json
# 格式: [{"num": 1, "title": "章节名", "outline": "章节内容概要"}, ...]

# 逐章生成，每章 3500 字，支持断点恢复
novelcraft write \
  --outline chapters.json \
  --words 3500 \
  --output novel_chapters/ \
  --json

# 从第 5 章恢复生成（中断后继续）
novelcraft write \
  --outline chapters.json \
  --resume 5 \
  --output novel_chapters/

# 使用人物表约束角色设定
novelcraft write \
  --outline chapters.json \
  --characters characters.json \
  --words 4000 \
  --temperature 0.85
```

#### 4. 续写已有内容

```bash
novelcraft continue \
  --input story.md \
  --prompt "接下来主角发现了一个秘密" \
  --words 2000 \
  --output story_continued.md
```

#### 5. 编辑/改写

```bash
# 使用预设动作
novelcraft edit --input story.md --action polish     # 润色
novelcraft edit --input story.md --action shorten    # 精简
novelcraft edit --input story.md --action expand     # 扩写
novelcraft edit --input story.md --action rewrite    # 改写

# 使用自定义指示
novelcraft edit --input story.md --prompt "将对话改得更口语化" --output edited.md
```

#### 6. 交互式对话

```bash
# 进入对话模式
novelcraft chat

# 自定义系统提示词
novelcraft chat --system "你是一位武侠小说作家"

# 加载已有对话继续
novelcraft chat --load previous_chat.md
```

### 通用选项

所有生成命令均支持以下通用选项：

| 选项 | 说明 |
|------|------|
| `--output, -o` | 输出文件路径 |
| `--json` | 以 JSON 格式输出（适合 AI Agent 解析） |
| `--quiet, -q` | 静默模式（不输出流式文本，仅显示进度） |
| `--system` | 自定义系统提示词 |

## 项目结构

```
novelcraft/
├── novel_cli/
│   ├── __init__.py          # 版本号
│   ├── main.py              # CLI 入口
│   ├── commands/
│   │   ├── outline.py       # 大纲生成
│   │   ├── generate.py      # 小说生成
│   │   ├── write.py         # 逐章长篇生成
│   │   ├── continue_.py     # 续写
│   │   ├── edit.py          # 编辑/改写
│   │   ├── chat.py          # 交互式对话
│   │   └── config.py        # 配置管理
│   ├── core/
│   │   ├── config.py        # 配置加载（pydantic-settings）
│   │   ├── client.py        # OpenAI SDK 封装
│   │   ├── chat_session.py  # 对话会话管理
│   │   └── generator.py     # 通用生成逻辑
│   └── utils/
│       └── display.py       # Rich 终端显示
├── tests/                   # 单元测试
├── pyproject.toml           # 项目配置
└── README.md
```

## 人物表格式

`write` 命令支持通过 `--characters` 参数传入人物表 JSON 文件，约束 AI 不自由编造角色：

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
      "恋人": "苏晓薇"
    },
    "background": "父亲早逝，在上海工作五年后失业返乡"
  },
  {
    "name": "苏晓薇",
    "role": "女主角",
    "age": 26,
    "identity": "镇中心小学教师",
    "personality": "温柔坚韧"
  }
]
```

## 适配不同模型

NovelCraft 兼容所有 OpenAI API 格式的模型服务：

```bash
# OpenAI
novelcraft config set --base-url "https://api.openai.com/v1" --model "gpt-4"

# 本地 Ollama
novelcraft config set --base-url "http://localhost:11434/v1" --model "llama3"

# 其他兼容服务
novelcraft config set --base-url "https://your-service.com/v1" --model "your-model"
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行特定测试
pytest tests/test_config.py
```

## 许可证

MIT License
