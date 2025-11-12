# Feature Specification: Cassandra Snapshot Downloader

**Feature Branch**: `001-cassandra-snapshot-downloader`
**Created**: 2025-11-11
**Status**: Draft
**Input**: User description: "Desktop application to systematically download screenshot snapshots (ByteArray) stored in Cassandra database to local folders"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Database Connection and Validation (Priority: P1)

As a database operator, I need to connect to the Cassandra database and verify the connection is working before performing any operations, so that I can ensure I have proper access and credentials.

**Why this priority**: Without a working database connection, no other functionality can work. This is the foundational capability that enables all downstream features.

**Independent Test**: Can be fully tested by entering connection credentials and clicking "Test Connection" - delivers immediate feedback on connectivity status without requiring any other features.

**Acceptance Scenarios**:

1. **Given** the application is launched, **When** I enter valid connection details (Host, Port, Username, Password, Keyspace) and click "Test Connection", **Then** the system displays "Connection Successful" message, enables search functionality, and automatically saves the connection settings to config file
2. **Given** I have previously connected successfully, **When** I launch the application, **Then** the system automatically populates the connection fields with the saved values from the last successful connection
3. **Given** I enter invalid credentials, **When** I click "Test Connection", **Then** the system displays a clear error message explaining the connection failure (e.g., "Authentication failed: Invalid username or password")
4. **Given** the database server is unreachable, **When** I attempt to connect, **Then** the system displays a timeout error within 5 seconds with guidance to check network connectivity
5. **Given** I enter incorrect Keyspace name, **When** I test connection, **Then** the system displays "Keyspace not found" error message

---

### User Story 2 - Search and Preview Snapshots (Priority: P1)

As a database operator, I need to search for snapshots by date range and equipment ID to identify which snapshots I want to download, so that I can verify the data exists before starting a potentially long download process.

**Why this priority**: Users need to confirm data exists and understand the scope before committing to downloads. This provides essential preview capability and prevents wasted download attempts.

**Independent Test**: Can be tested by establishing database connection, entering search criteria, and verifying results appear in the table - delivers value by showing data exists and its volume.

**Acceptance Scenarios**:

1. **Given** I launch the application for the first time, **When** the search filters section is displayed, **Then** the Start Date and End Date fields are both initialized to today's date and Equipment ID field is empty
2. **Given** I have previously performed a search, **When** I launch the application, **Then** the search filters (Start Date, End Date, Equipment ID) are automatically populated with the values from my last search
3. **Given** I am connected to the database, **When** I select a date range (start date to end date), enter an equipment ID, and click "Search", **Then** the system displays up to 20 matching snapshot records in a table showing year, month, day, eqpid, and fname, and saves these filter values to config file
4. **Given** search results exceed 20 records, **When** results are displayed, **Then** the system shows "Total: 1,234 records (showing first 20)" message
5. **Given** I click on a column header in the results table, **When** the table is displayed, **Then** the results are sorted by that column (ascending/descending toggle)
6. **Given** I attempt to search without entering required equipment ID, **When** I click "Search", **Then** the system displays warning message "Equipment ID is required" and prevents the search
7. **Given** I select only a start date without end date, **When** I search, **Then** the system searches from start date to current date
8. **Given** the search query takes longer than 10 seconds, **When** waiting for results, **Then** the system displays a timeout error and allows me to refine search criteria

---

### User Story 3 - Download Snapshots to Organized Folder Structure (Priority: P1)

As a database operator, I need to download all matching snapshots to a local folder with an organized directory structure, so that I can archive snapshots in a way that's easy to browse and manage.

**Why this priority**: This is the core value proposition of the application - bulk downloading with automatic organization. Without this, users would need to manually manage downloads.

**Independent Test**: Can be tested by searching for snapshots, selecting a save location, and clicking "Download All" - delivers complete value by producing organized folders with PNG files.

**Acceptance Scenarios**:

1. **Given** I have search results displayed, **When** I click "Select Save Path" and choose a folder, **Then** the system enables the "Download All" button
2. **Given** I click "Download All", **When** download begins, **Then** the system creates folder structure `[SavePath]/[Year]/[Month]/[Day]/[EquipmentID]/` and saves each snapshot as a PNG file using the fname from the database
3. **Given** a file already exists at the target path, **When** attempting to download that snapshot, **Then** the system skips the file and logs "Skipped: [filename] (already exists)"
4. **Given** download is in progress, **When** monitoring progress, **Then** the system displays a progress bar showing percentage complete and number of files processed out of total
5. **Given** download is in progress, **When** operations are executing, **Then** the system logs each action with status: "Success: [filename]", "Failed: [filename] - [error reason]", or "Skipped: [filename] (already exists)"
6. **Given** the total result set has 5,000 snapshots, **When** I click "Download All", **Then** the system downloads ALL matching snapshots (not just the 20 displayed), processing them in batches
7. **Given** download is in progress, **When** I click "Cancel Download", **Then** the system stops after completing the current file and displays "Download cancelled - [N] files completed"

