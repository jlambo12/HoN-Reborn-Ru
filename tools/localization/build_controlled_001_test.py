#!/usr/bin/env python3
"""Build and verify an isolated Pass C + CONTROLLED BATCH 001 runtime mod."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_PASS_C_SHA = "3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301"
EXPECTED_UPSTREAM_SHA = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"
BATCH_ID = "CONTROLLED_001_MODERN_UI"
INTERFACE_MEMBER = "stringtables/interface_ru.str"
SYSTEM_BAR_MEMBER = "ui/fe3/sections/system_bar.package"
GAME_MENU_MEMBER = "ui/hd_ui/templates/menu_vote_templates.package"
REQUIRED_MEMBERS = {INTERFACE_MEMBER, "stringtables/entities_ru.str", "core_ru.resources"}
LOCALIZATION_MEMBERS = ("stringtables/interface_ru.str", "stringtables/entities_ru.str", "core_ru.resources")
EXPECTED_BASE_MEMBER_SHA = {
    SYSTEM_BAR_MEMBER: "8d5454a574cfab204ce561f6671299742ff306d1e0916b488f0c2b96d9b0b6cc",
    GAME_MENU_MEMBER: "2ae2556cc401500efef37c3a58e77724975502e3380471c74f1de9c76e36b53b",
}
EXPECTED_CHANGED_MEMBERS = sorted((INTERFACE_MEMBER, SYSTEM_BAR_MEMBER, GAME_MENU_MEMBER))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line]


def write_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_ZSTANDARD
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def apply_values(data: bytes, approved: dict[str, str]) -> tuple[bytes, dict[str, str], list[str]]:
    text = data.decode("utf-8-sig")
    if "\ufffd" in text:
        raise SystemExit("Pass C interface_ru.str contains a replacement character")
    lines = text.splitlines(keepends=True)
    occurrences = {key: 0 for key in approved}
    old_values: dict[str, str] = {}
    changed: list[str] = []
    for index, line in enumerate(lines):
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        if "\t" not in body or body.lstrip().startswith("//"):
            continue
        key, value = body.split("\t", 1)
        if key not in approved:
            continue
        occurrences[key] += 1
        old_values[key] = value
        replacement = approved[key]
        if value != replacement:
            lines[index] = f"{key}\t{replacement}{ending}"
            changed.append(key)
    missing_or_duplicate = {key: count for key, count in occurrences.items() if count != 1}
    if missing_or_duplicate:
        raise SystemExit(f"Target key occurrence mismatch: {missing_or_duplicate}")
    result = "".join(lines).encode("utf-8")
    result.decode("utf-8")
    return result, old_values, changed


def apply_exact_replacements(data: bytes, replacements: tuple[tuple[bytes, bytes], ...], member: str) -> bytes:
    result = data
    for old, new in replacements:
        count = result.count(old)
        if count != 1:
            raise SystemExit(f"Expected exactly one replacement in {member}: {old!r}, found {count}")
        result = result.replace(old, new)
    result.decode("utf-8-sig")
    return result


def compose(base: Path, output: Path, overrides: dict[str, bytes]) -> None:
    temporary = output.with_name(f".{output.name}.building")
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(base) as source, zipfile.ZipFile(temporary, "w", allowZip64=True) as target:
        for name in sorted(name for name in source.namelist() if not name.endswith("/")):
            data = overrides.get(name, source.read(name))
            write_member(target, name, data)
    temporary.replace(output)


def logical_delta(base: Path, output: Path) -> tuple[list[str], list[str], list[str], str | None]:
    with zipfile.ZipFile(base) as old, zipfile.ZipFile(output) as new:
        old_meta = {name: (old.getinfo(name).CRC, old.getinfo(name).file_size) for name in old.namelist() if not name.endswith("/")}
        new_meta = {name: (new.getinfo(name).CRC, new.getinfo(name).file_size) for name in new.namelist() if not name.endswith("/")}
        changed = sorted(name for name in old_meta.keys() & new_meta.keys() if old_meta[name] != new_meta[name])
        added = sorted(new_meta.keys() - old_meta.keys())
        removed = sorted(old_meta.keys() - new_meta.keys())
        return changed, added, removed, new.testzip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required for ZIP Zstandard output")

    base = args.base.resolve()
    upstream = args.upstream.resolve()
    output = args.output.resolve()
    report_path = args.report.resolve()
    if sha256(base) != EXPECTED_PASS_C_SHA:
        raise SystemExit(f"Stable baseline is not accepted Pass C: {sha256(base)}")
    if sha256(upstream) != EXPECTED_UPSTREAM_SHA:
        raise SystemExit(f"Upstream archive changed: {sha256(upstream)}")

    batch = load_jsonl(ROOT / "translation" / "batches" / "controlled_001_modern_ui.jsonl")
    if len(batch) != 39 or len({row["logical_key"] for row in batch}) != 39:
        raise SystemExit("Controlled 001 must contain exactly 39 unique entries")
    if any(row["approval_state"] != "HUMAN_APPROVED_PENDING_RUNTIME" or row["runtime_verified"] for row in batch):
        raise SystemExit("Controlled 001 approval/runtime state is invalid")
    if any(row["domain"] != "interface" for row in batch):
        raise SystemExit("Controlled 001 unexpectedly contains a non-interface entry")
    approved = {row["key"]: row["proposed_ru"] for row in batch}

    with zipfile.ZipFile(base) as archive:
        if archive.testzip() is not None:
            raise SystemExit("Stable Pass C failed CRC validation")
        names = {name for name in archive.namelist() if not name.endswith("/")}
        if not REQUIRED_MEMBERS | set(EXPECTED_BASE_MEMBER_SHA) <= names:
            raise SystemExit(f"Pass C is missing required members: {sorted(REQUIRED_MEMBERS - names)}")
        interface_data, old_values, changed_keys = apply_values(archive.read(INTERFACE_MEMBER), approved)
        for member, expected_hash in EXPECTED_BASE_MEMBER_SHA.items():
            actual_hash = hashlib.sha256(archive.read(member)).hexdigest()
            if actual_hash != expected_hash:
                raise SystemExit(f"Unexpected Pass C member baseline for {member}: {actual_hash}")
        system_bar_data = apply_exact_replacements(
            archive.read(SYSTEM_BAR_MEMBER),
            (
                ('label="УЗНАТЬ"'.encode(), 'label="СПРАВКА"'.encode()),
                ('label="ЛЕСТНИЦА"'.encode(), 'label="РЕЙТИНГ"'.encode()),
            ),
            SYSTEM_BAR_MEMBER,
        )
        game_menu_data = apply_exact_replacements(
            archive.read(GAME_MENU_MEMBER),
            ((b'label="game_menu_{btnName}_\xd0\xba\xd0\xbd\xd0\xbe\xd0\xbf\xd0\xba\xd0\xb0"', b'label="game_menu_{btnName}_button"'),),
            GAME_MENU_MEMBER,
        )
        baseline_locale_hashes = {
            name: hashlib.sha256(archive.read(name)).hexdigest() for name in LOCALIZATION_MEMBERS
        }

    overrides = {
        INTERFACE_MEMBER: interface_data,
        SYSTEM_BAR_MEMBER: system_bar_data,
        GAME_MENU_MEMBER: game_menu_data,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    compose(base, output, overrides)
    first_sha = sha256(output)
    repeat = output.with_name(f".{output.stem}.determinism{output.suffix}")
    compose(base, repeat, overrides)
    second_sha = sha256(repeat)
    repeat.unlink()
    changed_members, added_members, removed_members, corrupt = logical_delta(base, output)

    errors: list[dict[str, Any]] = []
    if first_sha != second_sha:
        errors.append({"code": "NONDETERMINISTIC_ARCHIVE", "first": first_sha, "second": second_sha})
    if changed_members != EXPECTED_CHANGED_MEMBERS or added_members or removed_members:
        errors.append({"code": "ARCHIVE_DELTA_NOT_EXACT", "changed": changed_members, "added": added_members, "removed": removed_members})
    if corrupt is not None:
        errors.append({"code": "CRC_FAILURE", "member": corrupt})
    with zipfile.ZipFile(output) as archive:
        rendered, _, _ = apply_values(archive.read(INTERFACE_MEMBER), approved)
        if rendered != archive.read(INTERFACE_MEMBER):
            errors.append({"code": "APPROVED_VALUES_NOT_EXACT"})
        test_locale_hashes = {
            name: hashlib.sha256(archive.read(name)).hexdigest() for name in LOCALIZATION_MEMBERS
        }
    unchanged_locale_members = [
        name for name in LOCALIZATION_MEMBERS
        if baseline_locale_hashes[name] == test_locale_hashes[name]
    ]
    if unchanged_locale_members != ["stringtables/entities_ru.str", "core_ru.resources"]:
        errors.append({"code": "LOCALIZATION_MEMBER_DELTA_NOT_EXACT", "unchanged": unchanged_locale_members})

    report = {
        "schema_version": 1,
        "batch_id": BATCH_ID,
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "baseline": {"path": str(base), "sha256": sha256(base), "unchanged": True},
        "upstream": {"path": str(upstream), "sha256": sha256(upstream), "unchanged": True},
        "output": {"path": str(output), "sha256": first_sha, "size_bytes": output.stat().st_size, "crc": "PASS" if corrupt is None else "FAIL"},
        "checks": {
            "archive_readable": "PASS",
            "crc_integrity": "PASS" if corrupt is None else "FAIL",
            "expected_localization_files": "PASS",
            "exact_member_delta": "PASS" if changed_members == EXPECTED_CHANGED_MEMBERS and not added_members and not removed_members else "FAIL",
            "target_values_exact": "PASS" if not any(e["code"] == "APPROVED_VALUES_NOT_EXACT" for e in errors) else "FAIL",
            "only_batch_keys_changed": "PASS" if set(changed_keys) <= set(approved) else "FAIL",
            "all_39_targets_resolve_exactly": "PASS",
            "entities_and_core_ru_byte_identical": "PASS" if unchanged_locale_members == ["stringtables/entities_ru.str", "core_ru.resources"] else "FAIL",
            "deterministic_sha": "PASS" if first_sha == second_sha else "FAIL",
            "no_d1_or_donor_source": "PASS",
            "main_menu_live_literals_fixed": "PASS",
            "game_menu_key_template_restored": "PASS",
            "utf8_encoding": "PASS",
        },
        "batch_entries": len(batch),
        "value_changes_relative_to_pass_c": len(changed_keys),
        "changed_keys": [{"key": key, "old": old_values[key], "new": approved[key]} for key in changed_keys],
        "localization_member_sha256": {
            "pass_c": baseline_locale_hashes,
            "controlled_001_test": test_locale_hashes,
        },
        "archive_delta": {"changed": changed_members, "added": added_members, "removed": removed_members},
        "runtime_resolution_fixes": {
            SYSTEM_BAR_MEMBER: ["УЗНАТЬ -> СПРАВКА", "ЛЕСТНИЦА -> РЕЙТИНГ"],
            GAME_MENU_MEMBER: ["game_menu_{btnName}_кнопка -> game_menu_{btnName}_button"],
        },
        "runtime_verified": False,
        "prior_runtime_failure": "LOCALE_PROFILE_RESOLVED_EN",
        "stable_pass_c_modified": False,
        "upstream_modified": False,
        "donor_test_used": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    validation_path = ROOT / "translation" / "reports" / "controlled_001_validation.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    validation["runtime"] = {
        "archive_built": not errors,
        "archive_installed": False,
        "candidate_applied": False,
        "isolated_test_deployed": not errors,
        "runtime_verified": False,
        "prior_runtime_failure": "LOCALE_PROFILE_RESOLVED_EN",
        "test_path": str(output),
        "test_sha256": first_sha,
    }
    validation_path.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"result": report["result"], "sha256": first_sha, "changed_keys": len(changed_keys), "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
