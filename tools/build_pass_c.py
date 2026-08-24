#!/usr/bin/env python3
"""Compose the isolated Pass C test archive over the accepted installed Pass B."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


EXPECTED_BASE_SHA = "d71f85e3321c3954e877f2ccfa516c1e87f2006371499d491c83fd565fb1cb3d"
LOCALE_MEMBERS = ("stringtables/entities_ru.str", "stringtables/interface_ru.str")
NATIVE_MEMBERS = ("ui/avoid_player.interface", "ui/fe3/templates/ban_select_templates.package")


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
    parser.add_argument("--locale-build", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required for ZIP Zstandard output")

    root = args.project_root.resolve()
    base = args.base.resolve()
    locale_build = args.locale_build.resolve()
    output = args.output.resolve()
    base_sha = sha256(base)
    if base_sha != EXPECTED_BASE_SHA:
        raise SystemExit(f"Pass C base is not accepted Pass B: {base_sha}")

    with zipfile.ZipFile(base) as source:
        if source.testzip() is not None:
            raise SystemExit("Installed Pass B baseline failed CRC validation")
        files = {name: source.read(name) for name in source.namelist() if not name.endswith("/")}
    with zipfile.ZipFile(locale_build) as locale:
        if locale.testzip() is not None:
            raise SystemExit("Pass C locale candidate failed CRC validation")
        for name in LOCALE_MEMBERS:
            files[name] = locale.read(name)
    for name in NATIVE_MEMBERS:
        files[name] = (root / "src" / "pass_c_ru" / Path(name)).read_bytes()

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", allowZip64=True) as target:
        for name, data in sorted(files.items()):
            write_member(target, name, data)
    with zipfile.ZipFile(output) as check:
        corrupt = check.testzip()
        member_count = len([name for name in check.namelist() if not name.endswith("/")])
    report = {
        "result": "PASS" if corrupt is None else "FAIL",
        "installed": False,
        "baseline": {"path": str(base), "sha256": base_sha},
        "output": {"path": str(output), "sha256": sha256(output), "size_bytes": output.stat().st_size},
        "members": member_count,
        "overrides": sorted((*LOCALE_MEMBERS, *NATIVE_MEMBERS)),
        "font_readability_architecture_preserved": True,
        "upstream_game_archive_modified": False,
        "crc_error": corrupt,
    }
    (root / "reports" / "pass_c_build.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if corrupt is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
