# CassandraClient Interface Contract

**Component**: `database/cassandra_client.py`
**Purpose**: Manage Cassandra database connections and query execution
**Type**: Internal Python API

---

## Class: CassandraClient

### Responsibilities
- Establish and manage connection to Cassandra cluster
- Execute read-only queries (SELECT only per constitution)
- Handle connection lifecycle (connect, test, disconnect)
- Apply timeouts and error handling

### Constructor

```python
def __init__(self):
    """
    Initialize CassandraClient with no active connection.

    Postconditions:
        - self.cluster is None
        - self.session is None
        - self.is_connected is False
    """
```

---

### Method: connect

```python
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

    Raises:
        No exceptions raised - all errors returned as (False, message)

    Side Effects:
        - Sets self.cluster to Cluster instance
        - Sets self.session to connected Session instance
        - Sets self.is_connected to True on success

    Timeouts:
        - Connection timeout: 5 seconds (per config/settings.py)

    Error Handling:
        Returns (False, message) for:
        - cassandra.NoHostAvailable: "Cannot reach database server..."
        - cassandra.Unauthorized: "Invalid username or password..."
        - cassandra.InvalidRequest (Unknown keyspace): "Keyspace '{keyspace}' does not exist..."
        - Other exceptions: "Unexpected error ({exception_type})..."

    Constitution Compliance:
        - Uses PlainTextAuthProvider for username/password authentication
        - Read-only connection (no write permissions enforced at user level)
    """
```

**Example Usage**:
```python
client = CassandraClient()
success, message = client.connect(
    host="192.168.1.100",
    port=9042,
    username="readonly_user",
    password="secure_password",
    keyspace="production_data"
)

if success:
    print(f"✓ {message}")
else:
    print(f"✗ {message}")
```

---

### Method: test_connection

```python
def test_connection(self) -> tuple[bool, str]:
    """
    Verify database connection is active and responsive.

    Preconditions:
        - connect() must have been called successfully

    Returns:
        Tuple of (success: bool, message: str)
        - On success: (True, "Connection test passed")
        - On failure: (False, "Connection test failed: {reason}")

    Raises:
        No exceptions raised - all errors returned as (False, message)

    Side Effects:
        - Executes lightweight query: SELECT count(*) FROM snapshot LIMIT 1

    Timeouts:
        - Query timeout: 5 seconds (per config/settings.py)

    Error Handling:
        Returns (False, message) for:
        - Not connected: "No active connection - call connect() first"
        - cassandra.OperationTimedOut: "Connection test timed out..."
        - Other exceptions: "Connection test failed: {exception message}"
    """
```

**Example Usage**:
```python
success, message = client.test_connection()
if success:
    # Enable search functionality in UI
    search_button.setEnabled(True)
else:
    QMessageBox.warning(self, "Connection Test Failed", message)
```

---

### Method: query_snapshots

```python
def query_snapshots(
    self,
    start_date: date,
    end_date: date,
    eqpid: str,
    limit: int | None = None
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
        cassandra.OperationTimedOut: If query exceeds 10 second timeout

    Side Effects:
        - Executes one or more SELECT queries to Cassandra
        - May iterate through multiple year-month combinations

    Timeouts:
        - Query timeout: 10 seconds per month query (per config/settings.py)

    Performance:
        - Iterates queries by month to avoid ALLOW FILTERING
        - Fetches ALL matching records, then applies limit if specified
        - Memory-efficient: Returns iterator that can be consumed row-by-row

    Query Pattern:
        For each year-month in [start_date, end_date]:
            SELECT year, month, day, eqpid, fname, image
            FROM snapshot
            WHERE year = ? AND month = ? AND day >= ? AND day <= ? AND eqpid = ?

    Constitution Compliance:
        - Read-only query (SELECT only)
        - Uses parameterized queries (cassandra-driver PreparedStatement)
        - Filters on partition keys only (year, month, day, eqpid)
    """
```

**Example Usage**:
```python
from datetime import date

# Query all snapshots for CAM_001 in January 2025
snapshots = client.query_snapshots(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 31),
    eqpid="CAM_001"
)

print(f"Found {len(snapshots)} snapshots")

# Query limited results for preview
preview_snapshots = client.query_snapshots(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 31),
    eqpid="CAM_001",
    limit=20
)
```

---

### Method: count_snapshots

```python
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
        cassandra.OperationTimedOut: If query exceeds 10 second timeout

    Side Effects:
        - Executes COUNT query for each year-month combination

    Performance:
        - More efficient than fetching all records when only count is needed
        - Still requires iteration through month boundaries

    Query Pattern:
        For each year-month in [start_date, end_date]:
            SELECT COUNT(*) FROM snapshot
            WHERE year = ? AND month = ? AND day >= ? AND day <= ? AND eqpid = ?
    """
```

**Example Usage**:
```python
total = client.count_snapshots(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 31),
    eqpid="CAM_001"
)

if total > 1000:
    # Warn user about large download
    QMessageBox.warning(
        self,
        "Large Dataset",
        f"This will download {total} files. Continue?"
    )
```

