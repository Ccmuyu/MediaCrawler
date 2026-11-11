# -*- coding: utf-8 -*-
"""创作者模式的媒体目录布局。"""

from __future__ import annotations

import config
import pytest

from media_downloader import MediaItem, MediaType
from media_downloader.layout import (
    apply_creator_video_layout,
    creator_file_stem,
    save_creator_profile,
)
from media_downloader.paths import build_file_path, build_media_dir
from media_platform.bilibili import media as bili_media
from media_platform.douyin import media as douyin_media
from media_platform.kuaishou import media as kuaishou_media
from media_platform.weibo import media as weibo_media
from media_platform.xhs import media as xhs_media


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


def test_douyin_profile_uses_sec_uid_homepage():
    profile = douyin_media.creator_profile({
        "author": {
            "uid": "123",
            "sec_uid": CREATOR_ID,
            "unique_id": "dy_account",
            "nickname": "创作者甲",
            "signature": "第一行\n第二行",
            "gender": 1,
            "ip_location": "上海",
        }
    })

    assert profile["homepage"] == f"https://www.douyin.com/user/{CREATOR_ID}"
    assert profile["nickname"] == "创作者甲"
    assert profile["account"] == "dy_account"
    assert "gender" not in profile
    assert "ip_location" not in profile


def test_douyin_profile_without_sec_uid_has_no_homepage():
    profile = douyin_media.creator_profile({"author": {"uid": "123", "nickname": "只有数字号"}})

    assert profile["homepage"] == ""
    assert profile["nickname"] == "只有数字号"


def test_other_platforms_build_homepage_without_private_fields():
    xhs = xhs_media.creator_profile({
        "user": {"user_id": "u1", "nickname": "红薯", "red_id": "12345", "xsec_token": "tok", "desc": "简介"},
    })
    ks = kuaishou_media.creator_profile({
        "author": {"id": "3xabc", "name": "快手", "kwaiId": "kwai1"},
    })
    wb = weibo_media.creator_profile({
        "user": {
            "id": 99,
            "screen_name": "微博",
            "profile_url": "https://weibo.com/u/99",
            "description": "签名",
            "gender": "f",
            "ip_location": "上海",
            "followers_count": 10,
        }
    })
    bili = bili_media.creator_profile({"owner": {"mid": 777, "name": "UP", "sign": "空间签名"}})

    assert xhs["homepage"] == "https://www.xiaohongshu.com/user/profile/u1?xsec_token=tok&xsec_source=pc_feed"
    assert xhs["account"] == "12345"
    assert ks["homepage"] == "https://www.kuaishou.com/profile/3xabc"
    assert wb["homepage"] == "https://weibo.com/u/99"
    assert "ip_location" not in wb
    assert bili["homepage"] == "https://space.bilibili.com/777"


def test_creator_folder_saves_author_file(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CRAWLER_TYPE", "creator")
    monkeypatch.setattr(config, "MEDIA_SAVE_LAYOUT", "creator")
    profile = douyin_media.creator_profile({
        "author": {
            "sec_uid": CREATOR_ID,
            "unique_id": "dy_account",
            "nickname": "创作者甲",
            "signature": "第一行\n第二行",
        }
    })

    path = save_creator_profile(tmp_path, "dy", CREATOR_ID, profile)

    assert path is not None
    assert path.parent.name == CREATOR_ID
    assert path.read_text(encoding="utf-8") == (
        "昵称: 创作者甲\n"
        "账号: dy_account\n"
        "签名: 第一行 第二行\n"
        f"主页: https://www.douyin.com/user/{CREATOR_ID}\n"
    )
    assert save_creator_profile(tmp_path, "dy", CREATOR_ID, profile) == path


def test_author_file_is_not_written_outside_creator_layout(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CRAWLER_TYPE", "search")
    monkeypatch.setattr(config, "MEDIA_SAVE_LAYOUT", "creator")

    path = save_creator_profile(
        tmp_path,
        "dy",
        CREATOR_ID,
        {"nickname": "创作者甲", "homepage": "https://www.douyin.com/user/x"},
    )

    assert path is None
    assert not (tmp_path / "dy").exists()


def _video(content_id: str, stem: str = "video") -> MediaItem:
    return MediaItem(
        url="https://cdn/video.mp4",
        media_type=MediaType.VIDEO,
        content_id=content_id,
        stem=stem,
    )


def test_title_names_file_and_keeps_duplicates_apart(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CRAWLER_TYPE", "creator")
    monkeypatch.setattr(config, "MEDIA_SAVE_LAYOUT", "creator")
    monkeypatch.setattr(config, "MEDIA_FILE_NAME", "title")
    monkeypatch.setattr(config, "PLATFORM", "dy")
    monkeypatch.setattr(config, "SAVE_DATA_PATH", str(tmp_path))

    first = apply_creator_video_layout([_video("111")], CREATOR_ID, "夏天的风")
    second = apply_creator_video_layout([_video("222")], CREATOR_ID, "夏天的风 / 完整版")
    duplicate = apply_creator_video_layout([_video("333")], CREATOR_ID, "夏天的风")
    again = apply_creator_video_layout([_video("111")], CREATOR_ID, "夏天的风")

    assert first[0].stem == "夏天的风"
    assert second[0].stem == "夏天的风 _ 完整版"
    assert duplicate[0].stem == "夏天的风_333"
    assert again[0].stem == "夏天的风"
    assert build_file_path(tmp_path, first[0].stem, ".mp4").name == "夏天的风.mp4"


def test_id_mode_keeps_the_post_id(monkeypatch):
    monkeypatch.setattr(config, "CRAWLER_TYPE", "creator")
    monkeypatch.setattr(config, "MEDIA_SAVE_LAYOUT", "creator")
    monkeypatch.setattr(config, "MEDIA_FILE_NAME", "id")

    placed = apply_creator_video_layout([_video(AWEME_ID)], CREATOR_ID, "夏天的风")

    assert placed[0].stem == AWEME_ID


def test_empty_title_falls_back_to_post_id(monkeypatch):
    monkeypatch.setattr(config, "CRAWLER_TYPE", "creator")
    monkeypatch.setattr(config, "MEDIA_SAVE_LAYOUT", "creator")
    monkeypatch.setattr(config, "MEDIA_FILE_NAME", "title")

    placed = apply_creator_video_layout([_video(AWEME_ID, "001_live")], CREATOR_ID, "   ")

    assert placed[0].stem == f"{AWEME_ID}_001_live"


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
