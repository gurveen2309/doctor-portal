## Why

Clinical questions and medicine repeats require private structured doctor
decisions rather than chat, inferred refills or automated advice.

## What Changes

- Private clarification reply/missing-information/consultation-required flows.
- Lightweight visits, immutable instruction revisions and optional explicit
  follow-up dates.
- Doctor repeat approve/decline/consultation-required decisions with actor/time.
- Clinical/free-text exclusion from administrative summaries and logs/audit.

## Capabilities

### New Capabilities

- `clinical-workflows`: clarifications, versioned visits and explicit repeats.

### Modified Capabilities

None.

## Impact

Requires earlier verified core. Adds clinical models/services/templates/
migrations/tests. No full EMR, live chat or automated medicine advice.

## Execution Status

Pending draft. No clinical implementation or verification evidence.
