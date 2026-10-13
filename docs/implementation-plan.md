# Doctor's Portal implementation plan

> Execute inline in this isolated worktree using the executing-plans and
> test-driven-development skills. Do not create a large agent workflow.

**Goal:** Implement the approved portal-first core as sequential, independently
tested OpenSpec changes.

**Architecture:** Django modular monolith, PostgreSQL, native templates and
selective HTMX. Backend services own authorization and transactional decisions.

**Toolchain:** Poetry, pytest, Black (120), isort (Black profile), typed Python,
and a pinned repository-local OpenSpec CLI with telemetry disabled.

## Global constraints

The complete baseline is [approved-requirements.md](approved-requirements.md);
the file boundaries and transaction/permission interfaces are in
[architecture.md](architecture.md).

- One clinic and one doctor; India; `Asia/Kolkata`; aware datetimes.
- No real patient data, external patient messages, publishing, or deployment.
- Card numbers are identifiers, never authorization.
- All free text is potentially clinical.
- Every read/mutation/channel checks current permission.
- Explicit doctor decisions; no timeout approval or inferred medicine run-out.
- Real PostgreSQL tests establish concurrency, not SQLite.
- WhatsApp automation remains a later pilot.

## Execution status

All five core increments are implemented locally. Foundation preceded identity,
calendar, clinical and manual/UI test-first increments. Full PostgreSQL 17
acceptance passed 73 synthetic tests on 2026-10-13; strict typing covered 73
application/migration files. Actual dependency lockfiles and locally initialized
OpenSpec 1.14.1 exist. Review findings were reproduced and fixed with regression
tests for cancellation races, exception privacy, scoped cancellation, change
resolution, actionable queue, unavailable IDs and current-state replay feedback.

Core archive/commit/handoff lifecycle remains pending below. The four integrated
domain increments will share one implementation commit to keep cross-wired
settings/routes functional, followed by verified spec archive/evidence commits.
Real-provider/live-data/deployment gates and the later WhatsApp pilot remain
outside local acceptance. Python 3.13/Django 5.2 compatibility was verified.

## Increment 1: Foundation and specification workflow

**Files:** `pyproject.toml`, `poetry.lock`, `package.json`, `package-lock.json`,
`manage.py`, `config/{settings,urls,wsgi}.py`, `.env.example`,
`tests/test_foundation.py`, `openspec/config.yaml`,
`openspec/changes/portal-foundation/{proposal,design,tasks}.md`,
`openspec/changes/portal-foundation/specs/portal-runtime/spec.md`, `README.md`.

**Produces:** A reproducible PostgreSQL-only Django runtime, explicit
development/production settings, test runner, and initialized local OpenSpec
workflow. No patient functionality is implied by foundation completion.

- [x] Inspect available Python, Poetry, Node and PostgreSQL executables using
  shell access granted for this worktree; check Node meets OpenSpec's published
  floor and Python supports the chosen Django LTS.
- [x] Select and pin the published OpenSpec version in `package.json`; install
  to the repository with a lockfile. Run its version/help with
  `OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1`.
- [x] Use the installed CLI to initialize GitHub Copilot support with the
  default spec-driven schema; disable unrelated cloud files if the installed
  CLI supports that flag. Add domain/scenario constraints to `config.yaml`.
- [x] Create foundation artifacts using the actual CLI instructions. Specify
  PostgreSQL-only runtime, timezone, production fail-closed checks, and the
  synthetic-test fixture contract.
- [x] Add tests that assert `TIME_ZONE == "Asia/Kolkata"`, `USE_TZ is True`,
  PostgreSQL backend, no console OTP backend, and explicit missing-production
  configuration errors. Run `poetry run pytest tests/test_foundation.py -q`
  and observe failure before runtime implementation.
- [x] Implement settings/routing/dependencies, then run the same tests,
  `poetry run python manage.py check`, and strict CLI validation.
- [x] Document exact successful local bootstrap commands, archive only the
  verified foundation change using the CLI, and commit the increment.

## Increment 2: Identity, verified access, and doctor authentication

**Files:** `accounts/{models,services,views,forms,urls}.py`,
`patients/{models,permissions,services}.py`, `audit/{models,services}.py`,
corresponding migrations, `templates/accounts/`, `tests/conftest.py`,
`tests/test_identity.py`, `tests/test_otp.py`, `tests/test_otp_concurrency.py`,
`tests/test_doctor_auth.py`, `tests/test_doctor_setup.py`,
`openspec/changes/verified-identity/` artifacts and scenarios.

**Consumes:** Foundation database, Django sessions/CSRF and settings.

**Produces:** `require_doctor(actor)` and
`require_access(actor, patient, scope)` raising `PermissionDenied`, verified
patient/grant services, hashed OTP challenges and injected test delivery,
append-only audit metadata, and MFA-protected doctor entry.

- [x] Write the identity proposal, design, tasks and scenarios for unverified
  registration, existing card migration, administrative delegation, shared
  phone classification, guardian access and the 18th birthday boundary.
- [x] Add a synthetic matrix covering no grant, unverified grant, admin-only,
  private adult clinical grant, shared-phone adult, verified guardian before
  and on the birthday, and revoked grants. Assert card-number-only access
  fails and a session cannot upgrade classification.
- [x] Add OTP expiry, attempt exhaustion, consumption/replay and resend tests;
  provider configuration must fail closed. Assert plain OTPs never enter logs.
  Add doctor password-only denial, verified MFA acceptance, recovery audit,
  and direct-route tests including any administrative interface.
- [x] Run targeted identity/authentication tests and confirm intended failure.
- [x] Implement the models and narrow services, integrate maintained MFA,
  generate migrations, then run targeted tests and migration/check commands.
