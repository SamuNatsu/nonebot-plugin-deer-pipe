# AGENTS.md

NoneBot2 plugin ("🦌管签到") using `uv_build`, `src/` layout, single package `nonebot_plugin_deer_pipe`. User-facing strings and the README are Chinese; keep replies in Chinese. Target Python 3.10 (`.python-version`, `requires-python`), so avoid 3.11+ syntax/stdlib.

## Commands

```bash
uv sync                         # install deps + editable package (lockfile is committed)
uv run python scripts/dev.py    # run the plugin in a console REPL (interactive TUI)
uv build                        # build wheel + sdist
```

- `.env` (gitignored, not committed) sets `DRIVER=~none` and `DEER_PIPE_DEV=1` for local dev. In a fresh clone, recreate it or prefix the run command with `DRIVER=~none`, otherwise `nonebot.init()` fails with `ImportError: Please install FastAPI first` (NoneBot defaults to the `~fastapi` driver, which is not a dependency).
- `DEER_PIPE_DEV=1` dumps each generated calendar/rank PNG into the localstore plugin cache dir (they are otherwise only returned as bytes).
- There is no test suite, linter, or formatter config. CI (`.github/workflows/nightly.yaml`) only builds the package. Verify behavior manually through the dev script.

## Architecture notes

- `requirements.py` calls `nonebot.require(...)` for the four runtime plugins and must be imported before `matchers.py`; `__init__.py` enforces the order. New plugin dependencies also belong in `inherit_supported_adapters(...)` in `__init__.py` and in `pyproject.toml`.
- `matchers.py` holds all command handlers; `database.py` the SQLModel/SQLite layer; `image.py` PIL rendering; `font.py` multi-font rendering that splits text by font cmap (MiSans + color emoji); `schedule.py` APScheduler jobs.
- The SQLite file is named `userdata-v{DATABASE_VERSION}.db` (`constants.py`). There are no migrations: any schema change requires bumping `DATABASE_VERSION`, which creates a fresh database and abandons old data. Scheduled `cleanup()` (Mondays 04:00) already deletes records outside the current month and users left without records.
- `PLUGIN_VERSION` is read from installed distribution metadata (`importlib_metadata.version`), so importing the package outside an installed env fails.

## Releases

- Version lives in `pyproject.toml`; commit history uses conventional prefixes (`feat:`, `fix:`, `refactor:`, `release: vX.Y.Z`).
- To release: bump `version`, commit as `release: vX.Y.Z`, then tag `vX.Y.Z` and push. Tags matching `v*` trigger `.github/workflows/pypi-publish.yaml` (PyPI upload); every push only builds artifacts.
