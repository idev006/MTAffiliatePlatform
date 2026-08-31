# Path and Configuration Policy

Status: IMPLEMENTATION HANDOFF POLICY
Date: 2026-08-31

## 1. Purpose

Define project-wide rules for filesystem paths, runtime directories, settings and configuration so the application remains portable, testable, package-friendly and free from machine-specific hard-coded assumptions.

This policy is mandatory for all new code.

## 2. Governing Principles

1. Relative-first path design.
2. One authoritative PathManager / RuntimePaths service resolves filesystem locations.
3. No business/domain engine constructs machine-specific filesystem paths.
4. Operational and business-tunable values belong in typed configuration, not scattered constants.
5. TOML is the baseline human-editable configuration format.
6. Secrets are referenced separately and must not be committed in ordinary TOML files.
7. Effective configuration must be inspectable and auditable.
8. Tests must be able to replace roots/configuration without touching the real user filesystem.

## 3. PathManager Responsibility

A dedicated `PathManager` (or equivalent `RuntimePaths` service) is the only component allowed to resolve canonical runtime filesystem locations.

Conceptual responsibilities:
- detect application/install root;
- resolve runtime/data/config/log/cache/outbox/temp roots;
- normalize paths with `pathlib.Path`;
- create required writable directories at bootstrap;
- validate writable/read-only expectations;
- prevent accidental path escape where a managed root is required;
- expose relative logical locations to application code;
- support Portable Mode, Farm Mode, tests and packaged executable layouts.

PathManager is infrastructure/bootstrap-level functionality, not domain logic.

## 4. Canonical Runtime Roots

Conceptual roots:

```text
ApplicationRoot
RuntimeRoot
ConfigRoot
DataRoot
LogRoot
CacheRoot
OutboxRoot
TempRoot
ArtifactRoot
ToolRoot
```

Portable example:

```text
MTAffiliatePlatform/
├─ app/
├─ config/
│  ├─ default.toml
│  ├─ portable.toml
│  └─ local.toml          # local override, normally gitignored
├─ data/
│  └─ app.db
├─ logs/
├─ cache/
├─ outbox/
├─ artifacts/
├─ tools/
└─ runtime/
```

The exact physical root may differ in packaged/Farm Mode, but application code consumes logical paths through PathManager rather than assuming this directory layout directly.

## 5. Relative-First Rule

Repository/runtime-owned paths are expressed relative to an explicit managed root.

Preferred:

```text
config/default.toml
logs/
data/app.db
artifacts/publish-evidence/
```

Prohibited in source/business configuration:

```text
C:\Users\someone\Desktop\project\data\app.db
D:\Shopee\videos\...
/home/user/project/...
```

Absolute paths may exist only as resolved runtime values, external user-selected resources, OS/tool-discovered locations, or explicitly configured deployment mounts. They must never be baked into source code.

## 6. Path Resolution Rules

- Use Python `pathlib.Path` as baseline path abstraction.
- Avoid manual path concatenation using string separators.
- Do not depend on current working directory for correctness.
- Resolve from explicit roots supplied by bootstrap/composition root.
- Store canonical managed paths as relative logical values where practical.
- Convert to absolute resolved paths only at infrastructure boundary when an OS/library call requires it.
- Persisting paths in DB should prefer stable relative/logical references when the file belongs to managed project storage.
- External user files may require absolute/source references; record provenance and do not silently copy/relocate unless policy says so.

## 7. Testability

Tests must be able to instantiate PathManager with a temporary root.

Example conceptual test composition:

```text
TempRoot
├─ config/
├─ data/
├─ logs/
└─ outbox/
```

No test should require the developer's real home directory, desktop, repository checkout path or production data directory unless explicitly classified as an environment integration test.

## 8. TOML Configuration Hierarchy

Baseline hierarchy, lowest to highest precedence:

```text
built-in safe defaults
        ↓
config/default.toml
        ↓
config/<deployment-profile>.toml
        ↓
config/local.toml
        ↓
environment variables / secret references
        ↓
explicit command-line/runtime override where approved
```

Examples of deployment profiles:
- `portable.toml`
- `farm.toml`
- `test.toml`

The exact override mechanism is implemented by the configuration service but precedence must be deterministic and documented.

## 9. What Belongs in TOML

Examples:
- API host/port defaults;
- database mode/connection reference;
- relative runtime directory names;
- worker heartbeat/lease defaults;
- retry/backoff limits;
- resource thresholds;
- outbox limits;
- logging level/retention;
- feature flags;
- ruleset/profile references;
- device-host capacity settings;
- screen-stream quality profiles;
- product/offer policy values after business validation;
- media/fingerprint algorithm profile references.

Do not place secrets such as passwords, tokens or session cookies directly in committed TOML.

## 10. Hard-Coding Policy

Hard-coded values are acceptable only when they are true source-level invariants such as:
- protocol constant required by a standard;
- enum/state identifier;
- schema field name;
- mathematically fixed constant;
- deliberately immutable safety invariant documented by architecture.

Operational/business values that may vary by deployment, experiment, policy, platform behavior or scale must be configuration/rules, not hidden constants.

Suspicious examples that require review:
- fixed `10` devices;
- fixed heartbeat seconds;
- fixed retry count;
- fixed Shopee basket limit;
- fixed scoring weights;
- fixed local directories;
- fixed API URLs;
- fixed screen dimensions/coordinates;
- fixed timeout values scattered in adapters.

## 11. Typed Settings

Configuration is parsed into typed settings objects, baseline Pydantic v2.

Requirements:
- validation at startup;
- explicit units in names/types where ambiguity exists;
- bounded ranges for risky numeric values;
- human-readable validation errors;
- effective configuration snapshot available for diagnostics;
- secret values redacted from logs/diagnostics;
- configuration version/profile recorded where operationally relevant.

Domain engines should receive only the typed policy/config objects they need, not a global settings singleton.

## 12. Configuration Ownership

Configuration is divided conceptually into:
- bootstrap/deployment settings;
- infrastructure settings;
- operational limits;
- domain/business rulesets;
- feature flags;
- secret references.

Business rulesets are versioned separately when they affect decisions that must be auditable. Jobs/decisions should record the applicable ruleset/config version where needed.

## 13. Reload Policy

Not every setting is hot-reloadable.

Classes:
- STARTUP_ONLY — DB engine, fundamental roots, process topology;
- RELOADABLE_SAFE — logging level, some resource thresholds;
- VERSIONED_JOB_POLICY — scoring/ranking/retry/business policy; running jobs retain the captured version;
- SECRET_ROTATABLE — credentials through approved secret mechanism.

A config reload must never silently change the semantics of an already-running job that is supposed to use a captured ruleset.

## 14. Packaging Rule

Packaged executables must not assume writable access inside immutable application bundle resources.

Writable data/config/logs/outbox live under runtime paths resolved by PathManager.

Bundled read-only resources/tools are resolved separately from writable data roots.

## 15. Developer Acceptance Criteria

Foundation is conforming when:
1. PathManager/RuntimePaths exists behind an injectable interface/service.
2. No source module relies on developer-specific absolute paths.
3. Core behavior does not depend on current working directory.
4. TOML loader supports deterministic profile/override precedence.
5. typed settings validation exists.
6. test suite can use temporary roots/config files.
7. effective config can be inspected with secrets redacted.
8. architecture/static checks can detect obvious direct path/config violations.
9. mutable operational constants are centralized/configurable.
10. packaged and source-run path behavior have tests.

## 16. Governing Rule

**Resolve paths once at the infrastructure/bootstrap boundary; pass logical/typed values inward. Configure policy explicitly; do not scatter environment assumptions through code.**
