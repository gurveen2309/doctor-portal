# Doctor's Portal architecture

Status: approved requirements translated into implementation boundaries.
Foundation runtime and OpenSpec initialization verified; remaining core pending.

The requirements baseline is [approved-requirements.md](approved-requirements.md).
Implementation must not substitute technical convenience for its clinical
privacy, approval, concurrency, or production gates.

## Architectural decision

Use a Django modular monolith backed by PostgreSQL, with native templates and
selective HTMX. This keeps permissions, clinic decisions, and transaction
boundaries in one backend and avoids operating multiple services for a
single-doctor clinic.

A SPA with a public REST API adds duplicate authorization surfaces and
unnecessary deployment complexity. A general workflow engine or separate
microservices add operational burden and obscure cross-workflow invariants.
Neither is justified at 100-300 requests per day.

## File and module boundaries

| Module | Files | Responsibility |
| --- | --- | --- |
| Runtime | `config/settings.py`, `config/urls.py`, `config/wsgi.py` | Environment configuration, routing, middleware, production checks |
| Accounts | `accounts/models.py`, `accounts/services.py`, `accounts/views.py`, `accounts/forms.py` | Phone account, OTP challenge, verified doctor MFA/session handling |
| Patients | `patients/models.py`, `patients/permissions.py`, `patients/services.py` | Cards, doctor verification, scoped grants, guardian/adult boundaries |
| Audit | `audit/models.py`, `audit/services.py` | Append-only actor/action/record/time events without clinical text |
| Clinic | `clinic/models.py`, `clinic/services.py`, `clinic/views.py` | Public profile, published availability, closures, doctor settings |
| Intake | `intake/models.py`, `intake/services.py`, `intake/views.py`, `intake/forms.py` | Structured requests, received/review states, unified queue, duplicate suppression |
| Scheduling | `appointments/models.py`, `appointments/services.py` | Proposals, acceptance, calendar occupancy, atomic confirmation and replacement |
| Clinical | `clinical/models.py`, `clinical/services.py`, `clinical/views.py`, `clinical/forms.py` | Clarification responses, visits, instruction revisions, explicit repeat decisions |
| Operations | `operations/models.py`, `operations/services.py`, `operations/views.py`, `operations/forms.py` | Manual fulfillment, tracking, INR charges and receipt corrections |
| UI | `templates/`, `static/portal.css` | Mobile-friendly forms, authorized statuses, doctor workspace, emergency guidance |
| Tests | `tests/test_*.py`, `tests/conftest.py` | Synthetic fixtures, service invariants, authorization/CSRF/UI and PostgreSQL concurrency |
| Specifications | `openspec/config.yaml`, `openspec/changes/`, `openspec/specs/` | Proposed and verified capability contracts; CLI-managed lifecycle |

App names separate responsibilities, not deployable services. Avoid a generic
base service or rule framework. Introduce shared helpers only when concrete
callers need the same rule.

## Service and permission contract

Views validate forms and invoke domain services. Every externally reachable
operation supplies the actor. Services perform authorization again before
reading or mutating domain records. Template filtering is not authorization.

`require_doctor(actor)` checks both the doctor role and verified MFA state.
`require_access(actor, patient, scope)` checks an active doctor-verified grant,
current phone classification, patient age in clinic time, and the requested
administrative or clinical scope. Both raise Django `PermissionDenied`.
Selectors must not disclose unauthorized records through existence checks,
query parameters, related objects, free text, or partial responses.

Administrative views project a fixed allowlist of structured fields. They
never serialize an entire model. Treat notes, titles supplied by users,
reasons, addresses, and other free text as potentially clinical. Show necessary
delivery details only to actors authorized for the specific delivery operation.

Grants are checked from current database state on every request. Do not cache
authorization in a session. OTP controls account sign-in, not patient matching;
entering a card number creates no access grant. Guardian clinical access stops
at the child's 18th birthday unless a separately verified adult grant exists.

## Data model and states

Accounts and patients are distinct. `Account` has a unique normalized Indian
mobile, doctor role where applicable, and reviewed phone-control classification.
`Patient` has a unique card number, minimal identity fields, date of birth where
required for a child, and doctor verification metadata. `AccessGrant` binds an
account and patient, explicit scopes and relationship, verification and
revocation metadata.

`ClinicRequest` records patient, submitting actor/channel, typed workflow,
structured state, doctor priority, timestamps, a time-sensitive flag/reason,
private free text, and an actor-scoped idempotency key. States describe
received, missing information, consultation required, doctor decisions,
cancelled, and completed as appropriate to the request type. Transitions are
service-owned and tested; no timer approves anything.

