# -*- coding: utf-8 -*-
"""作品墙接口：内容文件、两种媒体目录、JSONL 和路径限制。"""

from __future__ import annotations

import json

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.main import app
from api.routers import data as data_router
from api.services.works import resolve_data_path


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(data_router, "DATA_DIR", tmp_path)
    return TestClient(app)


def _write_json(root, relative: str, records: list[dict]) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")


def test_post_directory_wins_over_creator_index(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    content_id = "7123"
    post = tmp_path / "dy" / "media" / content_id
    post.mkdir(parents=True)
    (post / "cover.jpg").write_bytes(b"cover")
    (post / "video.mp4").write_bytes(b"video")
    (post / "001.jpg").write_bytes(b"img")
    (post / "001_live.mp4").write_bytes(b"live")
    creator = tmp_path / "dy" / "media" / "creatorA"
    creator.mkdir()
    (creator / "name_index.txt").write_text(f"{content_id}|video\t别的标题\n", encoding="utf-8")
    (creator / "别的标题.mp4").write_bytes(b"other")
    _write_json(tmp_path, "dy/json/creator_contents_2026-11-21.json", [{
        "aweme_id": content_id,
        "title": "标题",
        "nickname": "张***三",
        "aweme_url": "https://www.douyin.com/video/7123",
        "liked_count": "3",
    }])

    response = client.get("/api/data/works", params={"file": "dy/json/creator_contents_2026-11-21.json"})

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["cover"] == "dy/media/7123/cover.jpg"
    assert item["images"] == ["dy/media/7123/001.jpg"]
    assert item["video"] == "dy/media/7123/video.mp4"
    assert [video["stem"] for video in item["videos"]] == ["video", "001_live"]
    assert item["author"] == "张***三"
    assert "\\" not in item["video"]


def test_creator_index_pairs_cover_and_ignores_title_suffix(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    creator = tmp_path / "xhs" / "media" / "user1"
    creator.mkdir(parents=True)
    (creator / "name_index.txt").write_text(
        "note1|video\t夏天的风\nnote1|cover\t夏天的风\n",
        encoding="utf-8",
    )
    (creator / "夏天的风.mp4").write_bytes(b"v")
    (creator / "夏天的风.jpg").write_bytes(b"j")
    (creator / "夏天的风_note2.mp4").write_bytes(b"nope")
    (creator / "author.txt").write_text("昵称: 红薯\n主页: https://example\n", encoding="utf-8")
    _write_json(tmp_path, "xhs/json/creator_contents_2026-11-21.json", [
        {"note_id": "note1", "title": "夏天的风", "nickname": "红***薯", "note_url": "https://www.xiaohongshu.com/explore/note1"},
        {"note_id": "note2", "title": "夏天的风", "nickname": "红***薯"},
    ])

    body = client.get("/api/data/works", params={"file": "xhs/json/creator_contents_2026-11-21.json"}).json()

    first, second = body["items"]
    assert first["cover"] == "xhs/media/user1/夏天的风.jpg"
    assert first["video"] == "xhs/media/user1/夏天的风.mp4"
    assert first["author"] == "红薯"
    assert first["images"] == []
    assert second["downloaded"] is False
    assert second["video"] is None
    assert second["author"] == "红***薯"


def test_id_named_file_matches_without_index(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    folder = tmp_path / "dy" / "media" / "creatorA"
    folder.mkdir(parents=True)
    (folder / "note9.mp4").write_bytes(b"v")
    (folder / "note9.jpg").write_bytes(b"j")
    (folder / "note9_001_live.mp4").write_bytes(b"live")
    _write_json(tmp_path, "dy/json/search_contents_2026-11-21.json", [{"aweme_id": "note9", "desc": ""}])

    item = client.get(
        "/api/data/works",
        params={"file": "dy/json/search_contents_2026-11-21.json"},
    ).json()["items"][0]

    assert item["video"] == "dy/media/creatorA/note9.mp4"
    assert item["cover"] == "dy/media/creatorA/note9.jpg"
    assert [video["path"] for video in item["videos"]] == [
        "dy/media/creatorA/note9.mp4",
        "dy/media/creatorA/note9_001_live.mp4",
    ]


def test_weibo_note_id_matches_local_media(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    folder = tmp_path / "wb" / "media" / "99"
    folder.mkdir(parents=True)
    (folder / "cover.jpg").write_bytes(b"c")
    (folder / "video.mp4").write_bytes(b"v")
    _write_json(tmp_path, "wb/json/creator_contents_2026-11-21.json", [{
        "note_id": "99",
        "content": "微博正文",
        "nickname": "微***博",
        "note_url": "https://m.weibo.cn/detail/99",
    }])

    item = client.get("/api/data/works", params={"file": "wb/json/creator_contents_2026-11-21.json"}).json()["items"][0]

    assert item["title"] == "微博正文"
    assert item["cover"] == "wb/media/99/cover.jpg"
    assert item["video"] == "wb/media/99/video.mp4"


def test_douyin_folder_uses_dy_media(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    content_id = "7708"
    media = tmp_path / "dy" / "media" / content_id
    media.mkdir(parents=True)
    (media / "video.mp4").write_bytes(b"v")
    (media / "cover.jpg").write_bytes(b"c")
    _write_json(tmp_path, "douyin/json/creator_contents_2026-11-21.json", [{
        "aweme_id": content_id,
        "title": "标题",
        "nickname": "张***三",
    }])

    response = client.get(
        "/api/data/works",
        params={"file": "douyin/json/creator_contents_2026-11-21.json"},
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert response.json()["platform"] == "dy"
    assert item["video"] == "dy/media/7708/video.mp4"
    assert item["cover"] == "dy/media/7708/cover.jpg"


def test_tieba_and_zhihu_content_files_are_rejected(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    _write_json(tmp_path, "tieba/json/creator_contents_2026-11-21.json", [{"note_id": "1"}])
    _write_json(tmp_path, "zhihu/json/creator_contents_2026-11-21.json", [{"content_id": "1"}])

    assert client.get("/api/data/works", params={"file": "tieba/json/creator_contents_2026-11-21.json"}).status_code == 400
    assert client.get("/api/data/works", params={"file": "zhihu/json/creator_contents_2026-11-21.json"}).status_code == 400


def test_jsonl_is_paged_and_listed(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    path = tmp_path / "ks" / "jsonl" / "search_contents_2026-11-21.jsonl"
    path.parent.mkdir(parents=True)
    lines = [json.dumps({"video_id": str(i), "title": f"t{i}"}, ensure_ascii=False) for i in range(30)]
    lines.insert(3, "{bad")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    listed = {item["path"]: item for item in client.get("/api/data/files").json()["files"]}
    saved = listed["ks/jsonl/search_contents_2026-11-21.jsonl"]
    assert saved["record_count"] == 31
    assert "\\" not in saved["path"]

    page = client.get(
        "/api/data/works",
        params={"file": "ks/jsonl/search_contents_2026-11-21.jsonl", "offset": 24, "limit": 24},
    ).json()
    assert page["total"] == 30
    assert [item["id"] for item in page["items"]] == ["24", "25", "26", "27", "28", "29"]

    comments = tmp_path / "ks" / "jsonl" / "creator_comments_2026-11-21.jsonl"
    comments.write_text('{"comment_id": "c1", "content": "hi"}\n\n', encoding="utf-8")
    preview = client.get("/api/data/files/ks/jsonl/creator_comments_2026-11-21.jsonl", params={"preview": True, "limit": 100})
    assert preview.status_code == 200
    assert preview.json()["total"] == 1
    assert preview.json()["data"][0]["comment_id"] == "c1"


def test_media_path_rejects_escape_and_non_media(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    media = tmp_path / "dy" / "media" / "7123"
    media.mkdir(parents=True)
    (media / "video.mp4").write_bytes(b"0123456789")
    (media / "author.txt").write_text("昵称: 甲\n", encoding="utf-8")

    with pytest.raises(HTTPException) as escaped:
        resolve_data_path(tmp_path, "dy/media/../../secret.txt")
    assert escaped.value.status_code == 403
    with pytest.raises(HTTPException) as backslash:
        resolve_data_path(tmp_path, "dy\\media\\..\\..\\secret.txt")
    assert backslash.value.status_code == 403
    assert client.get("/api/data/media/dy/media/../../secret.txt").status_code != 200
    assert client.get("/api/data/media/dy/media/7123/author.txt").status_code == 403

    partial = client.get("/api/data/media/dy/media/7123/video.mp4", headers={"Range": "bytes=0-3"})
    assert partial.status_code == 206
    assert partial.content == b"0123"
    assert partial.headers["content-type"].startswith("video/mp4")
    assert partial.headers["content-range"] == "bytes 0-3/10"


def test_creator_wall_count_matches_video_files(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    creator = "MS4wLjABAAAACreator"
    media = tmp_path / "dy" / "media" / creator
    media.mkdir(parents=True)
    (media / "name_index.txt").write_text(
        "a1|video\t作品一\na1|cover\t作品一\na2|video\t作品二\n",
        encoding="utf-8",
    )
    (media / "作品一.mp4").write_bytes(b"v1")
    (media / "作品一.jpg").write_bytes(b"c1")
    (media / "作品二.mp4").write_bytes(b"v2")
    (media / "author.txt").write_text("昵称: 暮暮\n", encoding="utf-8")
    contents = tmp_path / "douyin" / "creator" / creator / "contents.jsonl"
    contents.parent.mkdir(parents=True)
    lines = [
        {"aweme_id": "a1", "sec_uid": creator, "title": "作品一", "liked_count": "9"},
        {"aweme_id": "a1", "sec_uid": creator, "title": "作品一新", "liked_count": "10"},
        {"aweme_id": "missing", "sec_uid": creator, "title": "没有文件"},
    ]
    contents.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in lines) + "\n", encoding="utf-8")
    dated = tmp_path / "douyin" / "json" / "creator_contents_2026-11-21.json"
    dated.parent.mkdir(parents=True)
    dated.write_text("[]", encoding="utf-8")

    listed = client.get("/api/data/files").json()["files"]
    assert all("creator_contents_" not in item["name"] for item in listed)
    assert all(item["name"] != "contents.jsonl" for item in listed)

    creators = client.get("/api/data/creators").json()["creators"]
    assert creators == [{
        "platform": "dy",
        "creator_id": creator,
        "nickname": "暮暮",
        "avatar": None,
        "work_count": 2,
        "modified_at": creators[0]["modified_at"],
    }]

    page = client.get("/api/data/works", params={"platform": "dy", "creator": creator}).json()
    assert page["total"] == 2
    by_id = {item["id"]: item for item in page["items"]}
    assert set(by_id) == {"a1", "a2"}
    assert by_id["a1"]["title"] == "作品一新"
    assert by_id["a1"]["video"].endswith("作品一.mp4")
    assert by_id["a1"]["cover"].endswith("作品一.jpg")
    assert by_id["a1"]["stats"]["liked"] == "10"
