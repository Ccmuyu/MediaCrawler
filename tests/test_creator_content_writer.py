# -*- coding: utf-8 -*-
"""创作者模式的作品按 sec_uid 写成一份 JSONL，同一作品只留最新一条。"""

from __future__ import annotations

import asyncio
import json

import config
from tools.async_file_writer import AsyncFileWriter


def test_creator_contents_upsert_by_sec_uid(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SAVE_DATA_PATH", str(tmp_path))
    writer = AsyncFileWriter(platform="douyin", crawler_type="creator")
    asyncio.run(writer.write_single_item_to_json(
        {"aweme_id": "1", "sec_uid": "MS4w", "title": "旧", "creator_hash": "abc", "create_time": 1763222400},
        "contents",
    ))
    asyncio.run(writer.write_to_jsonl(
        {"aweme_id": "1", "sec_uid": "MS4w", "title": "新", "create_time": 1763222400},
        "contents",
    ))
    asyncio.run(writer.write_single_item_to_json(
        {"aweme_id": "2", "sec_uid": "MS4w", "title": "另一条", "create_time": 1765814400},
        "contents",
    ))

    folder = tmp_path / "douyin" / "creator" / "MS4w"
    november = [json.loads(line) for line in (folder / "contents_2025-11.jsonl").read_text(encoding="utf-8").splitlines()]
    december = [json.loads(line) for line in (folder / "contents_2025-12.jsonl").read_text(encoding="utf-8").splitlines()]
    assert november == [{"aweme_id": "1", "sec_uid": "MS4w", "title": "新", "create_time": 1763222400}]
    assert december == [{"aweme_id": "2", "sec_uid": "MS4w", "title": "另一条", "create_time": 1765814400}]
    assert not (tmp_path / "douyin" / "json").exists()


def test_search_contents_stay_in_the_dated_file(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SAVE_DATA_PATH", str(tmp_path))
    writer = AsyncFileWriter(platform="douyin", crawler_type="search")
    asyncio.run(writer.write_single_item_to_json(
        {"aweme_id": "1", "sec_uid": "MS4w", "title": "搜"},
        "contents",
    ))

    assert not (tmp_path / "douyin" / "creator").exists()
    assert list((tmp_path / "douyin" / "search" / "json").glob("search_contents_*.json"))
