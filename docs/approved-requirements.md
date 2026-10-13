# Approved Doctor's Portal requirements

Approved design date: 2026-10-13.

This is a requirements snapshot of the confirmed summary supplied to the
implementation session. The original design artifact was supplied at
`doctor-portal-design-contract.md` in the coordinating session's artifacts.
Access to that artifact was denied by tool approval. This document is not a
verbatim copy of it, and does not replace the original approval record.

The current request authorizes architecture, repository initialization,
OpenSpec, and implementation. The historical design-only restriction no longer
applies. No GitHub publication, deployment, real patient data, or real patient
messages are authorized.

## Purpose and scope

One clinic, one doctor, in India; the doctor performs all clinic administration.
Expected volume is 100-300 requests per day. The goal is to reduce routine
coordination calls and texts by at least 50% against a comparable prelaunch
baseline. The core is structured intake and a unified doctor queue, not a bot
or a full electronic medical record.

Use a Django modular monolith, PostgreSQL, server-rendered Django templates, and
selective HTMX. Rules and permissions belong to the backend. Use normal Django
sessions and CSRF. JSON exists only for a demonstrated integration need.
Exclude a SPA, public REST API, mobile app, microservices, tenancy, staff roles,
inventory/catalogue, and video consultations.

## Public information and requests

Publish configured clinic name, address, map link, contact, opening hours,
closures, doctor information, and factual general homeopathy information
without unsupported treatment claims. Consultations are in person.

Patients can request appointments, short clinical clarifications, and repeat
medicine with pickup/delivery preference. They can view authorized statuses and
history, accept alternative times, and request changes or cancellation. The
doctor can enter phone and in-person requests or bookings on a patient's behalf.
Every booking channel uses the same calendar.

Submission immediately displays received/awaiting review. There is no promised
15/30-minute human response, timeout approval, clinical triage, diagnosis, or
automatic clinical answer. A patient time-sensitive flag requires a reason;
the doctor determines priority. Display not-emergency and
not-continuously-monitored guidance.

## Scheduling

Appointments are request-and-approve, not instant slots. The doctor may confirm
the exact originally requested time or propose an alternative. Alternatives
are not reserved and require explicit patient acceptance.

Final confirmation must atomically recheck published availability and overlap.
Concurrent actions must not double-book. During rescheduling the original
confirmed booking remains until a valid replacement is accepted. Failed
acceptance preserves that booking. Availability edits never silently move or
cancel confirmed appointments.

## Clinical information

Clinical clarifications are structured private requests. The doctor can reply,
request missing information, or require consultation. There is no live chat.

Maintain lightweight patient cards and visit history. Doctor-written medicine,
precautions, and diet instructions are versioned. A follow-up date is optional
and explicit per visit. Do not infer run-out dates or a universal monthly
follow-up interval.

Repeat medicine requires an explicit doctor approval, decline, or
consultation-required decision with actor and time. Do not automatically renew
medicine. Preparation and shipment require approval.

## Fulfillment and payments

The doctor manually records carrier, tracking number or HTTPS tracking link,
and dispatch/delivery/cancellation status. Exclude courier APIs, labels, and
pickup automation. Cancellation after preparation or dispatch starts requires
review; it is not an automatic physical reversal.

Record manual INR charges for consultations, medicine, and delivery, and
external cash/UPI received amounts and status. Corrections are audited. Exclude
payment gateways, bank verification, automatic refunds, and claims that the
portal itself received money.

## Identity and authorization

An account is not a patient. Mobile OTP demonstrates control of a phone, not
patient identity or exclusive use. Unique patient card numbers are identifiers,
never authentication or access proof. Both new registrations and existing
records require doctor verification.

Gradually migrate active patients while preserving existing card numbers.
New numbers must not collide. Exclude historic OCR and full transcription;
the doctor may retain historical clinical information on paper.

Access requires an active, verified account-patient grant with explicit
scopes. Authorized adults may delegate administrative requests, but family
membership does not automatically confer clinical access. Shared-phone
accounts can have administrative access to adults. Adult clinical messages,
instructions, and history require doctor-verified personally controlled
mobile access. This is reviewed attestation, not proof from OTP. An account
cannot upgrade itself. Adults without private sign-in receive clinical details
directly from the doctor.

A verified guardian can manage a child's requests and clinical information.
Children require date of birth. Guardian clinical access does not continue
automatically at age 18; adult authorization is required.

