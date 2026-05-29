"""Data package — loads dialect dictionary and knowledge base."""
import json
import os

_data_dir = os.path.dirname(os.path.abspath(__file__))

# Load dialect dictionary
_dict_path = os.path.join(_data_dir, "dialect_dict.json")
DIALECT_DICT = []
if os.path.exists(_dict_path):
    with open(_dict_path) as f:
        raw = json.load(f)
        for cat, entries in raw.items():
            if isinstance(entries, list):
                DIALECT_DICT.extend(entries)

# Load knowledge base
_kb_path = os.path.join(_data_dir, "knowledge_base.md")
KNOWLEDGE_BASE = ""
if os.path.exists(_kb_path):
    with open(_kb_path) as f:
        KNOWLEDGE_BASE = f.read()
