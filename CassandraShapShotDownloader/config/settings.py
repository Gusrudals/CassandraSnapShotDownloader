"""Application configuration constants."""

# Database timeouts (seconds)
CONNECTION_TIMEOUT = 5.0
QUERY_TIMEOUT = 10.0

# UI display limits
TABLE_DISPLAY_LIMIT = 20

# Date range limits
MAX_DATE_RANGE_DAYS = 7

# Progress update frequency
PROGRESS_UPDATE_INTERVAL = 10  # Update UI every N files

# File system
DEFAULT_SAVE_PATH = "~/Downloads/cassandra_snapshots"

# Logging
LOG_FILE_PREFIX = "cassandra_downloader"
LOG_RETENTION_DAYS = 30
