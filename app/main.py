"""Configuration entry point for the job application automation project."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

if __package__:
    from .config import (
        DEFAULT_CONFIG_PATH,
        PROJECT_ROOT,
        ConfigurationError,
        boolean_setting,
        load_settings,
        platform_status,
        validate_settings,
    )
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from app.config import (
        DEFAULT_CONFIG_PATH,
        PROJECT_ROOT,
        ConfigurationError,
        boolean_setting,
        load_settings,
        platform_status,
        validate_settings,
    )


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
        configured_platforms = platform_status(settings)
        automation_enabled = boolean_setting(
            settings.get("automation", {}).get("enabled"), "automation.enabled"
        )
        approval_required = boolean_setting(
            settings.get("automation", {}).get("approval_required"),
            "automation.approval_required",
            True,
        )
    except ConfigurationError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2

    print("Configuration is valid.")
    print("Platforms:")
    print("\n".join(configured_platforms))
    print(f"Automation configured: {'yes' if automation_enabled else 'no'}")
    print(f"Application approval required: {'yes' if approval_required else 'no'}")
    print("Application submission is not implemented; no jobs were applied to.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