`AppointmentProposal` records the requested or proposed aware start/end and
explicit acceptance state. `Appointment` represents a confirmed occupancy,
not an alternative hold. Reschedule proposals reference the existing booking
without removing its occupancy.

`Visit` contains an optional explicit follow-up date. `InstructionRevision`
is immutable and sequential per visit; medicine, precautions and diet text are
doctor-written. Revisions preserve prior text without copying it into audit.

`RepeatDecision` records an explicit approve/decline/consultation-required
decision, doctor and time. `Fulfillment` records manual preparation, dispatch,
delivery and reviewed cancellation, plus optional carrier/tracking fields.

`Charge` and `ReceiptEntry` distinguish owed INR amounts from externally
received cash/UPI. Corrections preserve a trail instead of overwriting history
or implying a gateway/refund. Monetary amounts use decimal fields, never floats.

## Scheduling transaction

Published availability and closures are checked at final confirmation, not
only when a proposal is shown. Intervals are half-open: adjacent bookings may
touch; end must exceed start. All datetime inputs resolve in `Asia/Kolkata`
and are stored aware.

Serialize all calendar-writing and availability-editing services through one
clinic calendar row locked with `select_for_update()` inside `transaction.atomic()`.
Recheck overlap and publication under that lock. Back the confirmed booking
invariant with a PostgreSQL exclusion constraint on the active half-open
timestamp range. This protects against accidental alternate writing paths,
while the lock coordinates availability and multi-record replacement.

Patient acceptance consumes the proposal only after validation. For a
reschedule, cancel the original and create the replacement in the same
transaction after all checks pass. Any rejection or constraint error rolls
back the entire transaction, preserving the original confirmed appointment.
Availability edits report booked conflicts rather than silently changing them.

Doctor-entered phone/in-person bookings invoke the same service. Tests use
separate PostgreSQL connections and simultaneous contenders; SQLite is not
accepted as evidence.

## Authentication and production boundaries

Use maintained Django authentication/MFA components after verifying compatible
versions. Doctor routes, including settings and patient verification, require
an OTP-verified MFA session; do not leave Django admin as a weaker alternate
entry point. Recovery is an audited controlled process, not a public bypass.

Patient OTP challenges store hashes, expiry, attempts, resend cooldown and
consumption state. Delivery goes through a narrow provider adapter. Missing
production configuration raises an explicit configuration error; no console
backend and no secret logging. Tests inject a memory-only delivery fake.
Throttle by normalized account and defensible client-source limits; do not
trust arbitrary forwarded headers.

`config/checks.py` owns explicit production-gate checks. Production requires
PostgreSQL, HTTPS/session/CSRF cookie settings, non-default
secret configuration, delivery provider onboarding, doctor MFA/recovery setup,
and the live-data reviews in the requirements. A check must report missing
configuration, not make it look successful.

## User-facing surfaces

Public clinic information is configured, not invented. Patient screens show
authorized patient selection, request forms, immediate received status,
structured administrative statuses, proposal acceptance, and scoped clinical
history. Adult clinical details are absent from shared-phone/admin-only views.

Doctor screens include typed/aged/time-sensitive queue, calendar and
availability, patient verification/grants, phone intake, visit revisions and
repeat decisions, manual fulfillment and payment records. Every state-changing
route is POST with CSRF; HTMX is progressive enhancement of the same rules.
Display explicit errors without leaking secrets or private record contents.

## Deferred capabilities and restoration

WhatsApp, outbox automation, courier APIs, payment gateways, and generic
background infrastructure are not core implementation. A later pilot requires
its own OpenSpec change and policy/provider approvals.

Deployment planning requires managed hosting/PostgreSQL selection, encrypted
daily off-server backups, restore evidence, monitoring and patch ownership.
A restoration gate suspends patient access and automatic sending until grants
and actions are reconciled and old sessions invalidated. Preserve phone/paper
fallback. Do not describe a plan as a performed restore.

## Acceptance evidence

Each increment starts with OpenSpec proposal/design/scenarios/tasks and failing
pytest tests, followed by the smallest implementation and passing targeted
checks. Finish with integrated tests, real PostgreSQL concurrency, migration
drift checks, Django checks, formatting and chosen type checks, strict OpenSpec
validation, and whitespace checks.

Implemented capabilities enter `openspec/specs/` only after CLI validation and
verified archive/sync. Proposed capabilities stay pending. A mocked delivery
test is not a live-provider test; an architecture document is not initialized
OpenSpec or working application code.
