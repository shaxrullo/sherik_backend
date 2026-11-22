# Code Quality & Linting Guide

Maintaining code quality is essential for maintainability and preventing bugs. This project uses several tools to enforce code quality standards.

## Tools Overview

### Black - Code Formatter
- **Purpose**: Auto-format Python code
- **Standard**: PEP 8 compliant
- **Line Length**: 100 characters

### isort - Import Sorter
- **Purpose**: Sort and organize imports consistently
- **Profile**: Black-compatible

### flake8 - Linter
- **Purpose**: Check for PEP 8 violations and code issues
- **Checks**: Style, error-prone patterns, complexity

### bandit - Security Scanner
- **Purpose**: Identify common security issues
- **Checks**: SQL injection, hardcoded passwords, insecure functions

### Pre-commit Hooks
- **Purpose**: Run quality checks before committing
- **Tools**: Black, isort, flake8, bandit, trailing whitespace, etc.

## Setup

### Install Dependencies

```bash
pip install -r requirements.txt
pip install pre-commit
```

### Configure Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks on all files (optional)
pre-commit run --all-files
```

## Usage

### Manual Linting

#### Check Code Quality

```bash
./scripts/lint.sh
# or
./scripts/lint.sh | grep error
```

#### Auto-Format Code

```bash
./scripts/format.sh
# or manually:
black .
isort .
```

### Pre-commit Hook Workflow

```bash
# 1. Make changes to code
nano listings/views.py

# 2. Stage changes
git add listings/views.py

# 3. Attempt commit
git commit -m "Add new feature"
# Pre-commit hooks run automatically
# If checks fail, fix issues and try again

# 4. If formatting fixes are auto-applied, re-stage and commit
git add listings/views.py
git commit -m "Add new feature"
```

### CI/CD (GitHub Actions)

Automated checks run on every push and pull request:

```bash
# Tests
pytest --cov=. --cov-report=term-missing

# Formatting check
black --check .

# Imports
isort --check .

# Linting
flake8 listings/ favorites/ ...

# Security
bandit -r .
```

## Configuration Files

### `.flake8`
Flake8 configuration - defines:
- Max line length (100)
- Ignored rules (E501, W503, etc.)
- File exclusions (migrations, venv)

### `pyproject.toml`
Black and isort configuration:
- Line length: 100
- Target Python: 3.11+
- Import profile: black-compatible

### `pytest.ini`
Pytest configuration:
- Django settings module
- Test discovery patterns
- Coverage targets

### `.pre-commit-config.yaml`
Pre-commit hooks setup:
- Which tools to run
- Tool versions
- Arguments and exclusions

## Common Issues & Fixes

### Too many imports

```python
# ✗ Bad
from module import func1, func2, func3, func4, func5

# ✓ Good
from module import (
    func1,
    func2,
    func3,
    func4,
    func5,
)
```

### Line too long

```python
# ✗ Bad (> 100 chars)
result = SomeModel.objects.filter(status='active').select_related('author', 'city', 'district').prefetch_related('photos')

# ✓ Good (break into logical parts)
result = (
    SomeModel.objects
    .filter(status='active')
    .select_related('author', 'city', 'district')
    .prefetch_related('photos')
)
```

### Unused imports

```python
# ✗ Bad
from django.db import models
from django.conf import settings  # Unused
import os

# ✓ Good
from django.db import models
import os
```

### Whitespace issues

```python
# ✗ Bad - trailing whitespace
def my_function():    
    pass    

# ✓ Good
def my_function():
    pass
```

### Security issues

```python
# ✗ Bad - hardcoded password
password = "admin123"

# ✗ Bad - SQL injection risk
query = f"SELECT * FROM users WHERE id={user_id}"

# ✓ Good - use environment variable
password = os.getenv('ADMIN_PASSWORD')

# ✓ Good - use ORM
user = User.objects.get(id=user_id)
```

## Best Practices

1. **Run linting before committing**
   ```bash
   ./scripts/lint.sh
   ```

2. **Auto-format before staging**
   ```bash
   ./scripts/format.sh
   git add .
   ```

3. **Use an IDE with linting integration**
   - VS Code: Python extension
   - PyCharm: Built-in support
   - Vim: ALE/Syntastic plugins

4. **Fix issues early**
   - Don't accumulate lint issues
   - Address security warnings immediately

5. **Review GitHub Actions results**
   - Check PR CI/CD status
   - Fix any failing checks before merge

## IDE Integration

### VS Code

1. Install Python extension
2. Create `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": [
    "--max-line-length=100",
    "--exclude=migrations"
  ],
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=100"],
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### PyCharm

1. Settings → Editor → Code Style → Python
2. Set line length to 100
3. Enable Black formatter integration
4. Enable isort

## Disabling Checks (When Necessary)

### Single Line

```python
# noqa: E501 - Disable "line too long"
very_long_line = "..."  # noqa: E501

# type: ignore - Disable type checking
result = some_function()  # type: ignore
```

### Block

```python
# noinspection PyUnresolvedReference
result = some_external_library.function()
```

### File

```python
# flake8: noqa: E501
# This file has very long lines
```

**Important**: Only disable checks when necessary and add a comment explaining why.

## Continuous Integration

Checks run automatically on:
- **Every push**: GitHub Actions runs linting and tests
- **PRs**: Code quality gates must pass before merge
- **Pre-commit**: Local hooks prevent bad code from being committed

## Troubleshooting

### Pre-commit hooks not running
```bash
pre-commit install
pre-commit run --all-files
```

### Black and flake8 conflict
- Ensure flake8 config has: `ignore = E501, W503, E203`
- Use isort Black profile: `profile = black`

### Import order issues
```bash
isort . --profile black
```

### Too strict/relaxed checking
- Modify `.flake8` for flake8 rules
- Modify `pyproject.toml` for Black/isort rules
- Modify `.pre-commit-config.yaml` for hooks

## References

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [flake8 Documentation](https://flake8.pycqa.org/)
- [bandit Documentation](https://bandit.readthedocs.io/)
- [Pre-commit Framework](https://pre-commit.com/)
- [PEP 8 Style Guide](https://pep8.org/)
