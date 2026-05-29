"""Tests for data files (dialect_dict.json, knowledge_base.md)."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def test_dialect_dict_exists():
    """dialect_dict.json exists and is valid JSON."""
    file_path = PROJECT_ROOT / "data" / "dialect_dict.json"
    assert file_path.exists(), "dialect_dict.json does not exist"
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict), "dialect_dict.json must be a JSON object"


def test_dialect_dict_schema():
    """dialect_dict.json has correct schema with version, updated, and words keys."""
    with open(PROJECT_ROOT / "data" / "dialect_dict.json", encoding="utf-8") as f:
        data = json.load(f)
    assert "version" in data, "Missing 'version' key"
    assert "updated" in data, "Missing 'updated' key"
    assert "words" in data, "Missing 'words' key"
    assert isinstance(data["words"], list), "'words' must be an array"

    for entry in data["words"]:
        assert "word" in entry, f"Entry missing 'word': {entry}"
        assert "meaning" in entry, f"Entry missing 'meaning': {entry}"
        assert "example" in entry, f"Entry missing 'example': {entry}"
        assert "category" in entry, f"Entry missing 'category': {entry}"


def test_dialect_dict_min_entries():
    """dialect_dict.json has at least 20 entries."""
    with open(PROJECT_ROOT / "data" / "dialect_dict.json", encoding="utf-8") as f:
        data = json.load(f)
    count = len(data["words"])
    assert count >= 20, f"Expected at least 20 entries, got {count}"


def test_knowledge_base_exists():
    """knowledge_base.md exists."""
    file_path = PROJECT_ROOT / "data" / "knowledge_base.md"
    assert file_path.exists(), "knowledge_base.md does not exist"


def test_knowledge_base_sections():
    """knowledge_base.md contains at least 4 section headings."""
    with open(PROJECT_ROOT / "data" / "knowledge_base.md", encoding="utf-8") as f:
        content = f.read()
    sections = [line for line in content.split("\n") if line.startswith("## ")]
    assert len(sections) >= 4, f"Expected at least 4 sections, got {len(sections)}: {sections}"


def test_knowledge_base_min_length():
    """knowledge_base.md has at least 50 lines."""
    with open(PROJECT_ROOT / "data" / "knowledge_base.md", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) >= 50, f"Expected at least 50 lines, got {len(lines)}"
