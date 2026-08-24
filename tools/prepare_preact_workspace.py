#!/usr/bin/env python3
"""Create an isolated baseline Preact workspace from an audited snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    snapshot = args.snapshot.resolve()
    archive = args.archive.resolve()
    workspace = (root / "build" / "preact-baseline-workspace").resolve()
    expected_parent = (root / "build").resolve()
    if workspace.parent != expected_parent or workspace.name != "preact-baseline-workspace":
        raise SystemExit(f"Unsafe workspace target: {workspace}")
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)

    def ignore_generated(directory: str, names: list[str]) -> set[str]:
        """Drop app build output, but retain the vendored preact-qjs dist files."""
        current = Path(directory).resolve()
        ignored = {name for name in names if name in {"node_modules", "bun.exe", "__pycache__"}}
        if current.name == "preact" and current.parent == snapshot:
            ignored.add("dist")
        return ignored

    for name in ("preact", "preact-remote"):
        source = snapshot / name
        if source.is_dir():
            shutil.copytree(source, workspace / name, ignore=ignore_generated)

    # The shipped package-lock is stale relative to package.json; the matching
    # bun.lock and bundled Bun runtime are the reproducible install path.
    with zipfile.ZipFile(archive, "r") as zf:
        (workspace / "preact" / "bun.exe").write_bytes(zf.read("preact/bun.exe"))

    required = [
        workspace / "preact" / "package.json",
        workspace / "preact" / "package-lock.json",
        workspace / "preact" / "preact-qjs" / "package.json",
        workspace / "preact" / "src" / "main.tsx",
        workspace / "preact" / "public",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Incomplete Preact snapshot:\n" + "\n".join(missing))

    files = [path for path in workspace.rglob("*") if path.is_file()]
    digest = hashlib.sha256()
    for path in sorted(files):
        relative = path.relative_to(workspace).as_posix()
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    manifest = {
        "snapshot": str(snapshot),
        "workspace": str(workspace),
        "file_count": len(files),
        "source_bytes": sum(path.stat().st_size for path in files),
        "source_tree_sha256": digest.hexdigest(),
        "package_manager": "Bundled Bun runtime + bun.lock",
        "excluded": ["upstream app dist", "node_modules", "__pycache__"],
    }
    (workspace / "baseline-source-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
