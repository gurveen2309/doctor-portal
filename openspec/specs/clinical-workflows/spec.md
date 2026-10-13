# clinical-workflows Specification

## Purpose
Provide private structured clarifications, explicit follow-up and immutable
doctor-written instructions without automatic medicine renewal or advice.

## Requirements

### Requirement: Clarifications are private structured requests
Doctor MUST reply, request missing information or require consultation.
Clinical text MUST require clinical scope; no live chat or automated advice.

#### Scenario: Administrative account reads reply
- **GIVEN** a doctor has written a clarification response
- **WHEN** an administrative-only delegate requests full/partial detail
- **THEN** private reply text is not disclosed
- **AND** only permitted structured status is available

#### Scenario: Information missing
- **GIVEN** a clarification awaits review
- **WHEN** doctor requests missing information
- **THEN** the private outcome is recorded in the authorized request
- **AND** no unrestricted clinical chat channel is opened

#### Scenario: Clinical-only account cancels clarification
- **GIVEN** a current clinical grant without administrative scope
- **WHEN** the account cancels its clarification
- **THEN** the authorized cancellation succeeds without requiring unrelated administrative scope

### Requirement: Instructions are immutable revisions
Medicine/precautions/diet MUST be doctor-written and versioned with actor/time.
Application paths MUST retain unchanged earlier revisions.

#### Scenario: Instruction corrected
- **GIVEN** a first visit instruction revision
- **WHEN** doctor records a correction
- **THEN** a new sequential revision exists and the first is unchanged
- **AND** audit does not copy clinical text

#### Scenario: Instruction revisions compete
- **GIVEN** two permitted revisions of the same visit
- **WHEN** independent PostgreSQL transactions write concurrently
- **THEN** both clinical texts are retained in distinct sequential revisions

### Requirement: Follow-up is explicitly per visit
Follow-up MUST be optional and explicit. The system MUST NOT infer run-out
dates or a universal monthly interval.

#### Scenario: Follow-up absent
- **GIVEN** a visit has no follow-up date
- **WHEN** authorized history is shown
- **THEN** no inferred monthly/run-out date appears

### Requirement: Repeat needs explicit doctor approval
Repeat outcomes MUST record approve/decline/consultation required with
verified actor/time. Preparation/shipment MUST require approval. Time MUST
NOT produce approval or automatic renewal.

#### Scenario: Unanswered repeat ages
- **GIVEN** received repeat with no decision
- **WHEN** time passes
- **THEN** it remains unapproved and cannot be prepared/dispatched

#### Scenario: Consultation required
- **GIVEN** repeat awaits review
- **WHEN** doctor requires consultation
- **THEN** outcome includes actor/time without authorizing fulfillment

### Requirement: Free text stays out of administrative summaries
User/doctor free text MUST be treated as potentially clinical and omitted
from administrative-only summaries, ordinary logs and notification content.

#### Scenario: Reason/instructions recorded
- **GIVEN** request has private reason and instruction text
- **WHEN** administrative status is rendered
- **THEN** neither string is present in HTML/data
- **AND** permitted structured status remains visible

#### Scenario: Clinical exception is reported
- **GIVEN** an unexpected failure while a private form is processed
- **WHEN** the application reports or logs it
- **THEN** POST data, local values and exception payloads disclose no private text
