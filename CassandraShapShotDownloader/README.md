# Cassandra Snapshot Downloader

A desktop application for systematically downloading screenshot snapshots from Apache Cassandra database to local folders with organized hierarchical structure.

## Features

- **Database Connection**: Connect to Cassandra cluster with username/password authentication
- **Search Capability**: Search snapshots by date range and equipment ID
- **Preview Results**: View up to 20 matching records in sortable table
- **Bulk Download**: Download all matching snapshots with organized folder structure (Year/Month/Day/EquipmentID)
- **Progress Tracking**: Real-time progress bar and detailed logs during download
- **Error Handling**: Comprehensive error messages with actionable guidance
- **Background Processing**: UI remains responsive during large downloads
- **Secure Credentials**: Password masking and memory-only storage (no persistence to disk)

## Requirements

- **Python**: 3.11 or higher
- **Operating System**: Linux, Windows 10+, or macOS 10.15+
- **RAM**: Minimum 2GB available
- **Network**: Access to Cassandra cluster on configured port (default 9042)

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

### 4. Verify Installation

```bash
python -c "import PyQt5.QtWidgets; import cassandra; import PIL; print('All dependencies installed successfully')"
```

## Usage

### Launch Application

```bash
python main.py
```

### Basic Workflow

1. **Connect to Database**:
   - Enter connection details (Host, Port, Username, Password, Keyspace)
   - Click "Test Connection" to verify connectivity
   - Green status indicator confirms successful connection

2. **Search for Snapshots**:
   - Select date range using calendar widgets
   - Enter Equipment ID (required field)
   - Click "Search" to query database
   - Review results in table (sortable by clicking column headers)

3. **Download Snapshots**:
   - Click "Select Save Path" to choose download folder
   - Click "Download All" to begin download
   - Monitor progress bar and log messages
   - Downloaded files organized in folders: `Year/Month/Day/EquipmentID/filename.png`

### Folder Structure

Downloaded snapshots are organized hierarchically:

```
[SavePath]/
└── [Year]/
    └── [Month]/
        └── [Day]/
            └── [EquipmentID]/
                ├── snapshot_001.png
                ├── snapshot_002.png
                └── ...
```

**Example**:
```
/home/user/Downloads/snapshots/
└── 2025/
    └── 11/
        └── 11/
            └── CAM_001/
                ├── 1731283200_x100_y200.png
                └── 1731286800_x150_y250.png
```

## Troubleshooting

### Connection Issues

**Problem**: "Connection failed: Cannot reach database server"

**Solutions**:
- Verify Cassandra cluster is running
- Check network connectivity to database host
- Confirm port is correct (default 9042)
- Verify firewall allows connections

---

**Problem**: "Connection failed: Invalid username or password"

**Solutions**:
- Verify credentials are correct
- Check user has SELECT permissions on keyspace
- Try connecting via cqlsh to confirm credentials

---

**Problem**: "Keyspace does not exist"

**Solutions**:
- List available keyspaces: `cqlsh -e "DESCRIBE KEYSPACES;"`
- Verify keyspace name spelling (case-sensitive)

### Query Issues

**Problem**: "Query timed out after 10 seconds"

**Solutions**:
- Narrow date range (try 1 week instead of 1 year)
- Check Cassandra cluster performance
- Verify table has proper indexes on partition keys

---

**Problem**: "No results found"

**Solutions**:
- Verify equipment ID spelling (exact match required)
- Expand date range
- Check data exists in database using cqlsh

### Download Issues

**Problem**: "Permission denied when writing to folder"

**Solutions**:
- Select different save path with write permissions
- Check folder permissions
- Run with appropriate user permissions

---

**Problem**: "Insufficient disk space"

**Solutions**:
- Free up disk space
- Select different save path on drive with more space
- Reduce date range to download fewer files

---

**Problem**: "FAILED: filename.png - Invalid image data"

**Solutions**:
- This indicates corrupted data for that specific snapshot
- Download continues with remaining files
- Check database data quality for affected records

## Configuration

Application constants can be customized in `config/settings.py`:

```python
# Database timeouts (seconds)
CONNECTION_TIMEOUT = 5.0
QUERY_TIMEOUT = 10.0

# UI display limits
TABLE_DISPLAY_LIMIT = 20

# Date range limits
MAX_DATE_RANGE_DAYS = 365
```

## Database Schema

The application expects the following Cassandra table structure:

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

## License

[Your License Here]

## Support

For issues or questions:
- Check error messages for actionable guidance
- Review log files (created in application directory)
- Verify database schema matches expectations
