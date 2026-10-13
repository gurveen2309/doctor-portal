# Doctor's Portal

A portal-first application for one Indian clinic and one doctor, built around
structured patient requests and a doctor-managed queue.

The approved architecture is a Django modular monolith with PostgreSQL,
server-rendered Django templates and selective HTMX. OpenSpec changes define
requirements and acceptance scenarios before implementation.

This is a local synthetic implementation. No GitHub publication, production
deployment, real patient data or external patient messages are authorized.

## Design and implementation baseline

- [Approved requirements snapshot](docs/approved-requirements.md)
- [Architecture and file boundaries](docs/architecture.md)
- [Sequential implementation plan](docs/implementation-plan.md)
- [Production and operating gates](docs/production-gates.md)

The snapshot records the confirmed requirements supplied to the implementation
session, not a verbatim copy of the original approval artifact.

**Current state:** the portal-first core is implemented locally: verified
account/patient grants, bounded OTP and doctor MFA, structured intake and an
approval-based shared calendar, private clinical revisions and explicit repeat
decisions, manual fulfillment/INR records, and patient/doctor forms.
This is **not production-ready**. WhatsApp/outbox automation remains deferred.

## Reproducible tooling

`package.json` pins the repository-local OpenSpec CLI to `1.14.1` and declares
Node `>=20.19.0`. `pyproject.toml` declares Django 5.2 LTS, PostgreSQL driver, maintained
MFA tooling, pytest, Black (120), isort (Black profile), and type-check tooling.
Dependencies were resolved with Python 3.13 and Poetry 2.4.1.
`poetry.lock` and `package-lock.json` contain actual resolved dependencies.

OpenSpec 1.14.1 is initialized with GitHub Copilot support and
`--no-copilot-cloud`. Every invocation through npm scripts disables telemetry.
Changes contain proposal, design, tasks and acceptance scenarios. Strict
validation covers all five core capabilities. Archive only verified work.

Acceptance on 2026-10-13: **73 synthetic tests passed on PostgreSQL 17**,
including independent-connection calendar/OTP/revision concurrency, permission
and guardian boundaries, CSRF, immutable history, and exception-report/log
privacy. Django/schema checks and strict application typing passed. These are
local results, not real-provider, backup-restore, legal or pilot-outcome evidence.

The runtime rejects missing secrets/database configuration and reports unmet
production gates. `.env.example` is not loaded automatically: export variables
explicitly. No production secret or real delivery backend is supplied.

## Local setup

Use Python 3.11-3.14, Node >=20.19, Poetry and PostgreSQL. The verified host
used Python 3.13, Node 25.9 and an isolated PostgreSQL 17 Docker container.
Use your own development-only database credentials; never reuse synthetic
test secrets for production.

```sh
npm ci --ignore-scripts
npm run spec:version
npm run spec:help
npm run assets
poetry env use python3.13 # Or another installed supported interpreter.
poetry install
# Export DJANGO_ENV, DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS and POSTGRES_*
# as documented in .env.example before Django commands.
poetry run python manage.py migrate --noinput
poetry run python manage.py check
poetry run python manage.py setup_doctor
poetry run python manage.py runserver 127.0.0.1:8000
```

Use synthetic records only. `setup_doctor` confirms a real authenticator before
creating the single doctor; its setup/recovery output is sensitive and must not
be recorded, redirected or sent to third-party QR services. Doctor sign-in is
`/accounts/doctor-login/`, workspace `/doctor/`, patient portal `/portal/`.
Patient browser OTP sign-in intentionally remains unavailable until a real
provider adapter is configured. The pytest suite uses memory-only delivery;
there is no development console OTP or MFA bypass.

```sh
DJANGO_ENV=test poetry run pytest -q --tb=short --show-capture=no
poetry run python manage.py makemigrations --check --dry-run
poetry run mypy config accounts patients audit clinic intake appointments clinical operations manage.py
poetry run isort --check-only config accounts patients audit clinic intake appointments clinical operations tests manage.py
poetry run black --check config accounts patients audit clinic intake appointments clinical operations tests manage.py
npm run spec:validate
git diff --check
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
