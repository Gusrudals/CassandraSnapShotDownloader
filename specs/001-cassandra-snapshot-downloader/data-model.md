# Data Model

**Feature**: Cassandra Snapshot Downloader
**Date**: 2025-11-11
**Status**: Phase 1 Complete

## Overview

This document defines the data structures and relationships used in the Cassandra Snapshot Downloader application. The application operates on four primary entities: database snapshots, connection configurations, download jobs, and log entries.

---

## Entity Definitions

### 1. SnapshotRecord

Represents a single screenshot snapshot retrieved from the Cassandra database.

**Purpose**: Domain model for snapshot data retrieved from the `snapshot` table in Cassandra

**Attributes**:

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| year | int | Yes | Four-digit year when snapshot was captured | 2000 ≤ year ≤ 2100 |
| month | int | Yes | Month when snapshot was captured | 1 ≤ month ≤ 12 |
| day | int | Yes | Day of month when snapshot was captured | 1 ≤ day ≤ 31 |
| eqpid | str | Yes | Equipment identifier (unique device/camera name) | Non-empty string, alphanumeric + underscore |
| fname | str | Yes | Filename containing epoch time and coordinates | Non-empty string, must be sanitized before filesystem use |
| image | bytes | Yes | Binary image data (PNG format ByteArray) | Non-None, non-empty bytes object |

**Python Implementation**:
```python
from dataclasses import dataclass
from datetime import date

@dataclass
class SnapshotRecord:
    """Represents a snapshot retrieved from Cassandra."""

    year: int
    month: int
    day: int
    eqpid: str
    fname: str
    image: bytes

    @property
    def capture_date(self) -> date:
        """Return the snapshot's capture date."""
        return date(self.year, self.month, self.day)

    @property
    def folder_path(self) -> str:
        """Return the relative folder path: year/month/day/eqpid"""
        return f"{self.year}/{self.month:02d}/{self.day:02d}/{self.eqpid}"

    def __post_init__(self):
        """Validate snapshot data after initialization."""
        if not self.eqpid:
            raise ValueError("Equipment ID cannot be empty")
        if not self.fname:
            raise ValueError("Filename cannot be empty")
        if not self.image:
            raise ValueError("Image data cannot be empty")
```

**Relationships**:
- One SnapshotRecord belongs to one ConnectionConfiguration (through query context)
- One SnapshotRecord generates one FileOperationLogEntry during download

**Lifecycle**:
1. Created from Cassandra query result row
2. Passed to DownloadManager for processing
3. Converted to PNG file via file_handler
4. Discarded after file saved (no persistent storage)

---

### 2. ConnectionConfiguration

Represents the credentials and connection parameters for accessing the Cassandra database.

**Purpose**: Encapsulate database connection details for authentication and session establishment

**Attributes**:

| Attribute | Type | Required | Description | Validation | Security |
|-----------|------|----------|-------------|------------|----------|
| host | str | Yes | Cassandra cluster hostname or IP address | Non-empty, valid hostname/IP format | Stored in memory only |
| port | int | Yes | Cassandra native transport port | 1 ≤ port ≤ 65535, default 9042 | N/A |
| username | str | Yes | Database authentication username | Non-empty string | Stored in memory only |
| password | str | Yes | Database authentication password | Non-empty string | **Never logged, never persisted** |
| keyspace | str | Yes | Cassandra keyspace containing snapshot table | Non-empty string | Stored in memory only |

**Python Implementation**:
```python
from dataclasses import dataclass

@dataclass
class ConnectionConfiguration:
    """Cassandra database connection parameters."""

    host: str
    port: int
    username: str
    password: str
    keyspace: str

    def __post_init__(self):
        """Validate connection parameters."""
        if not self.host:
            raise ValueError("Host cannot be empty")
        if not (1 <= self.port <= 65535):
            raise ValueError(f"Invalid port: {self.port}")
        if not self.username:
            raise ValueError("Username cannot be empty")
        if not self.password:
            raise ValueError("Password cannot be empty")
        if not self.keyspace:
            raise ValueError("Keyspace cannot be empty")

    def __repr__(self):
        """Representation that excludes password."""
        return (f"ConnectionConfiguration(host='{self.host}', port={self.port}, "
                f"username='{self.username}', password='***', "
                f"keyspace='{self.keyspace}')")

    @property
    def contact_point(self) -> str:
        """Return formatted contact point for display."""
        return f"{self.host}:{self.port}/{self.keyspace}"
```

