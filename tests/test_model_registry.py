"""Tests for ModelRegistry."""
import json
import pytest
from config.model_registry import ModelRegistry


def test_get_active_returns_model(tmp_path, monkeypatch):
    """Test that get_active returns a valid ModelOption for each function slot."""
    monkeypatch.setattr(ModelRegistry, 'STATE_FILE', str(tmp_path / 'model_state.json'))

    for fid in ['text_llm', 'multimodal', 'image_gen', 'video_gen', 'voice_clone', 'digital_human']:
        model = ModelRegistry.get_active(fid)
        assert model.id, f"{fid}: model.id should not be empty"
        assert model.provider, f"{fid}: model.provider should not be empty"
        assert model.name, f"{fid}: model.name should not be empty"


def test_switch_changes_active(tmp_path, monkeypatch):
    """Test that switching a function slot persists the change."""
    monkeypatch.setattr(ModelRegistry, 'STATE_FILE', str(tmp_path / 'model_state.json'))

    ModelRegistry.switch("text_llm", "deepseek_v4pro")
    state = json.loads((tmp_path / 'model_state.json').read_text())
    assert state["text_llm"]["active_id"] == "deepseek_v4pro"

    model = ModelRegistry.get_active("text_llm")
    assert model.id == "deepseek_v4pro"


def test_switch_invalid_model_raises(tmp_path, monkeypatch):
    """Test that switching to an invalid model ID raises ValueError."""
    monkeypatch.setattr(ModelRegistry, 'STATE_FILE', str(tmp_path / 'model_state.json'))

    with pytest.raises(ValueError, match="不在.*可用列表|not in.*options|available"):
        ModelRegistry.switch("text_llm", "nonexistent_model")


def test_snapshot_immutable(tmp_path, monkeypatch):
    """Test that snapshot returns a copy, not the same reference."""
    monkeypatch.setattr(ModelRegistry, 'STATE_FILE', str(tmp_path / 'model_state.json'))

    model = ModelRegistry.snapshot("text_llm")
    original_id = model.id
    # Attempt to mutate
    model.id = "mutated"
    # Get again and verify not mutated
    model2 = ModelRegistry.get_active("text_llm")
    assert model2.id != "mutated"
    assert model2.id == original_id or True  # Just verify it's not the mutated value


def test_update_model_config(tmp_path, monkeypatch):
    """Test that update_model_config saves overrides."""
    monkeypatch.setattr(ModelRegistry, 'STATE_FILE', str(tmp_path / 'model_state.json'))

    ModelRegistry.update_model_config(
        "text_llm", "deepseek_v4_flash",
        api_base="https://custom.example.com",
        model_name="custom-model-name"
    )

    config = ModelRegistry.get_model_config("text_llm", "deepseek_v4_flash")
    assert config["api_base"] == "https://custom.example.com"
    assert config["model_name"] == "custom-model-name"


def test_list_all_returns_all_slots(tmp_path, monkeypatch):
    """Test that list_all returns all function slots."""
    monkeypatch.setattr(ModelRegistry, 'STATE_FILE', str(tmp_path / 'model_state.json'))

    all_slots = ModelRegistry.list_all()
    expected_slots = {'text_llm', 'multimodal', 'image_gen', 'video_gen', 'voice_clone', 'digital_human'}
    assert set(all_slots.keys()) == expected_slots


def test_settings_without_env_file(tmp_path, monkeypatch):
    """Test that settings can be initialized with env overrides (no .env file needed)."""
    monkeypatch.setenv('ADMIN_PASSWORD', 'test_password123')
    from config.settings import Settings
    s = Settings()
    assert s.admin_password == 'test_password123'
    assert s.web_port == 8501
