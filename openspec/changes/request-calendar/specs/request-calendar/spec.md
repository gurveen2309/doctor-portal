## ADDED Requirements

### Requirement: Clinic information is configured and factual
Public clinic facts MUST be configured, including published hours/closures.
The portal MUST NOT invent facts or unsupported treatment claims.

#### Scenario: Profile absent
- **GIVEN** no real clinic profile is configured
- **WHEN** the public page is requested
- **THEN** invented real-looking clinic details are not presented

### Requirement: Requests receive immediate acknowledgement
Successful submission MUST show received/awaiting review immediately. Queue
MUST show type/age/flag. Time-sensitive MUST require a private reason, and
priority MUST be set by the doctor. No human-response deadline is promised.

#### Scenario: Flag without reason
- **GIVEN** an authorized patient flags a request time-sensitive
- **WHEN** its reason is omitted
- **THEN** submission is rejected explicitly

#### Scenario: Valid request stored
- **GIVEN** a valid authorized submission
- **WHEN** it succeeds
- **THEN** received/awaiting review is displayed immediately
- **AND** no deadline, diagnosis or timer approval is implied

### Requirement: Repeated intake is idempotent
An actor's identical key/payload MUST produce one request. Different payload
under the same key MUST raise a conflict.

#### Scenario: Double submit
- **GIVEN** an actor's request was already stored
- **WHEN** identical payload/key is repeated
- **THEN** the original returns without another queue item

### Requirement: Final confirmation is atomic
Appointments MUST be approved. Exact requested time MAY be doctor-confirmed;
alternatives MUST be unreserved and explicitly accepted. Final confirmation
MUST atomically recheck current publication, closures and overlaps.

#### Scenario: Alternatives share an interval
- **GIVEN** two unaccepted alternatives at one interval
- **WHEN** neither is accepted
- **THEN** neither reserves or guarantees occupancy

#### Scenario: Acceptance competes with phone booking
- **GIVEN** acceptance and doctor phone booking overlap
- **WHEN** independent PostgreSQL transactions confirm concurrently
- **THEN** at most one confirmed appointment commits
- **AND** the other fails visibly without partial mutation

#### Scenario: Availability changed since proposal
- **GIVEN** a proposed interval was initially published
- **WHEN** it is closed/unpublished before acceptance
- **THEN** acceptance is rejected using current availability

### Requirement: Rescheduling preserves original booking
Original confirmation MUST remain until a valid replacement is accepted.
Failure MUST preserve original time/status.

#### Scenario: Target taken
- **GIVEN** an active original and unreserved reschedule proposal
- **WHEN** another booking takes the target before acceptance
- **THEN** acceptance fails and the original remains confirmed unchanged

#### Scenario: Patient has not accepted
- **GIVEN** a reschedule proposal awaits acceptance
- **WHEN** the calendar is viewed
- **THEN** the original still occupies its confirmed interval

### Requirement: All channels and availability changes are consistent
Portal/phone/in-person MUST use the same rules. Availability edits MUST NOT
silently move/cancel confirmed appointments.

#### Scenario: Closure intersects booking
- **GIVEN** a confirmed appointment intersects an availability edit
- **WHEN** the edit is applied
- **THEN** the conflict is visible without silently changing the booking

#### Scenario: Adjacent appointments
- **GIVEN** one appointment ends when the next begins
- **WHEN** the next is confirmed in published availability
- **THEN** half-open intervals are not treated as overlapping
