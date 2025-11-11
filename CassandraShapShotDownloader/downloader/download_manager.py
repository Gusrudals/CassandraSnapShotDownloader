"""Download manager for background snapshot downloading."""

import os
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from PyQt5.QtCore import QThread, pyqtSignal
from database.cassandra_client import CassandraClient
from downloader.file_handler import (
    create_folder_structure, file_exists, save_image, sanitize_filename
)
from utils.logger import FileOperationLogEntry, FileOperationStatus


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


class DownloadManager(QThread):
    """Background thread for downloading and organizing snapshot files."""

    # Define signals
    progress_updated = pyqtSignal(int, int, str)  # current, total, status
    log_message = pyqtSignal(str)
    download_completed = pyqtSignal(int, int, int)  # success, failed, skipped
    download_error = pyqtSignal(str)

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
            cassandra_client: Connected CassandraClient instance
            save_path: Root directory for downloaded files
            start_date: Beginning of date range
            end_date: End of date range
            eqpid: Equipment ID filter
        """
        super().__init__()
        self.cassandra_client = cassandra_client
        self.save_path = save_path
        self.start_date = start_date
        self.end_date = end_date
        self.eqpid = eqpid
        self._is_cancelled = False

    def run(self) -> None:
        """Execute download in background thread."""
        success_count = 0
        failed_count = 0
        skipped_count = 0

        try:
            # Query all snapshots
            self.log_message.emit(
                f"[{datetime.now().strftime('%H:%M:%S')}] Starting download for {self.eqpid} "
                f"from {self.start_date} to {self.end_date}..."
            )

            snapshots = self.cassandra_client.query_snapshots(
                self.start_date,
                self.end_date,
                self.eqpid,
                limit=None
            )

            total = len(snapshots)
            self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Found {total} snapshots to download")

            # Process each snapshot
            for idx, snapshot in enumerate(snapshots):
                # Check for cancellation
                if self._is_cancelled:
                    self.log_message.emit(
                        f"[{datetime.now().strftime('%H:%M:%S')}] Download cancelled after {idx} files"
                    )
                    break

                # Process file
                status = self._process_snapshot(snapshot)

                if status == "success":
                    success_count += 1
                elif status == "failed":
                    failed_count += 1
                else:
                    skipped_count += 1

                # Emit progress
                self.progress_updated.emit(idx + 1, total, status)

            # Emit completion
            self.log_message.emit(
                f"[{datetime.now().strftime('%H:%M:%S')}] Download complete: "
                f"{success_count} succeeded, {failed_count} failed, {skipped_count} skipped"
            )
            self.download_completed.emit(success_count, failed_count, skipped_count)

        except Exception as e:
            error_msg = f"Download failed: {str(e)}. Check your connection and try again."
            self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {error_msg}")
            self.download_error.emit(error_msg)

    def _process_snapshot(self, snapshot) -> str:
        """
        Process a single snapshot file.

        Returns:
            "success", "failed", or "skipped"
        """
        try:
            # Create folder structure
            folder_path = create_folder_structure(
                self.save_path,
                snapshot.year,
                snapshot.month,
                snapshot.day,
                snapshot.eqpid
            )

            # Sanitize filename
            safe_filename = sanitize_filename(snapshot.fname)
            file_path = os.path.join(folder_path, safe_filename)

            # Check if already exists
            if file_exists(file_path):
                self.log_message.emit(
                    f"[{datetime.now().strftime('%H:%M:%S')}] SKIPPED: {safe_filename} (already exists)"
                )
                return "skipped"

            # Save image
            save_image(snapshot.image, file_path)
            self.log_message.emit(
                f"[{datetime.now().strftime('%H:%M:%S')}] SUCCESS: {safe_filename}"
            )
            return "success"

        except ValueError as e:
            # Invalid data
            self.log_message.emit(
                f"[{datetime.now().strftime('%H:%M:%S')}] FAILED: {snapshot.fname} - {str(e)}"
            )
            return "failed"
        except PermissionError:
            self.log_message.emit(
                f"[{datetime.now().strftime('%H:%M:%S')}] FAILED: {snapshot.fname} - Permission denied"
            )
            return "failed"
        except OSError as e:
            if "No space left" in str(e):
                # Disk full - this is fatal
                raise OSError("Insufficient disk space. Free up space and try again.")
            else:
                self.log_message.emit(
                    f"[{datetime.now().strftime('%H:%M:%S')}] FAILED: {snapshot.fname} - {str(e)}"
                )
                return "failed"
        except Exception as e:
            self.log_message.emit(
                f"[{datetime.now().strftime('%H:%M:%S')}] FAILED: {snapshot.fname} - {str(e)}"
            )
            return "failed"

    def cancel(self) -> None:
        """Request cancellation of download (graceful stop after current file)."""
        self._is_cancelled = True
