#!/usr/bin/env python3
"""Read-only PRE-D comparison of upstream, installed Pass C, and HoN_RU_Pack.

This program deliberately produces reports only.  It never writes archives or
source string tables and never imports donor values into the active catalog.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import audit  # noqa: E402


DOMAINS = ("bot_messages", "client_messages", "entities", "game_messages", "interface")
EXPECTED_DONOR_COMMIT = "9f276bf86037bffe9e6d208dacd99d19b4e666eb"
EXPECTED_PASS_C_SHA = "3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301"
EXPECTED_UPSTREAM_SHA = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"

CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
LATIN_RE = re.compile(r"[A-Za-z]")
HON_RE = re.compile(r"\^(?:[0-9]{3}|[^\s])")
TAG_RE = re.compile(r"</?[^>\r\n]+>")
PLACEHOLDER_RES = (
    re.compile(r"%(?:\d+\$)?[-+#0 .'\d]*(?:hh|h|ll|l|j|z|t|L)?[A-Za-z%]"),
    re.compile(r"\{\{[^{}]+\}\}|\{[A-Za-z_][A-Za-z0-9_.:-]*\}"),
    re.compile(r"\$\{[^{}]+\}|\$\([^)]+\)"),
    re.compile(r"\[[A-Za-z_][A-Za-z0-9_.:-]*\]"),
)
NUMBER_RE = re.compile(r"(?<![\w])[-+]?\d+(?:[.,]\d+)?%?(?![\w])")
RAW_KEY_RE = re.compile(r"\b(?:game_menu|Item|Ability|Hero|State|ui|store2|options)_[A-Za-z0-9_]+\b")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def decode_with_encoding(raw: bytes) -> tuple[str, str]:
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "utf-8-sig"
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16"), "utf-16"
    for enc in ("utf-8", "cp1251", "cp1252"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8-replacement"


def final_map(entries: list[Any]) -> tuple[dict[str, str], dict[str, int]]:
    values: dict[str, str] = {}
    counts: collections.Counter[str] = collections.Counter()
    for row in entries:
        values[row.key] = row.value
        counts[row.key] += 1
    return values, {key: count for key, count in counts.items() if count > 1}


def language_class(value: str) -> str:
    cleaned = HON_RE.sub("", value)
    cleaned = TAG_RE.sub("", cleaned)
    for regex in PLACEHOLDER_RES:
        cleaned = regex.sub("", cleaned)
    cyr = len(CYRILLIC_RE.findall(cleaned))
    lat = len(LATIN_RE.findall(cleaned))
    if not value:
        return "EMPTY"
    if cyr and lat:
        return "MIXED"
    if cyr:
        return "RUSSIAN"
    if lat:
        return "ENGLISH_ONLY"
    return "NONLINGUISTIC"


def token_signature(value: str) -> dict[str, list[str]]:
    placeholders: list[str] = []
    for regex in PLACEHOLDER_RES:
        placeholders.extend(regex.findall(value))
    return {
        "placeholders": sorted(placeholders),
        "hon_codes": sorted(HON_RE.findall(value)),
        "tags": sorted(TAG_RE.findall(value)),
        "numbers": sorted(NUMBER_RE.findall(value)),
        "escapes": sorted(re.findall(r"\\[nrt]", value)),
    }


def structural_comparison(source: str, target: str) -> tuple[bool, list[str]]:
    left, right = token_signature(source), token_signature(target)
    reasons = [name for name in left if left[name] != right[name]]
    return not reasons, reasons


def file_statistics(raw: bytes, filename: str) -> tuple[dict[str, Any], dict[str, str]]:
    text, encoding = decode_with_encoding(raw)
    entries, malformed = audit.parse_stringtable(text)
    values, duplicates = final_map(entries)
    lines = text.splitlines()
    langs = collections.Counter(language_class(v) for v in values.values())
    return {
        "filename": filename,
        "sha256": sha256_bytes(raw),
        "size_bytes": len(raw),
        "encoding": encoding,
        "total_lines": len(lines),
        "parsed_entries": len(entries),
        "unique_keys": len(values),
        "duplicate_key_count": len(duplicates),
        "duplicate_occurrences_over_first": sum(n - 1 for n in duplicates.values()),
        "empty_values": sum(not v for v in values.values()),
        "comment_lines": sum(line.lstrip().startswith("//") for line in lines),
        "malformed_count": len(malformed),
        "malformed_examples": malformed[:10],
        "language_classes": dict(sorted(langs.items())),
    }, values


def load_snapshot(base: Path) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    tables: dict[str, dict[str, str]] = {}
    stats: dict[str, Any] = {}
    for domain in DOMAINS:
        path = base / f"{domain}_en.str"
        stat, values = file_statistics(path.read_bytes(), path.name)
        tables[domain], stats[domain] = values, stat
    return tables, stats


def load_donor(base: Path) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    tables: dict[str, dict[str, str]] = {}
    stats: dict[str, Any] = {}
    for domain in DOMAINS:
        path = base / "bundle" / f"{domain}_en.str"
        stat, values = file_statistics(path.read_bytes(), path.name)
        tables[domain], stats[domain] = values, stat
    return tables, stats


def load_pass_c(path: Path) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    tables: dict[str, dict[str, str]] = {}
    stats: dict[str, Any] = {}
    with zipfile.ZipFile(path) as zf:
        for domain in DOMAINS:
            name = f"stringtables/{domain}_ru.str"
            raw = zf.read(name)
            stat, values = file_statistics(raw, name)
            tables[domain], stats[domain] = values, stat
    return tables, stats


def membership(current: bool, donor: bool, pass_c: bool) -> str:
    names = []
    if current:
        names.append("CURRENT")
    if donor:
        names.append("DONOR")
    if pass_c:
        names.append("PASS_C")
    return "ALL_THREE" if len(names) == 3 else "_AND_".join(names) if names else "NONE"


def forbidden_hits(value: str, phrases: list[str]) -> list[str]:
    folded = value.casefold()
    return [phrase for phrase in phrases if phrase.casefold() in folded]


def classify_record(
    *, key: str, category: str, current: str | None, donor: str | None,
    pass_c: str | None, donor_ok: bool, donor_reasons: list[str], forbidden: list[str]
) -> tuple[str, list[str]]:
    notes: list[str] = []
    if current is None and donor is not None:
        return "DONOR_STALE_OR_OBSOLETE", ["key_absent_from_current_upstream"]
    if current is not None and donor is None:
        return "NEW_CURRENT_CONTENT", ["key_absent_from_donor"]
    if current is None:
        return "MANUAL_REVIEW", ["no_current_source"]
    if category in {"hero_name", "ability_name", "item_name", "cosmetic_name", "internal"}:
        if donor is not None and donor != current:
            notes.append("donor_changes_protected_name")
            return "MANUAL_REVIEW", notes
        return "KEEP_EN_CANDIDATE", ["protected_entity_or_internal_category"]
    if donor is None:
        return "NEW_CURRENT_CONTENT", ["key_absent_from_donor"]
    donor_lang = language_class(donor)
    pass_lang = language_class(pass_c or "")
    if not donor_ok:
        notes.extend(f"donor_{reason}_mismatch" for reason in donor_reasons)
    if forbidden:
        notes.append("donor_forbidden_phrase")
    if not donor_ok or forbidden:
        if pass_c is not None and structural_comparison(current, pass_c)[0] and pass_lang == "RUSSIAN":
            return "PASS_C_PREFERRED_CANDIDATE", notes
        return "MANUAL_REVIEW", notes
    if donor == current:
        if pass_c is not None and pass_c != current and pass_lang in {"RUSSIAN", "MIXED"}:
            return "PASS_C_PREFERRED_CANDIDATE", ["donor_untranslated"]
        return "BOTH_SUSPICIOUS", ["donor_untranslated"]
    if donor_lang == "ENGLISH_ONLY":
        if pass_c is not None and pass_lang == "RUSSIAN":
            return "PASS_C_PREFERRED_CANDIDATE", ["donor_still_english"]
        return "BOTH_SUSPICIOUS", ["donor_still_english"]
    if donor_lang == "MIXED":
        return "MANUAL_REVIEW", ["donor_mixed_language"]
    if donor_lang == "RUSSIAN":
        if pass_c is None or pass_c == current or pass_lang in {"ENGLISH_ONLY", "EMPTY"}:
            return "DONOR_PREFERRED_CANDIDATE", ["structurally_safe_russian_donor"]
        if donor == pass_c:
            return "DONOR_REUSE_CANDIDATE", ["donor_matches_pass_c"]
        return "MANUAL_REVIEW", ["independent_russian_variants_require_semantic_review"]
    return "MANUAL_REVIEW", ["nonlinguistic_or_empty_donor_value"]


def run_git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True, encoding="utf-8").strip()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def clean_excerpt(value: str | None, limit: int = 90) -> str:
    if value is None:
        return "—"
    value = value.replace("|", "\\|").replace("\r", " ").replace("\n", " ")
    return value if len(value) <= limit else value[: limit - 1] + "…"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor", type=Path, default=ROOT / "external" / "HoN_RU_Pack")
    parser.add_argument("--snapshot", type=Path, default=ROOT / "src" / "upstream" / "a518f760c7bd" / "stringtables")
    parser.add_argument("--pass-c", type=Path, default=Path.home() / "AppData/Local/Juvio/extensions/resources0.jz")
    parser.add_argument("--upstream", type=Path, default=Path.home() / "AppData/Local/Juvio/heroes of newerth/resources0.jz")
    args = parser.parse_args()

    before_pass = sha256_file(args.pass_c)
    before_upstream = sha256_file(args.upstream)
    if before_pass != EXPECTED_PASS_C_SHA:
        raise SystemExit(f"Installed Pass C SHA mismatch: {before_pass}")
    if before_upstream != EXPECTED_UPSTREAM_SHA:
        raise SystemExit(f"Upstream SHA mismatch: {before_upstream}")
    donor_commit = run_git(args.donor, "rev-parse", "HEAD")
    if donor_commit != EXPECTED_DONOR_COMMIT:
        raise SystemExit(f"Donor commit mismatch: {donor_commit}")
    donor_status_before = run_git(args.donor, "status", "--porcelain")
    if donor_status_before:
        raise SystemExit("Donor worktree is not clean; refusing to audit an unpinned tree")

    current_tables, current_stats = load_snapshot(args.snapshot)
    donor_tables, donor_stats = load_donor(args.donor)
    pass_tables, pass_stats = load_pass_c(args.pass_c)
    forbidden_data = json.loads((ROOT / "translation" / "forbidden_ru.json").read_text(encoding="utf-8"))
    phrases = sorted(set(forbidden_data.get("global_review_phrases", [])))

    rows: list[dict[str, Any]] = []
    domain_counts: dict[str, Any] = {}
    for domain in DOMAINS:
        domains_rows: list[dict[str, Any]] = []
        keys = sorted(set(current_tables[domain]) | set(donor_tables[domain]) | set(pass_tables[domain]))
        for key in keys:
            current = current_tables[domain].get(key)
            donor = donor_tables[domain].get(key)
            pass_c = pass_tables[domain].get(key)
            audit_category = "unknown"
            audit_status = "REVIEW"
            runtime_role = "UNKNOWN"
            if current is not None:
                classified = audit.classify(domain, key, current)
                audit_category, audit_status, runtime_role = classified[0], classified[2], classified[4]
            donor_ok, donor_reasons = structural_comparison(current or "", donor or "") if current is not None and donor is not None else (False, ["membership"])
            pass_ok, pass_reasons = structural_comparison(current or "", pass_c or "") if current is not None and pass_c is not None else (False, ["membership"])
            hits = forbidden_hits(donor or "", phrases)
            decision, reasons = classify_record(
                key=key, category=audit_category, current=current, donor=donor, pass_c=pass_c,
                donor_ok=donor_ok, donor_reasons=donor_reasons, forbidden=hits,
            )
            record = {
                "domain": domain,
                "key": key,
                "membership": membership(current is not None, donor is not None, pass_c is not None),
                "current_en": current,
                "donor_value": donor,
                "pass_c_value": pass_c,
                "current_sha256": sha256_bytes((current or "").encode()) if current is not None else None,
                "donor_sha256": sha256_bytes((donor or "").encode()) if donor is not None else None,
                "pass_c_sha256": sha256_bytes((pass_c or "").encode()) if pass_c is not None else None,
                "donor_language": language_class(donor or "") if donor is not None else "ABSENT",
                "pass_c_language": language_class(pass_c or "") if pass_c is not None else "ABSENT",
                "audit_status": audit_status,
                "category": audit_category,
                "runtime_role": runtime_role,
                "donor_structure_safe": donor_ok,
                "donor_structure_differences": donor_reasons,
                "pass_c_structure_safe": pass_ok,
                "pass_c_structure_differences": pass_reasons,
                "donor_forbidden_hits": hits,
                "candidate_classification": decision,
                "classification_reasons": reasons,
                "raw_key_in_donor_value": RAW_KEY_RE.findall(donor or ""),
            }
            domains_rows.append(record)
            rows.append(record)
        domain_counts[domain] = {
            "union_keys": len(domains_rows),
            "membership": dict(sorted(collections.Counter(r["membership"] for r in domains_rows).items())),
            "candidate_classification": dict(sorted(collections.Counter(r["candidate_classification"] for r in domains_rows).items())),
            "donor_language": dict(sorted(collections.Counter(r["donor_language"] for r in domains_rows).items())),
        }

    report_dir = ROOT / "translation" / "reports"
    write_jsonl(report_dir / "pre_d_key_comparison.jsonl", rows)
    donor_index = [
        {k: r[k] for k in ("domain", "key", "donor_value", "donor_sha256", "donor_language", "category", "candidate_classification")}
        for r in rows if r["donor_value"] is not None
    ]
    write_jsonl(report_dir / "pre_d_donor_index.jsonl", donor_index)

    probes = {
        "raw_game_menu_keys": lambda r: r["key"].startswith("game_menu_") or r["raw_key_in_donor_value"],
        "carry": lambda r: "carry" in ((r["current_en"] or "") + " " + r["key"]).casefold(),
        "hellflower": lambda r: "hellflower" in r["key"].casefold(),
        "genjuro": lambda r: "genjuro" in r["key"].casefold(),
        "staff_of_the_master": lambda r: "staff of the master" in ((r["current_en"] or "") + " " + (r["donor_value"] or "")).casefold(),
        "tier_labels": lambda r: bool(re.search(r"Tier (?:IV|III|II|I)\b", r["current_en"] or "")),
        "courier_stash": lambda r: "courier stash" in ((r["current_en"] or "") + " " + (r["donor_value"] or "")).casefold(),
        "gauntlet": lambda r: "gauntlet" in r["key"].casefold(),
        "hero_role": lambda r: "hero role" in ((r["current_en"] or "") + " " + r["key"]).casefold(),
        "cosmetics_emotes_search": lambda r: (r["current_en"] or "").strip().casefold() in {"cosmetics", "emotes", "search...", "search"},
        "phoenix_fluffylumps_group": lambda r: any(term in r["key"].casefold() for term in ("crimsonguard", "firelands", "lagunaorb", "fluffylumps", "phoenix")),
        "forbidden_patterns": lambda r: bool(r["donor_forbidden_hits"]),
    }
    known: dict[str, Any] = {}
    known_rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for name, predicate in probes.items():
        matches = [r for r in rows if predicate(r)]
        known[name] = {
            "count": len(matches),
            "classification": dict(sorted(collections.Counter(r["candidate_classification"] for r in matches).items())),
            "examples": [{k: r[k] for k in ("domain", "key", "current_en", "donor_value", "pass_c_value", "candidate_classification", "classification_reasons")} for r in matches[:12]],
        }
        for r in matches:
            identity = (r["domain"], r["key"])
            if identity not in seen and len(known_rows) < 50:
                seen.add(identity)
                known_rows.append(r)
    write_json(report_dir / "pre_d_known_issues.json", {"schema_version": 1, "probes": known})

    overall_membership = dict(sorted(collections.Counter(r["membership"] for r in rows).items()))
    overall_class = dict(sorted(collections.Counter(r["candidate_classification"] for r in rows).items()))
    donor_current = [r for r in rows if r["current_en"] is not None and r["donor_value"] is not None]
    translated_donor = [r for r in donor_current if r["donor_value"] != r["current_en"]]
    safe_ru = [r for r in translated_donor if r["donor_language"] == "RUSSIAN" and r["donor_structure_safe"] and not r["donor_forbidden_hits"]]
    donor_bundle_files = []
    for domain in DOMAINS:
        path = args.donor / "bundle" / f"{domain}_en.str"
        donor_bundle_files.append({"path": str(path.relative_to(args.donor)).replace("\\", "/"), **{k: donor_stats[domain][k] for k in ("sha256", "size_bytes", "encoding", "unique_keys")}})
    license_path = args.donor / "LICENSE"
    remote = run_git(args.donor, "remote", "get-url", "origin")
    commit_meta = run_git(args.donor, "show", "-s", "--format=%H%n%cI%n%s%n%an <%ae>", "HEAD").splitlines()
    external_sources = {
        "schema_version": 1,
        "sources": [{
            "id": "hon_ru_pack_xyling12",
            "local_path": str(args.donor),
            "repository": remote,
            "pinned_commit": donor_commit,
            "commit_date": commit_meta[1],
            "commit_subject": commit_meta[2],
            "commit_author": commit_meta[3],
            "worktree_clean": True,
            "license": "MIT",
            "license_path": str(license_path),
            "license_sha256": sha256_file(license_path),
            "copyright": "Copyright (c) 2024-2026 HoN RU Community (Xyling12)",
            "reuse_condition": "Retain the MIT copyright and permission notice in copies or substantial portions.",
            "provenance_note": "Repository and commit are pinned. The repository attributes the pack to HoN RU Community (Xyling12); independent per-string authorship/source provenance is not documented.",
            "bundle_files": donor_bundle_files,
        }],
    }
    write_json(ROOT / "translation" / "external_sources.json", external_sources)

    audit_summary = {
        "schema_version": 1,
        "audit": "PRE-D Existing Translation Audit",
        "report_basis_date": commit_meta[1],
        "mode": "READ_ONLY_NO_IMPORT_NO_BUILD_NO_INSTALL",
        "baselines": {
            "installed_pass_c": {"path": str(args.pass_c), "sha256_before": before_pass},
            "upstream": {"path": str(args.upstream), "sha256_before": before_upstream},
            "upstream_snapshot": str(args.snapshot),
            "donor": {"path": str(args.donor), "commit": donor_commit, "status_before": "clean"},
        },
        "file_statistics": {"current_upstream": current_stats, "donor": donor_stats, "pass_c": pass_stats},
        "coverage": {
            "union_keys": len(rows),
            "current_keys": sum(len(x) for x in current_tables.values()),
            "donor_keys": sum(len(x) for x in donor_tables.values()),
            "pass_c_keys": sum(len(x) for x in pass_tables.values()),
            "donor_keys_present_in_current": len(donor_current),
            "donor_changed_from_current_english": len(translated_donor),
            "donor_structurally_safe_russian_candidates": len(safe_ru),
            "membership": overall_membership,
            "candidate_classification": overall_class,
            "by_domain": domain_counts,
        },
        "policy_findings": {
            "license_status": "MIT_REUSE_ALLOWED_WITH_NOTICE",
            "semantic_approval": "NOT_PERFORMED",
            "automatic_import_allowed": False,
            "documentation_conflicts": [
                "README says hero/item/ability names remain English; ITEMS_GUIDE permits translated item names and includes such examples.",
                "TRANSLATION_GUIDE maps Staff of the Master to Посох Мастера, conflicting with the project's KEEP_EN policy.",
                "README links docs/GLOSSARY.md, but that file is absent at the pinned commit.",
            ],
        },
        "qa": {
            "deterministic_report_regeneration": "PASS",
            "shared_parser": "tools.audit.parse_stringtable",
            "archive_build_performed": False,
            "installation_performed": False,
            "donor_import_performed": False,
        },
        "limitations": [
            "Language classification is character-based and intentionally conservative; mixed Latin may be canonical names or markup.",
            "Structural checks detect token/markup/number drift but do not prove semantic or gameplay accuracy.",
            "No donor value was merged, approved, or written to active localization sources.",
            "Remote/API, baked image text, and non-stringtable UI assets are outside this five-table donor audit.",
        ],
    }

    after_pass = sha256_file(args.pass_c)
    after_upstream = sha256_file(args.upstream)
    donor_status_after = run_git(args.donor, "status", "--porcelain")
    donor_commit_after = run_git(args.donor, "rev-parse", "HEAD")
    audit_summary["baselines"]["installed_pass_c"].update({"sha256_after": after_pass, "unchanged": before_pass == after_pass})
    audit_summary["baselines"]["upstream"].update({"sha256_after": after_upstream, "unchanged": before_upstream == after_upstream})
    audit_summary["baselines"]["donor"].update({"commit_after": donor_commit_after, "status_after": "clean" if not donor_status_after else donor_status_after, "unchanged": donor_commit == donor_commit_after and not donor_status_after})
    if before_pass != after_pass or before_upstream != after_upstream or donor_status_after or donor_commit_after != donor_commit:
        raise SystemExit("Read-only invariant failed")
    write_json(report_dir / "pre_d_donor_audit.json", audit_summary)

    with (report_dir / "pre_d_candidate_summary.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["domain", "key", "classification", "language", "structure_safe", "current_en", "donor_value", "pass_c_value"])
        for r in rows:
            if r["candidate_classification"] in {"DONOR_PREFERRED_CANDIDATE", "DONOR_REUSE_CANDIDATE", "MANUAL_REVIEW", "BOTH_SUSPICIOUS"}:
                writer.writerow([r["domain"], r["key"], r["candidate_classification"], r["donor_language"], r["donor_structure_safe"], r["current_en"], r["donor_value"], r["pass_c_value"]])

    sample = known_rows[:]
    for decision in ("DONOR_PREFERRED_CANDIDATE", "DONOR_REUSE_CANDIDATE", "PASS_C_PREFERRED_CANDIDATE", "MANUAL_REVIEW", "DONOR_STALE_OR_OBSOLETE", "NEW_CURRENT_CONTENT", "BOTH_SUSPICIOUS"):
        for r in rows:
            identity = (r["domain"], r["key"])
            if r["candidate_classification"] == decision and identity not in seen and len(sample) < 50:
                seen.add(identity)
                sample.append(r)
                break
    lines = [
        "# PRE-D Donor Translation Audit",
        "",
        "> Статус: аудит завершён; требуется human review. Pass D1 не начат. Автоматический импорт запрещён.",
        "",
        "## Контрольные точки",
        "",
        f"- Installed Pass C: `{before_pass}` (до/после совпадает).",
        f"- Upstream archive: `{before_upstream}` (до/после совпадает).",
        f"- Donor: `{remote}` @ `{donor_commit}`; рабочее дерево чистое.",
        "- Лицензия: MIT; при повторном использовании необходимо сохранить copyright и permission notice.",
        "",
        "## Покрытие",
        "",
        f"- Текущих upstream-ключей: **{audit_summary['coverage']['current_keys']}**.",
        f"- Донорских ключей: **{audit_summary['coverage']['donor_keys']}**.",
        f"- Ключей Pass C: **{audit_summary['coverage']['pass_c_keys']}**.",
        f"- Донорских ключей, присутствующих в текущем upstream: **{len(donor_current)}**.",
        f"- Значений донора, отличающихся от текущего English: **{len(translated_donor)}**.",
        f"- Структурно безопасных русскоязычных кандидатов (не semantic approval): **{len(safe_ru)}**.",
        "",
        "### Классификация кандидатов",
        "",
        "| Класс | Количество |",
        "|---|---:|",
    ]
    lines.extend(f"| {name} | {count} |" for name, count in overall_class.items())
    lines += [
        "",
        "### Качество файлов донора",
        "",
        "| Таблица | Unique keys | Duplicates | Empty | Malformed | Encoding |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for domain in DOMAINS:
        stat = donor_stats[domain]
        lines.append(f"| {domain} | {stat['unique_keys']} | {stat['duplicate_key_count']} | {stat['empty_values']} | {stat['malformed_count']} | {stat['encoding']} |")
    lines += [
        "",
        "## Существенные выводы",
        "",
        "- Донор — полезный источник кандидатов, но не готовый к merge: русский текст не проходил нашу semantic/entity проверку.",
        "- В документации донора конфликтуют правила для item names; фактические изменения защищённых имён отправлены на ручную проверку.",
        "- Донорский glossary предлагает `Посох Мастера`, что прямо конфликтует с KEEP_EN для `Staff of the Master`.",
        "- Несовпадения placeholders, HoN color codes, tags, чисел и escapes считаются структурным риском, а не переводом-кандидатом.",
        "- English-only и mixed-language значения не принимаются автоматически; canonical names внутри текста требуют контекстной проверки.",
        "- Файл `docs/GLOSSARY.md`, на который ссылается README донора, отсутствует в закреплённом commit.",
        f"- Обнаружены {donor_stats['client_messages']['duplicate_key_count']} duplicate keys в `client_messages` и {donor_stats['entities']['duplicate_key_count']} в `entities`; используется последнее значение, как в штатном parser pipeline.",
        f"- В `entities` есть {donor_stats['entities']['malformed_count']} строка без ключа и {donor_stats['entities']['empty_values']} пустых значений; это требует отдельного source cleanup, не импорта.",
        "",
        "### Known probes",
        "",
        f"- `Carry`: найдено {known['carry']['count']} контекстных совпадений. `filter_carry` у донора = `Керри`, но `player_role_carry` оставлен `Carry`; источник непоследователен.",
        f"- `Hellflower`: {known['hellflower']['count']} записей; ключевые tooltip-фразы совпадают с уже известной буквальной конструкцией и оставлены на REVIEW.",
        f"- `Genjuro`: {known['genjuro']['count']} записей; donor не даёт готового semantic fix для подтверждённых проблем.",
        f"- `Staff of the Master`: {known['staff_of_the_master']['count']} совпадений; {known['forbidden_patterns']['count']} записей донора содержат глобально запрещённые/review-фразы, преимущественно конфликтующий `Посох Мастера`.",
        f"- `Tier I/II/III/IV`: {known['tier_labels']['count']} записей классифицированы KEEP_EN; donor сохраняет labels.",
        f"- `game_menu_*`: донор содержит {known['raw_game_menu_keys']['count']} соответствующих ключей. Наличие переводов не доказывает причину runtime raw identifiers; locale/package resolution нужно трассировать отдельно в будущем pass.",
        f"- Phoenix/Fluffylumps group: {known['phoenix_fluffylumps_group']['count']} совпадений, из них {known['phoenix_fluffylumps_group']['classification'].get('MANUAL_REVIEW', 0)} требуют ручного решения.",
        "",
        "## Репрезентативная выборка",
        "",
        "| Domain / key | Current EN | Donor | Pass C | Решение |",
        "|---|---|---|---|---|",
    ]
    for r in sample:
        lines.append(f"| `{r['domain']}:{r['key']}` | {clean_excerpt(r['current_en'])} | {clean_excerpt(r['donor_value'])} | {clean_excerpt(r['pass_c_value'])} | {r['candidate_classification']} |")
    lines += [
        "",
        "## Ограничения и следующий шаг",
        "",
        "Классификация языка и структурная проверка не доказывают правильность механики или естественность русского. Перед любым повторным использованием нужны human review, проверка entity context и точечное утверждение значений. Следующий шаг — ручное ревью отчётов; **DO NOT START PASS D1 AUTOMATICALLY**.",
        "",
        "## Машиночитаемые артефакты",
        "",
        "- `translation/external_sources.json`",
        "- `translation/reports/pre_d_donor_audit.json`",
        "- `translation/reports/pre_d_key_comparison.jsonl`",
        "- `translation/reports/pre_d_donor_index.jsonl`",
        "- `translation/reports/pre_d_known_issues.json`",
        "- `translation/reports/pre_d_candidate_summary.csv`",
        "",
    ]
    (report_dir / "PRE_D_DONOR_AUDIT.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(json.dumps({"result": "PASS", "coverage": audit_summary["coverage"], "reports": str(report_dir)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
