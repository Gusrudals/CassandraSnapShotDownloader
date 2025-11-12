"""Filesystem operations for folder creation and image file saving."""

import os
import re
import tempfile
from PIL import Image
from io import BytesIO


def sanitize_filename(fname: str) -> str:
    """
    Remove or replace invalid filesystem characters in filename.

    Invalid Characters: / \ : * ? " < > |

    Args:
        fname: Original filename from database

    Returns:
        Sanitized filename safe for all filesystems

    Raises:
        ValueError: If fname is empty after sanitization
    """
    # Replace invalid characters with underscore
    sanitized = re.sub(r'[/\\:*?"<>|]', '_', fname)

    # Ensure .png extension
    if not sanitized.lower().endswith('.png'):
        sanitized += '.png'

    if not sanitized or sanitized == '.png':
        raise ValueError("Filename is empty after sanitization")

    return sanitized


def create_folder_structure(
    base_path: str,
    year: int,
    month: int,
    day: int,
    eqpid: str
) -> str:
    """
    Create hierarchical folder structure for snapshot organization.

    Folder Structure: [base_path]/[year]/[month]/[day]/[eqpid]/

    Args:
        base_path: Root directory for all downloads (must exist)
        year: Four-digit year
        month: Month number (1-12)
        day: Day of month (1-31)
        eqpid: Equipment identifier

    Returns:
        Absolute path to created folder

    Raises:
        PermissionError: If user lacks write permissions
        OSError: If filesystem error occurs
        ValueError: If eqpid contains invalid characters after sanitization
    """
    # Sanitize equipment ID
    safe_eqpid = re.sub(r'[/\\:*?"<>|]', '_', eqpid)
    if not safe_eqpid:
        raise ValueError("Equipment ID is invalid")

    # Build path with zero-padded month and day
    folder_path = os.path.join(
        base_path,
        str(year),
        f"{month:02d}",
        f"{day:02d}",
        safe_eqpid
    )

    # Create folders (exist_ok=True means safe to call multiple times)
    os.makedirs(folder_path, exist_ok=True)

    return folder_path


def file_exists(file_path: str) -> bool:
    """
    Check if file already exists at specified path.

    Args:
        file_path: Absolute path to file

    Returns:
        True if file exists, False otherwise
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)


def save_image(image_bytes: bytes, file_path: str) -> None:
    """
    Convert ByteArray to PNG and save to filesystem.

    Args:
        image_bytes: Binary image data (PNG format expected)
        file_path: Absolute path for output PNG file

    Raises:
        ValueError: If image_bytes is invalid
        PermissionError: If cannot write to file_path
        OSError: If disk full or other filesystem error
    """
    if not image_bytes:
        raise ValueError("Image data is empty")

    # Handle case where Cassandra returns blob as str instead of bytes
    if isinstance(image_bytes, str):
        image_bytes = image_bytes.encode('latin-1')

    try:
        with Image.open(BytesIO(image_bytes)) as img:
            img.save(file_path, 'PNG')
    except Exception as e:
        # Re-raise with more specific error message
        if "cannot identify image file" in str(e).lower():
            raise ValueError("Invalid image data - cannot identify format")
        else:
            raise


def ensure_directory_writable(directory_path: str) -> tuple[bool, str]:
    """
    Verify directory exists and is writable.

    Args:
        directory_path: Path to verify

    Returns:
        Tuple of (is_writable: bool, message: str)
    """
    if not os.path.exists(directory_path):
        return (False, "Error: Directory does not exist")

    if not os.path.isdir(directory_path):
        return (False, "Error: Path is not a directory")

    # Try to create a temporary file to verify write access
    try:
        with tempfile.NamedTemporaryFile(dir=directory_path, delete=True):
            pass
        return (True, "Directory is writable")
    except PermissionError:
        return (False, "Error: Permission denied - cannot write to directory")
    except OSError as e:
        if "No space left" in str(e) or "Disk quota exceeded" in str(e):
            return (False, "Error: Insufficient disk space")
        return (False, f"Error: {str(e)}")
