# FileHandler Module Contract

**Component**: `downloader/file_handler.py`
**Purpose**: Filesystem operations for folder creation and image file saving
**Type**: Pure Python utility module (no classes, stateless functions)

---

## Module Overview

FileHandler provides stateless utility functions for managing the download folder structure and converting snapshot ByteArrays to PNG files. All functions are pure (no side effects beyond filesystem I/O) and can be imported and called independently.

---

## Function: create_folder_structure

```python
def create_folder_structure(
    base_path: str,
    year: int,
    month: int,
    day: int,
    eqpid: str
) -> str:
    """
    Create hierarchical folder structure for snapshot organization.

    Folder Structure:
        [base_path]/[year]/[month]/[day]/[eqpid]/

    Args:
        base_path: Root directory for all downloads (must exist)
        year: Four-digit year (e.g., 2025)
        month: Month number (1-12)
        day: Day of month (1-31)
        eqpid: Equipment identifier (sanitized)

    Returns:
        Absolute path to created folder (str)

    Raises:
        PermissionError: If user lacks write permissions to base_path
        OSError: If filesystem error occurs (disk full, invalid path)
        ValueError: If eqpid contains invalid filesystem characters after sanitization

    Side Effects:
        - Creates directory structure if it doesn't exist
        - Uses os.makedirs(exist_ok=True) - safe to call multiple times
        - Zero-pads month and day for consistent sorting (e.g., "01" not "1")

    Example:
        >>> create_folder_structure("/home/user/downloads", 2025, 1, 15, "CAM_001")
        "/home/user/downloads/2025/01/15/CAM_001"

    Implementation Notes:
        - Sanitize eqpid to remove/replace invalid filesystem characters
        - Use os.path.join for cross-platform compatibility
        - Verify base_path exists before attempting folder creation
    """
```

**Example Usage**:
```python
try:
    folder_path = create_folder_structure(
        base_path="/home/user/snapshots",
        year=2025,
        month=11,
        day=11,
        eqpid="CAMERA_01"
    )
    print(f"Folder ready: {folder_path}")
    # Output: "Folder ready: /home/user/snapshots/2025/11/11/CAMERA_01"

except PermissionError:
    print("Error: Cannot write to target directory. Check permissions.")
except OSError as e:
    print(f"Filesystem error: {str(e)}")
```

---

## Function: save_image

```python
def save_image(
    image_bytes: bytes,
    file_path: str
) -> None:
    """
    Convert ByteArray to PNG and save to filesystem.

    Args:
        image_bytes: Binary image data (PNG format expected)
        file_path: Absolute path for output PNG file (including filename)

    Returns:
        None

    Raises:
        ValueError: If image_bytes is None, empty, or invalid image format
        PermissionError: If cannot write to file_path location
        OSError: If disk full or other filesystem error
        PIL.UnidentifiedImageError: If ByteArray is not valid image data

    Side Effects:
        - Creates PNG file at file_path
        - Overwrites existing file if present (use file_exists() first to prevent)

    Performance:
        - Uses BytesIO for in-memory conversion (no temp files)
        - Image data garbage collected immediately after save

    Example:
        >>> image_data = b'\\x89PNG\\r\\n...'  # Valid PNG binary data
        >>> save_image(image_data, "/tmp/snapshot.png")
        # Creates /tmp/snapshot.png

    Implementation Notes:
        - Use PIL/Pillow: Image.open(BytesIO(image_bytes))
        - Explicitly specify format: img.save(file_path, 'PNG')
        - Validate image_bytes is not None/empty before processing
        - Use context manager for automatic resource cleanup
        - Handle Cassandra blob type compatibility: if image_bytes is str (when
          Cassandra driver returns blob as string), convert to bytes using
          latin-1 encoding to preserve binary data integrity
    """
```

**Example Usage**:
```python
from database.models import SnapshotRecord

def process_snapshot(snapshot: SnapshotRecord, save_folder: str):
    file_path = os.path.join(save_folder, sanitize_filename(snapshot.fname))

    # Check if already exists
    if file_exists(file_path):
        print(f"Skipped: {snapshot.fname} (already exists)")
        return

    # Save image
    try:
        save_image(snapshot.image, file_path)
        print(f"Success: {snapshot.fname}")
    except ValueError as e:
        print(f"Failed: {snapshot.fname} - Invalid image data")
    except PermissionError:
        print(f"Failed: {snapshot.fname} - Permission denied")
    except OSError as e:
        print(f"Failed: {snapshot.fname} - {str(e)}")
```

---

## Function: file_exists

