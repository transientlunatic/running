"""
API configuration.

Configuration for the REST API including database path,
API keys, and deployment settings.
"""

import os
import secrets
from typing import Set


class APIConfig:
    """
    Configuration for the race results API.

    Attributes:
        DATABASE_PATH: Path to SQLite database file
        API_KEYS: Set of valid API keys for authentication
        CORS_ENABLED: Whether to enable CORS for cross-origin requests
        DEBUG: Debug mode (should be False in production)

    Example:
        >>> config = APIConfig()
        >>> config.API_KEYS = {'your-secret-api-key-here'}
        >>> app = create_app(config=config)
    """

    # Database configuration
    DATABASE_PATH: str = os.environ.get("RACE_DB_PATH", "race_results.db")

    # Authentication - API keys should be set via environment or config file
    # Multiple keys can be added to support different clients
    _api_keys_env = os.environ.get("RACE_API_KEYS", "")
    API_KEYS: Set[str] = (
        set(key.strip() for key in _api_keys_env.split(",") if key.strip())
        if _api_keys_env
        else set()
    )

    # CORS settings
    CORS_ENABLED: bool = os.environ.get("RACE_API_CORS", "true").lower() == "true"

    # Debug mode - should be False in production
    DEBUG: bool = os.environ.get("RACE_API_DEBUG", "false").lower() == "true"

    # Flask settings
    SECRET_KEY: str = os.environ.get("RACE_API_SECRET_KEY", "change-this-in-production")

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000

    # Security settings
    MAX_RESULTS_PER_REQUEST: int = 10000  # Maximum results to add in a single request

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Warn if using default SECRET_KEY
        if self.SECRET_KEY == "change-this-in-production" and not self.DEBUG:
            import warnings

            warnings.warn(
                "Using default SECRET_KEY in production mode! "
                "Set RACE_API_SECRET_KEY environment variable.",
                RuntimeWarning,
                stacklevel=2,
            )

    MAX_PAGE_SIZE: int = 1000

    @classmethod
    def from_env(cls) -> "APIConfig":
        """Create configuration from environment variables."""
        config = cls()
        config.__post_init__()
        return config

    @classmethod
    def from_file(cls, config_path: str) -> "APIConfig":
        """
        Load configuration from a file.

        Args:
            config_path: Path to configuration file (Python module)

        Returns:
            APIConfig instance

        Raises:
            ValueError: If config_path is invalid or outside allowed directories

        Security Warning:
            This method executes arbitrary Python code from the config file.
            Only use this with trusted configuration files in controlled environments.
        """
        config = cls()

        if not os.path.exists(config_path):
            config.__post_init__()
            return config

        # Security: Validate config path to prevent path traversal attacks
        # Use realpath to resolve symlinks and .. components
        abs_config_path = os.path.realpath(config_path)

        # Ensure the config file has a .py extension
        if not abs_config_path.endswith(".py"):
            raise ValueError("Config file must have .py extension")

        # Ensure the resolved path stays within the allowed base directory
        # Restrict to the current working directory and its subdirectories
        allowed_base_dir = os.path.realpath(os.getcwd())
        try:
            # Check if the config file is within the allowed directory
            if (
                os.path.commonpath([allowed_base_dir, abs_config_path])
                != allowed_base_dir
            ):
                raise ValueError(
                    "Config path must be within the current working directory"
                )
        except ValueError:
            # commonpath raises ValueError if paths are on different drives (Windows)
            raise ValueError("Config path must be within the current working directory")

        # Load config file as Python module
        import importlib.util

        spec = importlib.util.spec_from_file_location("config", abs_config_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Update config from module - only uppercase attributes
            for key in dir(module):
                if key.isupper() and hasattr(config, key):
                    setattr(config, key, getattr(module, key))

        config.__post_init__()
        return config

    def add_api_key(self, key: str) -> None:
        """Add an API key to the valid keys set."""
        self.API_KEYS.add(key)

    def remove_api_key(self, key: str) -> None:
        """Remove an API key from the valid keys set."""
        self.API_KEYS.discard(key)

    def is_valid_api_key(self, key: str) -> bool:
        """
        Check if an API key is valid using timing-safe comparison.

        Args:
            key: API key to validate

        Returns:
            True if the key is valid, False otherwise
        """
        if not self.API_KEYS:
            return False

        # Use timing-safe comparison to prevent timing attacks
        for valid_key in self.API_KEYS:
            if secrets.compare_digest(key, valid_key):
                return True
        return False
