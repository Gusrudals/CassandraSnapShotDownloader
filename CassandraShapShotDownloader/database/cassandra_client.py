"""Cassandra database client for snapshot operations."""

from datetime import date, timedelta
from typing import Optional
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import cassandra.cluster
import cassandra
from config.settings import CONNECTION_TIMEOUT, QUERY_TIMEOUT
from database.models import SnapshotRecord


class CassandraClient:
    """Manage Cassandra database connections and query execution."""

    def __init__(self):
        """
        Initialize CassandraClient with no active connection.

        Postconditions:
            - self.cluster is None
            - self.session is None
            - self._is_connected is False
        """
        self.cluster: Optional[Cluster] = None
        self.session = None
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Check if client has active database connection."""
        return self._is_connected and self.session is not None

    def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        keyspace: str
    ) -> tuple[bool, str]:
        """
        Establish connection to Cassandra cluster and keyspace.

        Args:
            host: Cassandra cluster hostname or IP address
            port: Native transport port (typically 9042)
            username: Authentication username
            password: Authentication password
            keyspace: Target keyspace containing snapshot table

        Returns:
            Tuple of (success: bool, message: str)
            - On success: (True, "Connected to {host}:{port}/{keyspace}")
            - On failure: (False, "Connection failed: {detailed error message}")
        """
        try:
            # Setup authentication
            auth_provider = PlainTextAuthProvider(username=username, password=password)

            # Create cluster connection
            self.cluster = Cluster(
                [host],
                port=port,
                auth_provider=auth_provider,
                connect_timeout=CONNECTION_TIMEOUT
            )

            # Connect to keyspace
            self.session = self.cluster.connect(keyspace)
            self.session.default_timeout = QUERY_TIMEOUT

            self._is_connected = True
            return (True, f"Connected to {host}:{port}/{keyspace}")

        except cassandra.cluster.NoHostAvailable:
            return (
                False,
                "Connection failed: Cannot reach database server. "
                "Check that the host address and port are correct, "
                "and that your network allows connections to the database."
            )
        except cassandra.Unauthorized:
            return (
                False,
                "Connection failed: Invalid username or password. "
                "Verify your credentials and try again."
            )
        except cassandra.InvalidRequest as e:
            if "Unknown keyspace" in str(e):
                return (
                    False,
                    f"Connection failed: Keyspace '{keyspace}' does not exist. "
                    "Check the keyspace name and try again."
                )
            else:
                return (False, f"Connection failed: {str(e)}")
        except Exception as e:
            return (
                False,
                f"Connection failed: Unexpected error ({type(e).__name__}). "
                "Contact support if this persists."
            )

    def test_connection(self) -> tuple[bool, str]:
        """
        Verify database connection is active and responsive.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_connected:
            return (False, "No active connection - call connect() first")

        try:
            # Execute lightweight query on system table (Cassandra 3.11.6 compatible)
            self.session.execute("SELECT cluster_name FROM system.local", timeout=CONNECTION_TIMEOUT)
            return (True, "Connection test passed")
        except cassandra.OperationTimedOut:
            return (
                False,
                "Connection test timed out after 5 seconds. "
                "Check your network connection and ensure the database server is responsive."
            )
        except Exception as e:
            return (False, f"Connection test failed: {str(e)}")

    def disconnect(self) -> None:
        """Close connection to Cassandra cluster and release resources."""
        try:
            if self.session:
                self.session.shutdown()
                self.session = None
            if self.cluster:
                self.cluster.shutdown()
                self.cluster = None
            self._is_connected = False
        except Exception:
            # Errors during shutdown are logged but not propagated
            pass

    def query_snapshots(
        self,
        start_date: date,
        end_date: date,
        eqpid: str,
        limit: Optional[int] = None
    ) -> list[SnapshotRecord]:
        """
        Query snapshots within date range for specific equipment.

        Args:
            start_date: Beginning of date range (inclusive)
            end_date: End of date range (inclusive)
            eqpid: Equipment ID filter (exact match)
            limit: Maximum number of records to return (None = all)

        Returns:
            List of SnapshotRecord objects (empty list if no matches)

        Raises:
            ValueError: If eqpid is empty or date range is invalid
            RuntimeError: If not connected to database
            cassandra.OperationTimedOut: If query exceeds timeout
        """
        if not self.is_connected:
            raise RuntimeError("No active connection - call connect() first")

        if not eqpid or not eqpid.strip():
            raise ValueError("Equipment ID cannot be empty")

        if start_date > end_date:
            raise ValueError("Start date must be before or equal to end date")

        results = []

        # Query each day individually (required due to partition key structure)
        # Partition key: (eqpid, year, month, day) - all must be exact matches
        query = """
        SELECT year, month, day, eqpid, fname, image
        FROM snapshot
        WHERE eqpid = %s AND year = %s AND month = %s AND day = %s
        """

        current_date = start_date
        while current_date <= end_date:
            try:
                rows = self.session.execute(
                    query,
                    (eqpid, current_date.year, current_date.month, current_date.day)
                )

                for row in rows:
                    snapshot = SnapshotRecord(
                        year=row.year,
                        month=row.month,
                        day=row.day,
                        eqpid=row.eqpid,
                        fname=row.fname,
                        image=row.image
                    )
                    results.append(snapshot)

                    # Apply limit if specified
                    if limit and len(results) >= limit:
                        return results

            except cassandra.OperationTimedOut:
                raise cassandra.OperationTimedOut(
                    f"Query timed out after {QUERY_TIMEOUT} seconds. "
                    "Try narrowing your date range or check database performance."
                )

            # Move to next day
            current_date = current_date + timedelta(days=1)

        return results

    def count_snapshots(
        self,
        start_date: date,
        end_date: date,
        eqpid: str
    ) -> int:
        """
        Count total snapshots matching criteria without retrieving data.

        Args:
            start_date: Beginning of date range (inclusive)
            end_date: End of date range (inclusive)
            eqpid: Equipment ID filter (exact match)

        Returns:
            Total count of matching snapshots (0 if no matches)

        Raises:
            ValueError: If eqpid is empty or date range is invalid
            RuntimeError: If not connected to database
            cassandra.OperationTimedOut: If query exceeds timeout
        """
        if not self.is_connected:
            raise RuntimeError("No active connection - call connect() first")

        if not eqpid or not eqpid.strip():
            raise ValueError("Equipment ID cannot be empty")

        if start_date > end_date:
            raise ValueError("Start date must be before or equal to end date")

        total_count = 0

        # Query each day individually (required due to partition key structure)
        # Partition key: (eqpid, year, month, day) - all must be exact matches
        query = """
        SELECT COUNT(*) FROM snapshot
        WHERE eqpid = %s AND year = %s AND month = %s AND day = %s
        """

        current_date = start_date
        while current_date <= end_date:
            try:
                rows = self.session.execute(
                    query,
                    (eqpid, current_date.year, current_date.month, current_date.day)
                )
                total_count += rows[0].count

            except cassandra.OperationTimedOut:
                raise cassandra.OperationTimedOut(
                    f"Query timed out after {QUERY_TIMEOUT} seconds. "
                    "Try narrowing your date range or check database performance."
                )

            # Move to next day
            current_date = current_date + timedelta(days=1)

        return total_count
