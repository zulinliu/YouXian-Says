"""Async SQLite database connection with WAL mode."""
import os

import aiosqlite

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "youxian.db",
)


async def get_async_db():
    """Async generator providing per-request database connections.

    Yields aiosqlite.Connection with WAL mode, busy_timeout, and foreign_keys enabled.
    Use as FastAPI dependency: Depends(get_async_db)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA busy_timeout=5000")
        await db.execute("PRAGMA foreign_keys=ON")
        db.row_factory = aiosqlite.Row
        yield db


async def get_db_connection():
    """Get a direct async connection for scripts."""
    import aiosqlite

    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA busy_timeout=5000")
    await db.execute("PRAGMA foreign_keys=ON")
    db.row_factory = aiosqlite.Row
    return db
