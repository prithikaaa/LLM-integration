"""Load and validate application settings."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"
ENVIRONMENT_VARIABLE = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")


class ConfigurationError(ValueError):
    """Raised when application settings are missing or invalid."""


def expand_environment_variables(value: Any) -> Any:
    """Recursively expand ${NAME:default} placeholders in settings values."""
    if isinstance(value, dict):
        return {key: expand_environment_variables(item) for key, item in value.items()}
    if isinstance(value, list):
        return [expand_environment_variables(item) for item in value]
    if isinstance(value, str):
        return ENVIRONMENT_VARIABLE.sub(
            lambda match: os.environ.get(match.group(1), match.group(2) or ""),
            value,
        )
    return value


def load_settings(config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load YAML settings and expand environment-variable placeholders."""
    if not config_path.is_file():
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            settings = yaml.safe_load(config_file)
    except yaml.YAMLError as error:
        raise ConfigurationError(f"Invalid YAML in {config_path}: {error}") from error

    if not isinstance(settings, dict):
        raise ConfigurationError("The configuration root must be a YAML mapping.")

    return expand_environment_variables(settings)


def _mapping_section(settings: dict[str, Any], name: str) -> dict[str, Any]:
    section = settings.get(name, {})
    if not isinstance(section, dict):
        raise ConfigurationError(f"{name} must be a YAML mapping.")
    return section


def integer_setting(settings: dict[str, Any], path: tuple[str, ...], default: int) -> int:
    """Read an integer setting by dotted path, using default when it is absent."""
    value: Any = settings
    for key in path:
        if not isinstance(value, dict):
            value = None
            break
        value = value.get(key)

    if value is None:
        return default
    if isinstance(value, bool):
        raise ConfigurationError(f"{'.'.join(path)} must be an integer.")
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise ConfigurationError(f"{'.'.join(path)} must be an integer.") from error


def boolean_setting(value: Any, name: str, default: bool = False) -> bool:
    """Parse a boolean setting without treating arbitrary strings as true."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    raise ConfigurationError(f"{name} must be a boolean value.")


def validate_settings(settings: dict[str, Any]) -> None:
    """Validate matching, automation, and platform settings."""
    matching = _mapping_section(settings, "matching")
    automation = _mapping_section(settings, "automation")
    platforms = _mapping_section(settings, "platforms")

    minimum_score = integer_setting(
        {"matching": matching}, ("matching", "minimum_score"), 70
    )
    if not 0 <= minimum_score <= 100:
        raise ConfigurationError("matching.minimum_score must be between 0 and 100.")

    check_interval = integer_setting(
        {"automation": automation}, ("automation", "check_interval_minutes"), 30
    )
    if check_interval < 1:
        raise ConfigurationError("automation.check_interval_minutes must be at least 1.")

    application_limit = integer_setting(
        {"automation": automation}, ("automation", "max_applications_per_day"), 10
    )
    if application_limit < 1:
        raise ConfigurationError("automation.max_applications_per_day must be at least 1.")

    delay = integer_setting(
        {"automation": automation},
        ("automation", "delay_between_applications_seconds"),
        60,
    )
    if delay < 0:
        raise ConfigurationError(
            "automation.delay_between_applications_seconds cannot be negative."
        )

    boolean_setting(automation.get("enabled"), "automation.enabled")
    boolean_setting(automation.get("approval_required"), "automation.approval_required", True)

    for name in ("linkedin", "naukri"):
        platform = platforms.get(name, {})
        if not isinstance(platform, dict):
            raise ConfigurationError(f"platforms.{name} must be a YAML mapping.")
        boolean_setting(platform.get("enabled"), f"platforms.{name}.enabled")


def platform_status(settings: dict[str, Any]) -> list[str]:
    """Return platform readiness without exposing credential values."""
    platforms = _mapping_section(settings, "platforms")
    status = []
    for name in ("linkedin", "naukri"):
        platform = platforms.get(name, {})
        if not isinstance(platform, dict):
            raise ConfigurationError(f"platforms.{name} must be a YAML mapping.")

        enabled = boolean_setting(platform.get("enabled"), f"platforms.{name}.enabled")
        credentials_present = bool(platform.get("email") and platform.get("password"))
        if not enabled:
            state = "disabled"
        elif credentials_present:
            state = "enabled; credentials configured"
        else:
            state = "enabled; credentials missing"
        status.append(f"- {name.capitalize()}: {state}")
    return status