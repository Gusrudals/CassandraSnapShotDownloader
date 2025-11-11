"""Application entry point for Cassandra Snapshot Downloader."""

import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.logger import setup_logger


def main():
    """Main application entry point."""
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Cassandra Snapshot Downloader")

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Cassandra Snapshot Downloader")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start event loop
    try:
        exit_code = app.exec_()
        logger.info(f"Application exiting with code {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
