# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/zh-CN/).

## [0.1.0] - 2026-06-24

### Added

- `outline` command: generate novel outlines from prompts
- `generate` command: generate novel text from outlines or prompts
- `write` command: chapter-by-chapter long-form novel generation with resume support and character sheet constraints
- `continue` command: continue writing from existing content
- `edit` command: edit/rewrite content with preset actions (polish/shorten/expand/rewrite)
- `chat` command: interactive multi-turn conversation mode
- `config` command: manage API key, model, base URL, and system prompt
- Support for any OpenAI-compatible API (GPT-4, Ollama, local models, etc.)
- JSON output mode for AI Agent integration
- Dual configuration: environment variables and config file (`~/.novelcraft/config.json`)
- Streaming output with Rich terminal formatting
- Unified retry logic with exponential backoff for API calls
- Custom exception hierarchy for structured error handling
- Type annotations across the entire codebase (PEP 561 compliant)
- GitHub Actions CI (lint + type check + test matrix across Python 3.10/3.11/3.12)
- PyPI release workflow (tag-triggered)
- CLI integration tests using Typer CliRunner
- Real API integration tests (opt-in via environment variable)
