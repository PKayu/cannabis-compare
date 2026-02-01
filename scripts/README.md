# Development Scripts

Utility scripts for common development tasks on Windows.

## Quick Reference

| Script | Purpose |
|--------|---------|
| `commit-helper.bat` | Organize changes into logical commits |
| `start-dev.bat` | Start both backend and frontend servers |
| `start-backend.bat` | Start backend server only |
| `start-frontend.bat` | Start frontend server only |
| `install-deps.bat` | Install all dependencies (Python + Node) |
| `fix-python313.bat` | Fix Python 3.13 compatibility issues |
| `run-tests.bat` | Run all tests (pytest + jest) |
| `cleanup-docs.sh` | Audit documentation health (bash script) |

## Prerequisites

- Python 3.10+ installed and in PATH
- Node.js 18+ installed
- Git Bash or Windows Terminal (for .sh scripts)

---

## Scripts Reference

### commit-helper.bat

Organize uncommitted changes into logical commits with generated commit messages.

```cmd
scripts\commit-helper.bat
```

Features:
- Groups changes by file type (backend, frontend, scrapers, tests, docs, etc.)
- Suggests conventional commit messages based on changes
- Interactive selection of which changes to commit together
- Supports Co-Authored-By header generation

Workflow:
1. Shows all uncommitted changes grouped by category
2. Select a group to commit, specific files, or commit all
3. Review/edit the suggested commit message
4. Automatically stages and commits selected changes

Example output:
```
[SCRAPER] (3 files)
  [modified  ] backend/services/scrapers/wholesome_co_scraper.py
              +42/-12

[FRONTEND] (2 files)
  [untracked ] frontend/components/NewProduct.tsx
```

### start-dev.bat

Starts both backend and frontend servers in separate terminal windows.

```cmd
scripts\start-dev.bat
```

- Creates venv if missing
- Installs dependencies if needed
- Opens API docs in browser
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000

### start-backend.bat

Starts only the backend FastAPI server.

```cmd
scripts\start-backend.bat
```

- Activates virtual environment
- Runs uvicorn with hot reload
- **Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### start-frontend.bat

Starts only the frontend Next.js server.

```cmd
scripts\start-frontend.bat
```

- Runs `npm run dev`
- **Server**: http://localhost:3000

### install-deps.bat

Complete dependency installation for both backend and frontend.

```cmd
scripts\install-deps.bat
```

What it installs:
1. Creates Python virtual environment
2. Installs all Python packages (FastAPI, SQLAlchemy, etc.)
3. Installs Node.js packages via npm

Run this after cloning the repository.

### fix-python313.bat

Fixes SQLAlchemy compatibility issues when using Python 3.13.

```cmd
scripts\fix-python313.bat
```

- Upgrades SQLAlchemy to 2.0.36+
- Verifies backend imports
- Starts server if successful

Use this if you see errors like:
```
ModuleNotFoundError: No module named 'sqlalchemy.util._compat_py3k'
```

### run-tests.bat

Runs all test suites.

```cmd
scripts\run-tests.bat
```

- Runs backend pytest tests
- Runs frontend jest tests
- Shows summary of results

### cleanup-docs.sh

Bash script that audits documentation health and organization.

```bash
bash scripts/cleanup-docs.sh
```

Checks:
- Naming conventions
- File organization
- TODO/FIXME markers
- Workflow status
- Critical file existence

---

## Troubleshooting

### "venv not found" error

Run the install script first:
```cmd
scripts\install-deps.bat
```

### Port already in use

Kill existing processes:
```cmd
# Find process using port 8000
netstat -ano | findstr :8000
# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Python version issues

Ensure Python 3.10+ is installed:
```cmd
python --version
```

If using Python 3.13, run:
```cmd
scripts\fix-python313.bat
```

### npm errors

Clear npm cache and reinstall:
```cmd
cd frontend
npm cache clean --force
rmdir /s /q node_modules
npm install
```

---

## Related Documentation

- [Getting Started](../docs/GETTING_STARTED.md) - Full setup guide
- [Testing Guide](../docs/TESTING.md) - Testing documentation
- [Architecture](../docs/ARCHITECTURE.md) - System design