**Relationships**:
- One ConnectionConfiguration produces multiple SnapshotRecords (via queries)
- One ConnectionConfiguration is used by one CassandraClient instance

**Lifecycle**:
1. Created from UI form inputs when user clicks "Test Connection" or "Search"
2. Passed to CassandraClient for session establishment
3. Stored in MainWindow instance variables during application runtime
4. Destroyed when application closes (no persistence per constitution)

**Security Constraints** (per Constitution Principle V):
- Password MUST be masked in UI (QLineEdit.Password mode)
- Password MUST NOT appear in logs or error messages
- Entire configuration MUST NOT be persisted to disk
- Use `__repr__` override to prevent accidental password logging

---

### 3. DownloadJob

Represents a batch download operation with progress tracking and status.

**Purpose**: Track state and statistics for a multi-file download operation

**Attributes**:

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| start_date | date | Yes | Start of date range for snapshot search | start_date ≤ end_date |
| end_date | date | Yes | End of date range for snapshot search | end_date ≤ today |
| eqpid | str | Yes | Equipment ID filter | Non-empty string |
| save_path | str | Yes | Root directory for downloaded files | Must be writable directory |
| total_count | int | No | Total number of snapshots to download | ≥ 0, set after query completes |
| processed_count | int | No | Number of snapshots processed so far | 0 ≤ processed ≤ total |
| success_count | int | No | Number of successfully downloaded files | ≥ 0 |
| failed_count | int | No | Number of failed download attempts | ≥ 0 |
| skipped_count | int | No | Number of files skipped (already exist) | ≥ 0 |
| status | str | Yes | Current job status | One of: 'pending', 'running', 'completed', 'failed', 'cancelled' |
| error_message | str | No | Error description if status is 'failed' | Optional string |

**Python Implementation**:
```python
from dataclasses import dataclass, field
from datetime import date
from enum import Enum

class DownloadStatus(Enum):
    """Download job status states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class DownloadJob:
    """Tracks progress and status of a download operation."""

    # Query parameters
    start_date: date
    end_date: date
    eqpid: str
    save_path: str

    # Progress tracking
    total_count: int = 0
    processed_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0

    # Status
    status: DownloadStatus = DownloadStatus.PENDING
    error_message: str = ""

    @property
    def progress_percentage(self) -> float:
        """Calculate completion percentage (0-100)."""
        if self.total_count == 0:
            return 0.0
        return (self.processed_count / self.total_count) * 100

    @property
    def is_complete(self) -> bool:
        """Check if job has finished (success, failure, or cancellation)."""
        return self.status in (
            DownloadStatus.COMPLETED,
            DownloadStatus.FAILED,
            DownloadStatus.CANCELLED
        )

    def increment_success(self):
        """Record a successful file download."""
        self.processed_count += 1
        self.success_count += 1

    def increment_failed(self):
        """Record a failed file download."""
        self.processed_count += 1
        self.failed_count += 1

    def increment_skipped(self):
        """Record a skipped file (already exists)."""
        self.processed_count += 1
        self.skipped_count += 1
```

**Relationships**:
- One DownloadJob processes multiple SnapshotRecords
- One DownloadJob generates multiple FileOperationLogEntries
- One DownloadJob is managed by one DownloadManager thread

**State Transitions**:
```
PENDING → RUNNING → COMPLETED
        ↓
        → FAILED
        ↓
        → CANCELLED
```

**Lifecycle**:
1. Created when user clicks "Download All" button
2. Passed to DownloadManager thread
3. Updated via signal emissions as files are processed
4. Destroyed when DownloadManager thread completes and is cleaned up

