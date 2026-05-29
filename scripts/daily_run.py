#!/usr/bin/env python3
"""Daily production pipeline entry point.

Checks pending tasks, triggers agent workflows, generates reports.
Can be called from cron / systemd timer.
"""
import asyncio, json, sys, os
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))
os.environ.setdefault("ADMIN_PASSWORD", os.environ.get("ADMIN_PASSWORD", "daily_run"))


async def daily_pipeline():
    """Run the daily production pipeline."""
    from agents.ops_agent import OpsAgent
    ops = OpsAgent()

    print(f"=== 每日流程: {datetime.now().isoformat()} ===")

    # Step 1: Check for pending scripts to process
    print("\n[1/3] 检查待处理脚本...")
    try:
        import aiosqlite
        from web.database import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id, title FROM scripts WHERE status='draft' LIMIT 5"
            )
            pending = await cursor.fetchall()
            print(f"  待处理脚本: {len(pending)}")
    except Exception as e:
        print(f"  数据库检查跳过: {e}")

    # Step 2: Publish any approved videos
    print("\n[2/3] 检查待发布视频...")
    try:
        import aiosqlite
        from web.database import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT pq.id, pq.video_id, pq.platform, v.title
                   FROM publish_queue pq JOIN videos v ON pq.video_id = v.id
                   WHERE pq.status='pending' AND pq.scheduled_at <= datetime('now','localtime')
                   LIMIT 10"""
            )
            pending_pub = await cursor.fetchall()
            print(f"  待发布视频: {len(pending_pub)}")
    except Exception as e:
        print(f"  发布检查跳过: {e}")

    # Step 3: Collect analytics data
    print("\n[3/3] 采集数据...")
    data = await ops.collect_daily_data()
    print(f"  数据采集: {data.get('date', 'unknown')}")

    print(f"\n=== 每日流程完成 ===")


async def weekly_report():
    """Generate and save weekly report."""
    from agents.ops_agent import OpsAgent
    ops = OpsAgent()

    print("生成周报...")
    report = await ops.generate_weekly_report()

    output = PROJECT_DIR / "output" / f"weekly_report_{datetime.now().strftime('%Y%m%d')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"周报已保存: {output}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="攸县短视频每日自动流程")
    parser.add_argument("--weekly", action="store_true", help="生成周报")
    args = parser.parse_args()

    if args.weekly:
        asyncio.run(weekly_report())
    else:
        asyncio.run(daily_pipeline())
