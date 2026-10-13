# manual-operations-ui Specification

## Purpose
Expose authorized clinic workflows through mobile-friendly forms and manual
fulfillment/payment records while keeping live-data gates explicit.

## Requirements

### Requirement: Fulfillment requires approval
Preparation/dispatch MUST require approved repeat and verified doctor actor.
Carrier/tracking/status MUST be manual. Links MUST be HTTPS; delivery
addresses MUST be minimized.

#### Scenario: Unapproved preparation attempted
- **GIVEN** repeat lacks approval
- **WHEN** preparation or dispatch is requested
- **THEN** it fails explicitly without state change

#### Scenario: Manual dispatch recorded
- **GIVEN** approved repeat and verified doctor
- **WHEN** carrier/tracking is recorded
- **THEN** manual status/actor/time is stored
- **AND** no courier API/label/pickup automation is invoked

### Requirement: Physical cancellation requires review
Patient cancellation after preparation/dispatch MUST require doctor review,
not automatically undo physical actions.

#### Scenario: Cancellation after dispatch
- **GIVEN** manual dispatch recorded
- **WHEN** patient requests cancellation
- **THEN** review is pending and dispatch history remains
- **AND** no automatic courier reversal/refund occurs

### Requirement: Charges and external receipts stay distinct
Manual INR charges and external cash/UPI received records MUST be separate.
Corrections MUST preserve audited history. Portal MUST NOT claim bank/portal
receipt verification or execute automatic refunds.

#### Scenario: Charge without payment
- **GIVEN** doctor records medicine charge
- **WHEN** payment status is shown
- **THEN** owed charge is not represented as received money

#### Scenario: Receipt corrected
- **GIVEN** an incorrect manual receipt
- **WHEN** verified doctor corrects it
- **THEN** both entries remain traceable with actor/time
- **AND** balance changes without a bank/refund claim

### Requirement: UI preserves backend authorization and CSRF
Patient/doctor screens MUST use backend authorized selectors/services.
Mutations MUST require POST+CSRF. HTMX MUST NOT weaken scope.

#### Scenario: Forged patient identifier
- **GIVEN** account has only one patient grant
- **WHEN** another patient's ID is posted
- **THEN** action fails without private disclosure

#### Scenario: Missing HTMX CSRF
- **GIVEN** an authenticated session
- **WHEN** mutation POST lacks valid CSRF
- **THEN** it fails without domain change

#### Scenario: Password-only doctor route
- **GIVEN** doctor lacks MFA verification
- **WHEN** queue/settings/verification/operations is requested
- **THEN** private access is denied until MFA verification

### Requirement: Guidance is explicit
UI MUST show received status and not-emergency/not-continuously-monitored
guidance, without instant booking, advice or response-deadline implication.

#### Scenario: Mobile submission succeeds
- **GIVEN** authorized valid form
- **WHEN** it succeeds
- **THEN** received state and monitoring limitations are visible

### Requirement: Actionable work stays visible
The doctor queue MUST exclude terminal history unless an unresolved change or
physical cancellation review requires attention. History MUST remain accessible
separately without displacing pending work.

#### Scenario: Historical requests outnumber one page
- **GIVEN** terminal requests exceed the queue page size
- **WHEN** the doctor opens the actionable queue
- **THEN** pending work and unresolved cancellation reviews remain visible
- **AND** terminal records remain available in request history

### Requirement: Production and restore gates are separate
Live data MUST require operational/privacy/practice/dispensing/authentication
review, encrypted daily off-server backups and tested restore. Actual restore
MUST invalidate sessions and suspend patient access/sending pending reconciliation.

#### Scenario: Synthetic acceptance passes
- **GIVEN** local core tests pass
- **WHEN** readiness is reported
- **THEN** unresolved legal/provider/hosting/restore gates stay visible
- **AND** tests are not called live-provider or legal approval
