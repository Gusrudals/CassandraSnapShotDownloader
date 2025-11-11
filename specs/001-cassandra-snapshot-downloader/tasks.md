# Tasks: Cassandra Snapshot Downloader

**Input**: Design documents from `/specs/001-cassandra-snapshot-downloader/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are NOT included in this task list as they were not explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- All paths are relative to repository root: `cassandra-snapshot-downloader/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure: main.py, config/, ui/, database/, downloader/, utils/, tests/
- [X] T002 Create requirements.txt with dependencies: PyQt5>=5.15.0, cassandra-driver>=3.28.0, Pillow>=10.0.0, pytest>=7.4.0, pytest-qt>=4.2.0
- [X] T003 [P] Create .gitignore file for Python artifacts, __pycache__, venv/, *.pyc, *.log, .pytest_cache/
- [X] T004 [P] Create all __init__.py files in config/, ui/, database/, downloader/, utils/, tests/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create configuration constants in config/settings.py: CONNECTION_TIMEOUT=5.0, QUERY_TIMEOUT=10.0, TABLE_DISPLAY_LIMIT=20, MAX_DATE_RANGE_DAYS=365
- [X] T006 [P] Setup logging configuration in utils/logger.py: file handler with timestamp format, console handler, exclude password from logs
- [X] T007 [P] Create SnapshotRecord dataclass in database/models.py with attributes: year, month, day, eqpid, fname, image, capture_date property, folder_path property
- [X] T008 [P] Create ConnectionConfiguration dataclass in database/models.py with attributes: host, port, username, password, keyspace, validation, __repr__ that masks password
- [X] T009 [P] Create DownloadJob dataclass in downloader/download_manager.py with DownloadStatus enum and attributes: start_date, end_date, eqpid, save_path, counters, progress_percentage property
- [X] T010 [P] Create FileOperationLogEntry dataclass with FileOperationStatus enum in utils/logger.py: timestamp, filename, file_path, status, error_message, format_log_message() method

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Database Connection and Validation (Priority: P1) 🎯 MVP

**Goal**: Enable users to connect to Cassandra database and verify connection is working

**Independent Test**: Enter connection credentials, click "Test Connection", verify success/error message displays

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement CassandraClient.__init__() in database/cassandra_client.py: initialize cluster=None, session=None, is_connected=False
- [X] T012 [US1] Implement CassandraClient.connect() method: accept host, port, username, password, keyspace, use PlainTextAuthProvider, set 5s timeout, return (bool, str) tuple
- [X] T013 [US1] Add error handling to CassandraClient.connect(): catch NoHostAvailable, Unauthorized, InvalidRequest exceptions, return actionable error messages
- [X] T014 [US1] Implement CassandraClient.test_connection() method: execute lightweight query "SELECT count(*) FROM snapshot LIMIT 1", return (bool, str) tuple
- [X] T015 [US1] Implement CassandraClient.disconnect() method: shutdown session and cluster, set to None, update is_connected flag
- [X] T016 [US1] Add is_connected property to CassandraClient: return bool based on session state
- [X] T017 [P] [US1] Create MainWindow class in ui/main_window.py: inherit from QMainWindow, setup basic window with title and size
- [X] T018 [US1] Add connection form widgets to MainWindow: QLineEdit for host, QSpinBox for port (default 9042), QLineEdit for username, QLineEdit for password (masked), QLineEdit for keyspace
- [X] T019 [US1] Add connection buttons to MainWindow: QPushButton "Test Connection", QPushButton "Disconnect" (initially disabled), QLabel for connection status
- [X] T020 [US1] Implement MainWindow.on_test_connection_clicked() slot: create ConnectionConfiguration, call cassandra_client.connect(), display result in QMessageBox
- [X] T021 [US1] Update connection status display in MainWindow: show "Connected" in green or "Disconnected"/"Error" in red with details
- [X] T022 [US1] Implement MainWindow.on_disconnect_clicked() slot: call cassandra_client.disconnect(), update UI state, disable search controls
- [X] T023 [US1] Create main.py application entry point: setup QApplication, setup logger, create and show MainWindow, handle application exit

**Checkpoint**: At this point, User Story 1 should be fully functional - can test database connection and see clear error messages

---

## Phase 4: User Story 2 - Search and Preview Snapshots (Priority: P1)

**Goal**: Enable users to search for snapshots by date range and equipment ID, preview results in table

**Independent Test**: After establishing connection, enter search criteria (dates + equipment ID), click "Search", verify results table displays with record count

### Implementation for User Story 2

