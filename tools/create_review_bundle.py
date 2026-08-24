#!/usr/bin/env python3
"""Create the architecture-review bundle without game/media/build payloads."""

from __future__ import annotations

import argparse
import os
import zipfile
from pathlib import Path


TEXT_SUFFIXES = {
    ".bat", ".cjs", ".css", ".csv", ".d.ts", ".html", ".interface",
    ".js", ".json", ".jsonl", ".jsx", ".lock", ".lua", ".md", ".mjs",
    ".package", ".ps1", ".py", ".resources", ".str", ".ts", ".tsx",
    ".txt", ".xml", ".yaml", ".yml",
}
ROOT_FILES = {".gitignore", "README.md", "project.json"}
ROOT_DIRS = {"docs", "catalog", "reports", "tools", "scripts", "src", "tests", "translations"}
EXCLUDED_PARTS = {".git", "__pycache__", "node_modules", "backups", "build", "cache", "temp"}
MEDIA_SUFFIXES = {
    ".7z", ".avi", ".bin", ".bmp", ".dds", ".exe", ".gif", ".glb", ".gltf",
    ".ico", ".jpeg", ".jpg", ".jz", ".m4a", ".mkv", ".model", ".mov", ".mp3",
    ".mp4", ".ogg", ".png", ".psd", ".tga", ".ttf", ".wav", ".webm", ".webp",
    ".woff", ".woff2", ".zip",
}


def include(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if rel.as_posix() in ROOT_FILES:
        return True
    if not rel.parts or rel.parts[0] not in ROOT_DIRS:
        return False
    lowered = {part.lower() for part in rel.parts}
    if lowered & EXCLUDED_PARTS:
        return False
    if path.suffix.lower() in MEDIA_SUFFIXES:
        return False
    # Catalog and reports are explicit review artifacts; source directories are
    # restricted to textual/build-description files to avoid bundled media.
    if rel.parts[0] in {"catalog", "reports", "docs", "tools", "scripts", "tests", "translations"}:
        return True
    suffixes = "".join(path.suffixes[-2:]).lower()
    return path.suffix.lower() in TEXT_SUFFIXES or suffixes in TEXT_SUFFIXES or path.name in {"bun.lock", "package-lock.json"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    output = args.output.resolve()
    if output.parent != root or output.name not in {"HoN-Reborn-RU-review-bundle-v2.zip", "HoN-Reborn-RU-review-bundle-v3.zip", "HoN-Reborn-RU-phase2a-review.zip"}:
        raise SystemExit(f"Unsafe/unexpected output: {output}")
    files = sorted(
        (path for path in root.rglob("*") if path.is_file() and include(path, root)),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    temp = output.with_suffix(".zip.tmp")
    if temp.exists():
        temp.unlink()
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            rel = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(2026, 8, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes(), compresslevel=9)
    os.replace(temp, output)
    print(f"path={output}")
    print(f"size_bytes={output.stat().st_size}")
    print(f"file_count={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
