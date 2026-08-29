#!/usr/bin/env python3
"""Rebase the cumulative Russian mod onto the current game/PReact build.

The result is intentionally a thin overlay: current game assets remain owned by
the upstream archive, while the mod contains Russian stringtables, compatibility
aliases for legacy English-only lookup paths, reviewed native overrides and a
freshly compiled localized Preact entry bundle.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Juvio" / "heroes of newerth" / "resources0.jz"
HUMAN_BASE = ROOT / "build" / "human-ru" / "resources0.jz"
PREACT_DIST = ROOT / "src" / "extended_ru" / "preact" / "dist"
PREACT_REMOTE_DIST = ROOT / "src" / "extended_ru" / "preact-remote" / "dist"
OUTPUT = ROOT / "build" / "human-ru-current" / "resources0.jz"
REPORT = ROOT / "translation" / "reports" / "human_current_rebase.json"
CURRENT_NATIVE_REPORT = ROOT / "translation" / "reports" / "current_native_overrides.json"
LIVE_SNAPSHOT = ROOT / "translation" / "priority" / "live_scope_snapshot.json"
PREACT_MEMBERS = {
    "preact/dist/index.html": PREACT_DIST / "index.html",
    "preact/dist/index.js": PREACT_DIST / "index.js",
    "preact/dist/index.js.map": PREACT_DIST / "index.js.map",
    "preact/dist/assets/index.css": PREACT_DIST / "assets" / "index.css",
    "preact-remote/dist/index.html": PREACT_REMOTE_DIST / "index.html",
    "preact-remote/dist/index.js": PREACT_REMOTE_DIST / "index.js",
    "preact-remote/dist/assets/index.css": PREACT_REMOTE_DIST / "assets" / "index.css",
}
STRINGTABLE_DOMAINS = ("bot_messages", "client_messages", "entities", "game_messages", "interface")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_ZSTANDARD
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def build_once(path: Path, members: dict[str, bytes]) -> None:
    temporary = path.with_name(f".{path.name}.building")
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(temporary, "w", allowZip64=True) as archive:
        for name, data in sorted(members.items()):
            write_member(archive, name, data)
    temporary.replace(path)


def main() -> int:
    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required")
    snapshot = json.loads(LIVE_SNAPSHOT.read_text(encoding="utf-8"))
    if sha256(UPSTREAM) != snapshot["upstream"]["sha256"]:
        raise SystemExit("CURRENT upstream identity mismatch")
    human_report = json.loads((ROOT / "translation" / "reports" / "human_release_build.json").read_text(encoding="utf-8"))
    if human_report["result"] != "PASS" or sha256(HUMAN_BASE) != human_report["output"]["sha256"]:
        raise SystemExit("Human stringtable build is not a validated input")
    if any(not path.is_file() for path in PREACT_MEMBERS.values()):
        raise SystemExit("Fresh localized Preact dist is incomplete")

    override_report = json.loads((ROOT / "reports" / "phase2a_overrides.json").read_text(encoding="utf-8"))
    current_native = {row["source_file"] for row in override_report["native_files"]}
    current_runtime_native: dict[str, Path] = {}
    if CURRENT_NATIVE_REPORT.is_file():
        native_report = json.loads(CURRENT_NATIVE_REPORT.read_text(encoding="utf-8"))
        if native_report.get("result") != "PASS" or native_report.get("upstream_sha256") != snapshot["upstream"]["sha256"]:
            raise SystemExit("CURRENT native runtime overrides are not validated for this upstream")
        for row in native_report.get("files", []):
            path = Path(row["output"])
            if not path.is_file() or sha256(path) != row["sha256"]:
                raise SystemExit(f"CURRENT native runtime override identity mismatch: {path}")
            current_runtime_native[row["source_file"]] = path
    members: dict[str, bytes] = {}
    with zipfile.ZipFile(HUMAN_BASE) as old:
        if old.testzip() is not None:
            raise SystemExit("Human base CRC failed")
        for name in old.namelist():
            if name.endswith("/") or name.startswith("preact/"):
                continue
            # UI packages from the historical donor build are intentionally not
            # carried forward. They replace current Juvio screens wholesale and
            # caused stale matchmaking, Plinko, shop and role-priority layouts.
            # Only reviewed overrides rebuilt from the exact CURRENT upstream are
            # added below.
            if name == "core_ru.resources" or name.startswith("stringtables/"):
                members[name] = old.read(name)

    # Phase 2A native files were regenerated from the CURRENT upstream archive,
    # so they replace any same-named legacy override copied above.
    for name in sorted(current_native):
        path = ROOT / "src" / "extended_ru" / Path(name)
        if not path.is_file():
            raise SystemExit(f"Missing CURRENT native override: {name}")
        members[name] = path.read_bytes()
    for name, path in sorted(current_runtime_native.items()):
        members[name] = path.read_bytes()
    for name, path in PREACT_MEMBERS.items():
        members[name] = path.read_bytes()

    # Several legacy native UI paths ignore host_locale and always resolve the
    # English namespace. Runtime diagnosis proved that this produced raw keys or
    # English labels even though the matching RU entries existed. Alias the exact
    # current Russian tables instead of restoring stale whole-screen UI packages.
    for domain in STRINGTABLE_DOMAINS:
        ru_name = f"stringtables/{domain}_ru.str"
        if ru_name not in members:
            raise SystemExit(f"Required Russian stringtable missing: {ru_name}")
        members[f"stringtables/{domain}_en.str"] = members[ru_name]

    required = {
        "core_ru.resources", "stringtables/entities_ru.str",
        "stringtables/interface_ru.str",
        *(f"stringtables/{domain}_en.str" for domain in STRINGTABLE_DOMAINS),
        *PREACT_MEMBERS,
    }
    if missing := sorted(required - members.keys()):
        raise SystemExit(f"Required thin-overlay members missing: {missing}")

    errors: list[dict[str, object]] = []
    preact_js = members["preact/dist/index.js"].decode("utf-8")
    cyrillic = len(re.findall(r"[А-Яа-яЁё]", preact_js))
    if cyrillic < 2000:
        errors.append({"code": "PREACT_LOCALIZATION_NOT_PRESENT", "cyrillic_characters": cyrillic})
    entities = members["stringtables/entities_ru.str"].decode("utf-8-sig")
    for forbidden in ("Посох Мастера", "посох мастера", "Персонал Мастера", "персонал мастера"):
        if forbidden in entities:
            errors.append({"code": "FORBIDDEN_STAFF_ALIAS", "span": forbidden})

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    build_once(OUTPUT, members)
    first = sha256(OUTPUT)
    repeat = OUTPUT.with_name(f".{OUTPUT.stem}.repeat{OUTPUT.suffix}")
    build_once(repeat, members)
    second = sha256(repeat)
    repeat.unlink()
    with zipfile.ZipFile(OUTPUT) as built:
        corrupt = built.testzip()
        names = sorted(name for name in built.namelist() if not name.endswith("/"))
    if first != second:
        errors.append({"code": "NONDETERMINISTIC_ARCHIVE", "first": first, "second": second})
    if corrupt:
        errors.append({"code": "CRC_FAILURE", "member": corrupt})
    if names != sorted(members):
        errors.append({"code": "MEMBER_SET_MISMATCH"})

    result = {
        "schema_version": 1,
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "upstream": {"path": str(UPSTREAM), "sha256": sha256(UPSTREAM), "unchanged": True},
        "human_input": {"path": str(HUMAN_BASE), "sha256": sha256(HUMAN_BASE), "reviewed_keys": human_report["reviewed_keys"]},
        "preact": {"source": str(PREACT_DIST), "translated_literals": override_report["preact_literals"], "cyrillic_characters": cyrillic},
        "native_current_files": len(current_native) + len(current_runtime_native),
        "legacy_locale_aliases": list(STRINGTABLE_DOMAINS),
        "output": {"path": str(OUTPUT), "sha256": first, "size_bytes": OUTPUT.stat().st_size, "members": len(names), "crc": "PASS" if not corrupt else "FAIL"},
        "thin_overlay": True,
        "installed": False,
        "runtime_verified": False,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
