#!/usr/bin/env python3
"""Build a deterministic font/readability test archive over Phase 2A."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_member(zf: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_ZSTANDARD
    info.external_attr = 0o644 << 16
    zf.writestr(info, data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required for ZIP Zstandard output")
    root = args.project_root.resolve()
    base = (args.base or root / "build" / "phase2a" / "resources0.jz").resolve()
    output = (args.output or root / "build" / "font-readability" / "resources0.jz").resolve()
    overrides_root = root / "src" / "font_readability_ru"
    overrides = {
        path.relative_to(overrides_root).as_posix(): path.read_bytes()
        for path in sorted(overrides_root.rglob("*")) if path.is_file()
    }
    required = {"core_ru.resources", "ui/hd_ui/styles.package", "preact/dist/assets/index.css"}
    if set(overrides) != required:
        raise SystemExit(f"unexpected override set: {sorted(overrides)}")

    with zipfile.ZipFile(base) as source:
        if source.testzip():
            raise SystemExit("base Phase 2A archive failed CRC validation")
        files = {name: source.read(name) for name in source.namelist() if not name.endswith("/")}
    files.update(overrides)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", allowZip64=True) as target:
        for name, data in sorted(files.items()):
            write_member(target, name, data)
    with zipfile.ZipFile(output) as check:
        corrupt = check.testzip()
        members = check.namelist()
    report = {
        "result": "PASS" if not corrupt else "FAIL",
        "base": {"path": str(base), "sha256": sha256(base)},
        "output": {"path": str(output), "sha256": sha256(output), "size_bytes": output.stat().st_size},
        "members": len(members),
        "overrides": sorted(overrides),
        "crc_error": corrupt,
        "installed": False,
    }
    report_path = root / "reports" / "font_readability_build.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not corrupt else 2


if __name__ == "__main__":
    raise SystemExit(main())
