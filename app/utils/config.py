"""Configuration utilities for Gate Quote Pro."""
import os
from pathlib import Path


def get_app_data_dir() -> Path:
    """Get the application data directory."""
    app_dir = Path.home() / "Library" / "Application Support" / "GateQuotePro"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_resources_dir() -> Path:
    """Get the resources directory."""
    # Check if running from app bundle
    if hasattr(__file__, '__file__'):
        bundle_resources = Path(__file__).parent.parent.parent / "resources"
        if bundle_resources.exists():
            return bundle_resources

    # Check relative to home
    home_resources = Path.home() / "GateQuotePro" / "resources"
    if home_resources.exists():
        return home_resources

    # Create in app data dir
    resources = get_app_data_dir() / "resources"
    resources.mkdir(exist_ok=True)
    return resources


def get_default_prices_path() -> str:
    """Get path to default prices JSON file."""
    return str(get_resources_dir() / "default_prices.json")
