"""Shared fixtures for YouXian Says tests."""
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def branding_dir() -> Path:
    return PROJECT_ROOT / "templates" / "branding"


@pytest.fixture
def composer_output_dir(tmp_path) -> Path:
    return tmp_path / "output"
