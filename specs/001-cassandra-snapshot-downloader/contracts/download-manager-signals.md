# DownloadManager Signal/Slot Contract

**Component**: `downloader/download_manager.py`
**Purpose**: Background thread for downloading and organizing snapshot files
**Type**: PyQt5 QThread with Signal/Slot communication

---

## Class: DownloadManager (extends QThread)

### Overview

DownloadManager executes download operations in a background thread to prevent UI blocking. Communication between the background thread and main UI thread occurs exclusively through Qt signals (emitted from background) and slots (executed on main thread).

---

## Signals

### Signal: progress_updated

```python
progress_updated = pyqtSignal(int, int, str)
```

**Purpose**: Notify UI of download progress after each file operation

**Parameters**:
1. `current: int` - Number of files processed so far (1-indexed)
2. `total: int` - Total number of files to process
3. `status: str` - Status of most recent operation: "success", "failed", or "skipped"

**Emission Frequency**: Once per file processed

**Example Emission**:
```python
# In DownloadManager.run()
self.progress_updated.emit(15, 100, "success")  # 15/100 files, last file succeeded
self.progress_updated.emit(16, 100, "skipped")  # 16/100 files, last file skipped
```

**UI Handler Contract**:
```python
@pyqtSlot(int, int, str)
def on_progress_updated(self, current: int, total: int, status: str):
    """
    Update progress bar and status label.

    Args:
        current: Files processed (1-indexed)
        total: Total files to process
        status: Last operation status ("success", "failed", "skipped")

    Side Effects:
        - Updates QProgressBar value and maximum
        - Updates status label: "Downloading... {current}/{total}"
        - Does NOT log individual file (use log_message signal for that)
    """
    percentage = int((current / total) * 100) if total > 0 else 0
    self.progress_bar.setValue(percentage)
    self.status_label.setText(f"Downloading... {current}/{total} ({percentage}%)")
```

---

### Signal: log_message

```python
log_message = pyqtSignal(str)
```

**Purpose**: Send log messages to UI for real-time display and file logging

**Parameters**:
1. `message: str` - Formatted log message ready for display

**Emission Frequency**: Once per file operation + additional messages for start/cancel/completion events

**Message Format**:
```
"[HH:MM:SS] STATUS: filename - details"
```

**Example Emissions**:
```python
# Start of download
self.log_message.emit("[14:23:15] Starting download of 1,234 snapshots...")

# Success
self.log_message.emit("[14:23:16] SUCCESS: 1705334400_x100_y200.png")

# Failed
self.log_message.emit("[14:23:17] FAILED: corrupted_image.png - Invalid image data")

# Skipped
self.log_message.emit("[14:23:18] SKIPPED: existing_file.png (already exists)")

# Cancellation
self.log_message.emit("[14:23:20] Download cancelled after 45 files")

# Completion
self.log_message.emit("[14:25:30] Download complete: 1,200 succeeded, 10 failed, 24 skipped")
```

**UI Handler Contract**:
```python
@pyqtSlot(str)
def on_log_message(self, message: str):
    """
    Append log message to text display and file logger.

    Args:
        message: Formatted log message (includes timestamp and status)

    Side Effects:
        - Appends message to QTextEdit widget
        - Auto-scrolls to bottom
        - Writes to file logger
    """
    self.log_text_edit.append(message)
    self.log_text_edit.verticalScrollBar().setValue(
        self.log_text_edit.verticalScrollBar().maximum()
    )
    logger.info(message)
```

---

### Signal: download_completed

```python
download_completed = pyqtSignal(int, int, int)
```

**Purpose**: Notify UI that download has finished successfully (all files processed)

**Parameters**:
1. `success_count: int` - Number of files successfully downloaded
2. `failed_count: int` - Number of files that failed
3. `skipped_count: int` - Number of files skipped (already existed)

**Emission Frequency**: Once per download job, at completion

**Example Emission**:
```python
# In DownloadManager.run() after processing all files
self.download_completed.emit(1200, 10, 24)  # 1200 success, 10 failed, 24 skipped
```

**UI Handler Contract**:
```python
@pyqtSlot(int, int, int)
def on_download_completed(self, success: int, failed: int, skipped: int):
    """
    Handle successful download completion.

    Args:
        success: Number of successfully downloaded files
        failed: Number of failed download attempts
        skipped: Number of files skipped (already existed)

    Side Effects:
        - Displays completion message dialog
        - Re-enables download button
        - Hides cancel button
        - Cleans up download thread
    """
    total = success + failed + skipped
    message = (
        f"Download complete!\n\n"
        f"Total: {total} files\n"
        f"Success: {success}\n"
        f"Failed: {failed}\n"
        f"Skipped: {skipped}"
    )
    QMessageBox.information(self, "Download Complete", message)

    self.download_button.setEnabled(True)
    self.cancel_button.setVisible(False)

    if self.download_thread:
        self.download_thread.deleteLater()
        self.download_thread = None
```

