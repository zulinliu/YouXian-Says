"""Shared fixtures for agent tests."""
import pytest


@pytest.fixture
def mock_dialect_dict():
    return [
        {"mandarin": "好吃", "dialect": "好恰"},
        {"mandarin": "知道", "dialect": "晓得"},
    ]


@pytest.fixture
def sample_topic():
    return {
        "title": "攸县米粉为什么这么出名",
        "pillar": "美食",
        "difficulty": 3,
        "heat_prediction": 4,
    }


@pytest.fixture
def sample_script():
    return {
        "title": "攸县米粉探秘",
        "duration": 45,
        "sections": [
            {"hook": "晓得啵？攸县米粉出了攸县就变味了！"},
            {
                "content": "攸县米粉的历史可以追溯到...",
                "dialect_words": ["好恰", "晓得"],
            },
        ],
        "platform_focus": "douyin",
    }
