"""Main application window for Cassandra Snapshot Downloader."""

from datetime import date, datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QPushButton, QMessageBox,
    QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QProgressBar, QTextEdit
)
from PyQt5.QtCore import Qt, QDate, pyqtSlot
from PyQt5.QtGui import QPalette, QColor
from database.cassandra_client import CassandraClient
from database.models import ConnectionConfiguration
from downloader.download_manager import DownloadManager
from downloader.file_handler import ensure_directory_writable
from config.settings import TABLE_DISPLAY_LIMIT
from config.config_manager import ConfigManager
from utils.validators import validate_date_range, validate_eqpid
import cassandra


class MainWindow(QMainWindow):
    """Primary UI layout and orchestration for the application."""

    def __init__(self):
        """Initialize the main window with basic setup."""
        super().__init__()
        self.cassandra_client = CassandraClient()
        self.config_manager = ConfigManager()
        self.search_results = []
        self.download_thread = None
        self.save_path = ""

        self._setup_ui()
        self._load_saved_config()

    def _setup_ui(self):
        """Setup the user interface layout."""
        self.setWindowTitle("Cassandra Snapshot Downloader")
        self.setMinimumSize(900, 700)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Add connection section at top
        main_layout.addWidget(self._create_connection_section())

        # Add search section
        main_layout.addWidget(self._create_search_section())

        # Add results section
        main_layout.addWidget(self._create_results_section())

        # Add download section
        main_layout.addWidget(self._create_download_section())

        # Add progress and log section
        main_layout.addWidget(self._create_progress_section())

    def _load_saved_config(self):
        """Load saved configuration from files and populate UI fields."""
        # Load database connection config
        try:
            db_config = self.config_manager.load_db_connection()
            if db_config:
                self.host_edit.setText(db_config.get("host", ""))
                self.port_spin.setValue(db_config.get("port", 9042))
                self.username_edit.setText(db_config.get("username", ""))
                self.password_edit.setText(db_config.get("password", ""))
                self.keyspace_edit.setText(db_config.get("keyspace", ""))
        except Exception as e:
            # If loading fails, just continue with empty fields
            print(f"Failed to load database connection config: {e}")

        # Load search filters config
        try:
            search_config = self.config_manager.load_search_filters()
            if search_config:
                # Parse date strings and set date fields
                start_date_str = search_config.get("start_date")
                end_date_str = search_config.get("end_date")
                equipment_id = search_config.get("equipment_id", "")

                if start_date_str:
                    start_date = datetime.fromisoformat(start_date_str).date()
                    self.start_date_edit.setDate(QDate(start_date.year, start_date.month, start_date.day))

                if end_date_str:
                    end_date = datetime.fromisoformat(end_date_str).date()
                    self.end_date_edit.setDate(QDate(end_date.year, end_date.month, end_date.day))

                self.eqpid_edit.setText(equipment_id)
        except Exception as e:
            # If loading fails, dates will remain as today (default)
            print(f"Failed to load search filters config: {e}")

    def _create_connection_section(self) -> QGroupBox:
        """Create the database connection settings section."""
        group = QGroupBox("Database Connection")
        layout = QVBoxLayout()

        # Connection form fields
        form_layout = QVBoxLayout()

        # Host
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Host:"))
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("e.g., 192.168.1.100 or cassandra.example.com")
        host_layout.addWidget(self.host_edit)
        form_layout.addLayout(host_layout)

        # Port
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(9042)
        port_layout.addWidget(self.port_spin)
        port_layout.addStretch()
        form_layout.addLayout(port_layout)

        # Username
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Database username")
        username_layout.addWidget(self.username_edit)
        form_layout.addLayout(username_layout)

        # Password
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Database password")
        self.password_edit.setEchoMode(QLineEdit.Password)  # Mask password
        password_layout.addWidget(self.password_edit)
        form_layout.addLayout(password_layout)

        # Keyspace
        keyspace_layout = QHBoxLayout()
        keyspace_layout.addWidget(QLabel("Keyspace:"))
        self.keyspace_edit = QLineEdit()
        self.keyspace_edit.setPlaceholderText("Keyspace name")
        keyspace_layout.addWidget(self.keyspace_edit)
        form_layout.addLayout(keyspace_layout)

        layout.addLayout(form_layout)

        # Connection buttons
        button_layout = QHBoxLayout()
        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.clicked.connect(self.on_test_connection_clicked)
        button_layout.addWidget(self.test_connection_button)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.on_disconnect_clicked)
        self.disconnect_button.setEnabled(False)
        button_layout.addWidget(self.disconnect_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Connection status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.connection_status_label = QLabel("Disconnected")
        self._update_connection_status("Disconnected", False)
        status_layout.addWidget(self.connection_status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        group.setLayout(layout)
        return group

    def on_test_connection_clicked(self):
        """Handle Test Connection button click."""
        try:
            # Create connection configuration
            config = ConnectionConfiguration(
                host=self.host_edit.text(),
                port=self.port_spin.value(),
                username=self.username_edit.text(),
                password=self.password_edit.text(),
                keyspace=self.keyspace_edit.text()
            )

            # Attempt connection
            success, message = self.cassandra_client.connect(
                config.host,
                config.port,
                config.username,
                config.password,
                config.keyspace
            )

            if success:
                # Test the connection
                test_success, test_message = self.cassandra_client.test_connection()
                if test_success:
                    # Save database connection config on successful connection
                    try:
                        self.config_manager.save_db_connection(
                            host=config.host,
                            port=config.port,
                            username=config.username,
                            password=config.password,
                            keyspace=config.keyspace
                        )
                    except Exception as e:
                        print(f"Failed to save database connection config: {e}")

                    QMessageBox.information(self, "Connection Successful", message)
                    self._update_connection_status(f"Connected: {config.contact_point}", True)
                    self.disconnect_button.setEnabled(True)
                    self.test_connection_button.setEnabled(False)
                    self.search_button.setEnabled(True)
                else:
                    QMessageBox.warning(self, "Connection Test Failed", test_message)
                    self.cassandra_client.disconnect()
                    self._update_connection_status("Disconnected", False)
            else:
                QMessageBox.critical(self, "Connection Failed", message)
                self._update_connection_status("Connection Failed", False)

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))

    def on_disconnect_clicked(self):
        """Handle Disconnect button click."""
        self.cassandra_client.disconnect()
        self._update_connection_status("Disconnected", False)
        self.disconnect_button.setEnabled(False)
        self.test_connection_button.setEnabled(True)
        self.search_button.setEnabled(False)
        QMessageBox.information(self, "Disconnected", "Database connection closed.")

    def _update_connection_status(self, text: str, is_connected: bool):
        """Update connection status label with color coding."""
        self.connection_status_label.setText(text)

        # Set color based on connection state
        palette = self.connection_status_label.palette()
        if is_connected:
            palette.setColor(QPalette.WindowText, QColor(0, 150, 0))  # Green
        else:
            palette.setColor(QPalette.WindowText, QColor(200, 0, 0))  # Red
        self.connection_status_label.setPalette(palette)

    def _create_search_section(self) -> QGroupBox:
        """Create the search filters section."""
        group = QGroupBox("Search Filters")
        layout = QVBoxLayout()

        # Date range
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Start Date:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())  # Default to today
        date_layout.addWidget(self.start_date_edit)

        date_layout.addWidget(QLabel("End Date:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())  # Default to today
        date_layout.addWidget(self.end_date_edit)
        layout.addLayout(date_layout)

        # Equipment ID
        eqpid_layout = QHBoxLayout()
        eqpid_layout.addWidget(QLabel("Equipment ID: *"))
        self.eqpid_edit = QLineEdit()
        self.eqpid_edit.setPlaceholderText("Required - e.g., CAM_001")
        eqpid_layout.addWidget(self.eqpid_edit)
        layout.addLayout(eqpid_layout)

        # Search button
        button_layout = QHBoxLayout()
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.on_search_clicked)
        self.search_button.setEnabled(False)  # Disabled until connected
        button_layout.addWidget(self.search_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        group.setLayout(layout)
        return group

    def _create_results_section(self) -> QGroupBox:
        """Create the search results section."""
        group = QGroupBox("Search Results")
        layout = QVBoxLayout()

        # Results count label
        self.results_count_label = QLabel("No results")
        layout.addWidget(self.results_count_label)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Year", "Month", "Day", "Equipment ID", "Filename"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSortingEnabled(True)
        layout.addWidget(self.results_table)

        group.setLayout(layout)
        return group

    def on_search_clicked(self):
        """Handle Search button click."""
        # Validate equipment ID
        eqpid = self.eqpid_edit.text().strip()
        is_valid_eqpid, eqpid_error = validate_eqpid(eqpid)
        if not is_valid_eqpid:
            QMessageBox.warning(self, "Invalid Input", eqpid_error)
            return

        # Get and validate date range
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        is_valid_date, date_error = validate_date_range(start_date, end_date)
        if not is_valid_date:
            QMessageBox.warning(self, "Invalid Date Range", date_error)
            return

        # Save search filters to config
        try:
            self.config_manager.save_search_filters(
                start_date=start_date,
                end_date=end_date,
                equipment_id=eqpid
            )
        except Exception as e:
            print(f"Failed to save search filters config: {e}")

        try:
            # Count total results
            total_count = self.cassandra_client.count_snapshots(start_date, end_date, eqpid)

            if total_count == 0:
                QMessageBox.information(
                    self,
                    "No Results",
                    "No snapshots found matching your search criteria. Try adjusting the date range or equipment ID."
                )
                self.results_count_label.setText("No results")
                self.results_table.setRowCount(0)
                self.search_results = []
                return

            # Query results (limit to TABLE_DISPLAY_LIMIT for display, but store all for download)
            self.search_results = self.cassandra_client.query_snapshots(
                start_date, end_date, eqpid, limit=None
            )

            # Update count label
            if total_count > TABLE_DISPLAY_LIMIT:
                self.results_count_label.setText(
                    f"Total: {total_count} records (showing first {TABLE_DISPLAY_LIMIT})"
                )
            else:
                self.results_count_label.setText(f"Total: {total_count} records")

            # Populate table with first 20 results
            self._populate_results_table(self.search_results[:TABLE_DISPLAY_LIMIT])

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))
        except RuntimeError as e:
            QMessageBox.critical(self, "Connection Error", str(e))
        except cassandra.OperationTimedOut:
            QMessageBox.critical(
                self,
                "Query Timeout",
                "Query timed out after 10 seconds. Try narrowing your date range or check database performance."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Search failed: {str(e)}")

    def _populate_results_table(self, snapshots):
        """Populate results table with snapshot data."""
        self.results_table.setSortingEnabled(False)  # Disable while populating
        self.results_table.setRowCount(len(snapshots))

        for row_idx, snapshot in enumerate(snapshots):
            self.results_table.setItem(row_idx, 0, QTableWidgetItem(str(snapshot.year)))
            self.results_table.setItem(row_idx, 1, QTableWidgetItem(str(snapshot.month)))
            self.results_table.setItem(row_idx, 2, QTableWidgetItem(str(snapshot.day)))
            self.results_table.setItem(row_idx, 3, QTableWidgetItem(snapshot.eqpid))
            self.results_table.setItem(row_idx, 4, QTableWidgetItem(snapshot.fname))

        self.results_table.setSortingEnabled(True)  # Re-enable sorting

    def _create_download_section(self) -> QGroupBox:
        """Create the download controls section."""
        group = QGroupBox("Download")
        layout = QVBoxLayout()

        # Save path selection
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Save Path:"))
        self.save_path_edit = QLineEdit()
        self.save_path_edit.setReadOnly(True)
        self.save_path_edit.setPlaceholderText("Select download folder...")
        path_layout.addWidget(self.save_path_edit)

        self.select_path_button = QPushButton("Select Save Path")
        self.select_path_button.clicked.connect(self.on_select_save_path_clicked)
        path_layout.addWidget(self.select_path_button)
        layout.addLayout(path_layout)

        # Download buttons
        button_layout = QHBoxLayout()
        self.download_all_button = QPushButton("Download All")
        self.download_all_button.clicked.connect(self.on_download_all_clicked)
        self.download_all_button.setEnabled(False)
        button_layout.addWidget(self.download_all_button)

        self.cancel_download_button = QPushButton("Cancel Download")
        self.cancel_download_button.clicked.connect(self.on_cancel_download_clicked)
        self.cancel_download_button.setVisible(False)
        button_layout.addWidget(self.cancel_download_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        group.setLayout(layout)
        return group

    def _create_progress_section(self) -> QGroupBox:
        """Create the progress and log section."""
        group = QGroupBox("Progress & Logs")
        layout = QVBoxLayout()

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Log text area
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMaximumHeight(150)
        layout.addWidget(self.log_text_edit)

        group.setLayout(layout)
        return group

    def on_select_save_path_clicked(self):
        """Handle Select Save Path button click."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Save Folder",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if folder:
            # Validate folder is writable
            is_writable, message = ensure_directory_writable(folder)
            if not is_writable:
                QMessageBox.warning(self, "Invalid Directory", message)
                return

            self.save_path = folder
            self.save_path_edit.setText(folder)

            # Enable download button if we have search results
            if self.search_results:
                self.download_all_button.setEnabled(True)

    def on_download_all_clicked(self):
        """Handle Download All button click."""
        if not self.search_results:
            QMessageBox.warning(self, "No Results", "Please perform a search first.")
            return

        if not self.save_path:
            QMessageBox.warning(self, "No Save Path", "Please select a save path first.")
            return

        # Create download thread
        self.download_thread = DownloadManager(
            cassandra_client=self.cassandra_client,
            save_path=self.save_path,
            start_date=self.start_date_edit.date().toPyDate(),
            end_date=self.end_date_edit.date().toPyDate(),
            eqpid=self.eqpid_edit.text().strip()
        )

        # Connect signals
        self.download_thread.progress_updated.connect(self.on_progress_updated)
        self.download_thread.log_message.connect(self.on_log_message)
        self.download_thread.download_completed.connect(self.on_download_completed)
        self.download_thread.download_error.connect(self.on_download_error)

        # Update UI state
        self.download_all_button.setEnabled(False)
        self.cancel_download_button.setVisible(True)
        self.cancel_download_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text_edit.clear()

        # Start download
        self.download_thread.start()

    def on_cancel_download_clicked(self):
        """Handle Cancel Download button click."""
        if self.download_thread:
            self.download_thread.cancel()
            self.cancel_download_button.setEnabled(False)

    @pyqtSlot(int, int, str)
    def on_progress_updated(self, current: int, total: int, status: str):
        """Handle progress update signal."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)

    @pyqtSlot(str)
    def on_log_message(self, message: str):
        """Handle log message signal."""
        self.log_text_edit.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @pyqtSlot(int, int, int)
    def on_download_completed(self, success: int, failed: int, skipped: int):
        """Handle download completion signal."""
        total = success + failed + skipped
        message = (
            f"Download complete!\n\n"
            f"Total: {total} files\n"
            f"Success: {success}\n"
            f"Failed: {failed}\n"
            f"Skipped: {skipped}"
        )
        QMessageBox.information(self, "Download Complete", message)

        # Reset UI state
        self.download_all_button.setEnabled(True)
        self.cancel_download_button.setVisible(False)

        # Cleanup thread
        if self.download_thread:
            self.download_thread.deleteLater()
            self.download_thread = None

    @pyqtSlot(str)
    def on_download_error(self, error_message: str):
        """Handle download error signal."""
        QMessageBox.critical(self, "Download Failed", error_message)

        # Reset UI state
        self.download_all_button.setEnabled(True)
        self.cancel_download_button.setVisible(False)

        # Cleanup thread
        if self.download_thread:
            self.download_thread.deleteLater()
            self.download_thread = None

    def closeEvent(self, event):
        """Handle application close event."""
        if self.cassandra_client.is_connected:
            self.cassandra_client.disconnect()
        event.accept()
