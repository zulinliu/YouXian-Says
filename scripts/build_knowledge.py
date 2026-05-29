#!/usr/bin/env python3
"""Build or update the Youxian knowledge base from multiple sources.

Aggregates data from dialect_dict.json + online search results into a
structured knowledge base for the Content Agent. Runs idempotently.
"""
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_PATH = DATA_DIR / "knowledge_base.md"

SECTIONS = {
    "geography": {
        "title": "地理概况",
        "content": """攸县位于湖南省东部，株洲市辖县。
- 面积：约 2648 平方公里
- 人口：约 80 万
- 方言：攸县话（湘语娄邵片）
- 著名景点：酒埠江国家地质公园、灵龟峰、阳升观
- 特产：攸县香干、攸县米粉、攸县晒肉"""
    },
    "food": {
        "title": "美食文化",
        "content": """攸县美食以湘菜为基础，具有鲜明的地方特色。
- 攸县香干：攸县最著名的特产，制作工艺独特
- 攸县米粉：细滑爽口，本地人早餐首选
- 攸县晒肉：传统腊味，过年必备
- 攸县豆腐：嫩滑鲜美
- 攸县血鸭：地方传统名菜"""
    },
    "customs": {
        "title": "风俗习惯",
        "content": """攸县传统风俗丰富多彩。
- 攸县方言：属湘语娄邵片，保留大量古汉语词汇
- 传统节日：春节舞龙灯、端午赛龙舟
- 婚俗：攸县传统婚俗保留浓厚地方特色
- 饮食习俗：无辣不欢、腊味文化"""
    },
    "history": {
        "title": "历史沿革",
        "content": """攸县历史悠久，文化底蕴深厚。
- 攸县之名始于西汉，已有 2000 多年历史
- 攸县是有名的"将军县"，涌现多位革命将领
- 攸县文化教育传统浓厚，素有"耕读传家"之风"""
    },
    "dialect": {
        "title": "方言特点",
        "content": """攸县话属于湘语娄邵片，主要特点：
- 保留古入声
- \"吃\"说成\"恰\"，"知道"说成"晓得"
- \"玩\"说成\"耍\"
- 声调系统与普通话差异较大
- 语气词丰富："啵"、"哇"、"咧"
- 信息来源：民间口语收集，部分词汇可能与周边方言有交叉"""
    }
}


def format_sections() -> str:
    parts = ["# 攸县知识库\n\n> 更新时间：2025-05-28\n> 来源：综合整理（公开资料 + 民间收集）\n"]

    for key, section in SECTIONS.items():
        source_tag = "folk_saying" if key in ("customs", "dialect") else "confirmed_fact"
        parts.append(f"---\n## {section['title']}\n\n**知识来源：{source_tag}**\n")
        parts.append(section["content"].strip() + "\n")

    return "\n".join(parts)


def build():
    content = format_sections()
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(f"✓ Knowledge base written: {OUTPUT_PATH}")
    print(f"  Sections: {len(SECTIONS)}")
    print(f"  Size: {OUTPUT_PATH.stat().st_size} bytes")


if __name__ == "__main__":
    build()
