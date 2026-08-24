#!/usr/bin/env python3
"""Build a deterministic, donor-only HoN localization overlay.

The builder reads exactly five pinned HoN_RU_Pack string tables and creates a
minimal resources0.jz.  It does not invoke donor scripts or read Pass C.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path


EXPECTED_COMMIT = "9f276bf86037bffe9e6d208dacd99d19b4e666eb"
TABLES = (
    "bot_messages_en.str",
    "client_messages_en.str",
    "entities_en.str",
    "game_messages_en.str",
    "interface_en.str",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(donor: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(donor), *args], text=True, encoding="utf-8"
    ).strip()


def write_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_ZSTANDARD
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required for ZIP Zstandard output")

    donor = args.donor.resolve()
    output = args.output.resolve()
    report_path = args.report.resolve()
    commit = git(donor, "rev-parse", "HEAD")
    if commit != EXPECTED_COMMIT:
        raise SystemExit(f"Donor commit mismatch: {commit}")
    status = git(donor, "status", "--porcelain")
    if status:
        raise SystemExit("Donor worktree must be clean")

    source_files: list[dict[str, object]] = []
    members: dict[str, bytes] = {}
    for filename in TABLES:
        source = donor / "bundle" / filename
        if not source.is_file():
            raise SystemExit(f"Missing donor table: {source}")
        data = source.read_bytes()
        member = f"stringtables/{filename}"
        members[member] = data
        source_files.append(
            {
                "source": str(source),
                "member": member,
                "size_bytes": len(data),
                "sha256": sha256_bytes(data),
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.building")
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(temporary, "w", allowZip64=True) as archive:
        for name in sorted(members):
            write_member(archive, name, members[name])
    temporary.replace(output)

    with zipfile.ZipFile(output) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        corrupt = archive.testzip()
        if names != sorted(members):
            raise SystemExit(f"Archive member mismatch: {names}")
        for name, expected in members.items():
            if archive.read(name) != expected:
                raise SystemExit(f"Archive content mismatch: {name}")
    if corrupt is not None:
        raise SystemExit(f"Archive CRC failed: {corrupt}")
    if any(name.endswith("_ru.str") for name in names):
        raise SystemExit("Unexpected Pass C/Russian-locale table in donor overlay")

    report = {
        "result": "PASS",
        "purpose": "DONOR_TEST_0_RUNTIME_PREVIEW_ONLY",
        "donor": {
            "path": str(donor),
            "commit": commit,
            "worktree": "clean",
        },
        "output": {
            "path": str(output),
            "sha256": sha256_file(output),
            "size_bytes": output.stat().st_size,
            "crc": "PASS",
        },
        "members": names,
        "source_files": source_files,
        "member_count": len(names),
        "locale": "en",
        "contains_pass_c": False,
        "contains_upstream_archive": False,
        "donor_scripts_invoked": False,
    }
    write_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
