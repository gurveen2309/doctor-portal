## Purpose
Authenticate separate accounts and authorize doctor-verified patient scopes
with current revocation, adult/guardian boundaries and private audit.

## ADDED Requirements

### Requirement: Accounts and patients remain distinct
OTP, card numbers and family membership MUST NOT grant patient identity/access.
New and migrated cards MUST require doctor verification. Existing card numbers
MUST be preserved and new ones MUST not collide.

#### Scenario: Card number supplied without grant
- **GIVEN** a signed-in account lacks a verified patient grant
- **WHEN** it supplies an existing card number
- **THEN** no patient data or grant is returned automatically

#### Scenario: Active paper patient migrated
- **GIVEN** a doctor has verified an active record
- **WHEN** its portal card is created
- **THEN** the existing unique number is preserved
- **AND** historical text transcription is not required

### Requirement: Current scope governs every surface
Every read/mutation MUST require current active verified scope, including
direct URLs, HTMX and JSON. Revocation MUST apply immediately.

#### Scenario: Grant revoked in existing session
- **GIVEN** a signed-in account's clinical grant has been revoked
- **WHEN** that session reads or mutates the clinical record
- **THEN** access is denied without waiting for sign-out or cache expiry

#### Scenario: Administrative delegate follows clinical link
- **GIVEN** an administrative-only grant
- **WHEN** a clinical detail or partial response is requested
- **THEN** clinical/free-text information is not disclosed

#### Scenario: Unavailable identifier is enumerated
- **GIVEN** an account lacks access to a patient record
- **WHEN** it requests an existing unavailable or nonexistent identifier
- **THEN** both use the same not-found response
- **AND** direct and HTMX mutations disclose no object existence

### Requirement: Adult clinical scope needs reviewed private control
Shared-phone adult accounts MUST have no clinical access. Adult clinical scope
MUST require reviewed private phone and verified personal adult authorization.
Accounts MUST NOT upgrade their classification or grants.

#### Scenario: Shared phone passes OTP
- **GIVEN** a shared-phone account with administrative adult access
- **WHEN** it requests clinical messages/instructions/history after OTP
- **THEN** clinical access is denied

#### Scenario: Adult lacks private sign-in
- **GIVEN** no reviewed personally controlled mobile sign-in exists
- **WHEN** clinical details need communication
- **THEN** the portal does not disclose them to an administrative delegate
- **AND** direct doctor communication remains an outside-portal process

### Requirement: Guardian clinical scope expires at adulthood
Verified guardian clinical grants MUST require child DOB and relationship.
They MUST NOT continue automatically at 18.

#### Scenario: Eighteenth birthday reached
- **GIVEN** a previously valid guardian clinical grant
- **WHEN** clinic-local date reaches the patient's eighteenth birthday
- **THEN** guardian clinical access is denied
- **AND** adult authorization must be separately verified

#### Scenario: DOB missing
- **GIVEN** a purported child has no DOB
- **WHEN** guardian clinical verification is attempted
- **THEN** verification fails explicitly

### Requirement: OTP is bounded and private
OTP MUST expire, bound attempts, throttle resend and consume atomically.
Codes MUST NOT be logged. Missing real production delivery MUST fail closed.

#### Scenario: Code replayed concurrently
- **GIVEN** a challenge has been consumed successfully
- **WHEN** its code is replayed, including concurrent submission
- **THEN** no additional successful sign-in is created

#### Scenario: Provider missing
- **GIVEN** required production provider configuration is absent
- **WHEN** OTP delivery is requested
- **THEN** failure is explicit without printing/logging secrets
- **AND** no fake delivery or auth bypass activates

#### Scenario: Authentication exception is reported
- **GIVEN** a sign-in or provider operation raises unexpectedly
- **WHEN** Django reports or logs the failure
- **THEN** failure type and source location remain observable
- **AND** submitted/generated codes, phone, local values and exception payloads are withheld

### Requirement: Doctor access requires verified MFA
Every doctor route/settings/verification and enabled admin MUST require MFA.
Recovery MUST be controlled and audited.

#### Scenario: Password-only session
- **GIVEN** the doctor has authenticated without verified MFA
- **WHEN** any private workspace or doctor mutation is requested
- **THEN** it is denied or directed to MFA verification

### Requirement: Audit contains metadata only
Audit MUST append actor/action/record/time without clinical, OTP or address
content. Supported application paths MUST NOT update/delete audit events.

#### Scenario: Medicine instruction written
- **GIVEN** a permitted doctor instruction change
- **WHEN** its event is appended
- **THEN** actor/action/record/time is recorded
- **AND** instruction text is absent from audit and ordinary logs
