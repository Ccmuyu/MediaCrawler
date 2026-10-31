# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_downloader/layout.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

"""创作者模式下的媒体落盘布局。

``post`` 保持原样：每个作品一个目录，封面和视频放在一起。
``creator`` 只保留视频，目录改为创作者 ID，文件名用作品 ID，避免互相覆盖。
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Optional, Sequence

import config

from .types import MediaItem, MediaType

logger = logging.getLogger("MediaCrawler.media_downloader")

MEDIA_SAVE_LAYOUT_POST = "post"
MEDIA_SAVE_LAYOUT_CREATOR = "creator"


def creator_video_layout_enabled() -> bool:
    """创作者模式且选择了「仅视频、按创作者 ID 归档」时才改目录。"""
    if getattr(config, "CRAWLER_TYPE", "") != "creator":
        return False
    return str(getattr(config, "MEDIA_SAVE_LAYOUT", MEDIA_SAVE_LAYOUT_POST)) == MEDIA_SAVE_LAYOUT_CREATOR


def creator_file_stem(item: MediaItem) -> str:
    """同一创作者目录下用作品 ID 做文件名。

    B 站直链降级产物原来叫 ``video-durl``，这里保留 ``-durl`` 后缀，
    避免低清文件和 DASH 合流文件同名后被「已存在即跳过」卡住。
    """
    content_id = str(item.content_id or item.stem or "video")
    if item.stem == "video-durl":
        return f"{content_id}-durl"
    return content_id


def apply_creator_video_layout(items: Sequence[MediaItem], creator_id: str) -> list[MediaItem]:
    """按当前配置改写待下载列表。搜索和详情模式原样返回。

    下载器把 content_id 当作目录名。创作者模式下把它换成创作者 ID，文件名改成作品 ID。
    创作者 ID 为空时不改，避免不同作者的视频堆进同一个目录。
    """
    if not creator_video_layout_enabled():
        return list(items)

    folder_name = (creator_id or "").strip()
    if not folder_name:
        logger.warning("[download] 创作者目录模式缺少创作者 ID，仍按作品目录保存")
        return list(items)

    videos: list[MediaItem] = []
    for item in items:
        if item.media_type != MediaType.VIDEO:
            continue
        # content_id 在下载器里是目录名，不是作品 ID
        videos.append(replace(item, content_id=folder_name, stem=creator_file_stem(item)))

    skipped = len(items) - len(videos)
    if skipped and not videos:
        logger.info("[download] 创作者目录模式只保存视频，已跳过 %d 个非视频文件", skipped)
    return videos


def apply_creator_video_layout_item(item: Optional[MediaItem], creator_id: str) -> Optional[MediaItem]:
    """单个媒体任务的布局改写。封面等非视频在创作者目录模式下返回 None。"""
    if item is None:
        return None
    placed = apply_creator_video_layout([item], creator_id)
    return placed[0] if placed else None