Check permissions on every read, mutation, direct URL, HTMX response, and JSON
surface. Revocation takes effect immediately. All free text is potentially
clinical: omit it from administrative-only summaries, WhatsApp, and ordinary
logs. Audit actor, action, record ID, and time without duplicating medical
content. Application audit is append-only, not database-administrator
tamper-proof. Do not collect Aadhaar uploads. Collect a minimum delivery
address only when needed.

## Authentication and operations

Patient OTP needs expiring codes, bounded attempts, resend throttling, a
production delivery provider, and no OTP logging. Doctor MFA and controlled
recovery must be stronger than patient OTP. Restrict and audit technical
operations access. Prefer maintained authentication libraries.

Never silently enable console/mock OTP or an MFA bypass in production.
Missing provider credentials must fail closed. Tests may inject in-memory
delivery fakes without logging secrets. Real-provider onboarding is a
production gate, not a reason to abandon testable local implementation.

Use aware datetimes and `Asia/Kolkata`. Clinic settings are limited to
profile/contact, availability/closures, and notification settings. Follow-up
dates are per visit. Exclude a generic rule engine.

## Later WhatsApp pilot

Portal statuses and follow-up dates are core. WhatsApp is a later, separately
approved pilot, not a launch dependency. Exclude medicine ordering, refill
approval, courier commerce, and clinical chat within WhatsApp.

Use an official business integration only after number eligibility,
migration/coexistence, permission/opt-out, and supported category checks.
Business-initiated/outside-24-hour messages need approved templates. The India
OTC exception is not blanket homeopathy or commerce permission; a link is not
a policy bypass.

No Redis, Celery, or general workflow engine initially. Approved notification
automation would use a durable PostgreSQL outbox and scheduled Django sender:
transactional intent, bounded retries, abandoned-work recovery, consent and
stale-event checks, and visible failure. Provider acceptance is not delivery.
Do not claim exactly-once delivery. Reconcile unknown outcomes rather than
blindly duplicating. Verify and deduplicate callbacks if used. Notification
failure never undoes the clinic's decision.

## Hosting, restoration, and live-data gates

Managed application hosting and managed PostgreSQL are chosen over a VPS.
Provider, region, and costs are not selected. Do not invent rupee figures or a
localization mandate.

Require HTTPS, secret management, security/monitoring/patching, encrypted daily
off-server backups, and a successful restore test before going live. The user
accepts up to 24 hours of loss. After restore, pause automatic sending,
invalidate sessions, and suspend patient access until grants and actions are
reconciled. Keep phone/paper fallback.

Before real patient data, require privacy/professional-practice review,
dispensing/delivery legality review, privacy notice, verified delegation and
guardian processes, retention/deletion/backup-retention policy, grievance
contact, breach procedure, and production OTP onboarding/recovery.

Do not claim the full DPDP regime is in force in October 2026 or assume HIPAA,
localization, or a blanket healthcare exemption. The supplied source review
reports an 18-month core phase after November 2025 publication of DPDP Rules
2025, with printed 13 November versus digital-ID 14 November uncertainty.
Confirm official commencement sources before legal reliance. Do not invent
final legal policies or actual clinic information.

## Delivery and evidence

Use Poetry, pytest, Black with line length 120, isort's Black profile, and
types for new Python code. Check runtime compatibility for a maintained
Django LTS.

Install OpenSpec through a pinned repository-local
`@fission-ai/openspec` development dependency and lockfile, not globally.
Disable telemetry for each invocation with `OPENSPEC_TELEMETRY=0` and
`DO_NOT_TRACK=1`. Check the installed CLI's version/help before relying on
flags. Use the default spec-driven schema and
`init --tools github-copilot`; use `--no-copilot-cloud` only if supported.
Do not add a custom schema, graph pipeline, or workflow engine.

Write proposal, capability scenarios, design, and executable tasks before each
increment. Only archive/sync verified implemented changes. Keep the WhatsApp
pilot pending.

Verification must cover the permission matrix, revocation, card numbers
not authorizing access, guardian adulthood, actual PostgreSQL concurrency,
failed-reschedule preservation, all booking channels, no timeout medicine
approval, no preparation/dispatch without approval, duplicate intake,
versioned clinical text, audit privacy, manual payments, MFA-protected doctor
routes, missing production provider fail-closed behavior, minimal UI and CSRF.
Use synthetic fixtures only. Check migrations, Django system checks,
formatting/types, targeted then integrated tests, strict OpenSpec validation,
and diff whitespace. Do not use SQLite as PostgreSQL concurrency evidence or
claim live notification-provider tests.
