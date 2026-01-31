# AGENTS PLAYBOOK

This document is the single source of truth for autonomous and human agents working inside `top-stream-services-data-portugal`. It consolidates setup steps, canonical commands, quality gates, and code-style expectations. Read it once before touching the repo; skim it again whenever workflows or tooling change.

## 1. QUICK ORIENTATION
1. Python 3.12/3.13 only. Local dev assumes virtualenv/pyenv; CI pins 3.12 via GitHub Actions.
2. Core script is `top_pt_stream_services.py`; smoke tests live in `test_refactoring.py`.
3. There are no Cursor or Copilot override files (`.cursor/rules`, `.cursorrules`, `.github/copilot-instructions.md` are absent); follow this guide plus standard repo docs.
4. Documentation of note: `SETUP.md`, `README.md`, `DEVELOPER.md`, `CONTRIBUTING.md`, `API.md`.
5. Automation: `.github/workflows/code-quality.yml` enforces black, isort, flake8, bandit, and bytecode compilation.

## 2. ENVIRONMENT & DEPENDENCIES
- **Create env**: `python -m venv .venv && source .venv/bin/activate`
- **Core deps**: `pip install -r requirements.txt`
- **Dev deps**: `pip install -r requirements-dev.txt`
- **Env vars**: copy `.env.example` → `.env`; never commit `.env`. Required keys: `CLIENT_ID`, `CLIENT_SECRET`, `ACCESS_TOKEN`, `REFRESH_TOKEN`; optional flags `KIDS_LIST`, `PRINT_LISTS`; optional integration key `TMDB_API_KEY` (used to enrich data with TMDB & IMDb IDs).
- **Pre-commit**: `pre-commit install` after installing dev deps to mirror CI checks locally.

## 3. BUILD & EXECUTION COMMANDS
| Task | Command |
| --- | --- |
| Run main script (default behavior) | `python top_pt_stream_services.py`
| Manual run with inline env vars | `CLIENT_ID=... ACCESS_TOKEN=... python top_pt_stream_services.py`
| Compile-time sanity check | `python -m py_compile top_pt_stream_services.py`
| Install prod deps | `pip install -r requirements.txt`
| Install all tooling | `pip install -r requirements.txt && pip install -r requirements-dev.txt`
| Refresh OAuth tokens (manual) | see `SETUP.md` curl example; never script secrets into repo |

## 4. TESTING PLAYBOOK
1. **Default suite**: `python test_refactoring.py` (runs bundled smoke tests, prints ✓ markers).
2. **Pytest friendly**: after `pip install pytest`, run `python -m pytest test_refactoring.py`.
3. **Single test focus**: `python -m pytest test_refactoring.py -k config_initialization` (replace substring as needed: `tracker_initialization`, `main_function_exists`).
4. **Ad-hoc validation**: `python -m py_compile top_pt_stream_services.py` ensures syntax viability for CI parity.
5. **When adding files**: co-locate new tests beside implementation or extend `test_refactoring.py`; keep names `test_*` for pytest discovery.

## 5. LINT, FORMAT, SECURITY
| Check | Command | Notes |
| --- | --- | --- |
| Black | `black --line-length 120 --target-version py312 top_pt_stream_services.py` | Enforced via CI & pre-commit |
| isort | `isort --profile black --line-length 120 top_pt_stream_services.py` | Keep stdlib/3rd-party/local sections clean |
| Flake8 | `flake8 top_pt_stream_services.py --max-line-length=120` | Config in `.flake8`; ignores `E203`, `W503` |
| Bandit | `bandit -r top_pt_stream_services.py` | Security scan; exclude `tests/` |
| Pre-commit | `pre-commit run --all-files` | Mirrors hooks (trim, eof, yaml, debug statements) |

Always run the full lint stack before opening a PR. CI will block on any failure—avoid red builds by mirroring these steps locally.

## 6. CODE STYLE GUIDELINES
**Formatting**
- Black line length 120; target Python 3.12 semantics.
- Use trailing commas for multi-line collections to keep diffs minimal.
- isort uses profile `black`, multi-line output 3.

**Imports**
- Named imports preferred over wildcard.
- Group order: stdlib → third-party (`requests`, `bs4`, `dotenv`, etc.) → local modules.
- Keep `__all__` explicit when exporting utility helpers.

**Typing**
- Public functions and class methods require type hints.
- Prefer `collections.abc` types (`Sequence`, `Mapping`) for parameters; use concrete types for return values.
- Use `Literal` and `TypedDict` when modeling payloads; avoid `Any` unless unavoidable (document why).

