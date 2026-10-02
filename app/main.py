"""Configuration entry point for the job application automation project."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"
ENVIRONMENT_VARIABLE = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")


class ConfigurationError(ValueError):
    """Raised when the application configuration is missing or invalid."""


def _expand_environment_variables(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _expand_environment_variables(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_environment_variables(item) for item in value]
    if isinstance(value, str):
        return ENVIRONMENT_VARIABLE.sub(
            lambda match: os.environ.get(match.group(1), match.group(2) or ""),
            value,
        )
    return value


def load_settings(config_path: Path) -> dict[str, Any]:
    """Load YAML settings and expand ${NAME:default} environment placeholders."""
    if not config_path.is_file():
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            settings = yaml.safe_load(config_file)
    except yaml.YAMLError as error:
        raise ConfigurationError(f"Invalid YAML in {config_path}: {error}") from error

    if not isinstance(settings, dict):
        raise ConfigurationError("The configuration root must be a YAML mapping.")

    return _expand_environment_variables(settings)


def _integer_setting(settings: dict[str, Any], path: tuple[str, ...], default: int) -> int:
    value: Any = settings
    for key in path:
        if not isinstance(value, dict):
            value = None
            break
        value = value.get(key)

    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError) as error:
        name = ".".join(path)
        raise ConfigurationError(f"{name} must be an integer.") from error


def _boolean_setting(value: Any, name: str, default: bool = False) -> bool:
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
    """Validate settings that control matching and automation frequency."""
    minimum_score = _integer_setting(settings, ("matching", "minimum_score"), 70)
    if not 0 <= minimum_score <= 100:
        raise ConfigurationError("matching.minimum_score must be between 0 and 100.")

    check_interval = _integer_setting(
        settings, ("automation", "check_interval_minutes"), 30
    )
    if check_interval < 1:
        raise ConfigurationError("automation.check_interval_minutes must be at least 1.")

    application_limit = _integer_setting(
        settings, ("automation", "max_applications_per_day"), 10
    )
    if application_limit < 1:
        raise ConfigurationError("automation.max_applications_per_day must be at least 1.")

    delay = _integer_setting(
        settings, ("automation", "delay_between_applications_seconds"), 60
    )
    if delay < 0:
        raise ConfigurationError(
            "automation.delay_between_applications_seconds cannot be negative."
        )

    automation = settings.get("automation", {})
    if not isinstance(automation, dict):
        raise ConfigurationError("automation must be a YAML mapping.")
    _boolean_setting(automation.get("enabled"), "automation.enabled")
    _boolean_setting(automation.get("approval_required"), "automation.approval_required", True)


def _platform_status(settings: dict[str, Any]) -> list[str]:
    platforms = settings.get("platforms", {})
    if not isinstance(platforms, dict):
        raise ConfigurationError("platforms must be a YAML mapping.")

    status = []
    for name in ("linkedin", "naukri"):
        platform = platforms.get(name, {})
        if not isinstance(platform, dict):
            raise ConfigurationError(f"platforms.{name} must be a YAML mapping.")
        enabled = _boolean_setting(platform.get("enabled"), f"platforms.{name}.enabled")
        credentials_present = bool(platform.get("email") and platform.get("password"))
        if not enabled:
            state = "disabled"
        elif credentials_present:
            state = "enabled; credentials configured"
        else:
            state = "enabled; credentials missing"
        status.append(f"- {name.capitalize()}: {state}")
    return status


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load and validate job automation settings safely."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"settings YAML path (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="validate settings and report platform readiness",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    load_dotenv(PROJECT_ROOT / ".env")

    try:
        settings = load_settings(args.config)
        validate_settings(settings)
        platform_status = _platform_status(settings)
        automation_enabled = _boolean_setting(
            settings.get("automation", {}).get("enabled"), "automation.enabled"
        )
        approval_required = _boolean_setting(
            settings.get("automation", {}).get("approval_required"),
            "automation.approval_required",
            True,
        )
    except ConfigurationError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2

    print("Configuration is valid.")
    print("Platforms:")
    print("\n".join(platform_status))
    print(f"Automation configured: {'yes' if automation_enabled else 'no'}")
    print(f"Application approval required: {'yes' if approval_required else 'no'}")
    print("Application submission is not implemented; no jobs were applied to.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())