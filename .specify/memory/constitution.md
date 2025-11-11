<!--
Sync Impact Report - Constitution Update

Version Change: (initial template) → 1.0.0
Change Type: INITIAL - First ratification of project constitution

Modified Principles: N/A (new constitution)
Added Sections:
  - Core Principles (5 principles)
  - Database Safety Rules
  - Development Standards
  - Governance

Removed Sections: N/A (initial version)

Templates Requiring Updates:
  ✅ .specify/templates/plan-template.md - Constitution Check section already references constitution file
  ✅ .specify/templates/spec-template.md - No updates required (specification focuses on user requirements)
  ✅ .specify/templates/tasks-template.md - No updates required (task structure generic)

Follow-up TODOs: None

Rationale for Version 1.0.0:
  - Initial constitution establishment for Cassandra Snapshot Downloader project
  - User-provided principle: Read-only database operations (no schema changes, no data manipulation)
  - Standard principles derived from project requirements: data integrity, error handling, responsiveness, security, simplicity
-->

# Cassandra Snapshot Downloader Constitution

## Core Principles

### I. Read-Only Database Operations (NON-NEGOTIABLE)

**Rule**: This application connects to a production Cassandra database and MUST perform only SELECT operations. The application is FORBIDDEN from:
- Creating, altering, or dropping tables or keyspaces
- Inserting, updating, or deleting data
- Modifying any database schema or configuration
- Executing any DDL (Data Definition Language) statements
- Executing any DML (Data Manipulation Language) statements except SELECT

**Rationale**: The application operates against live production systems. Any write operations could corrupt operational data, violate compliance requirements, or cause system outages. Read-only access ensures the application cannot harm the source database regardless of bugs or user error.

**Enforcement**:
- Code reviews MUST verify no write operations exist in database layer
- Database connection SHOULD use read-only user credentials with SELECT-only grants
- Unit tests MUST verify only SELECT queries are generated
- Integration tests MUST NOT require write permissions

### II. Data Integrity and Validation

**Rule**: All data retrieved from the database MUST be validated before processing. The application MUST:
- Verify image ByteArray data is valid before conversion
- Sanitize filenames to prevent filesystem injection
- Validate date ranges before query execution
- Handle null, empty, or corrupted data gracefully
- Never assume database data is well-formed

**Rationale**: Production databases may contain corrupted data, unexpected null values, or malformed entries. Defensive validation prevents crashes, security vulnerabilities, and data corruption in downloaded files.

### III. Comprehensive Error Handling

**Rule**: Every external operation (database query, file write, network operation) MUST have explicit error handling with user-actionable messages. Error messages MUST:
- Clearly identify what failed and why
- Provide specific guidance on resolution (check network, verify permissions, free disk space)
- Never expose sensitive information (credentials, internal paths, stack traces to end users)
- Continue processing when individual operations fail (e.g., skip corrupted file, proceed to next)

**Rationale**: Database operators need clear feedback to troubleshoot issues without developer intervention. Actionable errors reduce support burden and improve user autonomy.

### IV. UI Responsiveness and User Control

**Rule**: All long-running operations (database queries, bulk downloads) MUST execute in background threads. The application MUST:
- Keep UI responsive (<1 second response time) during all operations
- Display real-time progress updates (progress bar, log messages)
- Allow users to cancel operations gracefully
- Never block the UI thread with I/O operations

**Rationale**: Users may need to download thousands of files. A frozen UI creates poor user experience and prevents users from monitoring or controlling operations.

### V. Security and Credential Protection

**Rule**: User credentials and sensitive data MUST be protected. The application MUST:
- Mask password fields in UI (display as • or *)
- Store credentials only in memory during runtime
- Never log passwords or sensitive connection strings
- Never persist credentials to disk in plain text
- Use secure connection options when available (SSL/TLS)

**Rationale**: Database credentials provide access to production systems. Exposure through UI, logs, or disk storage creates security vulnerabilities.

### VI. Simplicity and Single Responsibility

**Rule**: The application has ONE purpose: download snapshots from Cassandra to local folders. Features outside this scope MUST be rejected unless they directly support this core workflow. The application MUST NOT:
- Provide database administration capabilities
- Modify downloaded images (resizing, filtering, conversion to other formats)
- Upload data back to the database
- Implement complex data analysis or reporting

