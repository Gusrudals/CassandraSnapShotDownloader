# Implementation Plan: Cassandra Snapshot Downloader

**Branch**: `001-cassandra-snapshot-downloader` | **Date**: 2025-11-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-cassandra-snapshot-downloader/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a desktop application using PyQt5 that connects to a Cassandra database, allows users to search for screenshot snapshots by date range and equipment ID, and downloads matching snapshots to a local folder with organized hierarchical structure (Year/Month/Day/EquipmentID). The application must remain responsive during large downloads, provide real-time progress feedback, handle errors gracefully, and operate in read-only mode against the production database.

## Technical Context

**Language/Version**: Python 3.11+ (for modern type hints, asyncio support, and security patches)
**Primary Dependencies**:
- PyQt5 (GUI framework for cross-platform desktop application)
- cassandra-driver (DataStax Python driver for Apache Cassandra)
- Pillow (PIL fork for ByteArray to PNG image conversion)

**Storage**:
- Source: Apache Cassandra database (read-only access)
- Destination: Local filesystem (hierarchical folder structure)
- No application-level database or persistent storage

**Testing**: pytest with pytest-qt for GUI testing, unittest.mock for database mocking
**Target Platform**: Cross-platform desktop (Linux, Windows, macOS) with GUI support
**Project Type**: Single desktop application (no web/mobile components)
**Performance Goals**:
- Connection test: <5 seconds
- Search query: <10 seconds for date ranges up to 1 year
- Download throughput: Sequential processing with minimal inter-file delay
- UI responsiveness: <1 second response time during all operations

**Constraints**:
- Read-only database operations (no DDL/DML except SELECT)
- Single database connection (no pooling)
- Sequential file downloads (no parallel downloads)
- Memory efficient: Handle 10,000+ snapshots without overflow
- Display limit: 20 records in results table (all records available for download)
- No credential persistence to disk

**Scale/Scope**:
- Single-user desktop application
- Expected dataset: Tens of thousands of snapshots per search
- Target download volume: Up to 10,000 files per operation
- ~1,500-2,000 lines of code across 10-12 modules

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Read-Only Database Operations ✅ PASS

**Verification**:
- ✅ Feature spec explicitly requires read-only operations (FR-030 to FR-036)
- ✅ Technical context confirms "Read-only database operations (no DDL/DML except SELECT)"
- ✅ No create, update, delete operations in any user story
- ✅ Database layer will use SELECT queries only for connection test and snapshot retrieval

**Enforcement Plan**:
- Code review: Verify CassandraClient only implements SELECT methods
- Unit tests: Mock database to verify no write operations called
- Use database user with SELECT-only grants (recommended in deployment docs)

### Principle II: Data Integrity and Validation ✅ PASS

**Verification**:
- ✅ FR-008: Equipment ID validation before search execution
- ✅ Edge case handling: Invalid filename characters sanitized (spec line 123-124)
- ✅ Edge case handling: Null/empty ByteArray detection (spec line 132-133)
- ✅ Date range validation planned in validators.py (user input Phase 4)

**Implementation Plan**:
- validators.py: validate_date_range(), validate_eqpid()
- file_handler.py: Sanitize filenames before writing
- download_manager.py: Validate ByteArray before PNG conversion

### Principle III: Comprehensive Error Handling ✅ PASS

**Verification**:
- ✅ FR-030 to FR-036: Specific error scenarios with actionable messages
- ✅ User Story 5: Error recovery with detailed logging
- ✅ Error scenarios: Connection failure, timeout, disk full, corrupted data, permissions

**Implementation Plan**:
- All database operations wrapped in try-except with specific error types
- QMessageBox for user-facing errors with resolution guidance
- logger.py: File-based logging for audit trail
- Error messages follow pattern: "[What failed] - [Why] - [What to do]"

### Principle IV: UI Responsiveness and User Control ✅ PASS

**Verification**:
- ✅ FR-026 to FR-029: Background threads, responsiveness requirements
- ✅ User Story 4: UI responds within 1 second during operations
- ✅ Download uses QThread with signals for progress updates
- ✅ Cancel functionality planned (FR-028, FR-029)