- [ ] Validate/verify/archive the identity change and commit.

## Increment 3: Structured intake and safe appointment calendar

**Files:** `clinic/{models,services,views}.py`,
`intake/{models,services,views,forms}.py`,
`appointments/{models,services}.py`, corresponding migrations,
`tests/test_calendar.py`, `tests/test_invariants.py`, `tests/test_review_regressions.py`,
`openspec/changes/request-calendar/` artifacts and scenarios.

**Consumes:** Current grant checks, MFA checks and audit metadata.

**Produces:** Actor-scoped idempotent intake and unified typed queue;
request/propose/confirm/accept/change/cancel services sharing one locked
calendar and PostgreSQL overlap constraint.

- [x] Specify immediate received feedback, patient time-sensitive reason and
  doctor priority, no response deadline/autoapproval, requested-time direct
  confirmation, unreserved alternatives and explicit acceptance.
- [x] Add tests for duplicate submission, out-of-availability requests at
  confirmation, touching versus overlapping intervals, closures, phone and
  in-person channels, competing acceptance, proposal replay, and failed
  reschedule preserving the original booking.
- [x] Add transactional PostgreSQL tests with separate connections and
  synchronized competing workers. Assert exactly one contender commits for
  an overlapping slot, including mixed doctor-entered/patient-accepted paths.
- [x] Run the targeted tests and observe failure; implement service checks,
  calendar locking and database constraints, then rerun on PostgreSQL.
- [x] Verify availability edits do not move/cancel booked appointments;
  verify cancellation is actor-authorized, POST-only and audited.
- [ ] Validate/verify/archive the change and commit.

## Increment 4: Private clinical history and explicit medicine decisions

**Files:** `clinical/{models,services,views,forms}.py`,
corresponding migrations, `templates/clinical/`,
`tests/test_clinical.py`, `tests/test_identity.py`, `tests/test_invariants.py`,
`tests/test_error_privacy.py`,
`openspec/changes/clinical-workflows/` artifacts and scenarios.

**Consumes:** Typed intake, patient clinical grants, verified doctor actions,
and append-only audit metadata.

**Produces:** Private clarification responses, immutable instruction
revisions, explicit optional visit follow-up dates, doctor-only repeat
approve/decline/consultation-required decisions with actor and time.

- [x] Specify separate structured clarification decisions and private text;
  clinical grants apply to every detail and partial response. Medicine is
  never approved by elapsed time or shipment activity.
- [x] Add tests for doctor reply/missing information/consultation-required,
  revision sequencing and prior text retention, explicit absent/present
  follow-up date, repeat decision actors, no timeout approval, and admin-only
  summary omission of every private free-text field.
- [x] Add audit tests that reject update/delete through supported application
  paths and ensure metadata contains no medicine/instruction/reason text.
  Do not claim database-administrator tamper-proofing.
- [x] Run tests and confirm failure; implement services/views/revisions,
  generate migrations, rerun and check current-grant revocation behavior.
- [ ] Validate/verify/archive the change and commit.

## Increment 5: Manual operations and integrated minimal UI

**Files:** `operations/{models,services,views,forms}.py`,
corresponding migrations, `templates/{base,clinic,doctor,patients,intake}/`,
`static/portal.css`, application URLs, `tests/test_operations.py`,
`tests/test_ui.py`, `tests/test_progressive_ui.py`, `tests/test_review_regressions.py`,
`tests/test_error_privacy.py`, `docs/production-gates.md`,
`openspec/changes/manual-operations-ui/` artifacts and scenarios, `README.md`.

**Consumes:** Explicit repeat approvals, authorization and doctor MFA,
confirmed appointments, private clinical services and audit.

**Produces:** Manual approved fulfillment and external payment records,
mobile-friendly public/patient/doctor flows, visible error states, and
honest operational/live-data gates.

- [x] Specify pickup/delivery, minimal necessary address, HTTPS tracking,
  preparation/dispatch approval prerequisites, cancellation review after
  physical work starts, and manual INR charge/receipt corrections.
- [x] Add tests denying preparation and dispatch without approval, rejecting
  unsafe tracking URLs, preserving reviewed cancellation semantics,
  distinguishing charges from externally received cash/UPI, and auditing
  corrections without automatic refunds.
- [x] Add Django-client UI tests for public clinic information, OTP flow with
  injected fake, verified patient selection, received status, proposal
  acceptance, clinical scope omission and doctor queue/calendar/actions.
  Include forged IDs, revoked grants, HTMX requests, and CSRF-enforced POSTs.
- [x] Run targeted tests and observe failure; implement minimal templates,
  forms, authorized selectors and manual services, then rerun.
- [x] Record production gates: actual provider onboarding, MFA/recovery,
  privacy/dispensing/retention reviews, hosting selection, encrypted daily
  backups and restoration/session/access reconciliation. Do not invent
  legal policy text, public clinic details, cost figures or restore evidence.
- [ ] Validate/verify/archive the change and commit.

## Final integrated acceptance

- [x] Run all pytest tests on PostgreSQL, including concurrency and
  permission/CSRF/UI tests. Report exact commands and counts.
- [x] Run Django checks and migration-drift checks, Black/isort checks and
  the chosen compatible type checker. Fix failures caused by this work.
- [ ] Run the installed CLI's supported strict all-spec/change validation.
  Confirm every archived capability has implementation/test evidence, while
  WhatsApp remains pending and no live-provider delivery is claimed.
- [ ] Run `git diff --check`, inspect the final staged change, and commit
  without bypassing hooks or adding AI footers.
- [ ] Send the coordinator branch/path, commits, exact evidence,
  implemented OpenSpec state, remaining production gates, and any genuinely
  blocked core requirement. Do not publish or land the branch.
