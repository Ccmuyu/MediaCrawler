# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/api/services/works.py
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

"""把内容文件收成作品列表，并按作品 ID 对上 data/<平台>/media 里的文件。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from fastapi import HTTPException

from media_downloader.layout import sidecar_path
from media_downloader.paths import (
    ALLOWED_EXTENSIONS,
    CONTENT_ID_MAX_LENGTH,
    build_media_dir,
    sanitize_component,
)

CONTENT_PLATFORMS = frozenset({"xhs", "dy", "ks", "bili", "wb"})
# 记录目录用全名（douyin），媒体目录用短名（dy）。两边都认。
_FOLDER_TO_PLATFORM = {
    "xhs": "xhs",
    "dy": "dy",
    "douyin": "dy",
    "ks": "ks",
    "kuaishou": "ks",
    "bili": "bili",
    "bilibili": "bili",
    "wb": "wb",
    "weibo": "wb",
}
# 内容 JSONL 写在记录目录，媒体写在短名目录。预览用短名找视频，再用这个表找文案。
_PLATFORM_STORE = {
    "xhs": "xhs",
    "dy": "douyin",
    "ks": "kuaishou",
    "bili": "bili",
    "wb": "weibo",
}
_GENERIC_STEMS = frozenset({"video", "cover", "video-durl"})
_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".webp"})
_VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".flv", ".m4s"})
_VIDEO_RANK = {"video": 0, "video-durl": 1}

# id 字段、标题字段、原文链接、点赞、评论、收藏。没有的计数留空。
_FIELDS = {
    "dy": ("aweme_id", ("title", "desc"), "aweme_url", ("liked_count",), ("comment_count",), ("collected_count",)),
    "xhs": ("note_id", ("title", "desc"), "note_url", ("liked_count",), ("comment_count",), ("collected_count",)),
    "ks": ("video_id", ("title", "desc"), "video_url", ("liked_count",), (), ()),
    "bili": ("video_id", ("title",), "video_url", ("liked_count",), ("video_comment",), ("video_favorite_count",)),
    "wb": ("note_id", ("content",), "note_url", ("liked_count",), ("comments_count",), ()),
}

_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".flv": "video/x-flv",
    ".m4s": "video/mp4",
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
}


@dataclass
class _MediaFile:
    path: Path
    relpath: str
    stem: str
    suffix: str
    directory: Path


@dataclass
class _Index:
    signature: tuple
    by_content: dict[str, list[tuple[str, str, Path]]] = field(default_factory=dict)
    by_dir_stem: dict[tuple[Path, str], list[_MediaFile]] = field(default_factory=dict)
    by_dir: dict[Path, list[_MediaFile]] = field(default_factory=dict)
    loose: list[_MediaFile] = field(default_factory=list)


_cache: dict[tuple[str, str], _Index] = {}


def media_type_for(suffix: str) -> str | None:
    """白名单里的媒体类型。其它扩展名返回 None，调用方拒绝读取。"""
    return _MEDIA_TYPES.get(suffix.lower())


def resolve_data_path(data_dir: Path, raw: str) -> Path:
    """把请求里的相对路径收成 data 目录内的绝对路径。

    反斜杠先换成正斜杠。路径段里出现 ``..`` 直接拒绝，避免落到 data 外面。
    """
    text = (raw or "").replace("\\", "/").lstrip("/")
    parts = PurePosixPath(text).parts
    if not text or any(part in ("", ".", "..") for part in parts):
        raise HTTPException(status_code=403, detail="Access denied")
    base = data_dir.resolve()
    full = (base / text).resolve()
    try:
        full.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    return full


def relative_posix(data_dir: Path, file_path: Path) -> str:
    return file_path.resolve().relative_to(data_dir.resolve()).as_posix()


def count_jsonl_records(file_path: Path) -> int:
    """非空行数。不解析 JSON，坏行也算一条。"""
    total = 0
    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                total += 1
    return total


def preview_jsonl(file_path: Path, limit: int) -> tuple[list[dict], int]:
    """按行取出前 limit 条对象。坏行跳过，但仍计入 total。"""
    rows: list[dict] = []
    total = 0
    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            total += 1
            if len(rows) >= limit:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
    return rows, total


def works_page(data_dir: Path, file_rel: str, offset: int, limit: int) -> dict:
    """读一个内容文件，只给这一页做媒体匹配。"""
    full = resolve_data_path(data_dir, file_rel)
    if not full.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if full.suffix.lower() not in {".json", ".jsonl"}:
        raise HTTPException(status_code=400, detail="Not a content file")

    posix = relative_posix(data_dir, full)
    platform = _platform_of(posix)
    if platform not in CONTENT_PLATFORMS or not _is_contents_name(full.name):
        raise HTTPException(status_code=400, detail="Not a content file")

    records = _read_records(full)
    page = records[offset:offset + limit]
    return {
        "total": len(records),
        "file": posix,
        "platform": platform,
        "items": [_work_item(data_dir, platform, record) for record in page],
    }


def _platform_of(posix: str) -> str:
    """路径第一段是记录目录。返回媒体目录用的平台短名，认不出则为空。"""
    parts = PurePosixPath(posix).parts
    folder = parts[0].lower() if parts else ""
    return _FOLDER_TO_PLATFORM.get(folder, "")


def _is_contents_name(name: str) -> bool:
    parts = Path(name).stem.split("_")
    return len(parts) >= 2 and parts[1] == "contents"


def _read_records(file_path: Path) -> list[dict]:
    if file_path.suffix.lower() == ".jsonl":
        rows, _total = preview_jsonl(file_path, limit=10**9)
        return rows
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def _first_text(record: dict, keys: tuple[str, ...], limit: int = 0) -> str:
    for key in keys:
        value = str(record.get(key) or "").strip()
        if value:
            return value[:limit] if limit else value
    return ""


def _work_item(data_dir: Path, platform: str, record: dict) -> dict:
    id_key, title_keys, url_key, liked_keys, comment_keys, collected_keys = _FIELDS[platform]
    content_id = str(record.get(id_key) or "").strip()
    title_limit = 80 if platform == "wb" else 0
    title = _first_text(record, title_keys, title_limit) or content_id
    nickname = str(record.get("nickname") or "").strip()
    media = _match_media(data_dir, platform, content_id)
    author = media["author"] or nickname
    downloaded = bool(media["cover"] or media["images"] or media["videos"])
    return {
        "id": content_id,
        "title": title,
        "author": author,
        "source_url": str(record.get(url_key) or "").strip(),
        "stats": {
            "liked": _first_text(record, liked_keys),
            "comment": _first_text(record, comment_keys),
            "collected": _first_text(record, collected_keys),
        },
        "downloaded": downloaded,
        "cover": media["cover"],
        "images": media["images"],
        "video": media["video"],
        "videos": media["videos"],
    }


def _match_media(data_dir: Path, platform: str, content_id: str) -> dict:
    empty = {"cover": None, "images": [], "video": None, "videos": [], "author": ""}
    if not content_id:
        return empty
    index = _platform_index(data_dir, platform)
    post_dir = build_media_dir(data_dir, platform, content_id)
    if post_dir.is_dir():
        # 作品目录优先。同一作品若也在创作者目录里，不再往下看。
        return _from_files(index.by_dir.get(post_dir.resolve(), []), post=True)

    entries = index.by_content.get(content_id)
    if entries is not None:
        collected: list[tuple[str, _MediaFile]] = []
        seen: set[Path] = set()
        directories: list[Path] = []
        for original_stem, file_stem, directory in entries:
            if directory not in directories:
                directories.append(directory)
            for media in index.by_dir_stem.get((directory, file_stem), []):
                if media.path in seen:
                    continue
                seen.add(media.path)
                collected.append((original_stem, media))
        return _from_pairs(collected, directories)

    loose = [
        media for media in index.loose
        if _stem_is_content_file(media.stem, content_id)
    ]
    if not loose:
        return empty
    directories = []
    for media in loose:
        if media.directory not in directories:
            directories.append(media.directory)
    return _from_pairs([(media.stem, media) for media in loose], directories)


def _from_files(files: list[_MediaFile], post: bool) -> dict:
    return _from_pairs([(media.stem, media) for media in files], [files[0].directory] if files else [], post=post)


def _from_pairs(
    pairs: list[tuple[str, _MediaFile]],
    directories: list[Path],
    post: bool = False,
) -> dict:
    images = [(stem, media) for stem, media in pairs if media.suffix in _IMAGE_EXTENSIONS]
    videos = [(stem, media) for stem, media in pairs if media.suffix in _VIDEO_EXTENSIONS]
    videos.sort(key=lambda item: (_VIDEO_RANK.get(item[0], 2), item[0], item[1].relpath))

    cover_media: _MediaFile | None = None
    numbered = [media for stem, media in images if stem != "cover" and media.stem != "cover"]
    numbered.sort(key=lambda media: media.stem)
    if post:
        cover_media = next((media for _stem, media in images if media.stem == "cover"), None)
        if cover_media is None and numbered:
            cover_media = numbered[0]
        image_paths = [media.relpath for media in numbered]
    else:
        primary_stem = videos[0][1].stem if videos else ""
        for stem, media in images:
            if stem == "cover" or (primary_stem and media.stem == primary_stem):
                cover_media = media
                break
        if cover_media is None and images and not videos:
            cover_media = images[0][1]
        image_paths = []

    video_items = [{"path": media.relpath, "stem": stem} for stem, media in videos]
    author = "" if post else _author_name(directories)
    return {
        "cover": cover_media.relpath if cover_media else None,
        "images": image_paths,
        "video": video_items[0]["path"] if video_items else None,
        "videos": video_items,
        "author": author,
    }


def _creator_avatar(data_dir: Path, directory: Path) -> str | None:
    for name in ("avatar.jpg", "avatar.jpeg", "avatar.png", "avatar.webp"):
        path = sidecar_path(directory, name)
        if path.is_file() and path.stat().st_size > 0:
            return relative_posix(data_dir, path)
    return None


def _author_name(directories: list[Path]) -> str:
    for directory in directories:
        path = sidecar_path(directory, "author.txt")
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("昵称:"):
                return line.split(":", 1)[1].strip()
    return ""


def _stem_is_content_file(stem: str, content_id: str) -> bool:
    """只认作品 ID 本身、``ID-durl`` 和 ``ID_`` 开头。不以 ID 结尾的标题不算。"""
    if not content_id:
        return False
    if stem == content_id or stem == f"{content_id}-durl":
        return True
    prefix = f"{content_id}_"
    return stem.startswith(prefix) and len(stem) > len(prefix)


def _platform_index(data_dir: Path, platform: str) -> _Index:
    media_root = data_dir / platform / "media"
    signature = _signature(media_root)
    key = (str(data_dir.resolve()), platform)
    cached = _cache.get(key)
    if cached is not None and cached.signature == signature:
        return cached
    built = _build_index(data_dir, media_root, signature)
    _cache[key] = built
    return built


def _signature(media_root: Path) -> tuple:
    if not media_root.is_dir():
        return tuple()
    marks: list[tuple[str, int]] = []
    for child in media_root.iterdir():
        if not child.is_dir():
            continue
        marks.append((child.name, child.stat().st_mtime_ns))
        index_path = sidecar_path(child, "name_index.txt")
        if index_path.is_file():
            marks.append((f"{child.name}/{index_path.parent.name}/name_index.txt", index_path.stat().st_mtime_ns))
    return tuple(sorted(marks))


def _build_index(data_dir: Path, media_root: Path, signature: tuple) -> _Index:
    index = _Index(signature=signature)
    if not media_root.is_dir():
        return index
    for child in media_root.iterdir():
        if not child.is_dir():
            continue
        directory = child.resolve()
        index_path = sidecar_path(child, "name_index.txt")
        if index_path.is_file():
            _read_name_index(index, index_path, directory)
        for file_path in child.iterdir():
            if not file_path.is_file():
                continue
            suffix = file_path.suffix.lower()
            if suffix not in ALLOWED_EXTENSIONS:
                continue
            media = _MediaFile(
                path=file_path.resolve(),
                relpath=relative_posix(data_dir, file_path),
                stem=file_path.stem,
                suffix=suffix,
                directory=directory,
            )
            index.by_dir.setdefault(directory, []).append(media)
            index.by_dir_stem.setdefault((directory, media.stem), []).append(media)
            index.loose.append(media)
    return index


def _read_name_index(index: _Index, index_path: Path, directory: Path) -> None:
    seen: set[str] = set()
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if "\t" not in line:
            continue
        key, file_stem = line.split("\t", 1)
        if "|" not in key or not file_stem or key in seen:
            continue
        seen.add(key)
        content_id, original_stem = key.split("|", 1)
        if not content_id:
            continue
        index.by_content.setdefault(content_id, []).append((original_stem, file_stem, directory))


def list_creators(data_dir: Path) -> list[dict]:
    """每个有作品文件的创作者目录一条。条数是作品数，封面和索引文件不另算。"""
    creators: list[dict] = []
    for platform in sorted(CONTENT_PLATFORMS):
        media_root = data_dir / platform / "media"
        if not media_root.is_dir():
            continue
        for child in media_root.iterdir():
            if not child.is_dir():
                continue
            works = directory_works(data_dir, child)
            if not works:
                continue
            avatar = _creator_avatar(data_dir, child)
            creators.append({
                "platform": platform,
                "creator_id": child.name,
                "nickname": _author_name([child.resolve()]) or child.name,
                "avatar": avatar,
                "work_count": len(works),
                "modified_at": child.stat().st_mtime,
            })
    creators.sort(key=lambda item: item["modified_at"], reverse=True)
    return creators


def creator_works_page(data_dir: Path, platform: str, creator_id: str, offset: int, limit: int) -> dict:
    """一个创作者目录里的作品。总数等于目录里的作品文件数，对不上文件的记录不出现。"""
    short = (platform or "").strip().lower()
    if short not in CONTENT_PLATFORMS:
        raise HTTPException(status_code=400, detail="Unknown platform")
    safe = sanitize_component(creator_id, fallback="", max_length=CONTENT_ID_MAX_LENGTH)
    if not safe:
        raise HTTPException(status_code=400, detail="Unknown creator")
    media_root = (data_dir / short / "media").resolve()
    directory = (media_root / safe).resolve()
    if media_root != directory and media_root not in directory.parents:
        raise HTTPException(status_code=403, detail="Path not allowed")
    if not directory.is_dir():
        raise HTTPException(status_code=404, detail="Creator not found")

    works = directory_works(data_dir, directory)
    records = _creator_records(data_dir, short, safe)
    page = works[offset:offset + limit]
    return {
        "total": len(works),
        "file": "",
        "platform": short,
        "creator_id": safe,
        "items": [
            _creator_item(short, content_id, title, files, directory, records.get(content_id))
            for content_id, title, files in page
        ],
    }


def directory_works(data_dir: Path, directory: Path) -> list[tuple[str, str, list[_MediaFile]]]:
    """目录里的作品。同一作品的视频和封面算一条，author.txt 和 name_index.txt 不算。"""
    files = _visual_files(data_dir, directory)
    grouped = _content_groups(sidecar_path(directory, "name_index.txt"))
    indexed_stems = {file_stem for pairs in grouped.values() for _original, file_stem in pairs}
    works: list[tuple[str, str, list[_MediaFile]]] = []
    for content_id, pairs in grouped.items():
        stems = {file_stem for _original, file_stem in pairs}
        matched = [media for media in files if media.stem in stems]
        if not matched:
            continue
        works.append((content_id, _title_hint(content_id, pairs, matched), matched))

    video_stems = {media.stem for media in files if media.suffix in _VIDEO_EXTENSIONS}
    for media in files:
        if media.stem in indexed_stems:
            continue
        if media.suffix in _IMAGE_EXTENSIONS and (media.stem in video_stems or media.stem == "cover"):
            continue
        works.append((media.stem, media.stem, [media]))
    works.sort(key=lambda item: max(media.path.stat().st_mtime_ns for media in item[2]), reverse=True)
    return works


def _visual_files(data_dir: Path, directory: Path) -> list[_MediaFile]:
    files: list[_MediaFile] = []
    resolved = directory.resolve()
    for file_path in directory.iterdir():
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        if suffix not in _IMAGE_EXTENSIONS and suffix not in _VIDEO_EXTENSIONS:
            continue
        files.append(_MediaFile(
            path=file_path.resolve(),
            relpath=relative_posix(data_dir, file_path),
            stem=file_path.stem,
            suffix=suffix,
            directory=resolved,
        ))
    return files


def _content_groups(index_path: Path) -> dict[str, list[tuple[str, str]]]:
    grouped: dict[str, list[tuple[str, str]]] = {}
    if not index_path.is_file():
        return grouped
    seen: set[str] = set()
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if "\t" not in line:
            continue
        key, file_stem = line.split("\t", 1)
        if "|" not in key or not file_stem or key in seen:
            continue
        seen.add(key)
        content_id, original_stem = key.split("|", 1)
        if not content_id:
            continue
        grouped.setdefault(content_id, []).append((original_stem, file_stem))
    return grouped


def _title_hint(content_id: str, pairs: list[tuple[str, str]], files: list[_MediaFile]) -> str:
    for media in files:
        if media.suffix in _VIDEO_EXTENSIONS and media.stem not in _GENERIC_STEMS and media.stem != content_id:
            return media.stem
    for original, _file_stem in pairs:
        if original not in _GENERIC_STEMS and original != content_id:
            return original
    return content_id


def _creator_records(data_dir: Path, platform: str, creator_id: str) -> dict[str, dict]:
    store = _PLATFORM_STORE.get(platform, platform)
    folder = data_dir / store / "creator" / creator_id
    records: dict[str, dict] = {}
    if not folder.is_dir():
        return records
    id_key = _FIELDS[platform][0]
    files = sorted(path for path in folder.glob("contents*.jsonl") if path.is_file())
    for path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(item, dict):
                continue
            content_id = str(item.get(id_key) or "").strip()
            if content_id:
                records[content_id] = item
    return records


def _creator_item(
    platform: str,
    content_id: str,
    title_hint: str,
    files: list[_MediaFile],
    directory: Path,
    record: dict | None,
) -> dict:
    _id_key, title_keys, url_key, liked_keys, comment_keys, collected_keys = _FIELDS[platform]
    media = _from_pairs([(item.stem, item) for item in files], [directory])
    title = ""
    source_url = ""
    nickname = ""
    stats = {"liked": "", "comment": "", "collected": ""}
    if record:
        title_limit = 80 if platform == "wb" else 0
        title = _first_text(record, title_keys, title_limit)
        source_url = str(record.get(url_key) or "").strip()
        nickname = str(record.get("nickname") or "").strip()
        stats = {
            "liked": _first_text(record, liked_keys),
            "comment": _first_text(record, comment_keys),
            "collected": _first_text(record, collected_keys),
        }
    return {
        "id": content_id,
        "title": title or title_hint or content_id,
        "author": media["author"] or nickname,
        "source_url": source_url,
        "stats": stats,
        "downloaded": bool(media["cover"] or media["images"] or media["videos"]),
        "cover": media["cover"],
        "images": media["images"],
        "video": media["video"],
        "videos": media["videos"],
    }