---

### User Story 4 - Responsive UI During Long Operations (Priority: P2)

As a database operator, I need the application to remain responsive while downloading thousands of files, so that I can monitor progress or cancel operations without the application freezing.

**Why this priority**: Essential for usability with large datasets, but the core download functionality could work without this if users are willing to wait without interaction.

**Independent Test**: Can be tested by starting a large download and attempting to interact with the UI (scrolling logs, checking progress) - delivers improved user experience without blocking.

**Acceptance Scenarios**:

1. **Given** a download of 1,000+ files is in progress, **When** I interact with the application, **Then** the UI responds to clicks and updates within 1 second
2. **Given** download is running in background, **When** I scroll through the log messages, **Then** the log view scrolls smoothly without lag
3. **Given** search query is executing, **When** waiting for results, **Then** the UI remains interactive and displays a loading indicator

---

### User Story 5 - Error Recovery and Detailed Logging (Priority: P2)

As a database operator, I need clear error messages and detailed logs when problems occur, so that I can troubleshoot issues and retry failed operations.

**Why this priority**: Improves reliability and troubleshooting capability, but basic functionality can work with simple error messages.

**Independent Test**: Can be tested by deliberately causing errors (network disconnect, disk full, corrupted data) and verifying appropriate messages and logs appear.

**Acceptance Scenarios**:

1. **Given** the network connection is lost during download, **When** a download fails, **Then** the system logs "Failed: [filename] - Network error" and continues with next file
2. **Given** the target disk is full, **When** attempting to write a file, **Then** the system displays "Error: Insufficient disk space" and stops the download
3. **Given** a snapshot's image data is corrupted, **When** attempting to convert to PNG, **Then** the system logs "Failed: [filename] - Invalid image data" and skips to next file
4. **Given** the target folder requires special permissions, **When** attempting to create directories, **Then** the system displays "Error: Permission denied - cannot write to [path]"
5. **Given** any operation fails, **When** error occurs, **Then** all error messages include actionable guidance (e.g., "Check network connection and retry", "Free up disk space", "Verify folder permissions")

---

### User Story 6 - Secure Credential Handling (Priority: P3)

As a database operator, I need my database password to be protected from casual observation, so that credentials are not exposed on screen.

**Why this priority**: Important for security in shared environments, but core functionality works without this protection.

**Independent Test**: Can be tested by entering a password and verifying it displays as masked characters (e.g., dots or asterisks).

**Acceptance Scenarios**:

1. **Given** I am entering database credentials, **When** I type in the password field, **Then** each character is displayed as a masked symbol (•) instead of plain text
2. **Given** I have saved connection details in memory, **When** the application is running, **Then** credentials are kept only in memory and never written to disk in plain text

---

### Edge Cases

- **What happens when date range is invalid** (end date before start date)?
  - System displays validation error: "End date must be after start date"

- **What happens when the database table is empty** (no snapshots match criteria)?
  - System displays "No results found" message with suggestion to adjust search criteria

- **What happens when fname contains invalid filesystem characters**?
  - System sanitizes the filename by replacing invalid characters with underscores while preserving the .png extension

- **What happens when two snapshots have identical fname**?
  - The folder structure includes year/month/day/eqpid, so collisions are prevented by the hierarchical organization. If duplicates exist within the same date/equipment combination, the second file is skipped (duplicate detection).

- **What happens when the Cassandra cluster has multiple nodes and partial connectivity**?
  - System attempts connection to the specified host and reports success/failure for that specific connection point

- **What happens when image ByteArray is null or empty**?
  - System logs "Failed: [filename] - No image data" and continues to next snapshot

- **What happens when Cassandra returns blob data as string instead of bytes**?
  - System automatically handles multiple encoding formats: first attempts hex decoding (bytes.fromhex), then checks for Base64 encoding (if starts with 'iVBOR'), finally decodes to raw binary PNG data. This handles hex-encoded Base64 strings commonly returned by Cassandra blob columns

- **What happens when user attempts to download while no search has been performed**?
  - Download button remains disabled until search results are loaded

- **What happens when available disk space runs out mid-download**?
  - System detects write failure, logs error with disk space message, and stops download gracefully

- **What happens when user closes application during active download**?
  - System should prompt "Download in progress. Are you sure you want to exit?" with Yes/No options

## Requirements *(mandatory)*

### Functional Requirements

#### Database Connection (FR-001 to FR-007)