---

### 4. FileOperationLogEntry

Represents a single file download attempt (success, failure, or skip) for audit logging.

**Purpose**: Provide detailed audit trail of all file operations during download

**Attributes**:

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| timestamp | datetime | Yes | When the operation occurred | Auto-generated, UTC |
| filename | str | Yes | Snapshot filename being processed | Non-empty string |
| file_path | str | Yes | Full path where file was saved/attempted | Absolute path |
| status | str | Yes | Operation result | One of: 'success', 'failed', 'skipped' |
| error_message | str | No | Error details if status is 'failed' | Optional, populated on errors |

**Python Implementation**:
```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class FileOperationStatus(Enum):
    """File operation outcome."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class FileOperationLogEntry:
    """Records the result of a single file download attempt."""

    filename: str
    file_path: str
    status: FileOperationStatus
    error_message: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def format_log_message(self) -> str:
        """Format entry as a human-readable log line."""
        status_str = self.status.value.upper()
        base_msg = f"[{self.timestamp.strftime('%H:%M:%S')}] {status_str}: {self.filename}"

        if self.status == FileOperationStatus.FAILED and self.error_message:
            return f"{base_msg} - {self.error_message}"
        elif self.status == FileOperationStatus.SKIPPED:
            return f"{base_msg} (already exists)"
        else:
            return base_msg

    def to_file_log_line(self) -> str:
        """Format entry for file-based logging (more verbose)."""
        return (f"{self.timestamp.isoformat()} | {self.status.value.upper()} | "
                f"{self.file_path} | {self.error_message}")
```

**Relationships**:
- One FileOperationLogEntry corresponds to one SnapshotRecord
- Many FileOperationLogEntries belong to one DownloadJob

**Lifecycle**:
1. Created in DownloadManager after each file operation attempt
2. Emitted via `log_message` signal to UI
3. Appended to in-memory log display (QTextEdit)
4. Written to file log via logger module
5. Discarded when application closes (persists only in log file)

---

## Database Schema (Cassandra)

### snapshot Table

**Note**: This is the **source** schema in Cassandra. The application does NOT create or modify this table (read-only access per constitution).

**Table Structure**:
```cql
CREATE TABLE snapshot (
    year int,
    month int,
    day int,
    eqpid text,
    fname text,
    image blob,
    PRIMARY KEY ((year, month, day, eqpid), fname)
) WITH CLUSTERING ORDER BY (fname ASC);
```

**Partition Key**: `(year, month, day, eqpid)` - ensures snapshots for same equipment on same day are co-located

**Clustering Key**: `fname` - orders snapshots within partition by filename (typically contains epoch timestamp)

**Query Patterns**:
1. **Connection Test**: `SELECT count(*) FROM snapshot LIMIT 1`
2. **Count Query**: `SELECT COUNT(*) FROM snapshot WHERE year = ? AND month = ? AND day >= ? AND day <= ? AND eqpid = ?`
3. **Fetch Query**: `SELECT year, month, day, eqpid, fname, image FROM snapshot WHERE year = ? AND month = ? AND day >= ? AND day <= ? AND eqpid = ?`

**Assumptions** (from spec):
- Table already exists (not created by application)
- Schema matches above structure
- User has SELECT permissions on this table
- Image column contains valid PNG ByteArray data (though validation is required)

---

## Filesystem Data Model

### Folder Hierarchy

Downloaded files are organized in a hierarchical structure:

```
[SavePath]/
└── [Year]/
    └── [Month]/
        └── [Day]/
            └── [EquipmentID]/
                ├── snapshot_001.png
                ├── snapshot_002.png
                └── ...
```

**Example**:
```
/home/user/Downloads/cassandra_snapshots/
└── 2025/
    ├── 01/
    │   ├── 15/
    │   │   └── CAM_001/
    │   │       ├── 1705334400_x100_y200.png
    │   │       └── 1705338000_x150_y250.png
    │   └── 16/
    │       └── CAM_001/
    │           └── 1705420800_x120_y230.png
    └── 11/
        └── 11/
            └── CAM_002/
                └── 1731283200_x300_y400.png
```

