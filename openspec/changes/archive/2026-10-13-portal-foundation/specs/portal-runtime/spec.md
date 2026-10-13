## ADDED Requirements

### Requirement: Reproducible local tooling
Dependencies MUST use Poetry and pinned local OpenSpec with generated
lockfiles. OpenSpec MUST use the default schema with telemetry disabled.

#### Scenario: Clean local bootstrap
- **GIVEN** compatible runtimes and an approved PostgreSQL service
- **WHEN** documented installation and initialization run successfully
- **THEN** versions are reproducible from generated lockfiles
- **AND** no global install or custom schema is required

### Requirement: PostgreSQL and clinic timezone
The runtime MUST use PostgreSQL and aware datetimes in `Asia/Kolkata`.
It MUST NOT silently fall back to SQLite.

#### Scenario: Database configuration absent
- **GIVEN** required PostgreSQL configuration is missing
- **WHEN** application configuration or required checks execute
- **THEN** an explicit configuration failure is reported
- **AND** SQLite is not substituted

#### Scenario: Clinic time interpreted
- **GIVEN** a clinic-local appointment datetime
- **WHEN** the runtime interprets it
- **THEN** Asia/Kolkata is used and the stored datetime is aware

### Requirement: Production failures are explicit
Production MUST reject missing secrets, insecure transport settings and
unavailable real patient OTP delivery. It MUST NOT select debug mode,
generated fallback secrets or console/fake delivery.

#### Scenario: Delivery credentials missing
- **GIVEN** production mode lacks required provider configuration
- **WHEN** checks or an OTP delivery attempt execute
- **THEN** failure is visible without logging/printing a code
- **AND** sign-in is not bypassed

### Requirement: Specification evidence is honest
Only verified implemented capabilities MUST be archived/synced. Draft files
MUST NOT be described as successful CLI initialization.

#### Scenario: Execution approval denied
- **GIVEN** files can be written but CLI execution cannot be approved
- **WHEN** status is reported
- **THEN** installation, tests, migrations and commits remain unverified
- **AND** canonical implemented capabilities are not created
