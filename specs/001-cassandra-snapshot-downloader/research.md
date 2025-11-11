# Research & Technology Decisions

**Feature**: Cassandra Snapshot Downloader
**Date**: 2025-11-11
**Status**: Phase 0 Complete

## Overview

This document consolidates research findings and technology decisions for building a desktop application that downloads screenshot snapshots from Cassandra database to local filesystem. All technical unknowns from the implementation plan have been resolved.

---

## Technology Stack Decisions

### 1. GUI Framework: PyQt5

**Decision**: Use PyQt5 for the desktop GUI framework

**Rationale**:
- **Cross-platform support**: Single codebase runs on Linux, Windows, and macOS without modification
- **Mature and stable**: PyQt5 has been production-ready for years with extensive documentation
- **Rich widget library**: Built-in support for all required components (QTableWidget, QDateEdit, QProgressBar, QFileDialog, QGroupBox)
- **Threading support**: QThread provides native background task execution with signal-slot communication
- **Professional appearance**: Native look-and-feel on all platforms

**Alternatives considered**:
- **Tkinter**: Rejected due to limited widgets (no native table sorting, date pickers require third-party libraries), dated appearance
- **wxPython**: Rejected due to smaller community, less comprehensive documentation compared to PyQt5
- **Kivy**: Rejected as it targets mobile-first design, overkill for desktop-focused application
- **PyQt6/PySide6**: Not chosen to maintain compatibility with older Python environments (PyQt5 supports Python 3.7+)

