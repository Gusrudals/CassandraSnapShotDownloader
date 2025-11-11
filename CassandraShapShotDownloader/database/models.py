"""Data models for Cassandra snapshot downloader."""

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