- [X] T024 [P] [US2] Create input validation functions in utils/validators.py: validate_date_range(start_date, end_date) checking end > start, max 365 days, end <= today
- [X] T025 [P] [US2] Add validate_eqpid(eqpid: str) function in utils/validators.py: check non-empty, return (bool, str) tuple
- [X] T026 [US2] Implement CassandraClient.query_snapshots() method: accept start_date, end_date, eqpid, limit parameters, iterate through year-month combinations
- [X] T027 [US2] Implement month-by-month query logic in query_snapshots(): calculate day ranges per month, execute parameterized SELECT queries for each month
- [X] T028 [US2] Add query_snapshots() error handling: raise ValueError for invalid inputs, RuntimeError if not connected, handle OperationTimedOut
- [X] T029 [US2] Implement CassandraClient.count_snapshots() method: similar to query_snapshots but use COUNT(*) queries, return total int
- [X] T030 [P] [US2] Add search form widgets to MainWindow: QDateEdit for start_date and end_date (calendar popup), QLineEdit for equipment ID with required indicator
- [X] T031 [P] [US2] Add search button and results table to MainWindow: QPushButton "Search" (disabled until connected), QTableWidget with columns: year, month, day, eqpid, fname
- [X] T032 [P] [US2] Add results count label to MainWindow: QLabel showing "Total: N records (showing first 20)" or "Total: N records"
- [X] T033 [US2] Implement MainWindow.on_search_clicked() slot: validate inputs using validators, call count_snapshots() then query_snapshots(limit=20), populate table
- [X] T034 [US2] Implement table population logic: clear existing rows, add up to 20 rows with snapshot data, enable column sorting via QTableWidget headers
- [X] T035 [US2] Handle search errors in MainWindow: display QMessageBox for validation errors, timeouts, empty results with actionable messages
- [X] T036 [US2] Store full search results in MainWindow: keep list of ALL SnapshotRecords for download (not just 20 displayed), update download button enabled state

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - can connect, search, and preview results independently

---

## Phase 5: User Story 3 - Download Snapshots to Organized Folder Structure (Priority: P1)

**Goal**: Enable users to download all matching snapshots with automatic folder organization (year/month/day/eqpid)

**Independent Test**: After search results appear, select save path, click "Download All", verify PNG files created in organized folders

### Implementation for User Story 3