```python
def file_exists(file_path: str) -> bool:
    """
    Check if file already exists at specified path.

    Args:
        file_path: Absolute path to file

    Returns:
        True if file exists, False otherwise

    Raises:
        No exceptions raised

    Side Effects:
        - None (read-only filesystem check)

    Example:
        >>> file_exists("/tmp/existing.png")
        True
        >>> file_exists("/tmp/nonexistent.png")
        False

    Implementation Notes:
        - Wrapper around os.path.exists() and os.path.isfile()
        - Returns False for directories (only True for regular files)
    """
```

**Example Usage**:
```python
file_path = "/home/user/snapshots/2025/11/11/CAM_001/snapshot.png"

if file_exists(file_path):
    print("File already downloaded, skipping")
else:
    save_image(image_bytes, file_path)
```

---

## Function: sanitize_filename

```python
def sanitize_filename(fname: str) -> str:
    """
    Remove or replace invalid filesystem characters in filename.

    Invalid Characters:
        - Forward slash (/)
        - Backslash (\\)
        - Colon (:)
        - Asterisk (*)
        - Question mark (?)
        - Double quote (")
        - Less than (<)
        - Greater than (>)
        - Pipe (|)

    Args:
        fname: Original filename from database

    Returns:
        Sanitized filename safe for all filesystems (Windows, Linux, macOS)

    Raises:
        ValueError: If fname is empty after sanitization

    Side Effects:
        - None (pure string transformation)

    Example:
        >>> sanitize_filename('snapshot:12345*.png')
        'snapshot_12345_.png'

        >>> sanitize_filename('file<name>.png')
        'file_name_.png'

    Implementation Notes:
        - Replace invalid characters with underscore (_)
        - Preserve file extension (.png)
        - Ensure .png extension exists (append if missing)
        - Reject empty filenames after sanitization
    """
```

**Example Usage**:
```python
# Database filename may contain epoch time with special chars
db_filename = "1705334400:x100?y200.png"
safe_filename = sanitize_filename(db_filename)
# Result: "1705334400_x100_y200.png"

file_path = os.path.join(folder, safe_filename)
save_image(image_bytes, file_path)
```

---

## Function: get_folder_size

```python
def get_folder_size(folder_path: str) -> int:
    """
    Calculate total size of all files in folder (recursive).

    Args:
        folder_path: Path to folder to measure

    Returns:
        Total size in bytes (int)

    Raises:
        OSError: If folder does not exist or is not accessible

    Side Effects:
        - None (read-only filesystem traversal)

    Use Case:
        - Display total download size to user
        - Warn if insufficient disk space

    Example:
        >>> size_bytes = get_folder_size("/home/user/snapshots")
        >>> size_mb = size_bytes / (1024 * 1024)
        >>> print(f"Downloaded: {size_mb:.2f} MB")
        "Downloaded: 1234.56 MB"

    Implementation Notes:
        - Use os.walk() to traverse directory tree
        - Sum os.path.getsize() for all files
        - Skip symbolic links to avoid loops
    """
```

---

## Function: ensure_directory_writable

```python
def ensure_directory_writable(directory_path: str) -> tuple[bool, str]:
    """
    Verify directory exists and is writable.

    Args:
        directory_path: Path to verify

    Returns:
        Tuple of (is_writable: bool, message: str)
        - (True, "Directory is writable") on success
        - (False, "Error: {reason}") on failure

    Raises:
        No exceptions raised - errors returned as (False, message)

    Side Effects:
        - May create test file to verify write permissions (then deletes it)

    Error Messages:
        - Directory does not exist: "Error: Directory does not exist"
        - Not a directory: "Error: Path is not a directory"
        - No write permission: "Error: Permission denied - cannot write to directory"
        - Disk full: "Error: Insufficient disk space"

    Example:
        >>> is_writable, message = ensure_directory_writable("/home/user/downloads")
        >>> if not is_writable:
        ...     QMessageBox.warning(self, "Invalid Path", message)

    Implementation Notes:
        - Check os.path.exists(directory_path)
        - Check os.path.isdir(directory_path)
        - Attempt to create and delete temporary file to verify write access
        - Use tempfile module for safe test file creation
    """
```

**Example Usage**:
```python
# In MainWindow when user selects save path
save_path = QFileDialog.getExistingDirectory(self, "Select Save Folder")

is_writable, message = ensure_directory_writable(save_path)
if not is_writable:
    QMessageBox.warning(self, "Invalid Directory", message)
    return

self.save_path_edit.setText(save_path)
self.download_button.setEnabled(True)
```

