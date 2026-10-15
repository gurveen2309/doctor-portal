## Context

Approved architecture is one Django application, PostgreSQL and templates.
Execution approval resolved. Foundation is verified; other changes remain pending.

## Goals / Non-Goals

Goals: local reproducibility, explicit settings, visible production failure
and an actual CLI-backed spec lifecycle.

Non-goals: patient functionality, provider/hosting selection, production
readiness, global tooling changes and custom OpenSpec schemas.

## Decisions

Poetry owns Python dependencies; npm owns local OpenSpec `1.14.1`, confirmed
by the coordinator's public registry inspection. Node must be at least 20.19.
Use a maintained Django 5.2 LTS release compatible with the approved Python
range. Lock resolved versions only through actual package-manager execution.

`config/settings.py` uses explicit environment configuration, PostgreSQL,
`TIME_ZONE = "Asia/Kolkata"` and `USE_TZ = True`. No fallback SQLite, generated
production secret, debug mode or console/fake delivery.
`config/checks.py` reports named production gates; unavailable real delivery,
insecure transport and missing secrets produce visible errors.
`manage.py`, `config/urls.py` and `config/wsgi.py` are standard entry points.

Inspect installed CLI version/help, initialize using supported GitHub Copilot
flags, obtain artifact/status instructions, validate strictly and archive only
verified implementation. Every invocation sets `OPENSPEC_TELEMETRY=0` and
`DO_NOT_TRACK=1`. Disable unrelated cloud files only if supported.

## Risks / Trade-offs

- Published CLI flags may differ from main-branch documentation: check help.
- Missing PostgreSQL requires approved setup, not SQLite concurrency claims.
- Synthetic test success cannot establish legal/provider/restore readiness.

## Migration Plan

No application tables or patient records exist. Subsequent app increments
create migrations. Actual Poetry/npm dependency resolution produced lockfiles.

## Verification

First source tests in `tests/test_foundation.py` specify timezone and
PostgreSQL behavior. Verify intended failure before implementation, extend
with production-gate tests, then run targeted pytest, Django checks,
formatting/types and strict CLI validation. Record actual commands/results.
