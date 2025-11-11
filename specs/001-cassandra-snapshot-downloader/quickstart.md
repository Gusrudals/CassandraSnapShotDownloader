# Quickstart Guide: Cassandra Snapshot Downloader

**Feature**: Cassandra Snapshot Downloader
**Date**: 2025-11-11
**Target Audience**: Developers setting up the development environment

---

## Prerequisites

### System Requirements
- **Operating System**: Linux, Windows 10+, or macOS 10.15+
- **Python**: Version 3.11 or higher
- **RAM**: Minimum 2GB available
- **Disk Space**: 500MB for dependencies + space for downloaded snapshots
- **Network**: Access to Cassandra cluster on configured port (default 9042)

### Required Software
1. **Python 3.11+**: Install from python.org or your system package manager
2. **pip**: Python package installer (included with Python 3.11+)
3. **virtualenv** (recommended): `pip install virtualenv`
4. **Git**: For cloning repository

### Database Access
- Cassandra cluster hostname/IP and port
- Valid username and password with SELECT permissions
- Keyspace name containing `snapshot` table
- Network access to Cassandra cluster

---

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd cassandra-snapshot-downloader
```

### 2. Create Virtual Environment

**Linux/macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**:
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected Output**:
```
Successfully installed:
  - PyQt5-5.15.x
  - cassandra-driver-3.28.x
  - Pillow-10.x.x
  - pytest-7.4.x (dev)
  - pytest-qt-4.2.x (dev)
```

### 4. Verify Installation

```bash
python -c "import PyQt5.QtWidgets; import cassandra; import PIL; print('All dependencies installed successfully')"
```

**Expected Output**: `All dependencies installed successfully`

---

## Configuration

### Database Connection Settings

The application does not use configuration files (credentials are memory-only per constitution). Connection parameters are entered through the UI at runtime.

**Prepare the following information**:
- **Host**: Cassandra cluster IP or hostname (e.g., `192.168.1.100` or `cassandra.example.com`)
- **Port**: Native transport port (default: `9042`)
- **Username**: Database user with SELECT permissions
- **Password**: User password (will be masked in UI)
- **Keyspace**: Keyspace containing the `snapshot` table

### Application Settings (Optional)

To customize timeouts or display limits, edit `config/settings.py`:

```python
# Database timeouts (seconds)
CONNECTION_TIMEOUT = 5.0
QUERY_TIMEOUT = 10.0

# UI display limits
TABLE_DISPLAY_LIMIT = 20

