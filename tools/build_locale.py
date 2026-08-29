#!/usr/bin/env python3
"""Build a deterministic Russian extension archive from the catalog.

The builder never installs the result. Use --allow-fallback only for engineering
probes; production builds are strict and require all TRANSLATE rows to have RU.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath


PRINTF_RE = re.compile(r"%(?:\d+\$)?[-+#0 ]*(?:\d+|\*)?(?:\.\d+)?[A-Za-z%](?![A-Za-z])")
BRACE_TOKEN_RE = re.compile(r"\{[^{}\r\n]+\}")
TEMPLATE_TOKEN_RE = re.compile(r"\$\{[^{}\r\n]+\}")
HON_CONTROL_RE = re.compile(r"\^(?:[0-9]{3}|[^\s])")
ANGLE_TOKEN_RE = re.compile(r"<[^<>\r\n]+>")
LITERAL_ESCAPE_RE = re.compile(r"\\[rnt]")
HTML_TAG_RE = re.compile(r"<[^<>\r\n]+>")


def tokens(pattern: re.Pattern[str], value: str) -> Counter[str]:
    return Counter(pattern.findall(value))


def visible_text(value: str) -> str:
    return HTML_TAG_RE.sub("", HON_CONTROL_RE.sub("", value))


def visible_term_count(value: str, term: str, case_policy: str = "EXACT") -> int:
    flags = 0 if case_policy == "EXACT" else re.I
    return len(re.findall(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", visible_text(value), flags))


def load_catalog(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise SystemExit(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def validate(rows: list[dict], allow_fallback: bool, required_ids: set[str] | None = None) -> tuple[list[dict], list[dict]]:
    errors: list[dict] = []
    warnings: list[dict] = []
    ids = Counter(str(row.get("id", "")) for row in rows)
    for row_id, count in ids.items():
        if not row_id or count > 1:
            errors.append({"code": "duplicate_or_empty_id", "id": row_id, "count": count})

    valid_status = {"TRANSLATE", "KEEP_EN", "REVIEW", "DYNAMIC", "IMAGE_TEXT", "DEPRECATED"}
    for row in rows:
        row_id = row.get("id", "")
        english = str(row.get("english", ""))
        russian = str(row.get("russian", ""))
        status = row.get("status")
        expected_hash = hashlib.sha256(english.encode("utf-8")).hexdigest()
        if status not in valid_status:
            errors.append({"code": "invalid_status", "id": row_id, "status": status})
        if status == "TRANSLATE" and row.get("runtime_role", "DISPLAY_TEXT") != "DISPLAY_TEXT":
            errors.append({"code": "non_display_marked_translate", "id": row_id, "runtime_role": row.get("runtime_role")})
        if row.get("english_hash") != expected_hash:
            errors.append({"code": "english_hash_mismatch", "id": row_id})
        if status == "KEEP_EN" and russian != english:
            errors.append({"code": "protected_content_changed", "id": row_id})
        required = required_ids is None or row_id in required_ids
        if status == "TRANSLATE" and not russian and required:
            target = warnings if allow_fallback else errors
            target.append({"code": "missing_russian", "id": row_id})
        if russian:
            for label, pattern in (
                ("printf_token", PRINTF_RE),
                ("brace_token", BRACE_TOKEN_RE),
                ("template_token", TEMPLATE_TOKEN_RE),
                ("hon_control", HON_CONTROL_RE),
                ("angle_token", ANGLE_TOKEN_RE),
                ("literal_escape", LITERAL_ESCAPE_RE),
            ):
                if tokens(pattern, english) != tokens(pattern, russian):
                    errors.append({
                        "code": f"{label}_mismatch", "id": row_id,
                        "english": dict(tokens(pattern, english)),
                        "russian": dict(tokens(pattern, russian)),
                    })
            spans = row.get("locked_spans", [])
            human_runtime_override = row.get("classification_source") == "HUMAN_RUNTIME"
            if spans and not human_runtime_override:
                expected = Counter((span["canonical_text"], span.get("case_policy", "EXACT")) for span in spans)
                for (term, case_policy), expected_count in expected.items():
                    actual_count = visible_term_count(russian, term, case_policy)
                    if actual_count != expected_count:
                        errors.append({
                            "code": "locked_visible_span_mismatch", "id": row_id,
                            "term": term, "expected_count": expected_count, "russian_count": actual_count,
                        })
                signatures = Counter(
                    (span["canonical_text"], span.get("markup_prefix", ""), span.get("markup_suffix", ""))
                    for span in spans if span.get("markup_prefix") and span.get("markup_suffix")
                )
                for (term, prefix, suffix), expected_count in signatures.items():
                    actual_count = len(re.findall(re.escape(prefix + term + suffix), russian))
                    if actual_count != expected_count:
                        errors.append({
                            "code": "locked_span_markup_mismatch", "id": row_id, "term": term,
                            "markup_prefix": prefix, "markup_suffix": suffix,
                            "expected_count": expected_count, "russian_count": actual_count,
                        })
                for span in spans:
                    start, end = span.get("source_start"), span.get("source_end")
                    if not isinstance(start, int) or not isinstance(end, int) or visible_text(english[start:end]) != span["canonical_text"]:
                        errors.append({"code": "invalid_locked_source_span", "id": row_id, "span": span})
            elif not human_runtime_override:
                for term in row.get("protected_terms", []):
                    if visible_term_count(english, term) != visible_term_count(russian, term):
                        errors.append({
                            "code": "protected_term_mismatch", "id": row_id, "term": term,
                            "english_count": visible_term_count(english, term),
                            "russian_count": visible_term_count(russian, term),
                        })
            if russian.strip() == str(row.get("key", "")).strip():
                warnings.append({"code": "raw_localization_key", "id": row_id})
    return errors, warnings


def rendered_value(row: dict, allow_fallback: bool, required_ids: set[str] | None = None) -> str:
    if row["status"] == "KEEP_EN":
        return row["english"]
    if row.get("russian"):
        return row["russian"]
    if allow_fallback or (required_ids is not None and row["id"] not in required_ids) or row["status"] in {"REVIEW", "DYNAMIC", "IMAGE_TEXT", "DEPRECATED"}:
        return row["english"]
    raise RuntimeError(f"Missing Russian value: {row['id']}")


def deterministic_zip_write(zf: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_ZSTANDARD
    info.external_attr = 0o644 << 16
    zf.writestr(info, data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-fallback", action="store_true")
    parser.add_argument("--scope", type=Path, help="JSON scope manifest; strict only for selected catalog ids")
    args = parser.parse_args()
    if sys.version_info < (3, 14):
        raise SystemExit("Python 3.14+ is required for ZIP Zstandard output")

    root = args.project_root.resolve()
    catalog_path = (args.catalog or root / "catalog" / "strings.jsonl").resolve()
    output = (args.output or root / "build" / "resources0.jz").resolve()
    if args.snapshot:
        snapshot = args.snapshot.resolve()
    else:
        snapshots = sorted((root / "src" / "upstream").glob("*"))
        if not snapshots:
            raise SystemExit("No upstream snapshot. Run scripts/run_audit.ps1 first.")
        snapshot = snapshots[-1]

    rows = load_catalog(catalog_path)
    required_ids = None
    if args.scope:
        scope = json.loads(args.scope.resolve().read_text(encoding="utf-8"))
        required_ids = set(scope["selection"]["catalog"])
    errors, warnings = validate(rows, args.allow_fallback, required_ids)
    report = {
        "catalog": str(catalog_path), "snapshot": str(snapshot),
        "output": str(output), "allow_fallback": args.allow_fallback,
        "scope": str(args.scope.resolve()) if args.scope else None,
        "required_ids": len(required_ids) if required_ids is not None else None,
        "errors": errors, "warnings": warnings,
    }
    report_path = root / "reports" / "build_validation.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        print(json.dumps({"result": "failed", "errors": len(errors), "warnings": len(warnings)}, indent=2))
        return 2

    by_namespace: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_namespace[row["namespace"]].append(row)

    files: dict[str, bytes] = {}
    for namespace, namespace_rows in sorted(by_namespace.items()):
        content = "\n".join(
            f"{row['key']}\t{rendered_value(row, args.allow_fallback, required_ids)}"
            for row in namespace_rows
        ) + "\n"
        files[f"stringtables/{namespace}_ru.str"] = content.encode("utf-8")

    core_en = snapshot / "core_en.resources"
    regions = snapshot / "ui" / "scripts" / "fe3" / "regions.lua"
    if not core_en.is_file() or not regions.is_file():
        raise SystemExit("Snapshot lacks core_en.resources or regions.lua")
    files["core_ru.resources"] = core_en.read_bytes()
    region_text = regions.read_text(encoding="utf-8-sig")
    old = "return {'en', 'th'}"
    if region_text.count(old) != 2:
        raise SystemExit(f"regions.lua invariant changed: expected 2 occurrences of {old!r}")
    files["ui/scripts/fe3/regions.lua"] = region_text.replace(old, "return {'en', 'th', 'ru'}").encode("utf-8")

    extended_root = root / "src" / "extended_ru"
    if extended_root.is_dir():
        for path in sorted(extended_root.rglob("*")):
            if path.is_file():
                relative = path.relative_to(extended_root).as_posix()
                if PurePosixPath(relative).parts and ".." not in PurePosixPath(relative).parts:
                    files[relative] = path.read_bytes()

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", allowZip64=True) as zf:
        for name, data in sorted(files.items()):
            deterministic_zip_write(zf, name, data)

    report.update({
        "result": "ok", "files": len(files), "archive_size": output.stat().st_size,
        "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    })
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": "ok", "output": str(output), "files": len(files), "warnings": len(warnings)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