**Rationale**:
- Hierarchical organization makes browsing snapshots easy
- Year/Month/Day folders allow chronological navigation
- Equipment ID isolation prevents mixing different devices
- Matches partition key structure of Cassandra table

**Constraints**:
- Folder names are zero-padded for sorting (e.g., `01` not `1` for month)
- Equipment ID folder name must be filesystem-safe (no special characters)
- Duplicate detection: File exists check uses exact path match

---

## Data Flow Diagram

```
┌──────────────┐
│ User Input   │
│ (UI Forms)   │
└──────┬───────┘
       │
       ├─────────────────────────────────┐
       │                                 │
       v                                 v
┌─────────────────────┐        ┌──────────────────┐
│ ConnectionConfig    │        │ DownloadJob      │
│ - host, port        │        │ - date range     │
│ - username, password│        │ - eqpid          │
│ - keyspace          │        │ - save_path      │
└──────┬──────────────┘        └────┬─────────────┘
       │                            │
       v                            │
┌─────────────────────┐             │
│ CassandraClient     │             │
│ .test_connection()  │             │
│ .query_snapshots()  │◄────────────┘
└──────┬──────────────┘
       │
       │ (Query Results)
       │
       v
┌─────────────────────┐
│ List[SnapshotRecord]│
│ - year, month, day  │
│ - eqpid, fname      │
│ - image (bytes)     │
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│ DownloadManager     │
│ (QThread)           │
│ - processes records │
│ - emits signals     │
└──────┬──────────────┘
       │
       ├───────────────────────────────┐
       │                               │
       v                               v
┌─────────────────────┐      ┌────────────────────┐
│ FileHandler         │      │ FileOperationLog   │
│ .create_folders()   │      │ - timestamp        │
│ .save_image()       │      │ - filename, status │
│ .file_exists()      │      │ - error_message    │
└──────┬──────────────┘      └─────┬──────────────┘
       │                           │
       v                           v
┌─────────────────────┐      ┌────────────────────┐
│ Filesystem          │      │ UI Log Display     │
│ year/month/day/     │      │ & File Logger      │
│   eqpid/fname.png   │      │                    │
└─────────────────────┘      └────────────────────┘
```

---

## Validation Rules Summary

### SnapshotRecord
- ✅ year, month, day form valid date
- ✅ eqpid is non-empty
- ✅ fname is non-empty
- ✅ image is non-None, non-empty bytes

### ConnectionConfiguration
- ✅ host is non-empty string
- ✅ port is in range [1, 65535]
- ✅ username is non-empty
- ✅ password is non-empty (but never logged)
- ✅ keyspace is non-empty

### DownloadJob
- ✅ start_date ≤ end_date
- ✅ end_date ≤ today
- ✅ (end_date - start_date).days ≤ 365
- ✅ eqpid is non-empty
- ✅ save_path is writable directory
- ✅ status transitions follow valid state machine

### FileOperationLogEntry
- ✅ filename is non-empty
- ✅ file_path is absolute path
- ✅ status is valid enum value
- ✅ timestamp is auto-generated

---

## Implementation Files Mapping

| Entity | Implementation File | Purpose |
|--------|-------------------|---------|
| SnapshotRecord | `database/models.py` | Dataclass definition |
| ConnectionConfiguration | `database/models.py` | Dataclass definition |
| DownloadJob | `downloader/download_manager.py` | Dataclass + DownloadManager thread |
| FileOperationLogEntry | `utils/logger.py` | Dataclass + logging utilities |
| Validation Rules | `utils/validators.py` | Validation functions |
| Cassandra Queries | `database/cassandra_client.py` | CassandraClient class |
| File Operations | `downloader/file_handler.py` | Filesystem utilities |

---

## Next Steps

**Phase 1 Continuation**: Generate API contracts for internal component communication (signal/slot contracts, method signatures)

**Phase 2**: Generate actionable tasks based on this data model and the project structure
