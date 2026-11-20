# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/api/routers/data.py
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

import os
import json
from pathlib import Path
from typing import Iterator, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse

from ..services.works import (
    count_jsonl_records,
    creator_works_page,
    list_creators,
    media_type_for,
    preview_jsonl,
    relative_posix,
    resolve_data_path,
    works_page,
)

router = APIRouter(prefix="/data", tags=["data"])

# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"


def get_file_info(file_path: Path) -> dict:
    """Get file information"""
    stat = file_path.stat()
    record_count = None

    # Try to get record count
    try:
        if file_path.suffix == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    record_count = len(data)
        elif file_path.suffix == ".jsonl":
            record_count = count_jsonl_records(file_path)
        elif file_path.suffix == ".csv":
            with open(file_path, "r", encoding="utf-8") as f:
                record_count = sum(1 for _ in f) - 1  # Subtract header row
    except Exception:
        pass

    return {
        "name": file_path.name,
        "path": relative_posix(DATA_DIR, file_path),
        "size": stat.st_size,
        "modified_at": stat.st_mtime,
        "record_count": record_count,
        "type": file_path.suffix[1:] if file_path.suffix else "unknown"
    }


@router.get("/files")
async def list_data_files(platform: Optional[str] = None, file_type: Optional[str] = None):
    """Get data file list"""
    if not DATA_DIR.exists():
        return {"files": []}

    files = []
    supported_extensions = {".json", ".jsonl", ".csv", ".xlsx", ".xls"}

    for root, dirs, filenames in os.walk(DATA_DIR):
        root_path = Path(root)
        for filename in filenames:
            file_path = root_path / filename
            if file_path.suffix.lower() not in supported_extensions:
                continue
            if _hidden_from_browser(file_path):
                continue

            # Platform filter
            if platform:
                rel_path = str(file_path.relative_to(DATA_DIR))
                if platform.lower() not in rel_path.lower():
                    continue

            # Type filter
            if file_type and file_path.suffix[1:].lower() != file_type.lower():
                continue

            try:
                files.append(get_file_info(file_path))
            except Exception:
                continue

    # Sort by modification time (newest first)
    files.sort(key=lambda x: x["modified_at"], reverse=True)

    return {"files": files}