**Naming**
- Classes: `PascalCase` (`StreamingServiceTracker`).
- Functions/methods: `snake_case` (`scrape_top10`).
- Constants/config: `UPPER_SNAKE_CASE` (`REQUEST_TIMEOUT`).
- Private helpers: prefix `_` inside classes/modules for clarity.

**Docstrings & Comments**
- Module + class docstrings for complex flows; inline comments only for non-obvious logic (retry math, parsing quirks).
- Keep documentation in sync with `README.md`/`DEVELOPER.md` when behavior changes.

**Error Handling & Logging**
- Wrap all network I/O with `try/except requests.exceptions.RequestException`; include timeout parameters (default `REQUEST_TIMEOUT=30`).
- Never swallow exceptions silently—log via `logging` with actionable context (service name, list slug, status code).
- Use retry decorators (`retry_request`) for transient failures; cap attempts using `MAX_RETRIES` (10) and exponential backoff.
- When updating Trakt lists, surface partial failures but continue processing other services to maximize successful updates.

**Environment & Secrets**
- Access secrets via `os.getenv`; never default to plaintext tokens.
- Guard required env vars early (`_validate_trakt_setup`) and raise descriptive errors.

**Data & Payloads**
- Normalize scraped tuples to 7-tuples `(rank, title, slug, year, starring, tmdb_id, imdb_id)` before building Trakt payloads; downstream helpers may ignore the extra fields when only `(rank, title, slug)` are needed but must accept the full shape.
- Use helper factories (`create_type_trakt_list_payload`) to keep payload shape consistent.
- Validate API responses (status codes, JSON keys) before acting.

**Backward Compatibility**
- Maintain operational `main()` and legacy globals; CI smoke test enforces this. Any architectural change must keep CLI usage untouched unless README is updated simultaneously.

## 7. GIT & WORKFLOW
- Branch naming: `feat/<topic>`, `fix/<bug>`, or `chore/<task>`.
- Rebase over merge whenever possible; keep history linear for easier diffing.
- Run `pre-commit run --all-files` plus the full lint/test suite before pushing.
- Pull requests should mention affected streaming services and include manual test notes (command log + result summary).

## 8. CI REFERENCE
- Workflow: `.github/workflows/code-quality.yml` runs on push/PR to `main`.
- Steps: checkout → setup Python 3.12 → install `requirements-dev.txt` → black check → flake8 → bandit → isort check → (placeholder `mypy`) → `py_compile`.
- Keep workflows fast (<3 min). If you add heavier checks, gate behind optional jobs or run on nightly schedule.

## 9. SUPPORTING SCRIPTS & DOCS
- `diagnose_flixpatrol.py`: debugging helper for scraping issues; run with same env vars as main script.
- `DIAGNOSTIC_TOOL.md`: describes troubleshooting flows; keep in sync when altering telemetry/logging.
- `API.md`: canonical docs for FlixPatrol + Trakt endpoints; update when endpoints change.
- `SETUP.md`: onboarding instructions; update if dependencies or OAuth steps change.

## 10. ADDING OR MODIFYING FEATURES
1. Create/assign issue, outline scope.
2. Update `Config` for new service URLs or timeouts first.
3. Extend `StreamingServiceTracker` data structures (`*_list_data`) before touching business logic.
4. Add/adjust scraping + payload helpers; ensure new lists respect naming conventions and `display_numbers` flag.
5. Cover behavior in `test_refactoring.py` or new tests (prefer pytest-compatible functions).
6. Update docs + AGENTS.md when workflows change.

## 11. TROUBLESHOOTING CHECKLIST
- **ImportError**: ensure repo root is on `sys.path` (tests add it automatically).
- **HTTP failures**: verify env tokens; run with `PRINT_LISTS=True` for verbose logging.
- **CI lint failure**: run the specific tool locally; remember `black`/`isort` share the same line-length.
- **Bandit noise**: use targeted `nosec` comments sparingly and justify in PR.
- **Rate limits**: honor retry caps; avoid simultaneous manual + CI runs that hammer Trakt.

## 12. STATE OF RULESETS
- Cursor rules: none present in repo.
- GitHub Copilot instructions: none (`.github/copilot-instructions.md` missing).
- Therefore this AGENTS file plus repo docs define the entire policy surface.

## 13. FINAL REMINDERS
- Keep responses concise in PRs/issues; include exact commands executed and outputs summarized.
- Never commit secrets, OAuth tokens, or `.env` files.
- Prefer deterministic scripts—no random sleeps or unordered dict reliance.
- When in doubt, mirror the structure/patterns already in `StreamingServiceTracker` and related helpers.
- Update this document whenever you change commands, tooling, or style expectations so future agents stay aligned.
