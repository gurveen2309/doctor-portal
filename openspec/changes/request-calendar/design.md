## Context

Alternatives are not holds. Confirmation depends on current availability and
occupancy, not conditions at proposal time.

## Goals / Non-Goals

Goals: clear received state, duplicate suppression, one calendar and atomic
confirmation/replacement. Non-goals: instant booking, waitlist automation,
clinical triage, slot-duration guesses or response deadlines.

## Decisions

`ClinicProfile` contains configured public facts only.
`AvailabilityWindow`/`Closure` use aware intervals, not a generic rule engine.
No invented real clinic facts or unsupported treatment claims.

`ClinicRequest` separates type/status/channel/time/doctor priority from private
free text. Time-sensitive needs a private reason; administrative projections
show flag, not reason. Order actionable queue by doctor priority then age;
terminal history does not displace pending work or unresolved change/review.

`submit_request(actor, patient, kind, ..., idempotency_key)` checks current
permissions and an actor-scoped unique key. Same normalized payload/key
returns the original; different payload/key reuse raises an explicit conflict.
Do not log private payloads.
Replay feedback reflects the existing current state, not a new awaiting-review
claim after a request has already been decided or cancelled.

Appointments record exact requested start/end. Direct doctor confirmation
of that requested interval needs no new acceptance. Alternatives require
patient acceptance and create no occupancy. Acceptance checks current access,
proposal state and calendar before committing. Replay cannot double-create.

Lock the singleton calendar before confirmation/cancellation/availability
mutation. Recheck publication/closure/half-open overlap and use a PostgreSQL
active-range exclusion constraint as a second invariant.

Reschedule proposals reference the active original. Acceptance locks calendar,
proposal and original in consistent order. Validate before replacing states;
roll back the entire transaction on failure. Cancelled/superseded originals
cannot be replaced by stale proposals.
Change requests increment a version captured by the proposal. Acceptance
resolves only that version, preserving newer requests. Cancellation rechecks the
current request/occupancy under the calendar lock and supersedes alternatives
atomically; it never follows a view-selected stale branch.

Phone and in-person doctor intake invoke the same services with source actor/
channel. Availability edits expose intersections with bookings, never silently
change appointment times/statuses.

## Risks / Trade-offs

Calendar writes serialize at a scale where this is reasonable. Database
constraints alone cannot check published availability. Time-sensitive is not
triage or emergency assurance.

## Migration Plan

Create calendar/request/proposal/appointment tables and exclusion constraint.
Document required PostgreSQL extension privileges rather than omit protection.

## Verification

Independent PostgreSQL connections and synchronized contenders test mixed
channels, overlap/touching, availability races, replay and failed replacement.
SQLite is not accepted as concurrency evidence.