@router.get("/files/{file_path:path}")
async def get_file_content(file_path: str, preview: bool = True, limit: int = 100):
    """Get file content or preview"""
    full_path = DATA_DIR / file_path

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    # Security check: ensure within DATA_DIR
    try:
        full_path.resolve().relative_to(DATA_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    if preview:
        # Return preview data
        try:
            if full_path.suffix == ".json":
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return {"data": data[:limit], "total": len(data)}
                    return {"data": data, "total": 1}
            elif full_path.suffix.lower() == ".jsonl":
                rows, total = preview_jsonl(full_path, limit)
                return {"data": rows, "total": total}
            elif full_path.suffix == ".csv":
                import csv
                with open(full_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = []
                    for i, row in enumerate(reader):
                        if i >= limit:
                            break
                        rows.append(row)
                    # Re-read to get total count
                    f.seek(0)
                    total = sum(1 for _ in f) - 1
                    return {"data": rows, "total": total}
            elif full_path.suffix.lower() in (".xlsx", ".xls"):
                import pandas as pd
                # Read first limit rows
                df = pd.read_excel(full_path, nrows=limit)
                # Get total row count (only read first column to save memory)
                df_count = pd.read_excel(full_path, usecols=[0])
                total = len(df_count)
                # Convert to list of dictionaries, handle NaN values
                rows = df.where(pd.notnull(df), None).to_dict(orient='records')
                return {
                    "data": rows,
                    "total": total,
                    "columns": list(df.columns)
                }
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type for preview")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Return file download
        return FileResponse(
            path=full_path,
            filename=full_path.name,
            media_type="application/octet-stream"
        )


@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download file"""
    full_path = DATA_DIR / file_path

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    # Security check
    try:
        full_path.resolve().relative_to(DATA_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        path=full_path,
        filename=full_path.name,
        media_type="application/octet-stream"
    )


@router.get("/stats")
async def get_data_stats():
    """Get data statistics"""
    if not DATA_DIR.exists():
        return {"total_files": 0, "total_size": 0, "by_platform": {}, "by_type": {}}

    stats = {
        "total_files": 0,
        "total_size": 0,
        "by_platform": {},
        "by_type": {}
    }

    supported_extensions = {".json", ".jsonl", ".csv", ".xlsx", ".xls"}

    for root, dirs, filenames in os.walk(DATA_DIR):
        root_path = Path(root)
        for filename in filenames:
            file_path = root_path / filename
            if file_path.suffix.lower() not in supported_extensions:
                continue

            try:
                stat = file_path.stat()
                stats["total_files"] += 1
                stats["total_size"] += stat.st_size

                # Statistics by type
                file_type = file_path.suffix[1:].lower()
                stats["by_type"][file_type] = stats["by_type"].get(file_type, 0) + 1

                # Statistics by platform (inferred from path)
                rel_path = str(file_path.relative_to(DATA_DIR))
                for platform in ["xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu"]:
                    if platform in rel_path.lower():
                        stats["by_platform"][platform] = stats["by_platform"].get(platform, 0) + 1
                        break
            except Exception:
                continue

    return stats


def _hidden_from_browser(file_path: Path) -> bool:
    """按日期堆在一起的创作者内容，以及创作者目录里的文案文件，不进文件卡片。"""
    if file_path.name.startswith("creator_contents_"):
        return True
    if "creator" not in file_path.parts and "creators" not in file_path.parts:
        return False
    name = file_path.name
    return name == "contents.jsonl" or (name.startswith("contents_") and name.endswith(".jsonl"))


@router.get("/creators")
async def list_creator_catalog():
    """创作者目录。work_count 是该目录里的作品数。"""
    return {"creators": list_creators(DATA_DIR)}


@router.get("/works")
async def list_works(
    file: str = "",
    platform: str = "",
    creator: str = "",
    offset: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=100),
):
    """作品墙。传 creator 时按创作者目录分页，总数和目录里的作品文件数一致。"""
    if creator:
        return creator_works_page(DATA_DIR, platform, creator, offset, limit)
    if not file:
        raise HTTPException(status_code=400, detail="file or creator is required")
    return works_page(DATA_DIR, file, offset, limit)


def _file_chunks(path: Path, start: int, length: int) -> Iterator[bytes]:
    remaining = length
    with path.open("rb") as handle:
        handle.seek(start)
        while remaining > 0:
            chunk = handle.read(min(64 * 1024, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


@router.get("/media/{file_path:path}")
async def get_media(file_path: str, request: Request):
    """给图片和视频标签用。带 Range，播放时可以拖进度。"""
    full_path = resolve_data_path(DATA_DIR, file_path)
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    media_type = media_type_for(full_path.suffix)
    if media_type is None:
        raise HTTPException(status_code=403, detail="Unsupported media type")

    size = full_path.stat().st_size
    start = 0
    end = size - 1
    status = 200
    range_header = request.headers.get("range")
    if range_header and size > 0:
        unit, _, span = range_header.partition("=")
        if unit.strip() != "bytes" or "-" not in span:
            raise HTTPException(status_code=416, detail="Invalid range")
        start_text, end_text = span.split("-", 1)
        if start_text == "" and end_text == "":
            raise HTTPException(status_code=416, detail="Invalid range")
        try:
            if start_text == "":
                suffix = int(end_text)
                if suffix <= 0:
                    raise ValueError
                start = max(0, size - suffix)
            else:
                start = int(start_text)
                end = int(end_text) if end_text else size - 1
        except ValueError:
            raise HTTPException(status_code=416, detail="Invalid range")
        if start >= size or start > end:
            raise HTTPException(
                status_code=416,
                headers={"Content-Range": f"bytes */{size}"},
                detail="Range not satisfiable",
            )
        end = min(end, size - 1)
        status = 206

    length = 0 if size == 0 else end - start + 1
    headers = {"Accept-Ranges": "bytes", "Content-Length": str(length)}
    if status == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    return StreamingResponse(
        _file_chunks(full_path, start, length),
        status_code=status,
        media_type=media_type,
        headers=headers,
    )
