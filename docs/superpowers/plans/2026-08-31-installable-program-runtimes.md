# Installable Program Runtimes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make Program 1, Program 2, Program 3 and the combined Back Office easy to install/run independently while preserving one document-driven shared core.

**Architecture:** Keep the existing monorepo and inward dependency boundaries. Add separate runtime composition modules, profile-specific TOML files, console entrypoints and route gating so each install exposes only its intended program surface.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, Pydantic settings, SQLAlchemy/Alembic, pytest, Ruff.

## Global Constraints

- Use only `D:\dev\MTAffiliatePlatform\.venv` for local verification commands.
- Do not split domain/application code into separate repos.
- Do not duplicate business policy in installer or CLI code.
- Runtime composition may depend on concrete adapters; domain and engines may not.
- Program-specific installs must remain fake/testable and evidence-gated for real Shopee/browser/Android behavior.
- Config/settings and database files may be committed because the project owner confirmed they contain no secrets.
- `.venv`, caches, logs and generated runtime artifacts stay local.

---

### Task 1: Program-Gated API Factory

**Files:**
- Modify: `src/mtaffiliate/interfaces/api/app.py`
- Test: `tests/contract/test_program_runtime_profiles.py`

**Interfaces:**
- Consumes: existing `create_app(settings, program1, program2, program3)`.
- Produces: `create_app(..., enabled_programs: set[str] | None = None)` where `None` enables all programs and a specific set gates routes.

- [x] **Step 1: Write failing route-gating tests**

```python
def test_program1_profile_exposes_only_program1_routes() -> None:
    client = TestClient(create_app(Settings(), enabled_programs={"program1"}))
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/program1/shortlist").status_code == 200
    assert client.post("/api/v1/program2/observations", json={"observations": []}).status_code == 404
    assert client.post("/api/v1/program3/publish/evaluate", json={}).status_code == 404
```

- [x] **Step 2: Implement route gating**

Wrap Program 1, Program 2 and Program 3 route declarations in `if "programN" in enabled:` blocks and reject unknown program names with `ValueError`.

- [x] **Step 3: Run API profile tests**

Run: `D:\dev\MTAffiliatePlatform\.venv\Scripts\python.exe -m pytest tests\contract\test_program_runtime_profiles.py`

### Task 2: Separate Durable Bootstrap Functions

**Files:**
- Create: `src/mtaffiliate/bootstrap/program2.py`
- Create: `src/mtaffiliate/bootstrap/program3.py`
- Modify: `src/mtaffiliate/bootstrap/program2_program3.py`
- Test: `tests/integration/sqlite/test_program_runtime_bootstrap.py`

**Interfaces:**
- Produces: `build_durable_program2(settings: Settings, *, project_root: Path) -> Program2Service`
- Produces: `build_durable_program3(settings: Settings, *, project_root: Path) -> Program3Service`

- [x] **Step 1: Add tests for separate bootstraps**

Verify Program 2 can ingest/select offers and Program 3 can evaluate/record publish status using separate SQLite URLs.

- [x] **Step 2: Implement bootstrap split**

Move Program 2 service wiring into `program2.py`, Program 3 service wiring into `program3.py`, and keep `program2_program3.py` as a compatibility wrapper returning both.

- [x] **Step 3: Run SQLite bootstrap tests**

Run: `D:\dev\MTAffiliatePlatform\.venv\Scripts\python.exe -m pytest -m integration tests\integration\sqlite\test_program_runtime_bootstrap.py --timeout=60`

### Task 3: Runtime Modules and Console Scripts

**Files:**
- Create: `src/mtaffiliate/runtime/_factory.py`
- Create: `src/mtaffiliate/runtime/program1.py`
- Create: `src/mtaffiliate/runtime/program2.py`
- Create: `src/mtaffiliate/runtime/program3.py`
- Create: `src/mtaffiliate/runtime/all.py`
- Create: `src/mtaffiliate/interfaces/cli/run_api.py`
- Modify: `src/mtaffiliate/main.py`
- Modify: `pyproject.toml`
- Test: `tests/contract/test_program_runtime_profiles.py`

**Interfaces:**
- Produces ASGI apps: `mtaffiliate.runtime.program1:app`, `mtaffiliate.runtime.program2:app`, `mtaffiliate.runtime.program3:app`, `mtaffiliate.runtime.all:app`.
- Produces console scripts: `mtaffiliate-program1-api`, `mtaffiliate-program2-api`, `mtaffiliate-program3-api`, `mtaffiliate-all-api`.

- [x] **Step 1: Add import and CLI dispatch tests**

Import every runtime app and monkeypatch `uvicorn.run` to assert console scripts dispatch to the matching module path.

- [x] **Step 2: Implement runtime factory**

Load `config/<profile>.toml`, ensure runtime dirs, auto-migrate when configured, build only the services required by `enabled_programs`, and call the gated API factory.

- [x] **Step 3: Add pyproject scripts**

Add `[project.scripts]` entries for the four API launchers.

### Task 4: Program-Specific Config Profiles and Installer Documentation

**Files:**
- Create: `config/program1.toml`
- Create: `config/program2.toml`
- Create: `config/program3.toml`
- Create: `docs/affiliate-platform/INSTALLATION_PROFILES.md`
- Modify: `README.md`

**Interfaces:**
- Program 1 default DB: `sqlite:///data/program1.db`
- Program 2 default DB: `sqlite:///data/program2.db`
- Program 3 default DB: `sqlite:///data/program3.db`

- [x] **Step 1: Add TOML profiles**

Each profile sets `[app].environment`, `[database].url`, and `[database].auto_migrate = true`.

- [x] **Step 2: Document install/run commands**

Document editable install, wheel-style console scripts, direct Uvicorn module paths, and the `MTAFFILIATE_PROJECT_ROOT`, `MTAFFILIATE_PROFILE`, `MTAFFILIATE_HOST`, `MTAFFILIATE_PORT` environment variables.

- [x] **Step 3: Run full local gates**

Run Ruff, core CI-equivalent, SQLite CI-equivalent and stress through `.venv`.

