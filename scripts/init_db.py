#!/usr/bin/env python3
"""Initialize the YouXian Says database with all required tables."""

import os
import sqlite3

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "youxian.db",
)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'idea',
    topic_id INTEGER,
    script_id INTEGER,
    storyboard_id INTEGER,
    dialect_dictionary TEXT,
    fact_risk_level TEXT DEFAULT 'confirmed_fact',
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (topic_id) REFERENCES topics(id),
    FOREIGN KEY (script_id) REFERENCES scripts(id),
    FOREIGN KEY (storyboard_id) REFERENCES storyboards(id)
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    pillar TEXT,
    source TEXT DEFAULT 'user',
    status TEXT DEFAULT 'draft',
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

CREATE TABLE IF NOT EXISTS scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    title TEXT,
    dialect_words TEXT,
    status TEXT DEFAULT 'draft',
    fact_check_notes TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

CREATE TABLE IF NOT EXISTS storyboards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    shots TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

CREATE TABLE IF NOT EXISTS model_call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    model_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    channel TEXT NOT NULL,
    prompt_version TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    cost_estimate REAL DEFAULT 0,
    success INTEGER DEFAULT 0,
    error_message TEXT,
    quality_score REAL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS publish_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    scheduled_at TEXT,
    published_at TEXT,
    platform_post_id TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

CREATE TABLE IF NOT EXISTS analytics_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    date TEXT NOT NULL,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    followers INTEGER DEFAULT 0,
    collected_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

CREATE TABLE IF NOT EXISTS dialect_fixes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_text TEXT NOT NULL,
    fixed_text TEXT NOT NULL,
    context TEXT,
    source TEXT DEFAULT 'user_review',
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);
"""


def init_database():
    """Create all tables, set WAL mode, and verify."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript(SCHEMA_SQL)
    conn.commit()

    # Verify WAL mode
    wal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    conn.close()

    print(f"Database initialized at {DB_PATH}")
    print(f"Journal mode: {wal_mode}")

    # Count tables
    v = sqlite3.connect(DB_PATH)
    tables = v.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    v.close()
    print(
        f"Tables created ({len(tables)}): {', '.join(t[0] for t in tables)}"
    )


if __name__ == "__main__":
    init_database()
