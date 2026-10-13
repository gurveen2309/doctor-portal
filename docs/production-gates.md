# Production gates and operating boundaries

The application is a local synthetic implementation, not approval to store
real patient data, send patient messages, publish a repository or deploy.
Passing tests does not close the gates below.

## Before real patient data

The clinic must approve privacy/professional-practice review, medicine
dispensing/delivery legality, privacy notice, delegation/guardian processes,
retention/deletion and backup retention, grievance contact and breach response.
Do not substitute generated policies or assumptions about HIPAA, localization,
blanket exemptions or October 2026 DPDP commencement.

Review the approved source qualifications in `approved-requirements.md` and
confirm official commencement sources before legal reliance. Document the
clinic's approved policies separately once decided.

Configure actual clinic facts only after approval. The doctor verifies both
new registrations and migrated cards directly; preserve existing numbers.
Classifying a mobile as personally controlled is reviewed attestation, never
proof from OTP. Administrative delegates cannot receive adult clinical details.
Guardian clinical access stops at 18; leap-day DOB uses a conservative February
28 cutoff in a non-leap eighteenth year, subject to process review.

## Authentication and real OTP delivery

No console or mock delivery backend exists. `PATIENT_OTP_PROVIDER` must name
an installed real-provider adapter class with:

```python
def validate_configuration(self) -> None:
    """Offline validation; raise ImproperlyConfigured if credentials/setup are missing."""

def deliver(self, phone: str, code: str) -> None:
    """Deliver without logging secrets; raise OSError on explicit delivery failure."""
```

Provider selection, Indian sender/template onboarding, credentials, delivery
timeouts and error mapping must be approved and verified before use. The adapter
must not log phone/code/request payloads, treat an unknown outcome as certain
delivery, or include patient clinical data. Its offline validator must not send
messages. Import/contract/credential failures fail closed and appear in production
checks. Tests inject a memory-only fake; no live delivery is claimed.

Doctor sign-in requires password plus a confirmed django-otp TOTP device or
one-time static recovery token. No enabled Django admin or password-only doctor
workspace exists. Initial doctor/device provisioning uses the interactive
`poetry run python manage.py setup_doctor` command through controlled local
operations, after migrations. It confirms an authenticator before committing,
enforces one doctor and displays sensitive setup/recovery material only to the
operator. Never record/redirect/tee its terminal output or send the setup key to
a third-party QR service. Keep recovery tokens offline and restricted. Backup-token use
is audited and consumes the token. Replacing a lost MFA device requires verified
identity and controlled operator action, not a public recovery bypass.

Patient OTP is valid for five minutes, allows five verification attempts, and
is consumed atomically. Resend is limited per phone and per source address.
Source limits use server `REMOTE_ADDR`; configure managed proxy/client-source
handling deliberately before production rather than trusting arbitrary
forwarded headers. No phone or card number proves patient identity.

## Managed hosting and checks

Choose a managed app/PostgreSQL provider, region and actual quote. No provider,
region, rupee cost or localization mandate has been selected.

Use explicit production environment, unique secret, allowed hosts, HTTPS,
secure cookies, secret management, monitoring, patch ownership and restricted
operator/database access. Logs must exclude OTPs and clinical/free-text bodies.
Technical operators may have infrastructure privileges but no patient-facing
staff role. Restrict access, name and audit operations, and keep operator access
out of routine clinic workflow. Application audit is append-only through its
supported paths, not tamper-proof against database administrators.
Default Django exception reports and application logs deliberately withhold
request values, user representations, locals and exception payloads. Severity,
HTTP status, exception type and source locations remain available. Do not replace
this with verbose request/body logging or attach an unreviewed error-reporting
integration. Provider/infrastructure logging must be reviewed separately.

Run `poetry run python manage.py check --deploy` with actual production
configuration. `LIVE_DATA_APPROVED=yes` records an external reviewed gate;
setting it is not a substitute for that review. Missing real provider/legal
approval remains an explicit error. Do not suppress errors or use development/
test settings for live patient traffic.

## Backup and restoration

Require encrypted daily off-server PostgreSQL backups, access restrictions,
documented retention/deletion and a restore drill before live use. The accepted
recovery point objective permits up to 24 hours of lost writes, not guaranteed
zero loss. Include dependency versions/configuration in recovery materials but
keep secrets in approved secret storage.

Before any restore, disable ingress and all automatic sending. Restore to a
restricted environment, never directly expose recovered patient sessions.
The audited `accounts.services.hold_after_restore` operation suspends patient
access and deletes persisted Django sessions. Invoke it with a freshly verified
doctor actor through the controlled operating procedure before opening ingress.
The service is tested synthetically, not evidence of an actual backup restore.

Reconcile restored grants, revocations, clinic decisions, pending proposals,
physical shipments and payment corrections against doctor/phone/paper records.
Verify the doctor account and MFA/recovery state. Retain the suspension until
explicit reconciliation is approved; do not reactivate access just because the
server starts. Reconfirm patient access where needed. Preserve a record of the
restore/reconciliation evidence and authorizing operator/doctor.

Automatic sending remains disabled: no notification sender/outbox is implemented
in core. A future integration must pause during restoration and reconcile unknown
provider outcomes rather than replaying restored events blindly.

## Later WhatsApp pilot

WhatsApp is not a core dependency. A new approved OpenSpec change must cover
official business integration, number eligibility/migration/coexistence,
permission/opt-out, template/window/category policy and privacy. No clinical
chat, in-chat refill approval, ordering or courier commerce. Links are not policy
bypasses; India OTC exceptions are not blanket homeopathy permission.

If approved, use transactional PostgreSQL outbox and a scheduled sender with
bounded retries/recovery, current consent/stale-event checks and visible failure.
Provider acceptance is not delivery and no exactly-once guarantee is claimed.
Verify/deduplicate callbacks if used. Failures never undo clinic decisions.

## Pilot measurement

Before launch, capture a comparable baseline of routine coordination calls/texts
using aggregated counts only. Compare equivalent clinic days and request volume
during pilot, excluding clinical message content from measurement. The target is
at least a 50% reduction. No achieved reduction is claimed by local tests.
