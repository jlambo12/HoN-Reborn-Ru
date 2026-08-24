#!/usr/bin/env python3
"""Transactionally install the validated CURRENT Russian thin overlay."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--juvio-root", type=Path, required=True)
    args = parser.parse_args()
    project = args.project_root.resolve()
    juvio = args.juvio_root.resolve()
    game = juvio / "heroes of newerth" / "resources0.jz"
    extension_dir = juvio / "extensions"
    installed = extension_dir / "resources0.jz"
    build = project / "build" / "human-ru-current" / "resources0.jz"
    report_path = project / "translation" / "reports" / "human_current_rebase.json"
    snapshot_path = project / "translation" / "priority" / "live_scope_snapshot.json"
    if extension_dir != (juvio / "extensions").resolve() or build != (project / "build" / "human-ru-current" / "resources0.jz").resolve():
        raise SystemExit("Unsafe resolved install paths")
    for path in (game, build, report_path, snapshot_path):
        if not path.is_file():
            raise SystemExit(f"Required file missing: {path}")

    release = json.loads(report_path.read_text(encoding="utf-8"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    game_sha = digest(game)
    build_sha = digest(build)
    if game_sha != snapshot["upstream"]["sha256"]:
        raise SystemExit("Installed game no longer matches the validated CURRENT snapshot")
    if release.get("result") != "PASS" or build_sha != release["output"]["sha256"]:
        raise SystemExit("Russian release is not the validated rebase output")
    with zipfile.ZipFile(build) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise SystemExit(f"Release ZIP integrity failed at {corrupt}")

    timestamp = datetime.now(timezone.utc)
    stamp = timestamp.astimezone().strftime("%Y%m%d-%H%M%S")
    backup = None
    old_sha = None
    if installed.is_file():
        old_sha = digest(installed)
        backup_dir = extension_dir / "backups" / "human-ru-current"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"resources0-before-human-ru-{stamp}.jz"
        if backup.exists():
            raise SystemExit(f"Backup collision: {backup}")
        shutil.copy2(installed, backup)
        if digest(backup) != old_sha:
            raise SystemExit("Backup verification failed; installed extension was not changed")

    extension_dir.mkdir(parents=True, exist_ok=True)
    temporary = extension_dir / ".resources0-human-ru-current-install.tmp"
    if temporary.exists():
        temporary.unlink()
    shutil.copy2(build, temporary)
    if digest(temporary) != build_sha:
        temporary.unlink(missing_ok=True)
        raise SystemExit("Temporary install copy verification failed")
    os.replace(temporary, installed)
    if digest(installed) != build_sha:
        raise SystemExit("Installed extension verification failed")

    state = {
        "result": "INSTALLED",
        "timestamp_utc": timestamp.isoformat(),
        "game_archive": {"path": str(game), "sha256": game_sha, "unchanged": True},
        "previous_extension": {"sha256": old_sha, "backup": str(backup) if backup else None},
        "installed_extension": {"path": str(installed), "sha256": build_sha, "size_bytes": installed.stat().st_size},
        "runtime_verified": False,
    }
    state_path = project / "translation" / "reports" / "human_current_install_state.json"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