---

### Method: disconnect

```python
def disconnect(self) -> None:
    """
    Close connection to Cassandra cluster and release resources.

    Preconditions:
        - None (safe to call even if not connected)

    Returns:
        None

    Raises:
        No exceptions raised - errors are logged but not propagated

    Side Effects:
        - Calls session.shutdown() if session exists
        - Calls cluster.shutdown() if cluster exists
        - Sets self.session to None
        - Sets self.cluster to None
        - Sets self.is_connected to False

    Cleanup:
        - Should be called when application closes
        - Safe to call multiple times
    """
```

**Example Usage**:
```python
# In MainWindow.closeEvent
def closeEvent(self, event):
    if self.cassandra_client.is_connected:
        self.cassandra_client.disconnect()
    event.accept()
```

---

### Property: is_connected

```python
@property
def is_connected(self) -> bool:
    """
    Check if client has active database connection.

    Returns:
        True if session is active, False otherwise
    """
```

---

## Error Message Contracts

All error messages returned by CassandraClient MUST follow the pattern:
```
"[What failed]: [Why it failed]. [What user should do]"
```

### Error Message Examples

| Exception | Error Message |
|-----------|---------------|
| `NoHostAvailable` | "Connection failed: Cannot reach database server. Check that the host address and port are correct, and that your network allows connections to the database." |
| `Unauthorized` | "Connection failed: Invalid username or password. Verify your credentials and try again." |
| `InvalidRequest` (Unknown keyspace) | "Connection failed: Keyspace '{keyspace}' does not exist. Check the keyspace name and try again." |
| `OperationTimedOut` (connection) | "Connection test timed out after 5 seconds. Check your network connection and ensure the database server is responsive." |
| `OperationTimedOut` (query) | "Query timed out after 10 seconds. Try narrowing your date range or check database performance." |
| Not connected | "No active connection. Click 'Test Connection' to establish database connection first." |
| Invalid date range | "Invalid date range: End date must be after start date." |
| Empty eqpid | "Equipment ID cannot be empty. Please enter a valid equipment identifier." |

---

## Thread Safety

**CassandraClient is NOT thread-safe**. Design constraints:

- ✅ Create ONE CassandraClient instance per application (stored in MainWindow)
- ✅ Call `query_snapshots()` from background thread (DownloadManager)
- ✅ DO NOT call `connect()` or `disconnect()` from background thread
- ✅ cassandra-driver Session is thread-safe for reads (query execution)

**Safe Pattern**:
```python
# In MainWindow (main thread)
self.cassandra_client = CassandraClient()
self.cassandra_client.connect(...)

# Pass client to background thread
self.download_thread = DownloadManager(
    cassandra_client=self.cassandra_client,  # Pass reference, don't call methods
    ...
)

# In DownloadManager.run() (background thread)
snapshots = self.cassandra_client.query_snapshots(...)  # ✓ Safe (read-only)
```

---

## Testing Contract

### Required Test Cases

1. **Connection Success**: Valid credentials → (True, success message)
2. **Connection Failure - Invalid Host**: Wrong host → (False, "Cannot reach database server...")
3. **Connection Failure - Invalid Credentials**: Wrong password → (False, "Invalid username or password...")
4. **Connection Failure - Invalid Keyspace**: Wrong keyspace → (False, "Keyspace '...' does not exist...")
5. **Test Connection Success**: Connected client → (True, "Connection test passed")
6. **Test Connection Failure - Not Connected**: No connection → (False, "No active connection...")
7. **Query Success**: Valid date range + eqpid → List of SnapshotRecords
8. **Query Empty Results**: No matching data → Empty list
9. **Query Timeout**: Simulated timeout → OperationTimedOut exception
10. **Query Invalid Input**: Empty eqpid → ValueError
11. **Disconnect**: Verify session.shutdown() and cluster.shutdown() called

### Mocking Strategy

```python
from unittest.mock import Mock, patch
import pytest

@pytest.fixture
def mock_cassandra_cluster():
    with patch('cassandra.cluster.Cluster') as mock_cluster:
        mock_session = Mock()
        mock_cluster.return_value.connect.return_value = mock_session
        yield mock_cluster, mock_session

def test_connect_success(mock_cassandra_cluster):
    mock_cluster, mock_session = mock_cassandra_cluster
    client = CassandraClient()

    success, message = client.connect("localhost", 9042, "user", "pass", "keyspace")

    assert success is True
    assert "Connected to" in message
    mock_cluster.assert_called_once()
```

---

## Constitution Compliance Checklist

- ✅ **Principle I (Read-Only)**: Only SELECT queries, no DDL/DML
- ✅ **Principle II (Validation)**: Validates eqpid, date range before queries
- ✅ **Principle III (Error Handling)**: All errors caught, actionable messages returned
- ✅ **Principle IV (Responsiveness)**: Query methods can be called from background thread
- ✅ **Principle V (Security)**: Password never logged in error messages
- ✅ **Database Safety Rules**: Parameterized queries, partition key filtering, enforced timeouts