# Date range limits
MAX_DATE_RANGE_DAYS = 365
```

---

## Running the Application

### Launch Application

```bash
python main.py
```

**Expected Behavior**:
- Main window opens with connection settings form
- All controls initially disabled except connection fields and "Test Connection" button

### First-Time Setup Workflow

1. **Enter Database Credentials**:
   - Host: `192.168.1.100`
   - Port: `9042`
   - Username: `readonly_user`
   - Password: `********` (masked)
   - Keyspace: `production_snapshots`

2. **Test Connection**:
   - Click "Test Connection" button
   - Wait for response (max 5 seconds)
   - **Success**: Connection status shows "Connected" in green, search controls enabled
   - **Failure**: Error message displayed with resolution guidance

3. **Search for Snapshots**:
   - Select start date (e.g., `2025-01-01`)
   - Select end date (e.g., `2025-01-31`)
   - Enter equipment ID (e.g., `CAM_001`)
   - Click "Search"
   - Wait for results (max 10 seconds)

4. **Review Results**:
   - Results table displays up to 20 snapshots
   - Total count shown: "Total: 1,234 records (showing first 20)"
   - Click column headers to sort

5. **Download Snapshots**:
   - Click "Select Save Path" button
   - Choose download folder (e.g., `/home/user/Downloads/snapshots`)
   - Click "Download All" button
   - Monitor progress bar and log messages
   - Wait for completion dialog

6. **Verify Download**:
   ```bash
   ls -R /home/user/Downloads/snapshots
   ```

   **Expected Structure**:
   ```
   snapshots/
   └── 2025/
       └── 01/
           ├── 01/
           │   └── CAM_001/
           │       ├── snapshot_001.png
           │       └── snapshot_002.png
           └── 02/
               └── CAM_001/
                   └── snapshot_003.png
   ```

---

## Quick Reference

### Common Tasks

#### Change Database Connection
1. Click "Disconnect" (if connected)
2. Update connection fields
3. Click "Test Connection"

#### Export Large Dataset
1. Search with specific date range
2. Note total count (e.g., "Total: 10,000 records")
3. Ensure sufficient disk space (estimate: 10,000 × ~50KB = ~500MB)
4. Click "Download All"
5. Monitor progress (may take 10-30 minutes for 10,000 files)

#### Cancel Running Download
1. Click "Cancel Download" button
2. Wait for current file to complete
3. Check log for "Download cancelled after N files"
4. Already-downloaded files remain on disk

#### Resume Interrupted Download
1. Re-run same search query
2. Select same save path
3. Click "Download All"
4. Application automatically skips existing files (logged as "SKIPPED")

---

## Troubleshooting

### Connection Issues

**Problem**: "Connection failed: Cannot reach database server"

**Solutions**:
1. Verify Cassandra cluster is running: `nodetool status`
2. Check network connectivity: `ping <cassandra-host>`
3. Verify port is correct (default 9042): `netstat -an | grep 9042`
4. Check firewall rules allow connections to Cassandra port

---

**Problem**: "Connection failed: Invalid username or password"

**Solutions**:
1. Verify credentials are correct
2. Check user has permissions: `cqlsh -u <username> -p <password>`
3. Confirm user has SELECT grants on keyspace

---

**Problem**: "Connection failed: Keyspace 'xyz' does not exist"

**Solutions**:
1. List available keyspaces: `cqlsh -e "DESCRIBE KEYSPACES;"`
2. Verify keyspace name spelling (case-sensitive)
3. Confirm user has access to keyspace

---

### Query Issues

**Problem**: "Query timed out after 10 seconds"

**Solutions**:
1. Narrow date range (try 1 week instead of 1 year)
2. Check Cassandra cluster performance
3. Verify table has proper indexes on partition keys
4. Increase timeout in `config/settings.py` if necessary

---

**Problem**: "No results found"

**Solutions**:
1. Verify equipment ID spelling (exact match required)
2. Expand date range
3. Check data exists in database:
   ```sql
   SELECT count(*) FROM snapshot WHERE year=2025 AND month=1 AND eqpid='CAM_001';
   ```

---

### Download Issues

**Problem**: "Download failed: Permission denied when writing to folder"

**Solutions**:
1. Select different save path with write permissions
2. Check folder permissions: `ls -ld /path/to/folder`
3. Run with appropriate user permissions

---

**Problem**: "Download failed: Insufficient disk space"

**Solutions**:
1. Free up disk space
2. Select different save path on drive with more space
3. Reduce date range to download fewer files

---

**Problem**: "FAILED: filename.png - Invalid image data"

**Solutions**:
1. This indicates corrupted data in database (specific snapshot only)
2. Download continues with remaining files
3. Check database data quality
4. Note failed filenames from log for investigation

---

### Performance Issues

**Problem**: Application freezes during download

**Expected Behavior**: Application should remain responsive

**Solutions**:
1. Verify download is using background thread (check log messages continue)
2. If truly frozen, may indicate bug - check console for Python errors
3. Reduce dataset size to test

---

**Problem**: Download is very slow

**Expected Behavior**: ~50-100 files/second (depends on network, image sizes)

**Solutions**:
1. Check network latency to Cassandra cluster
2. Verify disk write speed (slow external drives)
3. Monitor Cassandra cluster load

---

## Development Workflow

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_cassandra_client.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Code Style

```bash
# Format code with black
pip install black
black .

