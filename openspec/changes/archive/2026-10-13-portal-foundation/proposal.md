## Why

The seed has no runtime or reproducible specification workflow. Establish
these without implying that patient workflows or production gates are finished.

## What Changes

- Initialize pinned repository-local OpenSpec with telemetry disabled,
  GitHub Copilot tooling and the default spec-driven schema.
- Establish Poetry-managed Django LTS/PostgreSQL, pytest, typed Python,
  Black (120), isort (Black profile) and explicit environment configuration.
- Document architecture, requirements provenance and actual bootstrap commands.
- Surface missing production configuration instead of insecure fallbacks.

## Capabilities

### New Capabilities

- `portal-runtime`: reproducible runtime, spec lifecycle and fail-closed settings.

### Modified Capabilities

None. No implemented canonical capability exists.

## Impact

Root manifests/lockfiles, `config/`, `manage.py`, foundation tests and OpenSpec
configuration. No integrations, patient data, publication or deployment.

## Execution Status

Implemented: pinned local CLI initialized, genuine dependency lockfiles,
PostgreSQL-only runtime, explicit production checks and standard entry points.
Eight foundation tests passed following expected missing-runtime failures.
Django, mypy, formatter and strict OpenSpec checks passed.
