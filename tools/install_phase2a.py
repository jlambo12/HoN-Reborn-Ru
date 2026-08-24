#!/usr/bin/env python3
"""Transactionally back up the probe and install the accepted Phase 2A archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path


GAME_SHA = "a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762"
PROBE_SHA = "1391aa8551180b7a7146556ff016e0ef092bacbf9eb6134b3ddcd0adacc22483"
PHASE2A_SHA = "9d5d4176ff51f1799df50d9f7f61ba387ec7cdc54244cb7393e8c87f7143945c"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
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
    build = project / "build" / "phase2a" / "resources0.jz"
    backup_dir = extension_dir / "backups"
    if extension_dir != (juvio / "extensions").resolve() or build != (project / "build" / "phase2a" / "resources0.jz").resolve():
        raise SystemExit("Unsafe resolved install paths")
    for path in (game, installed, build):
        if not path.is_file():
            raise SystemExit(f"Required file missing: {path}")
    game_sha, old_sha, build_sha = digest(game), digest(installed), digest(build)
    if game_sha != GAME_SHA:
        raise SystemExit(f"Game archive SHA mismatch: {game_sha}")
    if old_sha != PROBE_SHA:
        raise SystemExit(f"Existing extension is not the accepted probe: {old_sha}")
    if build_sha != PHASE2A_SHA:
        raise SystemExit(f"Phase 2A build SHA mismatch: {build_sha}")
    with zipfile.ZipFile(build) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise SystemExit(f"Phase 2A ZIP integrity failed at {corrupt}")
    timestamp = datetime.now(timezone.utc)
    stamp = timestamp.astimezone().strftime("%Y%m%d-%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"resources0-probe-{stamp}.jz"
    if backup.exists():
        raise SystemExit(f"Backup collision: {backup}")
    shutil.copy2(installed, backup)
    backup_sha = digest(backup)
    if backup_sha != old_sha:
        raise SystemExit("Backup verification failed; installed extension was not changed")
    temporary = extension_dir / ".resources0-phase2a-install.tmp"
    if temporary.exists():
        temporary.unlink()
    shutil.copy2(build, temporary)
    if digest(temporary) != PHASE2A_SHA:
        temporary.unlink(missing_ok=True)
        raise SystemExit("Temporary install copy verification failed")
    os.replace(temporary, installed)
    installed_sha = digest(installed)
    if installed_sha != PHASE2A_SHA:
        raise SystemExit(f"Installed extension verification failed: {installed_sha}")
    state = {
        "result": "INSTALLED",
        "timestamp_utc": timestamp.isoformat(),
        "game_archive": {"path": str(game), "size_bytes": game.stat().st_size, "sha256": game_sha},
        "old_extension": {"path": str(installed), "size_bytes": backup.stat().st_size, "sha256": old_sha},
        "backup": {"path": str(backup), "size_bytes": backup.stat().st_size, "sha256": backup_sha, "retained": True},
        "phase2a_source": {"path": str(build), "size_bytes": build.stat().st_size, "sha256": build_sha, "zip_integrity": "PASS"},
        "installed_extension": {"path": str(installed), "size_bytes": installed.stat().st_size, "sha256": installed_sha},
        "exe_dll_modified": False,
    }
    report = project / "reports" / "phase2a_install_state.json"
    report.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
