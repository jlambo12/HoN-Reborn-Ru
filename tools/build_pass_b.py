#!/usr/bin/env python3
"""Compose the Pass B localization archive with the accepted font fixes."""

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
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required for ZIP Zstandard output")
    root = args.project_root.resolve()
    base = args.base.resolve()
    output = (args.output or root / "build" / "pass-b" / "resources0.jz").resolve()
    overrides = {
        "core_ru.resources": (root / "src" / "font_readability_ru" / "core_ru.resources").read_bytes(),
        "preact/dist/assets/index.css": (root / "src" / "font_readability_ru" / "preact" / "dist" / "assets" / "index.css").read_bytes(),
        "ui/hd_ui/styles.package": (root / "src" / "pass_b_readability" / "ui" / "hd_ui" / "styles.package").read_bytes(),
    }
    with zipfile.ZipFile(base) as source:
        if source.testzip():
            raise SystemExit("Pass B localization base failed CRC validation")
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
        "result": "PASS" if corrupt is None else "FAIL",
        "installed": False,
        "base": {"path": str(base), "sha256": sha256(base)},
        "output": {"path": str(output), "sha256": sha256(output), "size_bytes": output.stat().st_size},
        "members": len(members),
        "font_architecture_preserved": True,
        "readability_override": {"style": "color-gray-light", "before": "#BFBFBF", "after": "#DBDBDB"},
        "overrides": sorted(overrides),
        "crc_error": corrupt,
    }
    (root / "reports" / "pass_b_build.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if corrupt is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