- [X] T037 [P] [US3] Implement sanitize_filename() function in downloader/file_handler.py: replace invalid characters (/, \, :, *, ?, ", <, >, |) with underscore, ensure .png extension
- [X] T038 [P] [US3] Implement create_folder_structure() function in downloader/file_handler.py: accept base_path, year, month, day, eqpid, create nested folders with os.makedirs, return folder path
- [X] T039 [P] [US3] Implement file_exists() function in downloader/file_handler.py: wrapper for os.path.exists() and os.path.isfile(), return bool
- [X] T040 [P] [US3] Implement save_image() function in downloader/file_handler.py: accept bytes and file_path, use PIL Image.open(BytesIO()), save as PNG, raise ValueError for invalid data
- [X] T041 [P] [US3] Implement ensure_directory_writable() function in downloader/file_handler.py: verify directory exists, is writable via temp file test, return (bool, str) tuple
- [X] T042 [US3] Create DownloadManager class in downloader/download_manager.py: extend QThread, define signals: progress_updated(int, int, str), log_message(str), download_completed(int, int, int), download_error(str)
- [X] T043 [US3] Implement DownloadManager.__init__(): accept cassandra_client, save_path, start_date, end_date, eqpid, initialize _is_cancelled=False
- [X] T044 [US3] Implement DownloadManager.run() method part 1: query all snapshots via cassandra_client.query_snapshots(), emit log_message for start, handle fatal errors
- [X] T045 [US3] Implement DownloadManager.run() method part 2: iterate through snapshots, check _is_cancelled flag, create folder structure, check file existence
- [X] T046 [US3] Implement DownloadManager.run() method part 3: for each file, save image using file_handler, track success/failed/skipped counts, emit progress_updated and log_message signals
- [X] T047 [US3] Implement DownloadManager.run() method part 4: handle individual file errors (log and continue), emit download_completed or download_error at end
- [X] T048 [US3] Implement DownloadManager.cancel() method: set _is_cancelled=True for graceful shutdown after current file
- [X] T049 [P] [US3] Add download controls to MainWindow: QPushButton "Select Save Path", QLineEdit for save path display (read-only), QPushButton "Download All" (disabled until search results)
- [X] T050 [P] [US3] Add progress widgets to MainWindow: QProgressBar, QPushButton "Cancel Download" (hidden initially), QTextEdit for log messages (read-only, auto-scroll)
- [X] T051 [US3] Implement MainWindow.on_select_save_path_clicked() slot: show QFileDialog.getExistingDirectory(), validate with ensure_directory_writable(), enable download button
- [X] T052 [US3] Implement MainWindow.on_download_all_clicked() slot: create DownloadManager with stored search results params, connect all signals, update UI state, start thread
- [X] T053 [US3] Implement MainWindow signal handlers: on_progress_updated() updates progress bar, on_log_message() appends to text edit and scrolls to bottom
- [X] T054 [US3] Implement MainWindow.on_download_completed() slot: show QMessageBox with success/failed/skipped counts, re-enable download button, hide cancel button, cleanup thread with deleteLater()
- [X] T055 [US3] Implement MainWindow.on_download_error() slot: show QMessageBox.critical with error message, re-enable download button, cleanup thread
- [X] T056 [US3] Implement MainWindow.on_cancel_download_clicked() slot: call download_thread.cancel(), disable cancel button, update status label

**Checkpoint**: All P1 user stories (US1, US2, US3) are now complete and functional - full download workflow works

---

## Phase 6: User Story 4 - Responsive UI During Long Operations (Priority: P2)

**Goal**: Ensure UI remains responsive during large downloads without freezing

**Independent Test**: Start download of 1000+ files, attempt to scroll logs, verify UI responds within 1 second

### Implementation for User Story 4

- [X] T057 [US4] Verify DownloadManager executes in background thread: confirm run() is not called directly, signals properly queued to main thread
- [X] T058 [US4] Verify search query responsiveness: ensure query_snapshots() can be called with progress indicator without blocking UI
- [X] T059 [US4] Add loading indicator to MainWindow: QProgressDialog or status bar spinner during search query execution
- [X] T060 [US4] Test UI interaction during download: verify table scrolling, log scrolling, button clicks respond within 1 second timeout requirement

**Checkpoint**: UI responsiveness verified for all long-running operations

---

## Phase 7: User Story 5 - Error Recovery and Detailed Logging (Priority: P2)

**Goal**: Provide clear error messages and detailed logs for troubleshooting

**Independent Test**: Trigger deliberate errors (disconnect network, fill disk), verify appropriate error messages and log entries appear

### Implementation for User Story 5

- [X] T061 [P] [US5] Enhance logger.py with structured log formatting: include timestamp, level, module, message for all log entries
- [X] T062 [P] [US5] Add log file rotation in logger.py: create new log file per session with timestamp in filename
- [X] T063 [US5] Enhance error messages in CassandraClient: ensure all errors follow pattern "[What failed]: [Why]. [What to do]"
- [X] T064 [US5] Enhance error messages in DownloadManager: add specific messages for network errors, disk full, corrupted data, permissions
- [X] T065 [US5] Add detailed logging to download workflow: log each file operation with FileOperationLogEntry, write to file logger
- [X] T066 [US5] Implement error recovery in DownloadManager: continue to next file after individual failures, only stop on fatal errors
- [X] T067 [US5] Add guidance to all error dialogs: include actionable steps in all QMessageBox error displays

**Checkpoint**: Error handling and logging are comprehensive and user-friendly

---

## Phase 8: User Story 6 - Secure Credential Handling (Priority: P3)

**Goal**: Protect database password from casual observation

**Independent Test**: Enter password in connection form, verify characters display as dots/asterisks

### Implementation for User Story 6

- [X] T068 [US6] Set password field echo mode in MainWindow: call password_edit.setEchoMode(QLineEdit.Password) to mask input
- [X] T069 [US6] Verify ConnectionConfiguration.__repr__() masks password: ensure password shows as '***' in string representation
- [X] T070 [US6] Verify password excluded from logs: check logger.py never logs connection password or connection config directly
- [X] T071 [US6] Verify no credential persistence: confirm no config file saving, credentials only in memory during runtime

**Checkpoint**: Password masking and security measures verified

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final touches and documentation

- [X] T072 [P] Create README.md with project overview, installation instructions, usage guide, troubleshooting section
- [X] T073 [P] Add docstrings to all public methods in CassandraClient, DownloadManager, file_handler functions
- [X] T074 [P] Add type hints to all function signatures across all modules
- [X] T075 Review and test error handling: verify all error paths display appropriate messages and don't crash
- [X] T076 Code cleanup: remove debug print statements, ensure consistent formatting, verify all imports used
- [X] T077 Validate against quickstart.md: follow all setup steps, verify application works as documented
- [X] T078 [P] Add application window icon (optional): create icon file and set with setWindowIcon() if desired
- [X] T079 Final constitution compliance check: verify read-only operations, no credential persistence, proper error handling throughout

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Phase 2
  - User Story 2 (P1): Depends on User Story 1 (needs CassandraClient, MainWindow)
  - User Story 3 (P1): Depends on User Story 2 (needs search results)
  - User Story 4 (P2): Depends on User Story 3 (validates threading)
  - User Story 5 (P2): Can enhance existing code after Phase 2, but best after US1-3 complete
  - User Story 6 (P3): Can start after User Story 1 (enhances connection form)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories (requires Phase 2 complete)
- **User Story 2 (P1)**: Requires User Story 1 complete (extends MainWindow, uses CassandraClient)
- **User Story 3 (P1)**: Requires User Story 2 complete (needs search results to download)
- **User Story 4 (P2)**: Requires User Story 3 complete (validates threading implementation)
- **User Story 5 (P2)**: Can work in parallel with other stories but enhances all of them
- **User Story 6 (P3)**: Requires User Story 1 complete (enhances connection UI)

### Within Each User Story

- Tasks marked [P] can run in parallel (different files, no blocking dependencies)
- Non-parallel tasks must run in sequence (listed in dependency order)
- Data models before services
- Services before UI integration
- Core implementation before error handling
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**: T003, T004 can run in parallel
**Phase 2 (Foundational)**: T006, T007, T008, T009, T010 can all run in parallel after T005
**User Story 1**: T011 and T017 can run in parallel (database vs UI modules)
**User Story 2**: T024, T025 can run in parallel; T030, T031, T032 can run in parallel
**User Story 3**: T037, T038, T039, T040, T041 can all run in parallel; T049, T050 can run in parallel
**User Story 5**: T061, T062 can run in parallel
**Phase 9 (Polish)**: T072, T073, T074, T078 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch these tasks in parallel for User Story 1:
Task T011: "Implement CassandraClient.__init__()" (database/cassandra_client.py)
Task T017: "Create MainWindow class" (ui/main_window.py)

# Then proceed sequentially:
Task T012: "Implement CassandraClient.connect()" (depends on T011)
Task T018: "Add connection form widgets" (depends on T017)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Database Connection)
4. **STOP and VALIDATE**: Test connection with real Cassandra database
5. Deploy/demo basic connection capability

