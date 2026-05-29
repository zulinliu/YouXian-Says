"""Tests for image generation service."""
import pytest
from pathlib import Path

from services.image_gen import generate_image, IMAGE_PROVIDERS


@pytest.mark.asyncio
async def test_generate_image_returns_path(tmp_output_dir):
    """generate_image returns a valid output path."""
    output_path = str(tmp_output_dir / "test_img.png")
    result = await generate_image("攸县米粉", output_path, job_id="test")
    assert Path(result).exists()
    assert result == output_path


@pytest.mark.asyncio
async def test_image_provider_registry():
    """IMAGE_PROVIDERS has entries for required providers."""
    assert "gpt_image2_relay" in IMAGE_PROVIDERS
    assert "mock" in IMAGE_PROVIDERS
    assert callable(IMAGE_PROVIDERS["mock"])


@pytest.mark.asyncio
async def test_mock_mode(tmp_output_dir):
    """Mock mode creates a valid PNG file."""
    output_path = str(tmp_output_dir / "mock_img.png")
    result = await generate_image("test prompt", output_path, job_id="test")
    assert Path(result).exists()
    # Verify it's a PNG
    with open(result, "rb") as f:
        header = f.read(8)
    assert header[:4] == b"\x89PNG", "Output should be a valid PNG"
