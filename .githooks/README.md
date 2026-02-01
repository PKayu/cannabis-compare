# Git Hooks

This directory contains git hooks that run automatically during git operations.

## Installed Hooks

### Pre-Commit
**Runs:** Before each commit
**What it does:**
- Validates Python syntax for all staged `.py` files
- Validates JSON syntax for all staged `.json` files
- Fails the commit if syntax errors are found

**Time:** < 1 second

### Commit-Msg
**Runs:** After commit message is written
**What it does:**
- Warns if commit doesn't follow conventional format (`feat:`, `fix:`, etc.)
- Validates `Co-Authored-By:` format if present
- Warns if subject line is too long (> 72 chars)

**Time:** < 1 second

## Conventional Commit Format

```
type(scope): description

[optional body]

[optional footer]

Co-Authored-By: Name <email@example.com>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `test` - Adding or updating tests
- `refactor` - Code refactoring
- `chore` - Maintenance tasks
- `perf` - Performance improvements
- `style` - Code style changes (formatting, etc.)
- `build` - Build system changes
- `ci` - CI/CD changes

## Bypassing Hooks

If you need to bypass hooks temporarily:
```bash
git commit --no-verify -m "message"
```

## Updating Hooks

To modify hook behavior, edit the `.py` files:
- `pre-commit.py` - Pre-commit validation logic
- `commit-msg.py` - Commit message validation logic

The `.bat` files are Windows wrappers that call the Python scripts.
