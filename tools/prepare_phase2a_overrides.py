#!/usr/bin/env python3
"""Generate isolated native and Preact Phase 2A overrides from reviewed catalogs."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def replace_on_line(lines: list[str], row: dict) -> None:
    index = int(row["source_line"]) - 1
    if not 0 <= index < len(lines):
        raise RuntimeError(f"line outside source: {row['id']}")
    english = row.get("english", row.get("literal", ""))
    russian = row["russian"]
    expected = int(row.get("source_column", 1)) - 1
    def safe_positions(line: str) -> list[int]:
        result = []
        for match in re.finditer(re.escape(english), line):
            start, end = match.span()
            if english[:1].isalnum() and start and (line[start - 1].isalnum() or line[start - 1] == "_"):
                continue
            if english[-1:].isalnum() and end < len(line) and (line[end].isalnum() or line[end] == "_"):
                continue
            result.append(start)
        return result

    candidates: list[tuple[int, int]] = []
    # Babel's JSX coordinates can drift by a few source lines around large
    # fragments and comments.  Keep the search local, but wide enough for the
    # audited patch-note components.
    for line_index in range(max(0, index - 250), min(len(lines), index + 251)):
        for position in safe_positions(lines[line_index]):
            candidates.append((line_index, position))
    if candidates:
        chosen_index, pos = min(candidates, key=lambda item: (abs(item[0] - index), abs(item[1] - expected)))
        line = lines[chosen_index]
    else:
        full = "".join(lines)
        pattern = re.compile(r"\s+".join(re.escape(part) for part in english.split()))
        matches = list(pattern.finditer(full))
        if len(matches) != 1:
            raise RuntimeError(f"literal not found uniquely at audited line: {row['id']} {row['source_file']}:{index + 1}")
        match = matches[0]
        # Retain the source line count so the remaining audited coordinates in
        # the same large TSX file stay valid.
        preserved_breaks = "\n" * full[match.start():match.end()].count("\n")
        lines[:] = (full[:match.start()] + russian + preserved_breaks + full[match.end():]).splitlines(keepends=True)
        return
    delimiter = line[pos - 1] if pos and line[pos - 1] in "'\"`" else ""
    replacement = russian
    if delimiter:
        replacement = replacement.replace("\\", "\\\\").replace(delimiter, "\\" + delimiter)
    lines[chosen_index] = line[:pos] + replacement + line[pos + len(english):]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--preact-workspace", type=Path, required=True)
    parser.add_argument("--scope", type=Path)
    parser.add_argument("--preact-scope", type=Path)
    parser.add_argument("--skip-native", action="store_true", help="Build only Preact overrides when native source coordinates have drifted")
    args = parser.parse_args()
    root = args.project_root.resolve()
    archive = args.archive.resolve()
    workspace = args.preact_workspace.resolve()
    scope_path = (args.scope or root / "catalog" / "phase2a_scope.json").resolve()
    preact_scope_path = (args.preact_scope or scope_path).resolve()
    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    preact_scope = json.loads(preact_scope_path.read_text(encoding="utf-8"))
    native_ids = set() if args.skip_native else set(scope["selection"]["native"])
    preact_ids = set(preact_scope["selection"]["preact"])
    native = [row for row in read_jsonl(root / "catalog" / "native_extended_ui.jsonl") if row["id"] in native_ids]
    preact = [row for row in read_jsonl(root / "catalog" / "preact_ui.jsonl") if row["id"] in preact_ids]

    extended = (root / "src" / "extended_ru").resolve()
    if extended != (root / "src" / "extended_ru").resolve():
        raise SystemExit("unsafe extended root")
    extended.mkdir(parents=True, exist_ok=True)
    native_by_file: dict[str, list[dict]] = defaultdict(list)
    for row in native:
        native_by_file[row["source_file"]].append(row)
    native_manifest = []
    with zipfile.ZipFile(archive) as zf:
        for name, rows in sorted(native_by_file.items()):
            raw = zf.read(name)
            text = raw.decode("utf-8-sig")
            lines = text.splitlines(keepends=True)
            for row in sorted(rows, key=lambda item: (item["source_line"], item["id"]), reverse=True):
                replace_on_line(lines, row)
            target = extended / Path(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("".join(lines), encoding="utf-8", newline="")
            native_manifest.append({"source_file": name, "translated_literals": len(rows)})

    preact_by_file: dict[str, list[dict]] = defaultdict(list)
    for row in preact:
        preact_by_file[row["source_file"]].append(row)
    patched = []
    skipped_missing = []
    for source_name, rows in sorted(preact_by_file.items()):
        relative = Path(source_name).relative_to("preact")
        target = workspace / "preact" / relative
        if not target.is_file():
            skipped_missing.append({"source_file": source_name, "rows": len(rows), "reason": "not present in CURRENT Preact source"})
            continue
        lines = target.read_text(encoding="utf-8-sig").splitlines(keepends=True)
        for row in sorted(rows, key=lambda item: (item["source_line"], item["source_column"], item["id"]), reverse=True):
            replace_on_line(lines, row)
        target.write_text("".join(lines), encoding="utf-8", newline="")
        patched.append({"source_file": source_name, "translated_literals": len(rows)})

    # Some player-facing strings live in code structures intentionally omitted
    # by the generic AST catalog (for example enum display maps and the very
    # large editorial patch-note components).  Apply reviewed, source-pinned
    # replacements for those strings as a separate reproducible layer.
    editorial_coordinates: dict[tuple[str, str], list[dict]] = defaultdict(list)
    editorial_report = root / "translation" / "reports" / "patch_editorial_all.jsonl"
    if editorial_report.is_file():
        for audit_row in read_jsonl(editorial_report):
            editorial_coordinates[(audit_row["source_file"], audit_row["english"])].append(audit_row)
    exact_preact_batches = []
    # Newer editorial completion batches intentionally contain longer source
    # passages than the earlier partial batches, so apply them first.
    runtime_batch_paths = sorted((root / "translation" / "human").glob("preact_runtime_batch_*.json"))
    runtime_batch_payloads = {
        path: json.loads(path.read_text(encoding="utf-8-sig"))
        for path in runtime_batch_paths
    }
    ordered_runtime_batches = [
        path for path in reversed(runtime_batch_paths)
        if runtime_batch_payloads[path].get("apply_order") != "post"
    ] + [
        path for path in runtime_batch_paths
        if runtime_batch_payloads[path].get("apply_order") == "post"
    ]
    for batch_path in ordered_runtime_batches:
        payload = runtime_batch_payloads[batch_path]
        batch_count = 0
        # Replace longer passages before their short JSX fragments (for
        # example a paragraph containing the standalone word "neither").
        for row in sorted(payload.get("rows", []), key=lambda item: len(item["english"]), reverse=True):
            source_name = row["source_file"]
            source_path = Path(source_name)
            if not source_name.startswith(("preact/", "preact-remote/")) or source_path.is_absolute() or ".." in source_path.parts:
                raise RuntimeError(f"unsafe exact Preact source path: {source_name}")
            target = workspace / source_path
            if not target.is_file():
                raise RuntimeError(f"exact Preact source missing: {source_name}")
            text = target.read_text(encoding="utf-8-sig")
            english = row["english"]
            russian = row["russian"]
            expected = int(row.get("expected_matches", 1))
            if english == russian:
                # Explicit KEEP_EN rows document reviewed terminology but do
                # not need a source rewrite, which also avoids stale editorial
                # coordinates when an upstream page is merely reflowed.
                continue
            found = text.count(english)
            if row.get("retired") is True:
                if found:
                    raise RuntimeError(
                        f"retired exact Preact source returned for {source_name} ({batch_path.name}): {english[:160]!r}"
                    )
                continue
            if found == expected:
                target.write_text(text.replace(english, russian), encoding="utf-8", newline="")
                batch_count += found
                continue
            # A cumulative catalog translation may have applied the same
            # reviewed Russian value before an exact runtime batch reaches it.
            # Treat that as satisfied instead of reporting source drift.
            if found == 0 and text.count(russian) == expected:
                continue
            # Editorial JSX is frequently reflowed without changing its visible
            # text. Accept whitespace-only source drift when the passage still
            # has the exact expected cardinality.
            flexible = re.compile(r"\s+".join(re.escape(part) for part in english.split()))
            flexible_matches = list(flexible.finditer(text))
            if len(flexible_matches) == expected:
                def replace_flexible(match: re.Match[str]) -> str:
                    missing_breaks = max(0, match.group(0).count("\n") - russian.count("\n"))
                    return russian + ("\n" * missing_breaks)

                target.write_text(flexible.sub(replace_flexible, text), encoding="utf-8", newline="")
                batch_count += len(flexible_matches)
                continue
            coordinates = editorial_coordinates.get((source_name, english), [])
            if len(coordinates) != expected:
                raise RuntimeError(
                    f"exact Preact match count changed for {source_name}: expected {expected}, "
                    f"found {found}, audited coordinates {len(coordinates)} ({batch_path.name}); "
                    f"source={english[:160]!r}"
                )
            lines = text.splitlines(keepends=True)
            for coordinate in sorted(coordinates, key=lambda item: int(item["source_line"]), reverse=True):
                pinned = dict(coordinate)
                pinned["russian"] = russian
                replace_on_line(lines, pinned)
            target.write_text("".join(lines), encoding="utf-8", newline="")
            batch_count += len(coordinates)
        exact_preact_batches.append({"file": batch_path.name, "replacements": batch_count})
    applied_preact = sum(item["translated_literals"] for item in patched)
    report = {
        "native_files": native_manifest,
        "native_literals": len(native),
        "preact_files": patched,
        "preact_literals": applied_preact,
        "preact_selected": len(preact),
        "preact_skipped_missing": skipped_missing,
        "preact_exact_batches": exact_preact_batches,
    }
    (root / "reports" / "phase2a_overrides.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"native_files": len(native_manifest), "native_literals": len(native), "preact_files": len(patched), "preact_literals": applied_preact, "preact_exact_replacements": sum(item["replacements"] for item in exact_preact_batches), "preact_skipped_missing": len(skipped_missing)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
