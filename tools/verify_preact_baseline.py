#!/usr/bin/env python3
"""Record integrity evidence for the isolated baseline Preact build."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    workspace = root / "build" / "preact-baseline-workspace"
    dist = workspace / "preact" / "dist"
    required = [dist / "index.html", dist / "index.js", dist / "assets" / "index.css"]
    missing = [str(path.relative_to(workspace)) for path in required if not path.is_file()]
    files = [path for path in dist.rglob("*") if path.is_file()] if dist.is_dir() else []
    with zipfile.ZipFile(args.archive.resolve()) as zf:
        shipped = [info for info in zf.infolist() if info.filename.startswith("preact/dist/") and not info.is_dir()]
        shipped_names = {PurePosixPath(info.filename).relative_to("preact/dist").as_posix() for info in shipped}
    built_names = {path.relative_to(dist).as_posix() for path in files}
    report = {
        "result": "PASS" if not missing else "FAIL",
        "workspace": str(workspace),
        "build_command": "bundled bun.exe install --frozen-lockfile && bundled bun.exe run build",
        "package_manager": "Bun 1.2.17",
        "lockfile": "preact/bun.lock",
        "required_outputs": {str(path.relative_to(dist)).replace("\\", "/"): path.is_file() for path in required},
        "missing_required_outputs": missing,
        "built_file_count": len(files),
        "built_bytes": sum(path.stat().st_size for path in files),
        "shipped_dist_file_count": len(shipped),
        "shipped_dist_bytes": sum(info.file_size for info in shipped),
        "same_relative_file_set": built_names == shipped_names,
        "built_only_count": len(built_names - shipped_names),
        "shipped_only_count": len(shipped_names - built_names),
        "key_output_sha256": {
            path.relative_to(dist).as_posix(): sha256(path) for path in required if path.is_file()
        },
        "notes": [
            "No source or localization modifications were applied before this build.",
            "The shipped package-lock.json is stale; bun.lock matches the bundled runtime and dependency graph.",
            "Vite emitted non-fatal unresolved runtime button URL and chunk-size warnings.",
        ],
    }
    output = root / "reports" / "preact_baseline_build.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