### Incremental Delivery (Recommended)

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test connection independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test search independently → Deploy/Demo
4. Add User Story 3 → Test download independently → Deploy/Demo (Core functionality complete!)
5. Add User Story 4 → Validate responsiveness → Deploy/Demo
6. Add User Story 5 → Enhanced error handling → Deploy/Demo
7. Add User Story 6 → Security enhancement → Deploy/Demo
8. Each story adds value without breaking previous stories

### Suggested MVP Scope

**Minimum Viable Product = User Stories 1, 2, 3** (All P1 stories)

This delivers complete core functionality:
- ✅ Connect to database
- ✅ Search for snapshots
- ✅ Download with organized folder structure

Stories 4, 5, 6 are enhancements that can be added incrementally.

---

## Task Summary

**Total Tasks**: 79

**By Phase**:
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 6 tasks
- Phase 3 (User Story 1): 13 tasks
- Phase 4 (User Story 2): 13 tasks
- Phase 5 (User Story 3): 20 tasks
- Phase 6 (User Story 4): 4 tasks
- Phase 7 (User Story 5): 7 tasks
- Phase 8 (User Story 6): 4 tasks
- Phase 9 (Polish): 8 tasks

**By Priority**:
- P1 (MVP): User Stories 1, 2, 3 = 46 tasks (Setup + Foundational + US1 + US2 + US3)
- P2 (Enhanced): User Stories 4, 5 = 11 tasks
- P3 (Security): User Story 6 = 4 tasks
- Infrastructure: 18 tasks (Setup, Foundational, Polish)

**Parallelizable Tasks**: 24 tasks marked with [P]

**Independent Test Criteria Met**:
- ✅ User Story 1: Test connection button provides immediate feedback
- ✅ User Story 2: Search returns visible results in table
- ✅ User Story 3: Download creates organized PNG files on disk
- ✅ User Story 4: UI remains responsive during operations
- ✅ User Story 5: Deliberate errors produce clear messages and logs
- ✅ User Story 6: Password displays as masked characters

---

## Notes

- All tasks include explicit file paths for implementation
- [P] tasks target different files and can run concurrently
- [Story] labels (US1-US6) map each task to its user story for traceability
- Each user story is independently completable and testable
- Tests were not included as they were not requested in the specification
- Stop at any checkpoint to validate story works independently before proceeding
- Follow constitution principles: read-only operations, no credential persistence, comprehensive error handling
