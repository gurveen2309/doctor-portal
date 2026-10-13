# Doctor's Portal

A portal-first application for one Indian clinic and one doctor, built around
structured patient requests and a doctor-managed queue.

The approved architecture is a Django modular monolith with PostgreSQL,
server-rendered Django templates and selective HTMX. OpenSpec changes define
requirements and acceptance scenarios before implementation.

This repository is being initialized locally. No GitHub publication, production
deployment or use of real patient data is part of initialization.

## Design and implementation baseline

- [Approved requirements snapshot](docs/approved-requirements.md)
- [Architecture and file boundaries](docs/architecture.md)
- [Sequential implementation plan](docs/implementation-plan.md)

The snapshot records the confirmed requirements supplied to the implementation
session, not a verbatim copy of the original approval artifact.

**Current state:** verified Django/PostgreSQL runtime and initialized OpenSpec.
Identity, scheduling, clinical workflows and manual operations remain pending.
This is not a production-ready patient application.

## Saved foundation inputs

`package.json` pins the repository-local OpenSpec CLI to `1.14.1` and declares
Node `>=20.19.0`, based on public registry metadata verified by the coordinating
session. `pyproject.toml` declares Django 5.2 LTS, PostgreSQL driver, maintained
MFA tooling, pytest, Black (120), isort (Black profile), and type-check tooling.
Dependencies were resolved with Python 3.13 and Poetry 2.4.1.
`poetry.lock` and `package-lock.json` contain actual resolved dependencies.

OpenSpec 1.14.1 is initialized with GitHub Copilot support and
`--no-copilot-cloud`. Every invocation through npm scripts disables telemetry.
Changes contain proposal, design, tasks and acceptance scenarios. Strict
validation passed for all five initial changes. Archive only verified work.

Eight foundation tests passed after six expected missing-runtime failures.
Django checks and foundation mypy/Black/isort checks passed.
The runtime rejects missing secrets/database configuration and reports unmet
production gates. `.env.example` is not loaded automatically; export variables
explicitly. No production secret or delivery backend is supplied.

## Local setup

Use Python 3.11-3.14, Node >=20.19, Poetry and PostgreSQL. The verified host
used Python 3.13, Node 25.9 and an isolated PostgreSQL 17 Docker container.
Use your own development-only database credentials; never reuse synthetic
test secrets for production.

```sh
npm ci --ignore-scripts
npm run spec:version
npm run spec:help
poetry install
# Export DJANGO_ENV, DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS and POSTGRES_*
# as documented in .env.example before Django commands.
poetry run pytest tests/test_foundation.py -q
poetry run python manage.py check
npm run spec:validate
```

Initialization was performed with
`npm run spec -- init --tools github-copilot --no-copilot-cloud`.
Do not reinitialize or overwrite existing artifacts. Inspect work with
`npm run spec -- status --change <name>` and
`npm run spec -- instructions apply --change <name>`.
`npm run spec:validate` runs the verified `validate --all --strict` flags.
`npm run spec -- archive <name> --yes` syncs completed capability specs; use it
only after implementation and verification.

Follow the sequential implementation plan: observe intended test failures,
implement the increment, run targeted and integrated checks on PostgreSQL,
then validate/archive/commit only verified work. Real-provider onboarding,
legal/privacy/dispensing review, hosting, backups and tested restoration remain
production gates. WhatsApp/outbox automation remains a later pilot.
