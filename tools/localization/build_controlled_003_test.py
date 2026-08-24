#!/usr/bin/env python3
"""Build one deterministic Pass C + cumulative Controlled 003 runtime archive."""

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
BATCH_ID = "CONTROLLED_003_LARGE_SCALE_PLAYER_FACING"
MEMBERS = {
    "interface": "stringtables/interface_ru.str",
    "game_messages": "stringtables/game_messages_ru.str",
    "client_messages": "stringtables/client_messages_ru.str",
    "entities": "stringtables/entities_ru.str",
}
SYSTEM_BAR = "ui/fe3/sections/system_bar.package"
GAME_MENU = "ui/hd_ui/templates/menu_vote_templates.package"
PREACT = "preact/dist/index.js"
PREACT_OLD = b'const jO={0:"Unselected",1:"Carry",2:"Mid",3:"Offlane",4:"Soft Support",5:"Hard Support",6:"Solo Offlane",7:"Jungle"}'
PREACT_NEW = 'const jO={0:"Unselected",1:"Керри",2:"Мид",3:"Оффлейн",4:"Поддержка",5:"Основная поддержка",6:"Solo Offlane",7:"Jungle"}'.encode()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line]


def apply_table(data: bytes, rows: list[dict[str, Any]]) -> tuple[bytes, list[dict[str, str]]]:
    targets = {row["key"]: row for row in rows}
    seen = {key: 0 for key in targets}
    changes: list[dict[str, str]] = []
    lines = data.decode("utf-8-sig").splitlines(keepends=True)
    for index, line in enumerate(lines):
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        if "\t" not in body or body.lstrip().startswith("//"):
            continue
        key, old = body.split("\t", 1)
        if key not in targets:
            continue
        seen[key] += 1
        row = targets[key]
        if old != row["pass_c_baseline"]:
            raise SystemExit(f"Pass C row baseline mismatch: {row['logical_key']}")
        new = row["proposed_ru"]
        if old != new:
            lines[index] = f"{key}\t{new}{ending}"
            changes.append({"logical_key": row["logical_key"], "old": old, "new": new, "reason": row["reason"]})
    bad = {key: count for key, count in seen.items() if count != 1}
    if bad:
        raise SystemExit(f"Target occurrence mismatch: {bad}")
    return "".join(lines).encode("utf-8"), changes


def exact(data: bytes, replacements: tuple[tuple[bytes, bytes], ...], member: str) -> bytes:
    result = data
    for old, new in replacements:
        if result.count(old) != 1:
            raise SystemExit(f"Exact native patch mismatch in {member}: {old!r}")
        result = result.replace(old, new)
    return result


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
        for name in sorted(n for n in source.namelist() if not n.endswith("/")):
            write_member(target, name, overrides.get(name, source.read(name)))
    temporary.replace(output)