**Best Practices**:
- Use `.ui` files from Qt Designer for complex layouts (optional but recommended for maintainability)
- Separate UI logic from business logic (MainWindow orchestrates, doesn't implement download logic)
- Use signal-slot pattern for component communication
- Always execute I/O operations in QThread, never on main thread
- Use `deleteLater()` for proper thread cleanup

**Resources**:
- Official docs: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- Threading guide: https://doc.qt.io/qt-5/qthread.html
- Signal-slot patterns: https://doc.qt.io/qt-5/signalsandslots.html

---

### 2. Cassandra Database Driver: cassandra-driver

**Decision**: Use DataStax `cassandra-driver` (official Python driver for Apache Cassandra)

**Rationale**:
- **Official support**: Maintained by DataStax, the primary Cassandra commercial sponsor
- **Full protocol support**: Implements native Cassandra binary protocol v3/v4
- **Connection management**: Built-in connection pooling (though we'll use single connection per constitution)
- **Authentication support**: PlainTextAuthProvider for username/password auth
- **Query timeouts**: Configurable timeouts at session and query level
- **Type safety**: Automatic Python type conversion for Cassandra types (ByteArray, int, text)

**Alternatives considered**:
- **Direct CQL shell integration**: Rejected - no programmatic access, can't retrieve binary data easily
- **REST API wrapper**: Rejected - no standard Cassandra REST API, would require custom server component

**Best Practices**:
- Use `Cluster.connect()` with explicit contact points and port
- Set `default_timeout` on session creation (5 seconds for connection, 10 seconds for queries)
- Use prepared statements for repeated queries (optimization, though only 2 query types in our app)
- Handle `cassandra.OperationTimedOut`, `cassandra.Unauthorized`, `cassandra.NoHostAvailable` exceptions specifically
- Call `cluster.shutdown()` and `session.shutdown()` on disconnect to release resources

**Query Pattern**:
```python
# Connection with timeout
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

auth_provider = PlainTextAuthProvider(username='user', password='pass')
cluster = Cluster([host], port=port, auth_provider=auth_provider,
                   connect_timeout=5.0)
session = cluster.connect(keyspace)
session.default_timeout = 10.0

# Parameterized query (prevents injection, though all inputs are typed)
query = """
SELECT year, month, day, eqpid, fname, image
FROM snapshot
WHERE year = ? AND month = ? AND day >= ? AND day <= ? AND eqpid = ?
"""
rows = session.execute(query, (year, month, start_day, end_day, eqpid))
```

**Resources**:
- Driver docs: https://docs.datastax.com/en/developer/python-driver/latest/
- API reference: https://docs.datastax.com/en/developer/python-driver/latest/api/
- Best practices: https://docs.datastax.com/en/developer/python-driver/latest/performance/

---

### 3. Image Processing: Pillow (PIL Fork)

**Decision**: Use Pillow for ByteArray to PNG conversion

**Rationale**:
- **De facto standard**: Pillow is the most widely used Python image library
- **ByteArray support**: `Image.open(BytesIO(byte_array))` handles in-memory binary data
- **PNG output**: Simple `.save(path, 'PNG')` method
- **Format validation**: Automatically detects invalid image data and raises `PIL.UnidentifiedImageError`
- **No external dependencies**: Pure Python implementation, cross-platform

**Alternatives considered**:
- **OpenCV (cv2)**: Rejected - massive dependency for simple task, C++ bindings harder to install
- **imageio**: Rejected - less mature, smaller community
- **Direct binary write**: Rejected - need format validation, can't verify ByteArray is valid PNG

**Best Practices**:
- Wrap `Image.open()` in try-except to catch corrupted data
- Use context manager when possible: `with Image.open(BytesIO(data)) as img: img.save(path)`
- Specify format explicitly: `img.save(path, 'PNG')` to avoid extension-based guessing
- Check ByteArray is not None/empty before processing

**Code Pattern**:
```python
from PIL import Image
from io import BytesIO

def save_image(image_bytes: bytes, file_path: str) -> bool:
    """Convert ByteArray to PNG and save to file."""
    if not image_bytes:
        raise ValueError("Image data is empty")

    try:
        with Image.open(BytesIO(image_bytes)) as img:
            img.save(file_path, 'PNG')
        return True
    except PIL.UnidentifiedImageError:
        raise ValueError("Invalid image data - cannot identify format")
```

**Resources**:
- Pillow docs: https://pillow.readthedocs.io/en/stable/
- BytesIO handling: https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.open

---

### 4. Testing Framework: pytest + pytest-qt

**Decision**: Use pytest for testing, pytest-qt for GUI testing

**Rationale**:
- **Industry standard**: pytest is the most popular Python testing framework
- **Fixtures**: Easy to create reusable test fixtures (mock database, temp directories)
- **Parameterization**: Test multiple scenarios with `@pytest.mark.parametrize`
- **pytest-qt plugin**: Provides `qtbot` fixture for testing PyQt5 applications
- **Mocking support**: Works seamlessly with `unittest.mock` for database mocking

**Alternatives considered**:
- **unittest**: Rejected - more verbose, pytest offers better fixtures and assertions
- **nose**: Rejected - project is in maintenance mode, pytest is actively developed

**Best Practices**:
- Mock `CassandraClient` for all tests (no real database connections in tests)
- Use `qtbot.waitSignal()` to test asynchronous signal emissions
- Create fixtures for common setups (MainWindow instance, temp directories)
- Test error paths explicitly (connection failures, invalid inputs, disk full scenarios)

**Test Structure**:
```python
import pytest
from unittest.mock import Mock, patch
from pytestqt.qtbot import QtBot

@pytest.fixture
def mock_cassandra_client():
    client = Mock(spec=CassandraClient)
    client.test_connection.return_value = True
    return client

def test_search_requires_eqpid(qtbot, mock_cassandra_client):
    """Test that search validates equipment ID is not empty."""
    window = MainWindow()
    window.cassandra_client = mock_cassandra_client
    qtbot.addWidget(window)

    # Leave eqpid empty, click search
    window.search_button.click()

    # Verify error message displayed
    assert "Equipment ID is required" in window.status_label.text()
    mock_cassandra_client.query_snapshots.assert_not_called()
```

**Resources**:
- pytest docs: https://docs.pytest.org/
- pytest-qt: https://pytest-qt.readthedocs.io/
- Mocking guide: https://docs.python.org/3/library/unittest.mock.html

---

## Cassandra Integration Patterns

### Date Range Query Design

**Challenge**: Cassandra requires filtering on partition keys (year, month, day) efficiently

**Solution**: Convert user's date range to multiple queries by year/month combinations

**Rationale**:
- Cassandra table is partitioned by (year, month, day, eqpid)
- WHERE clause must include partition key prefix for efficient queries
- Date ranges spanning months/years require multiple queries or ALLOW FILTERING (which we reject per constitution)

**Implementation Pattern**:
```python
def query_date_range(session, start_date, end_date, eqpid):
    """Query snapshots across date range by iterating month boundaries."""
    results = []

    # Generate all year-month combinations in range
    current = start_date.replace(day=1)
    while current <= end_date:
        year, month = current.year, current.month

        # Determine day range for this month
        if current.year == start_date.year and current.month == start_date.month:
            start_day = start_date.day
        else:
            start_day = 1

        if current.year == end_date.year and current.month == end_date.month:
            end_day = end_date.day
        else:
            # Last day of month
            if month == 12:
                next_month = current.replace(year=year+1, month=1)
            else:
                next_month = current.replace(month=month+1)
            end_day = (next_month - timedelta(days=1)).day

        # Query this month's data
        query = """
        SELECT year, month, day, eqpid, fname, image
        FROM snapshot
        WHERE year = ? AND month = ? AND day >= ? AND day <= ? AND eqpid = ?
        """
        rows = session.execute(query, (year, month, start_day, end_day, eqpid))
        results.extend(rows)

        # Move to next month
        if month == 12:
            current = current.replace(year=year+1, month=1)
        else:
            current = current.replace(month=month+1)

    return results
```

**Best Practice**: Limit date range queries to reasonable spans (e.g., max 1 year) to prevent excessive query iterations

---

### Memory-Efficient Batch Processing

**Challenge**: Downloading 10,000+ images could exhaust memory if all loaded at once

**Solution**: Stream results row-by-row, process and discard immediately

**Rationale**:
- cassandra-driver returns results as iterator by default (lazy loading)
- Process each row, save image, discard binary data before next row
- Avoids loading all ByteArrays into memory simultaneously

**Implementation Pattern**:
```python
def download_all(session, query_params, save_path, progress_callback):
    """Download snapshots with memory-efficient streaming."""
    rows = query_date_range(session, **query_params)

    # Consume iterator one row at a time
    for idx, row in enumerate(rows):
        # Extract data
        year, month, day, eqpid, fname, image_bytes = row

        # Build file path
        folder = os.path.join(save_path, str(year), str(month), str(day), eqpid)
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, fname)

        # Skip if exists
        if os.path.exists(file_path):
            progress_callback(idx + 1, "skipped")
            continue

        # Save image (image_bytes discarded after this)
        try:
            save_image(image_bytes, file_path)
            progress_callback(idx + 1, "success")
        except Exception as e:
            progress_callback(idx + 1, f"failed: {str(e)}")

        # image_bytes now out of scope, garbage collected
```

---

## PyQt5 Threading Best Practices

### Background Task Pattern with QThread

**Challenge**: Long-running downloads must not block UI

**Solution**: Subclass QThread, emit signals for progress/completion, connect to UI slots

**Pattern**:
```python
from PyQt5.QtCore import QThread, pyqtSignal

class DownloadManager(QThread):
    # Define signals (can only be class attributes, not instance)
    progress_updated = pyqtSignal(int, int, str)  # current, total, status
    log_message = pyqtSignal(str)
    download_completed = pyqtSignal(int, int, int)  # success, failed, skipped
    download_error = pyqtSignal(str)

    def __init__(self, cassandra_client, save_path, query_params):
        super().__init__()
        self.cassandra_client = cassandra_client
        self.save_path = save_path
        self.query_params = query_params
        self._is_cancelled = False

    def run(self):
        """Executed in background thread when start() is called."""
        try:
            # Query database
            rows = self.cassandra_client.query_snapshots(**self.query_params)
            total = len(rows) if hasattr(rows, '__len__') else 0

            success, failed, skipped = 0, 0, 0
            for idx, row in enumerate(rows):
                if self._is_cancelled:
                    self.log_message.emit(f"Download cancelled after {idx} files")
                    break

                # Process file
                status = self._process_row(row)
                if status == "success":
                    success += 1
                elif status == "failed":
                    failed += 1
                else:
                    skipped += 1

                # Emit progress
                self.progress_updated.emit(idx + 1, total, status)
                self.log_message.emit(f"[{status}] {row.fname}")

            self.download_completed.emit(success, failed, skipped)

        except Exception as e:
            self.download_error.emit(f"Download failed: {str(e)}")

    def cancel(self):
        """Request cancellation (checked in run loop)."""
        self._is_cancelled = True
```

**UI Integration**:
```python
# In MainWindow.__init__
self.download_thread = None

def on_download_clicked(self):
    # Create thread
    self.download_thread = DownloadManager(
        self.cassandra_client,
        self.save_path,
        self.query_params
    )

    # Connect signals to slots
    self.download_thread.progress_updated.connect(self.update_progress_bar)
    self.download_thread.log_message.connect(self.append_log)
    self.download_thread.download_completed.connect(self.on_download_complete)
    self.download_thread.download_error.connect(self.show_error_dialog)

    # Start background execution
    self.download_thread.start()

    # Update UI state
    self.download_button.setEnabled(False)
    self.cancel_button.setVisible(True)

def on_download_complete(self, success, failed, skipped):
    self.download_button.setEnabled(True)
    self.cancel_button.setVisible(False)
    self.download_thread.deleteLater()  # Clean up thread
    QMessageBox.information(
        self,
        "Download Complete",
        f"Success: {success}, Failed: {failed}, Skipped: {skipped}"
    )
```

**Critical Rules**:
- Never call UI methods directly from thread (use signals only)
- Always call `deleteLater()` after thread completes
- Use `wait()` if you need to ensure thread has finished before proceeding

---

## Error Handling Patterns

### User-Facing Error Messages

**Principle**: Every error message must tell user (1) what failed, (2) why, (3) what to do

**Pattern**:
```python
try:
    cluster.connect(keyspace)
except cassandra.NoHostAvailable as e:
    return (False,
            "Connection failed: Cannot reach database server. "
            "Check that the host address and port are correct, "
            "and that your network allows connections to the database.")

except cassandra.Unauthorized as e:
    return (False,
            "Connection failed: Invalid username or password. "
            "Verify your credentials and try again.")

except cassandra.InvalidRequest as e:
    if "Unknown keyspace" in str(e):
        return (False,
                f"Connection failed: Keyspace '{keyspace}' does not exist. "
                "Check the keyspace name and try again.")
    else:
        return (False, f"Connection failed: {str(e)}")

except Exception as e:
    return (False,
            f"Connection failed: Unexpected error ({type(e).__name__}). "
            "Contact support if this persists.")
```

### Logging Pattern

**Requirements**:
- File-based log for audit trail
- Console log for development
- Exclude sensitive data (passwords)
- Include timestamps, severity, context

**Implementation**:
```python
import logging
from datetime import datetime

def setup_logger():
    """Configure application logging."""
    logger = logging.getLogger('cassandra_downloader')
    logger.setLevel(logging.DEBUG)

    # File handler (detailed logs)
    log_file = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler (info and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Usage
logger = setup_logger()
logger.info(f"Connecting to {host}:{port}")  # No password logged!
logger.debug(f"Query: {query_text}")
logger.error(f"Failed to save {fname}: {error_message}")
```

---

## Input Validation Patterns

### Date Range Validation

```python
from datetime import date

def validate_date_range(start_date: date, end_date: date) -> tuple[bool, str]:
    """Validate date range is logical and reasonable."""
    if start_date > end_date:
        return (False, "End date must be after start date")

    if (end_date - start_date).days > 365:
        return (False, "Date range cannot exceed 1 year. Please narrow your search.")

    if end_date > date.today():
        return (False, "End date cannot be in the future")

    return (True, "")
```

### Filename Sanitization

```python
import re

def sanitize_filename(fname: str) -> str:
    """Remove or replace invalid filesystem characters."""
    # Replace invalid characters with underscore
    # Invalid: / \ : * ? " < > |
    sanitized = re.sub(r'[/\\:*?"<>|]', '_', fname)

    # Ensure .png extension
    if not sanitized.lower().endswith('.png'):
        sanitized += '.png'

    return sanitized
```

---

## Configuration Constants

**File**: `config/settings.py`

```python
"""Application configuration constants."""

# Database timeouts (seconds)
CONNECTION_TIMEOUT = 5.0
QUERY_TIMEOUT = 10.0

# UI display limits
TABLE_DISPLAY_LIMIT = 20

# Date range limits
MAX_DATE_RANGE_DAYS = 365

# Progress update frequency
PROGRESS_UPDATE_INTERVAL = 10  # Update UI every N files

# File system
DEFAULT_SAVE_PATH = "~/Downloads/cassandra_snapshots"

# Logging
LOG_FILE_PREFIX = "cassandra_downloader"
LOG_RETENTION_DAYS = 30
```

---

## Dependency Versions

**File**: `requirements.txt`

```
PyQt5>=5.15.0,<6.0.0
cassandra-driver>=3.28.0,<4.0.0
Pillow>=10.0.0,<11.0.0
pytest>=7.4.0,<8.0.0
pytest-qt>=4.2.0,<5.0.0
```

**Rationale**:
- **PyQt5 5.15.x**: Last version before PyQt6 major changes, stable and well-tested
- **cassandra-driver 3.28.x**: Latest 3.x series, mature and production-ready
- **Pillow 10.x**: Latest major version with security patches
- **pytest/pytest-qt**: Latest versions for testing (dev dependency)

**Version pinning strategy**: Use pessimistic version constraints (`>=X.Y.0,<X+1.0.0`) to allow patch updates but prevent breaking changes

---

## Research Summary

All technical unknowns have been resolved:

✅ **GUI Framework**: PyQt5 selected for cross-platform desktop UI
✅ **Database Driver**: cassandra-driver for Cassandra connectivity
✅ **Image Processing**: Pillow for ByteArray to PNG conversion
✅ **Testing**: pytest + pytest-qt for unit and GUI testing
✅ **Threading Pattern**: QThread with signals for background tasks
✅ **Query Strategy**: Month-by-month iteration to avoid ALLOW FILTERING
✅ **Memory Management**: Stream-based processing to handle large datasets
✅ **Error Handling**: Specific exception types with actionable messages
✅ **Validation**: Input sanitization and range checking patterns defined
✅ **Logging**: File and console logging with sensitive data exclusion

**Next Phase**: Proceed to Phase 1 (Data Model and Contracts)
