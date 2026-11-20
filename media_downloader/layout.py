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
``creator`` 把视频放到创作者 ID 目录。文件名默认用作品标题，
标题重复时再带上作品 ID，也可以改回用作品 ID。
抖音和小红书有封面时一并放进这个目录，和正片同名、扩展名不同。
图文没有单独封面时用第一张图，其余图片不保存。其他平台仍然只保存视频。
创作者目录下的 ``meta`` 里放 ``author.txt``、``name_index.txt`` 和 ``avatar.jpg``，
方便从 sec_uid 这类目录名认出是谁，又不和作品文件混在一起。
"""

from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path
from typing import Mapping, Optional, Sequence

import config

from .paths import ALLOWED_EXTENSIONS, STEM_MAX_LENGTH, build_media_dir, sanitize_component
from .types import MediaItem, MediaType

logger = logging.getLogger("MediaCrawler.media_downloader")

MEDIA_SAVE_LAYOUT_POST = "post"
MEDIA_SAVE_LAYOUT_CREATOR = "creator"
MEDIA_FILE_NAME_ID = "id"
MEDIA_FILE_NAME_TITLE = "title"
CREATOR_META_DIR = "meta"
AUTHOR_FILE_NAME = "author.txt"
AVATAR_FILE_NAME = "avatar.jpg"
# 记录「哪条作品用了哪个文件名」。没有它，标题相同的下一次下载会把已有文件当成自己的。
NAME_INDEX_FILE = "name_index.txt"
_PRIMARY_STEMS = {"video", "media", "cover"}
# 创作者目录里补封面。其他平台的封面字段还不在这条路径上处理。
_COVER_PLATFORMS = frozenset({"dy", "xhs"})

# 只留能认出这个目录是谁的字段。性别、IP、粉丝数不写进媒体目录。
_AUTHOR_LINES = (
    ("nickname", "昵称"),
    ("account", "账号"),
    ("signature", "签名"),
    ("homepage", "主页"),
)


def creator_video_layout_enabled() -> bool:
    """创作者模式且选择了按创作者 ID 归档时才改目录。"""
    if getattr(config, "CRAWLER_TYPE", "") != "creator":
        return False
    return str(getattr(config, "MEDIA_SAVE_LAYOUT", MEDIA_SAVE_LAYOUT_CREATOR)) == MEDIA_SAVE_LAYOUT_CREATOR


def media_file_name_mode() -> str:
    """创作者目录下的文件名方案。未识别的值按标题处理。"""
    value = str(getattr(config, "MEDIA_FILE_NAME", MEDIA_FILE_NAME_TITLE) or "").strip().lower()
    if value == MEDIA_FILE_NAME_ID:
        return MEDIA_FILE_NAME_ID
    return MEDIA_FILE_NAME_TITLE


def creator_file_stem(item: MediaItem) -> str:
    """同一创作者目录下用作品 ID 做文件名。

    B 站直链降级产物原来叫 ``video-durl``，这里保留 ``-durl`` 后缀，
    避免低清文件和 DASH 合流文件同名后被「已存在即跳过」卡住。
    实况图的 ``001_live`` 也要留下，否则会和正片写成同一个文件。
    """
    content_id = str(item.content_id or item.stem or "video")
    if item.stem == "video-durl":
        return f"{content_id}-durl"
    if item.stem and item.stem not in _PRIMARY_STEMS:
        return f"{content_id}_{item.stem}"
    return content_id


def _preferred_title_stem(item: MediaItem, title: str) -> str:
    """标题文件名。空标题退回作品 ID。实况图和直链降级保留原来的后缀。"""
    content_id = str(item.content_id or item.stem or "video")
    base = sanitize_component(title, "", max_length=80)
    if not base:
        return creator_file_stem(item)
    if item.stem == "video-durl":
        suffix = "-durl"
    elif item.stem and item.stem not in _PRIMARY_STEMS:
        suffix = f"_{item.stem}"
    else:
        suffix = ""
    room = STEM_MAX_LENGTH - len(suffix)
    head = base[: max(1, room)].rstrip(" .") or content_id[: max(1, room)]
    return sanitize_component(f"{head}{suffix}", content_id, max_length=STEM_MAX_LENGTH)


def _with_content_id(stem: str, content_id: str) -> str:
    """标题已被占用时把作品 ID 接在后面。ID 已经在末尾则不重复接。"""
    suffix = f"_{content_id}"
    if stem.endswith(suffix):
        return stem
    room = STEM_MAX_LENGTH - len(suffix)
    head = stem[: max(1, room)].rstrip(" .") or content_id[: max(1, room)]
    return sanitize_component(f"{head}{suffix}", content_id, max_length=STEM_MAX_LENGTH)


def relocate_creator_sidecars(media_dir: Path) -> None:
    """把旧位置的作者说明和文件名索引挪进 meta。已经在 meta 里的不动。"""
    if not media_dir.is_dir():
        return
    meta = media_dir / CREATOR_META_DIR
    for name in (AUTHOR_FILE_NAME, NAME_INDEX_FILE):
        source = media_dir / name
        target = meta / name
        if source.is_file() and not target.exists():
            meta.mkdir(parents=True, exist_ok=True)
            source.replace(target)


def sidecar_path(media_dir: Path, name: str) -> Path:
    """说明文件的读取路径。meta 里有就用 meta，否则仍认创作者目录根上的旧文件。"""
    nested = media_dir / CREATOR_META_DIR / name
    if nested.is_file():
        return nested
    legacy = media_dir / name
    if legacy.is_file():
        return legacy
    return nested


def _name_index_path(creator_id: str) -> Optional[Path]:
    platform = str(getattr(config, "PLATFORM", "") or "").strip()
    if not platform:
        return None
    base = Path(getattr(config, "SAVE_DATA_PATH", "") or "data")
    media_dir = build_media_dir(base, platform, creator_id)
    relocate_creator_sidecars(media_dir)
    return media_dir / CREATOR_META_DIR / NAME_INDEX_FILE


def _load_name_index(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    found: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "\t" not in line:
            continue
        key, stem = line.split("\t", 1)
        if key and stem:
            found[key] = stem
    return found


def _used_stems(directory: Path, reserved: Mapping[str, str]) -> set[str]:
    used = {stem for stem in reserved.values() if stem}
    if not directory.is_dir():
        return used
    for file_path in directory.iterdir():
        if file_path.suffix.lower() in ALLOWED_EXTENSIONS:
            used.add(file_path.stem)
    return used


def _keep_creator_cover() -> bool:
    """抖音、小红书的创作者目录保存封面。平台值来自当前爬取配置。"""
    platform = str(getattr(config, "PLATFORM", "") or "").strip().lower()
    return platform in _COVER_PLATFORMS


def _is_cover_item(item: MediaItem) -> bool:
    return item.media_type == MediaType.IMAGE and item.stem == "cover"


def _items_for_creator_folder(items: Sequence[MediaItem]) -> list[MediaItem]:
    """视频都留。抖音和小红书再留一张封面，图文没有单独封面时用第一张图。

    封面放在视频后面，好让文件名先分给正片，封面再沿用同一个名字。
    """
    videos = [item for item in items if item.media_type == MediaType.VIDEO]
    if not _keep_creator_cover():
        return videos
    covers = [item for item in items if _is_cover_item(item)]
    if covers:
        return [*videos, covers[0]]
    images = [item for item in items if item.media_type == MediaType.IMAGE]
    if not images:
        return videos
    return [*videos, replace(images[0], stem="cover")]


def _assign_stems(items: Sequence[MediaItem], creator_id: str, title: str) -> list[str]:
    """给这一组文件分配文件名。标题方案会记住分配结果，同一作品再次下载沿用原名。

    封面和正片用同一个文件名，只是扩展名不同。封面自己不占一个新的标题，
    避免把正片挤成「标题_作品ID」。
    """
    if media_file_name_mode() == MEDIA_FILE_NAME_ID:
        return [creator_file_stem(item) for item in items]

    index_path = _name_index_path(creator_id)
    index = _load_name_index(index_path) if index_path else {}
    media_dir = index_path.parent.parent if index_path is not None else None
    used = _used_stems(media_dir, index) if media_dir is not None else set(index.values())
    stems: list[str | None] = [None] * len(items)
    changed = False

    def assign_file(item: MediaItem) -> str:
        nonlocal changed
        key = f"{item.content_id}|{item.stem}"
        content_id = str(item.content_id or "video")
        if key in index:
            stem = index[key]
            used.add(stem)
            return stem
        stem = _preferred_title_stem(item, title)
        if stem in used:
            stem = _with_content_id(stem, content_id)
        if stem in used:
            stem = _with_content_id(f"{stem}_{item.stem}", content_id)
        index[key] = stem
        changed = True
        used.add(stem)
        return stem

    for index_in_batch, item in enumerate(items):
        if _is_cover_item(item):
            continue
        stems[index_in_batch] = assign_file(item)

    for index_in_batch, item in enumerate(items):
        if not _is_cover_item(item):
            continue
        key = f"{item.content_id}|{item.stem}"
        if key in index:
            stem = index[key]
        else:
            stem = index.get(f"{item.content_id}|video", "")
            if not stem:
                stem = _preferred_title_stem(item, title)
                content_id = str(item.content_id or "cover")
                if stem in used:
                    stem = _with_content_id(stem, content_id)
            index[key] = stem
            changed = True
        used.add(stem)
        stems[index_in_batch] = stem

    if changed and index_path is not None:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        body = "\n".join(f"{key}\t{value}" for key, value in index.items())
        index_path.write_text(body + "\n", encoding="utf-8")
    if any(stem is None for stem in stems):
        raise RuntimeError("creator file name was not assigned")
    return [stem for stem in stems if stem is not None]


def apply_creator_video_layout(
    items: Sequence[MediaItem],
    creator_id: str,
    title: str = "",
) -> list[MediaItem]:
    """按当前配置改写待下载列表。搜索和详情模式原样返回。

    下载器把 content_id 当作目录名。创作者模式下把它换成创作者 ID。
    文件名默认用作品标题；标题为空或选择了 ID 方案时仍用作品 ID。
    抖音和小红书多留一张封面，文件名与正片相同。
    创作者 ID 为空时不改，避免不同作者的视频堆进同一个目录。
    """
    if not creator_video_layout_enabled():
        return list(items)

    folder_name = (creator_id or "").strip()
    if not folder_name:
        logger.warning("[download] 创作者目录模式缺少创作者 ID，仍按作品目录保存")
        return list(items)

    selected = _items_for_creator_folder(items)
    stems = _assign_stems(selected, folder_name, title)
    placed = [
        replace(item, content_id=folder_name, stem=stem)
        for item, stem in zip(selected, stems)
    ]

    skipped = len(items) - len(selected)
    if skipped:
        logger.info("[download] 创作者目录未保存 %d 个图片文件", skipped)
    return placed


def format_creator_profile(profile: Mapping[str, str]) -> str:
    """把作者卡片收成几行文本。空字段省略，没有昵称也没有主页时返回空串。"""
    lines: list[str] = []
    for key, label in _AUTHOR_LINES:
        value = str(profile.get(key) or "").replace("\r", " ").replace("\n", " ").strip()
        if value:
            lines.append(f"{label}: {value}")
    if not any(line.startswith("昵称:") or line.startswith("主页:") for line in lines):
        return ""
    return "\n".join(lines) + "\n"


def save_creator_profile(
    base_dir: Path,
    platform: str,
    creator_id: str,
    profile: Mapping[str, str],
) -> Optional[Path]:
    """把作者卡片写到创作者目录 meta/author.txt。

    只在创作者目录布局下写入。视频已存在被跳过时也写，否则旧目录一直对不上人。
    内容没变则不重写。搜索和详情模式直接返回。
    """
    if not creator_video_layout_enabled():
        return None
    folder_name = (creator_id or "").strip()
    text = format_creator_profile(profile)
    if not folder_name or not text:
        return None
    directory = build_media_dir(base_dir, platform, folder_name)
    directory.mkdir(parents=True, exist_ok=True)
    relocate_creator_sidecars(directory)
    path = directory / CREATOR_META_DIR / AUTHOR_FILE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return path
    path.write_text(text, encoding="utf-8")
    return path


def apply_creator_video_layout_item(
    item: Optional[MediaItem],
    creator_id: str,
    title: str = "",
) -> Optional[MediaItem]:
    """单个媒体任务的布局改写。

    抖音和小红书的封面会留在创作者目录里。其他平台的封面返回 None。
    """
    if item is None:
        return None
    placed = apply_creator_video_layout([item], creator_id, title)
    return placed[0] if placed else None
