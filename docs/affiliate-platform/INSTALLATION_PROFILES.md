# Installation Profiles

Status: IMPLEMENTATION HANDOFF BASELINE
Date: 2026-08-31

## Purpose

MTAffiliatePlatform remains one authoritative repository and shared core, but it now exposes separate install/run surfaces for each operational program.

This supports installing or launching:
- Program 1 — Product Discovery / Product Intelligence
- Program 2 — Affiliate Offer Intelligence & Automation
- Program 3 — Content Publishing / Android Device Farm
- All programs together for integrated Back Office development

## Runtime Entry Points

Direct ASGI module paths:

```powershell
uvicorn mtaffiliate.runtime.program1:app --host 127.0.0.1 --port 8001
uvicorn mtaffiliate.runtime.program2:app --host 127.0.0.1 --port 8002
uvicorn mtaffiliate.runtime.program3:app --host 127.0.0.1 --port 8003
uvicorn mtaffiliate.runtime.all:app --host 127.0.0.1 --port 8000
```

Console scripts after package installation:

```powershell
mtaffiliate-program1-api
mtaffiliate-program2-api
mtaffiliate-program3-api
mtaffiliate-all-api
```

Console scripts read:
- `MTAFFILIATE_HOST`, default `127.0.0.1`
- `MTAFFILIATE_PORT`, default `8000`

## Configuration Profiles

The runtime factory loads `config/default.toml`, then the profile file, then `config/local.toml` if present.

Default profiles:
- Program 1: `config/program1.toml`
- Program 2: `config/program2.toml`
- Program 3: `config/program3.toml`
- Combined Back Office: `config/portable.toml`

Default database URLs:
- Program 1: `sqlite:///data/program1.db`
- Program 2: `sqlite:///data/program2.db`
- Program 3: `sqlite:///data/program3.db`
- Combined Back Office: `sqlite:///data/app.db`

The project owner confirmed configuration and database files may be committed because they contain no secrets. `.venv`, caches, logs and generated runtime artifacts remain local.

## Project Root

For source checkout development, the runtime can resolve the project root from the package source layout.

For packaged installs, set:

```powershell
$env:MTAFFILIATE_PROJECT_ROOT = "D:\dev\MTAffiliatePlatform"
```

The project root is where `config/`, `data/`, `migrations/` and `alembic.ini` are resolved.

## Route Boundaries

Program-specific runtimes expose only their own API routes:
- Program 1 runtime exposes `/api/v1/program1/*`
- Program 2 runtime exposes `/api/v1/program2/*`
- Program 3 runtime exposes `/api/v1/program3/*`

All runtimes expose `/health`.

The combined runtime exposes all program routes.

## Boundary Rule

Installers and runtime entry points are composition-root concerns only. They may wire settings, migrations and concrete repositories, but they must not contain scoring, duplicate policy, Scene policy, selector behavior or other business decisions.