**Implementation Plan**:
- DownloadManager extends QThread for background execution
- All I/O operations off main thread
- Signal-slot architecture for progress updates
- Cancel button available during downloads

### Principle V: Security and Credential Protection ✅ PASS

**Verification**:
- ✅ FR-037: Password masking in UI
- ✅ FR-038: Credentials in memory only (no disk persistence)
- ✅ User Story 6: Secure credential handling
- ✅ No credential logging planned

**Implementation Plan**:
- QLineEdit.setEchoMode(QLineEdit.Password) for password field
- Connection credentials stored in instance variables only
- Logger excludes password fields
- No configuration file persistence

### Principle VI: Simplicity and Single Responsibility ✅ PASS

**Verification**:
- ✅ Single purpose: Download snapshots from Cassandra to local folders
- ✅ No database administration features
- ✅ No image manipulation (only ByteArray → PNG conversion)
- ✅ No upload capabilities
- ✅ No complex analytics or reporting

**Implementation Plan**:
- Reject any features outside snapshot download workflow
- Keep UI focused: Connection → Search → Download
- Minimal configuration (only connection and save path)

### Database Safety Rules ✅ PASS

**Query Construction**:
- ✅ Will use cassandra-driver parameterized queries
- ✅ WHERE clauses filter on partition keys (year, month, day, eqpid per spec)
- ✅ No ALLOW FILTERING planned
- ✅ Timeouts enforced (10s search, 5s connection test per FR-031, FR-002)

**Connection Management**:
- ✅ Single connection (per Technical Context constraints)
- ✅ Connection close on disconnect
- ✅ Connection state displayed in UI (FR-003)
- ✅ No automatic retry (user-initiated retry only)

**Data Retrieval**:
- ✅ Batch processing planned to avoid memory exhaustion (FR-039)
- ✅ No caching beyond current operation
- ✅ Full dataset retrieved but only 20 displayed (FR-013, FR-017)

### Gate Status: ✅ ALL GATES PASSED

No constitution violations detected. Feature specification and technical approach fully comply with all project principles. Proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
cassandra-snapshot-downloader/
├── main.py                      # Application entry point, QApplication initialization
├── requirements.txt             # Python dependencies (PyQt5, cassandra-driver, Pillow)
├── README.md                    # Project documentation, setup, and usage instructions
├── .gitignore                   # Python artifacts, virtual environment, IDE files
│
├── config/
│   ├── __init__.py
│   └── settings.py              # Application constants (timeouts, limits, defaults)
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py           # MainWindow class - primary UI layout and orchestration
│   ├── widgets.py               # Custom widgets (if needed for reusable components)
│   └── resources/               # Icons, stylesheets (optional for polish)
│
├── database/
│   ├── __init__.py
│   ├── cassandra_client.py      # CassandraClient - connection, queries, session management
│   └── models.py                # SnapshotRecord dataclass
│
├── downloader/
│   ├── __init__.py
│   ├── download_manager.py      # DownloadManager QThread - download orchestration
│   └── file_handler.py          # Filesystem utilities (folder creation, PNG saving)
│
├── utils/
│   ├── __init__.py
│   ├── logger.py                # Logging configuration and utilities
│   └── validators.py            # Input validation (date ranges, equipment ID)
│
└── tests/                       # Optional testing structure
    ├── __init__.py
    ├── test_cassandra_client.py # Database layer tests (mocked)
    ├── test_validators.py       # Input validation tests
    ├── test_file_handler.py     # File operations tests
    └── test_download_manager.py # Download logic tests (mocked database)
```

**Structure Decision**:

This follows the **single project** structure (Option 1) as this is a standalone desktop application with no web/mobile components. The organization separates concerns into logical layers:

- **ui/** - PyQt5 presentation layer (windows, widgets, user interaction)
- **database/** - Data access layer (Cassandra connection, query execution)
- **downloader/** - Business logic layer (download orchestration, file operations)
- **utils/** - Cross-cutting concerns (logging, validation)
- **config/** - Configuration constants
- **tests/** - Optional unit and integration tests

The structure aligns with the user's proposed directory layout while following Python packaging best practices (each package has `__init__.py`, flat hierarchy to avoid deep nesting).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations detected. This section is intentionally left empty.