---

### Signal: download_error

```python
download_error = pyqtSignal(str)
```

**Purpose**: Notify UI of fatal error that stopped entire download operation

**Parameters**:
1. `error_message: str` - User-friendly error message following constitution pattern

**Emission Frequency**: Once if fatal error occurs (database connection lost, disk full, permissions error)

**Example Emissions**:
```python
# Database connection lost
self.download_error.emit(
    "Download failed: Lost connection to database. "
    "Check your network and reconnect before retrying."
)

# Disk full
self.download_error.emit(
    "Download failed: Insufficient disk space. "
    "Free up space on the target drive and try again."
)

# Permission denied
self.download_error.emit(
    "Download failed: Permission denied when writing to folder. "
    "Ensure you have write permissions to the selected path."
)
```

**UI Handler Contract**:
```python
@pyqtSlot(str)
def on_download_error(self, error_message: str):
    """
    Handle fatal download error.

    Args:
        error_message: User-friendly error description with resolution guidance

    Side Effects:
        - Displays error dialog
        - Re-enables download button
        - Hides cancel button
        - Cleans up download thread
    """
    QMessageBox.critical(self, "Download Failed", error_message)

    self.download_button.setEnabled(True)
    self.cancel_button.setVisible(False)

    if self.download_thread:
        self.download_thread.deleteLater()
        self.download_thread = None
```

---

## Constructor

```python
def __init__(
    self,
    cassandra_client: CassandraClient,
    save_path: str,
    start_date: date,
    end_date: date,
    eqpid: str
):
    """
    Initialize DownloadManager background thread.

    Args:
        cassandra_client: Connected CassandraClient instance (thread-safe for reads)
        save_path: Root directory for downloaded files (must exist and be writable)
        start_date: Beginning of date range for snapshot query
        end_date: End of date range for snapshot query
        eqpid: Equipment ID filter

    Preconditions:
        - cassandra_client.is_connected must be True
        - save_path must be valid, writable directory
        - start_date <= end_date
        - eqpid must be non-empty

    Postconditions:
        - Thread is initialized but NOT started (call .start() to begin)
        - self._is_cancelled is False
    """
    super().__init__()
    self.cassandra_client = cassandra_client
    self.save_path = save_path
    self.start_date = start_date
    self.end_date = end_date
    self.eqpid = eqpid
    self._is_cancelled = False
```

---

## Public Methods

### Method: run

```python
def run(self) -> None:
    """
    Execute download in background thread (called by QThread.start()).

    This method runs in the background thread. DO NOT call directly - use start().

    Process:
        1. Query all snapshots from Cassandra
        2. For each snapshot:
            a. Check if cancelled
            b. Create folder structure
            c. Check if file exists
            d. Convert ByteArray to PNG and save
            e. Emit progress_updated and log_message signals
        3. Emit download_completed or download_error signal

    Signals Emitted:
        - log_message: Start, per-file status, completion/cancellation
        - progress_updated: After each file processed
        - download_completed: On successful completion
        - download_error: On fatal error

    Exception Handling:
        - Individual file errors: Log and continue to next file
        - Fatal errors (database, disk): Emit download_error and exit
    """
```

---

### Method: cancel

```python
def cancel(self) -> None:
    """
    Request cancellation of download (graceful stop after current file).

    Thread-Safety: Safe to call from main thread while run() executes in background.

    Side Effects:
        - Sets self._is_cancelled to True
        - run() will check this flag after each file and stop if True

    Timing:
        - Cancellation is NOT immediate
        - Current file operation completes before stopping
        - Final log_message emitted: "Download cancelled after N files"
    """
    self._is_cancelled = True
```

**Example Usage**:
```python
# In MainWindow when cancel button clicked
@pyqtSlot()
def on_cancel_clicked(self):
    if self.download_thread and self.download_thread.isRunning():
        self.download_thread.cancel()
        self.cancel_button.setEnabled(False)  # Prevent multiple cancellations
        self.status_label.setText("Cancelling...")
```

---

## Complete Usage Example

