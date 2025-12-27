"""
API configuration.

Configuration for the REST API including database path,
API keys, and deployment settings.
"""

import os
from typing import Set, Optional
from pathlib import Path


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
    DATABASE_PATH: str = os.environ.get(
        'RACE_DB_PATH',
        'race_results.db'
    )
    
    # Authentication - API keys should be set via environment or config file
    # Multiple keys can be added to support different clients
    API_KEYS: Set[str] = set(os.environ.get('RACE_API_KEYS', '').split(',')) if os.environ.get('RACE_API_KEYS') else set()
    
    # CORS settings
    CORS_ENABLED: bool = os.environ.get('RACE_API_CORS', 'true').lower() == 'true'
    
    # Debug mode - should be False in production
    DEBUG: bool = os.environ.get('RACE_API_DEBUG', 'false').lower() == 'true'
    
    # Flask settings
    SECRET_KEY: str = os.environ.get('RACE_API_SECRET_KEY', 'change-this-in-production')
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000
    
    @classmethod
    def from_env(cls) -> 'APIConfig':
        """Create configuration from environment variables."""
        return cls()
    
    @classmethod
    def from_file(cls, config_path: str) -> 'APIConfig':
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to configuration file (Python module)
            
        Returns:
            APIConfig instance
        """
        config = cls()
        
        if not os.path.exists(config_path):
            return config
        
        # Load config file as Python module
        import importlib.util
        spec = importlib.util.spec_from_file_location("config", config_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Update config from module
            for key in dir(module):
                if key.isupper() and hasattr(config, key):
                    setattr(config, key, getattr(module, key))
        
        return config
    
    def add_api_key(self, key: str) -> None:
        """Add an API key to the valid keys set."""
        self.API_KEYS.add(key)
    
    def remove_api_key(self, key: str) -> None:
        """Remove an API key from the valid keys set."""
        self.API_KEYS.discard(key)
    
    def is_valid_api_key(self, key: str) -> bool:
        """Check if an API key is valid."""
        return key in self.API_KEYS