---

## Error Handling Patterns

All file_handler functions follow consistent error handling:

### Pattern 1: Raise Exceptions (for save_image, create_folder_structure)
```python
try:
    create_folder_structure(base_path, year, month, day, eqpid)
    save_image(image_bytes, file_path)
    return "success"
except ValueError as e:
    return f"failed: Invalid data - {str(e)}"
except PermissionError:
    return "failed: Permission denied"
except OSError as e:
    if "No space left" in str(e):
        return "failed: Disk full"
    else:
        return f"failed: Filesystem error - {str(e)}"
```

### Pattern 2: Return Tuple (for ensure_directory_writable)
```python
is_valid, message = ensure_directory_writable(path)
if not is_valid:
    QMessageBox.critical(self, "Error", message)
    return
```

---

## Testing Contract

### Required Test Cases

1. **create_folder_structure - Success**: Creates nested folders with correct names
2. **create_folder_structure - Existing Folders**: Succeeds when folders already exist
3. **create_folder_structure - Permission Denied**: Raises PermissionError
4. **create_folder_structure - Invalid eqpid**: Sanitizes special characters
5. **save_image - Valid PNG**: Creates PNG file successfully
6. **save_image - Invalid Data**: Raises ValueError for corrupted bytes
7. **save_image - Empty Bytes**: Raises ValueError
8. **save_image - None Bytes**: Raises ValueError
9. **file_exists - File Exists**: Returns True for existing file
10. **file_exists - File Missing**: Returns False for non-existent file
11. **file_exists - Directory**: Returns False for directory path
12. **sanitize_filename - Special Characters**: Replaces invalid chars with underscores
13. **sanitize_filename - Missing Extension**: Appends .png
14. **ensure_directory_writable - Valid Directory**: Returns (True, success message)
15. **ensure_directory_writable - Non-existent**: Returns (False, error message)
16. **ensure_directory_writable - No Permission**: Returns (False, permission error)

### Mocking Strategy

```python
import pytest
from unittest.mock import patch, mock_open
import os

def test_create_folder_structure_success(tmp_path):
    """Test folder creation with real filesystem (pytest tmp_path fixture)."""
    folder = create_folder_structure(
        base_path=str(tmp_path),
        year=2025,
        month=11,
        day=11,
        eqpid="CAM_001"
    )

    expected = os.path.join(str(tmp_path), "2025", "11", "11", "CAM_001")
    assert folder == expected
    assert os.path.exists(folder)
    assert os.path.isdir(folder)

@patch('PIL.Image.open')
def test_save_image_invalid_data(mock_image_open):
    """Test save_image with corrupted image data."""
    from PIL import UnidentifiedImageError

    mock_image_open.side_effect = UnidentifiedImageError("Cannot identify image file")

    with pytest.raises(ValueError, match="Invalid image data"):
        save_image(b"corrupted_data", "/tmp/test.png")
```

---

## Cross-Platform Compatibility

All file_handler functions MUST work correctly on:
- ✅ Linux (primary development/deployment target)
- ✅ Windows (path separators, drive letters, reserved names)
- ✅ macOS (case sensitivity, path conventions)

**Best Practices**:
- Use `os.path.join()` for path construction (not string concatenation)
- Use `os.sep` for platform-specific separators when needed
- Sanitize filenames to avoid Windows reserved names (CON, PRN, AUX, etc.)
- Handle both forward and backslash in input paths

---

## Performance Considerations

### Memory Efficiency
```python
# ✓ Good: Process one image at a time
for snapshot in snapshots:
    save_image(snapshot.image, file_path)
    # snapshot.image garbage collected after save

# ✗ Bad: Load all images into memory
images = [(snap.fname, snap.image) for snap in snapshots]  # Memory explosion
for fname, image in images:
    save_image(image, file_path)
```

### Disk I/O Optimization
```python
# Check existence before expensive operations
if not file_exists(file_path):
    folder = create_folder_structure(base_path, year, month, day, eqpid)
    save_image(image_bytes, file_path)
else:
    # Skip early, avoid folder creation overhead
    return "skipped"
```

---

## Constitution Compliance Checklist

- ✅ **Principle II (Validation)**: sanitize_filename() removes unsafe characters
- ✅ **Principle II (Validation)**: ensure_directory_writable() pre-validates paths
- ✅ **Principle III (Error Handling)**: All functions provide clear error messages
- ✅ **Simplicity**: Stateless functions, no complex dependencies
- ✅ **Security**: Filename sanitization prevents path traversal attacks
