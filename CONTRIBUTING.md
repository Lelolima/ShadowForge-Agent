# Contributing to ShadowForge

First off, thank you for considering contributing to ShadowForge! It's people
like you that make this tool better for the entire security community.

## Code of Conduct

This project and everyone participating in it is governed by our
[Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to
uphold this code. Please report unacceptable behavior to security@shadowforge.dev.

## Legal & Ethical Requirements

**This project is for authorized security testing ONLY.** Before contributing:

- Never contribute code that facilitates unauthorized access to systems
- Never include real API keys, passwords, or credentials in contributions
- Ensure your contributions respect privacy and data protection laws (LGPD, GDPR)
- All offensive capabilities must include proper ethical guardrails
- Contributions that remove or weaken ethical safeguards will be rejected
- You must have the legal right to submit the code (no proprietary code leaks)

## How Can I Contribute?

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](../../issues)
2. If not, create a new issue using the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md)
3. Include:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, GPU)
   - Relevant logs (redact any API keys or sensitive data)

### Suggesting Enhancements

1. Open an issue using the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md)
2. Describe the feature, its use case, and why it would benefit most users
3. Include any security considerations (does it add attack surface? new guardrails needed?)

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with clear, atomic commits
4. Add tests covering new functionality
5. Ensure all tests pass (`python -m pytest tests/ -v`)
6. Run linting (`ruff check . && ruff format .`)
7. Run type checking (`mypy core/ models/ planning/`)
8. Run security scan (`bandit -r core/ models/ planning/ -ll --skip B101,B311`)
9. Push to your fork and open a Pull Request

#### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Security improvement

## Ethical Considerations
- [ ] This change does NOT weaken ethical guardrails
- [ ] This change does NOT enable unauthorized access
- [ ] New attack capabilities include appropriate safeguards

## Testing
- [ ] Tests added/updated
- [ ] All existing tests pass
- [ ] Tested in simulation mode

## Checklist
- [ ] Code follows project style guidelines (ruff, mypy)
- [ ] Self-review of code completed
- [ ] Comments added for complex logic
- [ ] Documentation updated if needed
```

## Commit Message Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `security` | Security vulnerability fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, semicolons) |
| `refactor` | Code refactoring without feature change |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `build` | Build system or dependencies |
| `ci` | CI configuration changes |
| `chore` | Maintenance tasks |

### Examples

```
feat(vision): add YOLOv8 UI element detection
fix(nim): handle rate limiting with exponential backoff
security(ethics): prevent bypass of authorization check
docs(readme): add RAG setup instructions
test(core): add OODA loop state machine tests
```

### Breaking Changes

Indicate breaking changes with `!` after the type or with a `BREAKING CHANGE:`
footer:

```
feat(api)!: change NIM client interface to async-only

BREAKING CHANGE: NIMClient.query() now requires await
```

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/NVIDIA-ShadowForge-Agent.git
cd NVIDIA-ShadowForge-Agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Copy and configure environment
cp .env.example .env
# Edit .env with your NVIDIA API key

# Verify environment
python scripts/health_check.py
python scripts/validate_env.py

# Run tests
python -m pytest tests/ -v
```

## Coding Standards

### Python

- **Python 3.10+**: Use modern type hints (`X | Y` instead of `Union`)
- **Async-first**: All I/O operations should be async
- **Type hints**: All public functions must have type annotations
- **Docstrings**: Google-style docstrings for all public APIs
- **Language**: Code in English; comments/docs may be in Portuguese
- **Line length**: 100 characters maximum (enforced by ruff)
- **Imports**: Use `from __future__ import annotations` in all modules

### Example Docstring

```python
from __future__ import annotations

async def scan_target(host: str, ports: str = "1-1000") -> ScanResult:
    """Perform a port scan on the specified target.

    Args:
        host: Target IP address or hostname.
        ports: Port range to scan (default: 1-1000).

    Returns:
        ScanResult object with discovered services.

    Raises:
        AuthorizationError: If target is not in whitelist.
        ConnectionError: If target is unreachable.
    """
```

### Security Requirements for Code

1. **Never hardcode credentials** -- use environment variables
2. **Never log sensitive data** -- API keys, passwords, tokens must be redacted
3. **Always add ethical guardrails** to new attack capabilities
4. **Use parameterized queries** -- never string-concatenate SQL or shell commands
5. **Validate all inputs** -- use Pydantic models for configuration
6. **Handle errors gracefully** -- never expose stack traces to unauthenticated users

## Project Structure

```
core/           # Agent engine, config, state, memory
models/         # NVIDIA NIM, Riva, embeddings, prompts
vision/         # Screen capture, OCR, detection, understanding
control/        # Mouse, keyboard, shell, stealth
planning/       # Orchestrator, RAG (MITRE/OWASP)
speech/         # ASR, TTS, voice interface
hacker_tools/   # Recon, exploit, post-exploitation, reporting
tests/          # Test suite
scripts/        # Utility scripts
config/         # YAML configuration
```

## Release Process

1. Update version in `pyproject.toml` and `config/default.yaml`
2. Update `CHANGELOG.md` with new entries
3. Create a git tag (`git tag v1.x.x`)
4. Push tag to trigger release workflow
5. Create GitHub Release with changelog excerpt