- **FR-001**: System MUST allow users to input Cassandra connection parameters: Host (IP/hostname), Port (number), Username (text), Password (masked text), and Keyspace (text)
- **FR-002**: System MUST provide a "Test Connection" button that validates connectivity and authentication within 5 seconds
- **FR-003**: System MUST display connection status clearly (e.g., "Connected", "Disconnected", "Error: [details]")
- **FR-004**: System MUST prevent search and download operations when database is not connected
- **FR-005**: System MUST authenticate using username and password credentials via Cassandra's standard authentication mechanism
- **FR-006**: System MUST save connection parameters to config file (`config/db_connection.json`) upon successful connection test
- **FR-007**: System MUST load saved connection parameters from config file on application startup and populate the connection fields with saved values if available

#### Search Functionality (FR-008 to FR-016)

- **FR-008**: System MUST provide date range selection using calendar widgets for start date and end date
- **FR-009**: System MUST initialize Start Date and End Date fields to today's date on first application launch (when no saved filters exist)
- **FR-010**: System MUST provide text input field for equipment ID (eqpid) marked as required
- **FR-011**: System MUST validate that equipment ID is not empty before executing search
- **FR-012**: System MUST query Cassandra table `snapshot` with WHERE clause filtering by year/month/day range and eqpid
- **FR-013**: System MUST retrieve all matching records from the database (not limited to display count)
- **FR-014**: System MUST display search results in a table with columns: year, month, day, eqpid, fname (excluding image column)
- **FR-015**: System MUST display total record count with format "Total: [N] records (showing first 20)" or "Total: [N] records" if 20 or fewer
- **FR-016**: System MUST save search filter values (Start Date, End Date, Equipment ID) to config file (`config/search_filters.json`) each time the Search button is clicked
- **FR-017**: System MUST load saved search filter values from config file on application startup and populate the search fields if saved values exist (taking precedence over default today's date)

#### Results Display (FR-018 to FR-020)

- **FR-018**: System MUST limit table display to first 20 records regardless of total result count
- **FR-019**: System MUST allow users to sort table by clicking column headers (toggle ascending/descending)
- **FR-020**: System MUST enable download controls only after successful search with results

#### Download Functionality (FR-021 to FR-029)

- **FR-021**: System MUST provide folder browser dialog for selecting save path
- **FR-022**: System MUST download ALL matching records from search query (not just the 20 displayed)
- **FR-023**: System MUST create hierarchical folder structure: `[SavePath]/[Year]/[Month]/[Day]/[EquipmentID]/`
- **FR-024**: System MUST convert image ByteArray from database to PNG file format
- **FR-025**: System MUST save files using the original fname from the database
- **FR-026**: System MUST check if file exists before writing and skip if already present (no overwrite)
- **FR-027**: System MUST display progress bar showing percentage complete during download
- **FR-028**: System MUST display progress as "[current]/[total]" file count
- **FR-029**: System MUST log each file operation with status: Success, Failed, or Skipped

#### User Interface Layout (FR-030 to FR-034)

- **FR-030**: System MUST arrange UI in vertical sections: Connection Settings (top), Search Filters (below connection), Results Table (center, largest area), Download Controls (bottom), Progress and Logs (bottom-most)
- **FR-031**: System MUST keep UI responsive during all operations (respond to user input within 1 second)
- **FR-032**: System MUST execute database queries and file operations in background threads to prevent UI blocking
- **FR-033**: System MUST provide "Cancel Download" button that becomes visible during active downloads
- **FR-034**: System MUST process cancellation gracefully, completing current file before stopping

#### Error Handling (FR-035 to FR-041)

- **FR-035**: System MUST display clear error messages for connection failures including reason (authentication, network, timeout, invalid keyspace)
- **FR-036**: System MUST handle query timeouts by displaying error after 10 seconds and allowing retry
- **FR-037**: System MUST detect disk write failures and display specific error (insufficient space, permission denied, path invalid)
- **FR-038**: System MUST detect corrupted or invalid image data and skip those records with logged error
- **FR-039**: System MUST continue downloading remaining files if individual file operations fail
- **FR-040**: System MUST provide actionable guidance in all error messages (what to check, how to fix)
- **FR-041**: System MUST log all errors with timestamp, filename (if applicable), and error details

#### Security and Configuration (FR-042 to FR-044)

- **FR-042**: System MUST display password field characters as masked symbols (e.g., • or *)
- **FR-043**: System MUST store connection credentials in config file (`config/db_connection.json`) in plaintext for convenience (encryption not required per user specification)
- **FR-044**: System MUST exclude config files containing credentials from version control by adding them to `.gitignore`

#### Performance and Scalability (FR-045 to FR-047)

- **FR-045**: System MUST process downloads in batches to avoid loading all image data into memory simultaneously
- **FR-046**: System MUST handle search result sets of 10,000+ records without memory overflow
- **FR-047**: System MUST optimize download throughput by processing files sequentially with minimal delay between operations

### Key Entities

- **Snapshot**: Represents a screenshot image captured at a specific time for a specific equipment. Attributes include temporal data (year, month, day), equipment identifier (eqpid), filename with metadata (epoch time, click coordinates), and binary image data.

- **Connection Configuration**: Represents the credentials and location needed to access the Cassandra database. Includes host address, port number, authentication credentials (username, password), and keyspace identifier. Persisted to `config/db_connection.json` for automatic loading on subsequent application launches.

- **Search Filter Configuration**: Represents the search criteria for querying snapshots. Includes start date, end date, and equipment ID. Persisted to `config/search_filters.json` after each search operation for automatic restoration on subsequent application launches.

- **Download Job**: Represents a batch download operation. Tracks source query criteria, destination path, total file count, processed count, success/failure/skip counts, and current status (running, cancelled, completed, failed).

- **File Operation Log Entry**: Represents a single file download attempt. Includes filename, operation timestamp, status (success/failed/skipped), error details (if failed), and target file path.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully test database connection and receive clear feedback within 5 seconds of clicking "Test Connection"
- **SC-002**: Users can execute search queries and view results within 10 seconds for date ranges up to 1 year
- **SC-003**: System successfully downloads and organizes 10,000 snapshot files without crashing or running out of memory
- **SC-004**: Application UI remains responsive (responds to user input within 1 second) even during downloads of 5,000+ files
- **SC-005**: 100% of successfully retrieved image ByteArrays are correctly converted to valid PNG files
- **SC-006**: Users can identify and resolve connection errors without external documentation based on error messages provided
- **SC-007**: Download operations automatically skip existing files, preventing data duplication and wasted network bandwidth
- **SC-008**: Users can cancel long-running downloads and receive confirmation within 2 seconds that cancellation is processing
- **SC-009**: All file operation results (success/failure/skip) are logged and visible to users in real-time during downloads
- **SC-010**: Password credentials are never visible in plain text on screen after entry

### Assumptions

1. **Database Schema Stability**: The Cassandra `snapshot` table schema (year, month, day, eqpid, fname, image) will not change during application usage
2. **Network Reliability**: Users have stable network connection to Cassandra cluster; transient failures are acceptable but sustained connectivity is required
3. **File System Compatibility**: Target save paths are on file systems that support the folder structure depth (at least 5 levels: root/year/month/day/eqpid/)
4. **Image Format Consistency**: All image ByteArrays in the database are PNG-compatible binary data (standard PNG format)
5. **Date Range Reasonableness**: Users will search within reasonable date ranges (not entire decades) to keep query results manageable
6. **Single User Operation**: Application is designed for single-user desktop use, not concurrent multi-user access
7. **Cassandra Availability**: The Cassandra cluster is operational and accessible during application use
8. **Local Disk Capacity**: Users have sufficient local disk space for their intended downloads (application will detect exhaustion but assumes initial capacity)
9. **Standard Authentication**: Cassandra cluster uses standard username/password authentication (not Kerberos or other advanced methods)
10. **Desktop Environment**: Application runs on standard desktop OS with GUI support and adequate system resources (minimum 2GB RAM, dual-core CPU)
11. **Config File Security**: Users accept that connection credentials (including passwords) are stored in plaintext in local config files for convenience, and are responsible for protecting their local file system from unauthorized access
12. **Config File Persistence**: Users understand that saved connection and search filter settings persist across application sessions and will automatically populate on next launch

### Dependencies

- **Cassandra Cluster Access**: Requires operational Cassandra cluster with `snapshot` table containing the expected schema
- **Network Connectivity**: Requires network access from desktop to Cassandra cluster on specified port
- **Credentials**: Requires valid database username and password with SELECT permissions on target keyspace and table
- **Local File System Permissions**: Requires write permissions on target save directory and ability to create nested folders

### Constraints

- **Display Limitation**: Results table shows maximum 20 records for UI performance, though all matching records are available for download
- **Query Timeout**: Search queries must complete within 10 seconds or will timeout
- **Connection Timeout**: Connection tests must complete within 5 seconds
- **Single Connection**: Application maintains one database connection at a time (no connection pooling)
- **Sequential Downloads**: Files are downloaded sequentially (not parallel) to maintain memory efficiency and predictable logging
- **No Resume Capability**: If download is cancelled or fails, user must restart from beginning (already-downloaded files will be skipped)
- **No Selective Download**: Download operates on entire search result set (cannot select specific individual files from results table)
- **Read-Only Operations**: Application only performs SELECT queries; no INSERT, UPDATE, or DELETE operations on database
