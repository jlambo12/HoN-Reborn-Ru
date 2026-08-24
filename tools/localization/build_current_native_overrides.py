#!/usr/bin/env python3
"""Build exact native text overrides from the validated CURRENT archive."""

from __future__ import annotations

import hashlib
import json
import zipfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = Path.home() / "AppData" / "Local" / "Juvio" / "heroes of newerth" / "resources0.jz"
BATCH_DIR = ROOT / "translation" / "human"
OUTPUT_ROOT = ROOT / "src" / "current_native_ru"
REPORT = ROOT / "translation" / "reports" / "current_native_overrides.json"
SNAPSHOT = ROOT / "translation" / "priority" / "live_scope_snapshot.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    upstream_sha = sha256_file(UPSTREAM)
    if upstream_sha != snapshot["upstream"]["sha256"]:
        raise SystemExit("CURRENT upstream identity mismatch")

    grouped: dict[str, list[dict]] = defaultdict(list)
    batches = []
    for path in sorted(BATCH_DIR.glob("native_runtime_batch_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        batches.append(payload["batch_id"])
        for row in payload.get("rows", []):
            grouped[row["source_file"]].append(row)

    files = []
    with zipfile.ZipFile(UPSTREAM) as archive:
        for source_file, rows in sorted(grouped.items()):
            data = archive.read(source_file)
            replacements = 0
            for row in rows:
                encoding = row.get("source_encoding", "utf-8")
                old = row["english"].encode(encoding)
                new = row["russian"].encode("utf-8")
                found = data.count(old)
                if found != row.get("expected_matches", 1):
                    raise SystemExit(f"Exact native match count changed for {source_file}: {found}")
                data = data.replace(old, new)
                replacements += found
            target = OUTPUT_ROOT / source_file
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            files.append({
                "source_file": source_file,
                "output": str(target),
                "sha256": hashlib.sha256(data).hexdigest(),
                "replacements": replacements,
            })

    report = {
        "schema_version": 1,
        "result": "PASS",
        "upstream_sha256": upstream_sha,
        "batches": batches,
        "files": files,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
