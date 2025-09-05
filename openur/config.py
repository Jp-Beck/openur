"""
Configuration management for OpenUR.
"""
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

class OpenURConfig:
    """Configuration manager for OpenUR."""

    DEFAULT_CONFIG = {
        'rtde': {
            'frequency': 125,
            'timeout': 10,
            'max_retries': 3
        },
        'dashboard': {
            'port': 29999,
            'timeout': 10,
            'max_retries': 3
        },
        'urscript': {
            'port': 30003,
            'timeout': 10,
            'max_retries': 3
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(levelname)s - %(message)s'
        }
    }

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_file: Path to configuration file (optional)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_file = config_file

        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)

    def load_from_file(self, config_file: str):
        """Load configuration from file."""
        try:
            import json
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                self._merge_config(file_config)
        except Exception as e:
            logging.warning(f"Failed to load config file {config_file}: {e}")

    def _merge_config(self, new_config: Dict[str, Any]):
        """Merge new configuration into existing config."""
        for section, values in new_config.items():
            if section in self.config and isinstance(values, dict):
                self.config[section].update(values)
            else:
                self.config[section] = values

    def get(self, section: str, key: str = None, default: Any = None):
        """Get configuration value."""
        if key is None:
            return self.config.get(section, default)
        return self.config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any):
        """Set configuration value."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def save_to_file(self, config_file: str):
        """Save configuration to file."""
        try:
            import json
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config file {config_file}: {e}")
            raise

def get_default_config_path() -> str:
    """Get default configuration file path."""
    home = Path.home()
    config_dir = home / '.openur'
    config_dir.mkdir(exist_ok=True)
    return str(config_dir / 'config.json')
