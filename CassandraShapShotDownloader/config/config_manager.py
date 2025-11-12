"""Configuration file manager for persisting settings."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import date


class ConfigManager:
    """Manages reading and writing configuration files."""

    def __init__(self):
        """Initialize configuration manager with config directory path."""
        self.config_dir = Path(__file__).parent
        self.db_config_file = self.config_dir / "db_connection.json"
        self.search_filters_file = self.config_dir / "search_filters.json"

    def save_db_connection(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        keyspace: str
    ) -> None:
        """Save database connection settings to config file.

        Args:
            host: Database host address
            port: Database port number
            username: Database username
            password: Database password (stored in plaintext)
            keyspace: Keyspace name
        """
        config = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "keyspace": keyspace
        }

        try:
            with open(self.db_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to save database connection config: {e}")

    def load_db_connection(self) -> Optional[Dict[str, Any]]:
        """Load database connection settings from config file.

        Returns:
            Dictionary with connection settings, or None if file doesn't exist
        """
        if not self.db_config_file.exists():
            return None

        try:
            with open(self.db_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load database connection config: {e}")

    def save_search_filters(
        self,
        start_date: date,
        end_date: date,
        equipment_id: str
    ) -> None:
        """Save search filter settings to config file.

        Args:
            start_date: Search start date
            end_date: Search end date
            equipment_id: Equipment ID filter
        """
        config = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "equipment_id": equipment_id
        }

        try:
            with open(self.search_filters_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to save search filters config: {e}")

    def load_search_filters(self) -> Optional[Dict[str, Any]]:
        """Load search filter settings from config file.

        Returns:
            Dictionary with filter settings, or None if file doesn't exist.
            Date strings are returned as-is (caller must parse them).
        """
        if not self.search_filters_file.exists():
            return None

        try:
            with open(self.search_filters_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load search filters config: {e}")