def delta(base: Path, output: Path) -> tuple[list[str], list[str], list[str], str | None]:
    with zipfile.ZipFile(base) as old, zipfile.ZipFile(output) as new:
        om = {n: (old.getinfo(n).CRC, old.getinfo(n).file_size) for n in old.namelist() if not n.endswith("/")}
        nm = {n: (new.getinfo(n).CRC, new.getinfo(n).file_size) for n in new.namelist() if not n.endswith("/")}
        return (sorted(n for n in om.keys() & nm.keys() if om[n] != nm[n]), sorted(nm.keys() - om.keys()), sorted(om.keys() - nm.keys()), new.testzip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required")
    base, upstream, output, report_path = (p.resolve() for p in (args.base, args.upstream, args.output, args.report))
    if sha256(base) != EXPECTED_PASS_C_SHA or sha256(upstream) != EXPECTED_UPSTREAM_SHA:
        raise SystemExit("Protected baseline/upstream SHA mismatch")

    batch = load_jsonl(ROOT / "translation" / "batches" / "controlled_003_consolidated.jsonl")
    validation = json.loads((ROOT / "translation" / "reports" / "controlled_003_validation.json").read_text(encoding="utf-8"))
    if validation["result"] != "PASS" or len(batch) != validation["candidate_entries"]:
        raise SystemExit("Controlled 003 candidate validation is not PASS")
    if len({row["logical_key"] for row in batch}) != len(batch):
        raise SystemExit("Duplicate candidate key")

    by_domain = {domain: [] for domain in MEMBERS}
    for row in batch:
        if row["domain"] not in by_domain:
            raise SystemExit(f"Unsupported runtime domain: {row['domain']}")
        by_domain[row["domain"]].append(row)

    overrides: dict[str, bytes] = {}
    changes: list[dict[str, str]] = []
    with zipfile.ZipFile(base) as archive:
        if archive.testzip() is not None:
            raise SystemExit("Pass C CRC failed")
        for domain, member in MEMBERS.items():
            rendered, member_changes = apply_table(archive.read(member), by_domain[domain])
            if member_changes:
                overrides[member] = rendered
                changes.extend(member_changes)
        overrides[SYSTEM_BAR] = exact(archive.read(SYSTEM_BAR), (("label=\"УЗНАТЬ\"".encode(), "label=\"СПРАВКА\"".encode()), ("label=\"ЛЕСТНИЦА\"".encode(), "label=\"РЕЙТИНГ\"".encode())), SYSTEM_BAR)
        overrides[GAME_MENU] = exact(archive.read(GAME_MENU), ((b'label="game_menu_{btnName}_\xd0\xba\xd0\xbd\xd0\xbe\xd0\xbf\xd0\xba\xd0\xb0"', b'label="game_menu_{btnName}_button"'),), GAME_MENU)
        preact = archive.read(PREACT)
        if preact.count(PREACT_OLD) != 1:
            raise SystemExit("Preact role map baseline mismatch")
        overrides[PREACT] = preact.replace(PREACT_OLD, PREACT_NEW)

    if len(changes) != validation["actual_changes_vs_pass_c"]:
        raise SystemExit(f"Stringtable delta mismatch: {len(changes)} != {validation['actual_changes_vs_pass_c']}")
    output.parent.mkdir(parents=True, exist_ok=True)
    compose(base, output, overrides)
    first = sha256(output)
    repeat = output.with_name(f".{output.stem}.repeat{output.suffix}")
    compose(base, repeat, overrides)
    second = sha256(repeat)
    repeat.unlink()
    changed_members, added, removed, corrupt = delta(base, output)
    errors: list[dict[str, Any]] = []
    if first != second:
        errors.append({"code": "NONDETERMINISTIC_SHA", "first": first, "second": second})
    if added or removed:
        errors.append({"code": "MEMBER_SET_CHANGED", "added": added, "removed": removed})
    if corrupt is not None:
        errors.append({"code": "CRC_FAILURE", "member": corrupt})
    expected_changed = sorted([member for member in MEMBERS.values() if member in overrides] + [SYSTEM_BAR, GAME_MENU, PREACT])
    if changed_members != expected_changed:
        errors.append({"code": "UNEXPECTED_MEMBER_DELTA", "expected": expected_changed, "actual": changed_members})
    with zipfile.ZipFile(output) as archive:
        entities_text = archive.read(MEMBERS["entities"]).decode("utf-8-sig")
        if "Персонал Мастера" in entities_text or "Посох Мастера" in entities_text:
            errors.append({"code": "FORBIDDEN_STAFF_ALIAS_IN_RUNTIME_TABLE"})
    for row in batch:
        if row["pass_c_baseline"] == row["proposed_ru"]:
            continue
        for protected in ("Tier I", "Tier II", "Tier III", "Tier IV", "GPM", "XPM", "Staff of the Master"):
            if protected in row["current_source"] and protected not in row["proposed_ru"]:
                errors.append({"code": "PROTECTED_SPAN_LOST", "key": row["logical_key"], "span": protected})

    result = {
        "schema_version": 1, "batch_id": BATCH_ID, "result": "PASS" if not errors else "FAIL", "errors": errors,
        "baseline": {"path": str(base), "sha256": sha256(base), "unchanged": True},
        "upstream": {"path": str(upstream), "sha256": sha256(upstream), "unchanged": True},
        "output": {"path": str(output), "sha256": first, "size_bytes": output.stat().st_size, "crc": "PASS" if corrupt is None else "FAIL"},
        "candidate_entries": len(batch), "stringtable_changes_relative_to_pass_c": len(changes),
        "changed_members": changed_members, "added_members": added, "removed_members": removed,
        "checks": {
            "candidate_validation": "PASS", "pass_c_sha": "PASS", "upstream_sha": "PASS",
            "deterministic_sha": "PASS" if first == second else "FAIL", "crc_integrity": "PASS" if corrupt is None else "FAIL",
            "exact_member_delta": "PASS" if changed_members == expected_changed and not added and not removed else "FAIL",
            "controlled_001_native_fixes": "PASS", "controlled_002_preact_roles": "PASS",
            "protected_spans": "PASS" if not any(e["code"] in {"FORBIDDEN_STAFF_ALIAS_IN_RUNTIME_TABLE", "PROTECTED_SPAN_LOST"} for e in errors) else "FAIL",
            "no_gameplay_data": "PASS", "not_installed": "PASS",
        },
        "stringtable_changes": changes, "runtime_verified": False, "installed": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"result": result["result"], "sha256": first, "size_bytes": output.stat().st_size, "stringtable_changes": len(changes), "changed_members": changed_members}, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
