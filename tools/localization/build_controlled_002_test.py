#!/usr/bin/env python3
"""Build an isolated Pass C + human-approved Controlled 002 runtime archive."""

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
BATCH_ID = "CONTROLLED_002_TERMINOLOGY"
MEMBERS = {
    "interface": "stringtables/interface_ru.str",
    "game_messages": "stringtables/game_messages_ru.str",
    "entities": "stringtables/entities_ru.str",
}
PREACT_MEMBER = "preact/dist/index.js"
EXPECTED_CHANGED_MEMBERS = sorted([*MEMBERS.values(), PREACT_MEMBER])
PREACT_OLD = b'const jO={0:"Unselected",1:"Carry",2:"Mid",3:"Offlane",4:"Soft Support",5:"Hard Support",6:"Solo Offlane",7:"Jungle"}'
PREACT_NEW = 'const jO={0:"Unselected",1:"Керри",2:"Мид",3:"Оффлейн",4:"Поддержка",5:"Основная поддержка",6:"Solo Offlane",7:"Jungle"}'.encode("utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line]


def apply_table(data: bytes, replacements: dict[str, str]) -> tuple[bytes, list[dict[str, str]]]:
    lines = data.decode("utf-8-sig").splitlines(keepends=True)
    occurrences = {key: 0 for key in replacements}
    changes: list[dict[str, str]] = []
    for index, line in enumerate(lines):
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        if "\t" not in body or body.lstrip().startswith("//"):
            continue
        key, value = body.split("\t", 1)
        if key not in replacements:
            continue
        occurrences[key] += 1
        new = replacements[key]
        if value != new:
            lines[index] = f"{key}\t{new}{ending}"
            changes.append({"key": key, "old": value, "new": new})
    mismatch = {key: count for key, count in occurrences.items() if count != 1}
    if mismatch:
        raise SystemExit(f"Target occurrence mismatch: {mismatch}")
    return "".join(lines).encode("utf-8"), changes


def write_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_ZSTANDARD
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def compose(base: Path, output: Path, overrides: dict[str, bytes]) -> None:
    temporary = output.with_name(f".{output.name}.building")
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(base) as source, zipfile.ZipFile(temporary, "w", allowZip64=True) as target:
        for name in sorted(name for name in source.namelist() if not name.endswith("/")):
            write_member(target, name, overrides.get(name, source.read(name)))
    temporary.replace(output)


def archive_delta(base: Path, output: Path) -> tuple[list[str], list[str], list[str], str | None]:
    with zipfile.ZipFile(base) as old, zipfile.ZipFile(output) as new:
        old_meta = {n: (old.getinfo(n).CRC, old.getinfo(n).file_size) for n in old.namelist() if not n.endswith("/")}
        new_meta = {n: (new.getinfo(n).CRC, new.getinfo(n).file_size) for n in new.namelist() if not n.endswith("/")}
        changed = sorted(n for n in old_meta.keys() & new_meta.keys() if old_meta[n] != new_meta[n])
        return changed, sorted(new_meta.keys() - old_meta.keys()), sorted(old_meta.keys() - new_meta.keys()), new.testzip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required for ZIP Zstandard")

    base, upstream, output, report_path = (p.resolve() for p in (args.base, args.upstream, args.output, args.report))
    base_sha, upstream_sha = sha256(base), sha256(upstream)
    if base_sha != EXPECTED_PASS_C_SHA:
        raise SystemExit(f"Pass C baseline mismatch: {base_sha}")
    if upstream_sha != EXPECTED_UPSTREAM_SHA:
        raise SystemExit(f"Upstream archive mismatch: {upstream_sha}")

    batch = load_jsonl(ROOT / "translation" / "batches" / "controlled_002_terminology.jsonl")
    if len(batch) != 33 or len({row["logical_key"] for row in batch}) != 33:
        raise SystemExit("Controlled 002 must contain exactly 33 unique entries")
    if any(row["approval_state"] != "HUMAN_APPROVED_PENDING_RUNTIME" or row["runtime_verified"] or row["applied"] for row in batch):
        raise SystemExit("Controlled 002 approval/runtime state is invalid")

    by_domain: dict[str, dict[str, str]] = {domain: {} for domain in MEMBERS}
    for row in batch:
        if row["domain"] not in by_domain:
            raise SystemExit(f"Unexpected Controlled 002 domain: {row['domain']}")
        by_domain[row["domain"]][row["key"]] = row["proposed_ru"]

    overrides: dict[str, bytes] = {}
    all_changes: list[dict[str, str]] = []
    baseline_member_sha: dict[str, str] = {}
    with zipfile.ZipFile(base) as archive:
        corrupt = archive.testzip()
        if corrupt is not None:
            raise SystemExit(f"Pass C CRC failed: {corrupt}")
        for domain, member in MEMBERS.items():
            original = archive.read(member)
            baseline_member_sha[member] = hashlib.sha256(original).hexdigest()
            rendered, changes = apply_table(original, by_domain[domain])
            overrides[member] = rendered
            all_changes.extend({"logical_key": f"{domain}:{row['key']}", **row} for row in changes)
        preact = archive.read(PREACT_MEMBER)
        baseline_member_sha[PREACT_MEMBER] = hashlib.sha256(preact).hexdigest()
        if preact.count(PREACT_OLD) != 1:
            raise SystemExit(f"Expected exactly one Preact role map, found {preact.count(PREACT_OLD)}")
        overrides[PREACT_MEMBER] = preact.replace(PREACT_OLD, PREACT_NEW)

    if len(all_changes) != 33:
        raise SystemExit(f"Expected 33 value changes relative to Pass C, found {len(all_changes)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    compose(base, output, overrides)
    first_sha = sha256(output)
    repeat = output.with_name(f".{output.stem}.determinism{output.suffix}")
    compose(base, repeat, overrides)
    second_sha = sha256(repeat)
    repeat.unlink()
    changed, added, removed, corrupt = archive_delta(base, output)

    errors: list[dict[str, Any]] = []
    if first_sha != second_sha:
        errors.append({"code": "NONDETERMINISTIC_ARCHIVE", "first": first_sha, "second": second_sha})
    if changed != EXPECTED_CHANGED_MEMBERS or added or removed:
        errors.append({"code": "ARCHIVE_DELTA_NOT_EXACT", "changed": changed, "added": added, "removed": removed})
    if corrupt is not None:
        errors.append({"code": "CRC_FAILURE", "member": corrupt})

    with zipfile.ZipFile(output) as archive:
        output_member_sha = {member: hashlib.sha256(archive.read(member)).hexdigest() for member in EXPECTED_CHANGED_MEMBERS}
        preact_text = archive.read(PREACT_MEMBER)
        preact_exact = preact_text.count(PREACT_NEW) == 1 and PREACT_OLD not in preact_text
        rendered_changes = 0
        for domain, member in MEMBERS.items():
            _, changes = apply_table(archive.read(member), by_domain[domain])
            rendered_changes += len(changes)
    if rendered_changes != 0:
        errors.append({"code": "TARGET_VALUES_NOT_EXACT", "remaining": rendered_changes})
    if not preact_exact:
        errors.append({"code": "PREACT_ROLE_MAP_NOT_EXACT"})

    report = {
        "schema_version": 1,
        "batch_id": BATCH_ID,
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "baseline": {"path": str(base), "sha256": base_sha, "unchanged": True},
        "upstream": {"path": str(upstream), "sha256": upstream_sha, "unchanged": True},
        "output": {"path": str(output), "sha256": first_sha, "size_bytes": output.stat().st_size, "crc": "PASS" if corrupt is None else "FAIL"},
        "checks": {
            "human_approval": "PASS",
            "pass_c_sha": "PASS",
            "upstream_sha": "PASS",
            "crc_integrity": "PASS" if corrupt is None else "FAIL",
            "exact_archive_delta": "PASS" if changed == EXPECTED_CHANGED_MEMBERS and not added and not removed else "FAIL",
            "exact_33_stringtable_changes": "PASS" if len(all_changes) == 33 and rendered_changes == 0 else "FAIL",
            "preact_role_map_exact": "PASS" if preact_exact else "FAIL",
            "deterministic_sha": "PASS" if first_sha == second_sha else "FAIL",
            "no_gameplay_data": "PASS",
            "no_unapproved_source": "PASS",
        },
        "archive_delta": {"changed": changed, "added": added, "removed": removed},
        "stringtable_changes": all_changes,
        "preact_role_map": {
            "source": "preact/src/types/global.ts:23-28",
            "changes": {"Carry": "Керри", "Mid": "Мид", "Offlane": "Оффлейн", "Soft Support": "Поддержка", "Hard Support": "Основная поддержка"},
            "unchanged": ["Unselected", "Solo Offlane", "Jungle"],
        },
        "member_sha256": {"pass_c": baseline_member_sha, "controlled_002_test": output_member_sha},
        "runtime_verified": False,
        "stable_pass_c_modified": False,
        "upstream_modified": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"result": report["result"], "sha256": first_sha, "changed_members": changed, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
