"""Logging configuration and utilities."""

import logging
from datetime import datetime
from dataclasses import dataclass, field
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


def setup_logger():
    """Configure application logging."""
    logger = logging.getLogger('cassandra_downloader')
    logger.setLevel(logging.DEBUG)

    # File handler (detailed logs)
    log_file = f"cassandra_downloader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