**Rationale**: Feature creep increases complexity, maintenance burden, and testing requirements. A focused application is easier to verify for database safety compliance and easier for users to understand.

## Database Safety Rules

### Query Construction

- All queries MUST use parameterized statements or driver-level query builders
- WHERE clauses MUST only filter on indexed partition keys (year, month, day, eqpid)
- ALLOW FILTERING MUST NOT be used (indicates inefficient query design)
- Query timeouts MUST be enforced (10 seconds for search queries, 5 seconds for connection tests)

### Connection Management

- Only ONE database connection active at any time (no connection pooling needed for read-only single-user app)
- Connections MUST be closed when no longer needed
- Connection state MUST be clearly displayed to users
- Failed connections MUST be retried only on user request (no automatic retry loops)

### Data Retrieval

- Image ByteArrays MUST be processed in batches to avoid memory exhaustion
- Retrieved data MUST NOT be cached beyond the current operation
- Search queries retrieve ALL matching records but only display first 20 (full dataset available for download)
- No pagination required (single query per search operation)

## Development Standards

### Testing Requirements

While tests are not mandatory for all features, when tests are implemented they MUST:
- Verify database operations are read-only (mock/stub write operations to ensure they fail)
- Validate error handling for network failures, invalid data, and permission errors
- Test UI responsiveness during simulated long operations
- Verify credential masking in UI components
- Test file organization structure matches specification

### Code Review Gates

All code changes MUST pass review verifying:
- No DDL or DML (except SELECT) statements present
- Error handling with actionable messages exists for all I/O operations
- Long operations execute in background threads
- Credentials are not logged or persisted
- Feature additions align with single-responsibility principle

### Performance Standards

- Connection test: Complete within 5 seconds or timeout
- Search query: Return results within 10 seconds or timeout
- UI response: Acknowledge user input within 1 second during operations
- Download throughput: Process files sequentially with minimal delay
- Memory usage: Handle 10,000+ snapshots without memory overflow

### Documentation Requirements

- All public functions MUST have docstrings explaining purpose, parameters, return values, and exceptions
- Error messages MUST be documented with recommended user actions
- Database schema assumptions MUST be documented
- Folder structure generation logic MUST be documented

## Governance

### Amendment Process

This constitution represents the non-negotiable requirements for database safety and application scope. Amendments require:

1. **Proposal**: Document proposed change with rationale
2. **Impact Analysis**: Identify affected code, tests, and documentation
3. **Risk Assessment**: For database safety changes, document risk to production systems
4. **Approval**: Explicit approval required before implementation
5. **Migration**: Update all references in templates, documentation, and code
6. **Version Bump**: Increment constitution version per semantic versioning rules

### Versioning Policy

Constitution versions follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Changes that remove or weaken database safety protections, or fundamentally alter application scope
- **MINOR**: New principles added, existing principles expanded with additional requirements
- **PATCH**: Clarifications, wording improvements, typo fixes without semantic changes

### Compliance Verification

All feature specifications, implementation plans, and code reviews MUST verify compliance with:

- **Principle I**: No write operations to database (read-only verification)
- **Principle II**: Data validation for all external inputs
- **Principle III**: Error handling with actionable messages
- **Principle IV**: Background execution for long operations
- **Principle V**: Credential protection in UI and logs
- **Principle VI**: Feature scope limited to snapshot download workflow

### Violation Handling

Constitution violations are categorized as:

- **Critical**: Database write operations, credential exposure - MUST be rejected immediately
- **Major**: Missing error handling, UI blocking, data validation gaps - MUST be fixed before merge
- **Minor**: Documentation gaps, suboptimal performance - MAY be addressed in follow-up

### Complexity Justification

Any feature that violates constitution principles MUST be justified with:
- Specific user need that cannot be met within principles
- Simpler alternative that was rejected and why
- Risk mitigation plan if principle violation is approved
- Plan to return to compliance in future iteration

Use the Complexity Tracking table in implementation plans to document approved violations.

**Version**: 1.0.0 | **Ratified**: 2025-11-11 | **Last Amended**: 2025-11-11