# Lint with flake8
pip install flake8
flake8 --max-line-length=100

# Type checking with mypy
pip install mypy
mypy --strict main.py database/ downloader/ ui/ utils/
```

### Build Standalone Executable (Optional)

```bash
# Install PyInstaller
pip install pyinstaller

# Create single-file executable
pyinstaller --onefile --windowed --name CassandraSnapshotDownloader main.py

# Output: dist/CassandraSnapshotDownloader
```

---

## Project Structure Reference

```
cassandra-snapshot-downloader/
├── main.py                      # Launch this file to start application
├── requirements.txt             # Dependencies (install with pip)
├── README.md                    # Project documentation
├── .gitignore                   # Git ignore rules
│
├── config/
│   └── settings.py              # Customize timeouts and limits here
│
├── ui/
│   └── main_window.py           # Main UI implementation
│
├── database/
│   ├── cassandra_client.py      # Database connection logic
│   └── models.py                # Data structures
│
├── downloader/
│   ├── download_manager.py      # Download orchestration
│   └── file_handler.py          # File operations
│
├── utils/
│   ├── logger.py                # Logging configuration
│   └── validators.py            # Input validation
│
└── tests/                       # Test suite (optional)
```

---

## Expected Database Schema

The application expects the following Cassandra table to exist:

```cql
CREATE TABLE snapshot (
    year int,
    month int,
    day int,
    eqpid text,
    fname text,
    image blob,
    PRIMARY KEY ((year, month, day, eqpid), fname)
);
```

**Verify Schema**:
```bash
cqlsh -e "DESCRIBE TABLE production_snapshots.snapshot;"
```

---

## Logging

### Log File Location

Logs are created in the application directory with timestamp:
```
cassandra_downloader_20251111_142315.log
```

### Log Levels

- **INFO**: Normal operations (connection, search, download progress)
- **WARNING**: Non-fatal issues (skipped files, corrupted data)
- **ERROR**: Fatal errors (connection lost, disk full)

### View Real-Time Logs

**Linux/macOS**:
```bash
tail -f cassandra_downloader_*.log
```

**Windows**:
```cmd
Get-Content -Path "cassandra_downloader_*.log" -Wait
```

---

## Next Steps

1. **Read User Documentation**: See README.md for end-user instructions
2. **Review Architecture**: See `/specs/001-cassandra-snapshot-downloader/data-model.md`
3. **Understand Contracts**: See `/specs/001-cassandra-snapshot-downloader/contracts/`
4. **Start Development**: Follow implementation plan in `/specs/001-cassandra-snapshot-downloader/plan.md`

---

## Getting Help

### Documentation Resources
- **Feature Specification**: `/specs/001-cassandra-snapshot-downloader/spec.md`
- **Implementation Plan**: `/specs/001-cassandra-snapshot-downloader/plan.md`
- **Data Model**: `/specs/001-cassandra-snapshot-downloader/data-model.md`
- **Research Notes**: `/specs/001-cassandra-snapshot-downloader/research.md`

### Technical Support
- Check error messages - they include resolution guidance
- Review log files for detailed error information
- Verify database schema matches expectations

### Development Support
- Run tests to verify installation: `pytest`
- Check constitution compliance: `/specs/.specify/memory/constitution.md`
- Review code contracts: `/specs/001-cassandra-snapshot-downloader/contracts/`

---

## Quick Start Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Cassandra connection credentials available
- [ ] Network access to Cassandra cluster verified
- [ ] Application launches without errors (`python main.py`)
- [ ] Connection test succeeds
- [ ] Sample search returns results
- [ ] Test download completes successfully
- [ ] Downloaded PNG files verified

**Estimated Setup Time**: 15-30 minutes

---

**Version**: 1.0
**Last Updated**: 2025-11-11
