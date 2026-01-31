# AGENTS PLAYBOOK

Single source of truth for agents working in `top-stream-services-data-portugal`. Read before modifying the repo.

## 1. QUICK ORIENTATION

- **Python 3.12/3.13 only** with virtualenv/pyenv
- **Core script**: `top_pt_stream_services.py` (single-file architecture)
- **Tests**: `test_refactoring.py` (pytest-compatible smoke tests)
- **Diagnostic helper**: `diagnose_flixpatrol.py`
- **No Cursor/Copilot rules**: `.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md` are absent
- **Key docs**: `README.md`, `SETUP.md`, `DEVELOPER.md`, `API.md`, `CONTRIBUTING.md`

## 2. ENVIRONMENT SETUP

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # Production deps
pip install -r requirements-dev.txt      # Dev deps (black, isort, flake8, bandit)
pre-commit install                        # Enable hooks
```

**Required env vars** (copy `.env.example` → `.env`, never commit):
`CLIENT_ID`, `CLIENT_SECRET`, `ACCESS_TOKEN`, `REFRESH_TOKEN`

**Optional**: `KIDS_LIST`, `PRINT_LISTS`, `TMDB_API_KEY`

## 3. COMMANDS

| Task | Command |
|------|---------|
| Run main script | `python top_pt_stream_services.py` |
| Syntax check | `python -m py_compile top_pt_stream_services.py` |
| Run all tests | `python test_refactoring.py` |
| Run tests (pytest) | `python -m pytest test_refactoring.py -v` |
| **Single test** | `python -m pytest test_refactoring.py -k "config_initialization"` |
| Format code | `black --line-length 120 --target-version py312 .` |
| Sort imports | `isort --profile black --line-length 120 .` |
| Lint | `flake8 --max-line-length=120` |
| Security scan | `bandit -r . --exclude ./tests` |
| All pre-commit | `pre-commit run --all-files` |

**Full lint stack**:
```bash
black --line-length 120 . && isort --profile black --line-length 120 . && flake8 && bandit -r .
```

## 4. CODE STYLE

### Formatting
- **Line length**: 120 chars (Black, isort, Flake8)
- **Target**: Python 3.12
- Flake8 ignores: `E203`, `W503` (see `.flake8`)

### Imports (order: stdlib → third-party → local)
```python
import logging
import os
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
```

### Typing
- Type hints **required** on public functions/methods
- Use `collections.abc` types for params, concrete types for returns
- Avoid `Any` unless documented

### Naming
| Type | Convention | Example |
|------|------------|---------|
| Classes | `PascalCase` | `StreamingServiceTracker`, `Config` |
| Functions | `snake_case` | `scrape_top10`, `update_list` |
| Constants | `UPPER_SNAKE_CASE` | `REQUEST_TIMEOUT`, `MAX_RETRIES` |
| Private | `_` prefix | `_validate_trakt_setup` |

### Error Handling
```python
try:
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
except requests.exceptions.RequestException as e:
    logging.error(f"Request failed: {e}")
    return None
```
- Never swallow exceptions silently
- Use `logging` with actionable context
- Use `retry_request` decorator for transient failures
- Constants: `REQUEST_TIMEOUT=30`, `MAX_RETRIES=10`, `BACKOFF_FACTOR=2`

### Data Structures
- Scraped data: 7-tuples `(rank, title, slug, year, starring, tmdb_id, imdb_id)`
- Use payload helpers: `create_type_trakt_list_payload`, `create_mixed_trakt_list_payload`
- Validate API responses before processing

## 5. ARCHITECTURE

### Key Classes
- `Config`: Centralized config (env vars, URLs, timeouts)
- `TMDBRateLimiter`: Rate limiting (40 req/10s)
- `StreamingServiceTracker`: Main orchestration class

### Adding New Services
1. Add URL to `Config.urls`
2. Create list data dict + slug constant
3. Update `_scrape_all_services()` and `_update_all_lists()`
4. Add tests and update docs

### Backward Compatibility
Global variables maintained for legacy support:
```python
config = Config()
CLIENT_ID = config.CLIENT_ID  # etc.
```

## 6. GIT WORKFLOW

- **Branches**: `feat/<topic>`, `fix/<bug>`, `chore/<task>`
- Rebase over merge; keep history linear
- Run full lint/test stack before pushing
- PRs: mention affected services + test notes

## 7. TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| `ImportError` | Ensure repo root on `sys.path` |
| HTTP failures | Verify tokens; `PRINT_LISTS=True` for debug |
| Lint failures | Check line-length consistency (120) |
| Rate limits | Honor `MAX_RETRIES`; avoid concurrent runs |

## 8. QUICK REFERENCE

```bash
# Format, lint, test
black --line-length 120 . && isort --profile black --line-length 120 . && flake8 && python test_refactoring.py

# Single test
python -m pytest test_refactoring.py -k "tracker_initialization" -v

# Debug run
PRINT_LISTS=True python top_pt_stream_services.py
```

## 9. SUPPORTING FILES

| File | Purpose |
|------|---------|
| `pyproject.toml` | Black/isort config |
| `.flake8` | Flake8 config |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `diagnose_flixpatrol.py` | Scraping debug |
| `API.md` | Endpoint documentation |

---

**Update this file** when commands, tooling, or style change.
