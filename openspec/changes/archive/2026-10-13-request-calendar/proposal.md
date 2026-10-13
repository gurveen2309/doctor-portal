## Why

Structured intake reduces coordination only with one queue and a safe calendar
shared by portal, phone and in-person channels.

## What Changes

- Configured public clinic facts and published availability/closures.
- Typed idempotent requests with immediate received state and doctor priority.
- Approval scheduling, unreserved alternatives, explicit acceptance and atomic
  current availability/overlap checks.
- Preserve original bookings during unaccepted/failed reschedules.

## Capabilities

### New Capabilities

- `request-calendar`: unified intake, clinic availability and safe scheduling.

### Modified Capabilities

None.

## Impact

Requires verified identity/foundation. Adds clinic/intake/appointments, forms,
migrations and actual PostgreSQL concurrency tests. No instant slots or timers.

## Execution Status

Pending draft. No scheduling code, migrations or concurrency evidence.
