#!/usr/bin/env python3
"""
Configuration Loader for Project Prometheus
============================================

Loads configuration from config.yaml with support for:
- Environment variable overrides
- Default values
- Path resolution
- Config validation

Usage:
    from config_loader import get_config, Config

    # Simple usage
    config = get_config()
    api_key = config.get('api.anthropic.key')
    timeout = config.get('api.semantic_scholar.timeout', default=30)

    # Typed access
    model = config.get_str('api.anthropic.default_model')
    max_tokens = config.get_int('api.anthropic.max_tokens')
    enabled = config.get_bool('features.rich_display')
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Try to import yaml, provide helpful error if not available
try:
    import yaml
except ImportError:
    yaml = None


class ConfigError(Exception):
    """Configuration error."""
    pass


class Config:
    """Configuration manager with environment variable override support."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration.

        Args:
            config_path: Path to config.yaml file. If None, searches default locations.
        """
        self._config_path = self._find_config_path(config_path)
        self._config: Dict[str, Any] = {}
        self._loaded = False

    def _find_config_path(self, config_path: Optional[Path]) -> Path:
        """Find configuration file path.

        Args:
            config_path: Explicitly provided path or None.

        Returns:
            Path to config.yaml.

        Raises:
            ConfigError: If config file cannot be found.
        """
        if config_path:
            if config_path.exists():
                return config_path
            raise ConfigError(f"Config file not found: {config_path}")

        # Search for config.yaml in common locations
        search_paths = [
            Path.cwd() / "config.yaml",
            Path(__file__).parent.parent / "config.yaml",
            Path(__file__).parent / "config.yaml",
        ]

        for path in search_paths:
            if path.exists():
                return path

        # Return default path even if it doesn't exist (will use defaults)
        return Path.cwd() / "config.yaml"

    def _expand_env_vars(self, value: Any) -> Any:
        """Expand environment variables in a value.

        Supports format: ${ENV_VAR:default_value}

        Args:
            value: Value to expand.

        Returns:
            Expanded value with environment variables resolved.
        """
        if isinstance(value, str):
            # Match ${VAR} or ${VAR:default}
            pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'

            def replace_var(match):
                var_name = match.group(1)
                default = match.group(2) if match.group(2) is not None else ''
                return os.environ.get(var_name, default)

            return re.sub(pattern, replace_var, value)

        elif isinstance(value, dict):
            return {k: self._expand_env_vars(v) for k, v in value.items()}

        elif isinstance(value, list):
            return [self._expand_env_vars(item) for item in value]

        return value

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration.

        Format: PROMETHEUS_<SECTION>_<SUBSECTION>_<KEY>
        Example: PROMETHEUS_API_ANTHROPIC_KEY overrides api.anthropic.key

        Args:
            config: Configuration dictionary.

        Returns:
            Configuration with overrides applied.
        """
        prefix = "PROMETHEUS_"

        for env_key, env_value in os.environ.items():
            if not env_key.startswith(prefix):
                continue

            # Parse the key path
            key_path = env_key[len(prefix):].lower().split('_')

            if len(key_path) < 2:
                continue

            # Navigate to the target location
            current = config
            for key in key_path[:-1]:
                if key not in current:
                    current[key] = {}
                elif not isinstance(current[key], dict):
                    current[key] = {}
                current = current[key]

            # Set the value (try to parse as JSON for complex types)
            final_key = key_path[-1]
            current[final_key] = self._parse_env_value(env_value)

        return config

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type.

        Args:
            value: String value from environment.

        Returns:
            Parsed value (bool, int, float, list, or str).
        """
        # Boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # None/null
        if value.lower() in ('null', 'none', ''):
            return None

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Float
        try:
            return float(value)
        except ValueError:
            pass

        # List (comma-separated)
        if ',' in value and not value.startswith('['):
            return [item.strip() for item in value.split(',')]

        return value

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values.

        Returns:
            Default configuration dictionary.
        """
        return {
            "api": {
                "anthropic": {
                    "key": "",
                    "key_file": "~/.prometheus/anthropic_key.txt",
                    "default_model": "claude-sonnet-4-20250514",
                    "max_tokens": 4096,
                    "temperature": 0.7,
                },
                "semantic_scholar": {
                    "key": "",
                    "base_url": "https://api.semanticscholar.org/graph/v1",
                    "timeout": 30,
                    "rate_limit": 5,
                },
                "arxiv": {
                    "base_url": "http://export.arxiv.org/api/query",
                    "timeout": 30,
                    "rate_limit_delay": 3,
                    "max_results": 100,
                },
            },
            "paths": {
                "base_dir": ".",
                "core_dir": "Core",
                "prompts_dir": "Core/prompts",
                "tools_dir": "Core/tools",
                "projects_dir": "Projects",
                "logs_dir": "Logs",
                "checkpoints_dir": "Checkpoints",
                "communication_dir": "Communication",
                "inbox_dir": "Communication/inbox",
                "outbox_dir": "Communication/outbox",
            },
            "logging": {
                "level": "INFO",
                "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                "date_format": "%Y-%m-%d %H:%M:%S",
            },
            "features": {
                "rich_display": True,
                "interactive_selection": True,
                "verbose": False,
            },
            "defaults": {
                "project": {
                    "domain": "机器学习",
                    "language": "zh-CN",
                },
                "task": {
                    "max_attempts": 3,
                    "retry_delay": 5,
                },
            },
        }

    def load(self, reload: bool = False) -> Dict[str, Any]:
        """Load configuration from file.

        Args:
            reload: Force reload even if already loaded.

        Returns:
            Configuration dictionary.
        """
        if self._loaded and not reload:
            return self._config

        # Start with defaults
        config = self._get_default_config()

        # Load from file if exists
        if self._config_path.exists():
            if yaml is None:
                raise ConfigError(
                    "PyYAML is required to load config.yaml. "
                    "Install it with: pip install pyyaml"
                )

            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}

                # Deep merge with defaults
                config = self._deep_merge(config, file_config)
            except yaml.YAMLError as e:
                raise ConfigError(f"Error parsing config.yaml: {e}")
            except IOError as e:
                raise ConfigError(f"Error reading config.yaml: {e}")

        # Expand environment variables in config
        config = self._expand_env_vars(config)

        # Apply environment variable overrides
        config = self._apply_env_overrides(config)

        self._config = config
        self._loaded = True

        return self._config

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary.
            override: Override dictionary.

        Returns:
            Merged dictionary.
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get(
        self,
        key: str,
        default: Any = None,
        use_env: bool = True
    ) -> Any:
        """Get configuration value by dot-notation key.

        Args:
            key: Configuration key (e.g., "api.anthropic.key").
            default: Default value if key not found.
            use_env: Also check environment variables.

        Returns:
            Configuration value or default.
        """
        self.load()

        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Try environment variable
                if use_env:
                    env_key = 'PROMETHEUS_' + '_'.join(keys).upper()
                    env_value = os.environ.get(env_key)
                    if env_value is not None:
                        return self._parse_env_value(env_value)

                return default

        return value

    def get_str(self, key: str, default: str = "") -> str:
        """Get string configuration value.

        Args:
            key: Configuration key.
            default: Default value.

        Returns:
            String value.
        """
        value = self.get(key, default)
        return str(value) if value is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value.

        Args:
            key: Configuration key.
            default: Default value.

        Returns:
            Integer value.
        """
        value = self.get(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value.

        Args:
            key: Configuration key.
            default: Default value.

        Returns:
            Float value.
        """
        value = self.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value.

        Args:
            key: Configuration key.
            default: Default value.

        Returns:
            Boolean value.
        """
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1')
        return bool(value)

    def get_list(self, key: str, default: Optional[List] = None) -> List:
        """Get list configuration value.

        Args:
            key: Configuration key.
            default: Default value.

        Returns:
            List value.
        """
        if default is None:
            default = []
        value = self.get(key, default)
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [item.strip() for item in value.split(',')]
        return default

    def get_path(self, key: str, default: Optional[str] = None) -> Path:
        """Get path configuration value, resolved relative to base_dir.

        Args:
            key: Configuration key.
            default: Default value.

        Returns:
            Resolved Path object.
        """
        path_str = self.get_str(key, default or ".")
        base_dir = self.get_path('paths.base_dir', '.')

        path = Path(path_str)
        if not path.is_absolute():
            path = base_dir / path

        return path.resolve()

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section.

        Args:
            section: Section name (e.g., "api.anthropic").

        Returns:
            Section dictionary or empty dict if not found.
        """
        self.load()

        keys = section.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return {}

        return value if isinstance(value, dict) else {}

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value (in memory only).

        Args:
            key: Configuration key.
            value: Value to set.
        """
        self.load()

        keys = key.split('.')
        current = self._config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def save(self) -> None:
        """Save current configuration to file.

        Raises:
            ConfigError: If yaml is not available or save fails.
        """
        if yaml is None:
            raise ConfigError(
                "PyYAML is required to save config.yaml. "
                "Install it with: pip install pyyaml"
            )

        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        except IOError as e:
            raise ConfigError(f"Error saving config.yaml: {e}")

    @property
    def config_path(self) -> Path:
        """Get configuration file path."""
        return self._config_path

    def __repr__(self) -> str:
        return f"Config(path={self._config_path}, loaded={self._loaded})"


# Global config instance
_config_instance: Optional[Config] = None


def get_config(config_path: Optional[Path] = None, reload: bool = False) -> Config:
    """Get global configuration instance.

    Args:
        config_path: Optional path to config file.
        reload: Force reload configuration.

    Returns:
        Config instance.
    """
    global _config_instance

    if _config_instance is None or reload:
        _config_instance = Config(config_path)
        _config_instance.load()

    return _config_instance


def reset_config() -> None:
    """Reset global configuration instance."""
    global _config_instance
    _config_instance = None


# Convenience functions
def get(key: str, default: Any = None) -> Any:
    """Get configuration value."""
    return get_config().get(key, default)


def get_str(key: str, default: str = "") -> str:
    """Get string configuration value."""
    return get_config().get_str(key, default)


def get_int(key: str, default: int = 0) -> int:
    """Get integer configuration value."""
    return get_config().get_int(key, default)


def get_bool(key: str, default: bool = False) -> bool:
    """Get boolean configuration value."""
    return get_config().get_bool(key, default)


# CLI test
if __name__ == "__main__":
    print("Configuration Loader Test")
    print("=" * 40)

    config = get_config()

    print(f"Config path: {config.config_path}")
    print(f"Loaded: {config._loaded}")
    print()

    # Test various config values
    test_keys = [
        "api.anthropic.default_model",
        "api.anthropic.max_tokens",
        "api.semantic_scholar.timeout",
        "paths.logs_dir",
        "logging.level",
        "features.rich_display",
    ]

    for key in test_keys:
        value = config.get(key)
        print(f"  {key}: {value}")

    print()
    print("Path resolution test:")
    print(f"  logs_dir: {config.get_path('paths.logs_dir')}")
    print(f"  prompts_dir: {config.get_path('paths.prompts_dir')}")
