# Contributing to NovelCraft

Thank you for your interest in contributing to NovelCraft! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork and clone the repository:

```bash
git clone https://github.com/your-username/novelcraft.git
cd novelcraft
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

3. Verify the installation:

```bash
novelcraft version
pytest -v
```

## Development Workflow

1. Create a feature branch from `main`:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes, following the code conventions below.

3. Run linting and type checking:

```bash
ruff check novel_cli/ tests/
mypy novel_cli/ --ignore-missing-imports
```

4. Run the tests:

```bash
pytest -v
```

5. Commit your changes with a clear message:

```bash
git commit -m "feat: add new feature description"
```

6. Push and create a Pull Request.

## Code Conventions

- **Type annotations**: All public functions must have complete type annotations (parameters and return values).
- **No inline comments**: Do not add comments unless absolutely necessary. Code should be self-documenting.
- **Chinese user-facing strings**: All CLI help text, error messages, and user-facing output should be in Chinese.
- **Import style**: Use absolute imports. Group imports as: stdlib, third-party, local.

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`

## Testing

- All new features must include tests.
- Use `pytest` for all tests.
- Unit tests go in `tests/` and mock external API calls.
- Integration tests that require a real API should be guarded by `@pytest.mark.skipif` with the `NOVELCRAFT_INTEGRATION_TEST` environment variable.
- Run the full test suite before submitting:

```bash
pytest -v --tb=short
```

## Reporting Issues

When reporting bugs, please include:

- NovelCraft version (`novelcraft version`)
- Python version (`python --version`)
- Operating system
- Steps to reproduce
- Expected behavior vs actual behavior
- Error output or logs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
