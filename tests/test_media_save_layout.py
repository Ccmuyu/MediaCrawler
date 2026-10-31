# -*- coding: utf-8 -*-
"""创作者模式的媒体目录布局。"""

from __future__ import annotations

import config
import pytest

from media_downloader import MediaItem, MediaType
from media_downloader.layout import apply_creator_video_layout, creator_file_stem
from media_downloader.paths import build_media_dir
from media_platform.douyin import media as douyin_media


CREATOR_ID = "MS4wLjABAAAA" + ("Ab12" * 16)
AWEME_ID = "76590219797764004"


def _video_and_cover() -> list[MediaItem]:
    return [
        MediaItem(url="https://cdn/cover.jpg", media_type=MediaType.IMAGE, content_id=AWEME_ID, stem="cover"),
        MediaItem(url="https://cdn/video.mp4", media_type=MediaType.VIDEO, content_id=AWEME_ID, stem="video"),
    ]


def test_post_layout_keeps_cover_and_video(monkeypatch):
    monkeypatch.setattr(config, "CRAWLER_TYPE", "creator")
    monkeypatch.setattr(config, "MEDIA_SAVE_LAYOUT", "post")

    placed = apply_creator_video_layout(_video_and_cover(), CREATOR_ID)

    assert [item.stem for item in placed] == ["cover", "video"]
    assert {item.content_id for item in placed} == {AWEME_ID}


def test_creator_layout_keeps_only_videos_under_creator_id(monkeypatch):
    monkeypatch.setattr(config, "CRAWLER_TYPE", "creator")
    monkeypatch.setattr(config, "MEDIA_SAVE_LAYOUT", "creator")

    placed = apply_creator_video_layout(_video_and_cover(), CREATOR_ID)

    assert len(placed) == 1
    assert placed[0].media_type is MediaType.VIDEO
    assert placed[0].content_id == CREATOR_ID
    assert placed[0].stem == AWEME_ID


def test_creator_layout_ignored_outside_creator_mode(monkeypatch):
    monkeypatch.setattr(config, "CRAWLER_TYPE", "search")
    monkeypatch.setattr(config, "MEDIA_SAVE_LAYOUT", "creator")

    placed = apply_creator_video_layout(_video_and_cover(), CREATOR_ID)

    assert len(placed) == 2
    assert placed[1].content_id == AWEME_ID


def test_creator_layout_without_creator_id_keeps_post_folders(monkeypatch):
    monkeypatch.setattr(config, "CRAWLER_TYPE", "creator")
    monkeypatch.setattr(config, "MEDIA_SAVE_LAYOUT", "creator")

    placed = apply_creator_video_layout(_video_and_cover(), "")

    assert placed[1].content_id == AWEME_ID
    assert placed[1].stem == "video"


def test_durl_fallback_keeps_a_distinct_filename():
    item = MediaItem(
        url="https://cdn/low.mp4",
        media_type=MediaType.VIDEO,
        content_id="BV1xxxx",
        stem="video-durl",
    )

    assert creator_file_stem(item) == "BV1xxxx-durl"


def test_douyin_creator_id_prefers_sec_uid():
    aweme = {
        "aweme_id": AWEME_ID,
        "author": {"uid": "123", "sec_uid": CREATOR_ID},
        "video": {"play_addr": {"url_list": ["https://cdn/video.mp4"]}},
    }

    assert douyin_media.extract_creator_id(aweme) == CREATOR_ID


def test_creator_folder_keeps_long_sec_uid(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CRAWLER_TYPE", "creator")
    monkeypatch.setattr(config, "MEDIA_SAVE_LAYOUT", "creator")
    aweme = {
        "aweme_id": AWEME_ID,
        "author": {"sec_uid": CREATOR_ID},
        "video": {"play_addr": {"url_list": ["https://cdn/video.mp4"]}},
    }
    placed = apply_creator_video_layout(
        douyin_media.build_media_items(aweme),
        douyin_media.extract_creator_id(aweme),
    )

    directory = build_media_dir(tmp_path, "dy", placed[0].content_id)

    assert directory.name == CREATOR_ID
    assert placed[0].stem == AWEME_ID


@pytest.mark.parametrize(
    ("crawler_type", "layout", "enabled_videos"),
    [
        ("creator", "creator", 1),
        ("detail", "creator", 2),
    ],
)
def test_image_posts_are_skipped_only_in_creator_folder_mode(monkeypatch, crawler_type, layout, enabled_videos):
    monkeypatch.setattr(config, "CRAWLER_TYPE", crawler_type)
    monkeypatch.setattr(config, "MEDIA_SAVE_LAYOUT", layout)
    images = [
        MediaItem(url="https://cdn/1.jpg", media_type=MediaType.IMAGE, content_id="note", stem="001"),
    ]

    placed = apply_creator_video_layout(images, CREATOR_ID)

    assert len(placed) == (0 if enabled_videos == 1 else 1)