```python
# In MainWindow class

def on_download_all_clicked(self):
    """Handle Download All button click."""
    # Create download thread
    self.download_thread = DownloadManager(
        cassandra_client=self.cassandra_client,
        save_path=self.save_path_edit.text(),
        start_date=self.start_date_edit.date().toPyDate(),
        end_date=self.end_date_edit.date().toPyDate(),
        eqpid=self.eqpid_edit.text()
    )

    # Connect signals to slots
    self.download_thread.progress_updated.connect(self.on_progress_updated)
    self.download_thread.log_message.connect(self.on_log_message)
    self.download_thread.download_completed.connect(self.on_download_completed)
    self.download_thread.download_error.connect(self.on_download_error)

    # Update UI state
    self.download_button.setEnabled(False)
    self.cancel_button.setVisible(True)
    self.cancel_button.setEnabled(True)
    self.progress_bar.setValue(0)
    self.log_text_edit.clear()

    # Start background thread
    self.download_thread.start()

@pyqtSlot()
def on_cancel_clicked(self):
    """Handle Cancel button click."""
    if self.download_thread:
        self.download_thread.cancel()
        self.cancel_button.setEnabled(False)
        self.status_label.setText("Cancelling after current file...")
```

---

## Signal Emission Order

### Successful Download (No Errors)

```
1. log_message: "Starting download of N snapshots..."
2. For each file:
    - progress_updated: (current, total, status)
    - log_message: "[TIME] STATUS: filename"
3. log_message: "Download complete: X succeeded, Y failed, Z skipped"
4. download_completed: (success_count, failed_count, skipped_count)
```

### Download with Fatal Error

```
1. log_message: "Starting download of N snapshots..."
2. For each file until error:
    - progress_updated: (current, total, status)
    - log_message: "[TIME] STATUS: filename"
3. log_message: "[TIME] ERROR: Fatal error occurred"
4. download_error: "Download failed: {error message with guidance}"
```

### Cancelled Download

```
1. log_message: "Starting download of N snapshots..."
2. For each file until cancellation:
    - progress_updated: (current, total, status)
    - log_message: "[TIME] STATUS: filename"
3. log_message: "Download cancelled after N files"
4. download_completed: (success_count, failed_count, skipped_count)
   [Note: Emits completed, not error, for graceful cancellation]
```

---

## Thread Safety Rules

### Safe Operations in run() (Background Thread)
- ✅ Call cassandra_client.query_snapshots() (read-only, thread-safe)
- ✅ Call file_handler.create_folder_structure()
- ✅ Call file_handler.save_image()
- ✅ Call os.path.exists()
- ✅ Emit signals (automatically queued to main thread)
- ✅ Access self._is_cancelled (read/write, atomic boolean)

### Unsafe Operations (Never Call from run())
- ❌ Update UI widgets directly (e.g., self.progress_bar.setValue())
- ❌ Call QMessageBox.show() or other blocking dialogs
- ❌ Access MainWindow instance variables directly

### Communication Rule
**Background thread → Main thread**: Use signals only
**Main thread → Background thread**: Use cancel() method or pass data via constructor

---

## Testing Contract

### Required Test Cases

1. **Download Success**: All files downloaded → download_completed emitted with correct counts
2. **Download with Skips**: Existing files → skipped_count > 0
3. **Download with Failures**: Corrupted images → failed_count > 0, other files continue
4. **Download Cancellation**: cancel() called mid-download → stops after current file
5. **Download Fatal Error**: Database disconnect → download_error emitted
6. **Progress Updates**: Verify progress_updated emitted after each file
7. **Log Messages**: Verify log_message format matches specification
8. **Signal Order**: Verify signals emitted in correct sequence

### Mocking Strategy

```python
from unittest.mock import Mock
from pytestqt.qtbot import QtBot
import pytest

def test_download_success(qtbot):
    # Mock dependencies
    mock_client = Mock(spec=CassandraClient)
    mock_client.query_snapshots.return_value = [
        Mock(year=2025, month=1, day=1, eqpid="CAM_001",
             fname="test.png", image=b"fake_png_data")
    ]

    # Create download manager
    manager = DownloadManager(
        cassandra_client=mock_client,
        save_path="/tmp/test",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 1),
        eqpid="CAM_001"
    )

    # Setup signal spies
    with qtbot.waitSignal(manager.download_completed, timeout=5000) as blocker:
        manager.start()

    # Verify signal emitted with correct counts
    success, failed, skipped = blocker.args
    assert success == 1
    assert failed == 0
```

---

## Constitution Compliance Checklist

- ✅ **Principle IV (Responsiveness)**: Runs in QThread background, UI never blocks
- ✅ **Principle III (Error Handling)**: Individual file errors logged, download continues
- ✅ **Principle III (Error Messages)**: Fatal errors include actionable guidance
- ✅ **Database Safety**: Only calls read-only query_snapshots() method
- ✅ **User Control**: Provides cancel() method for graceful termination
