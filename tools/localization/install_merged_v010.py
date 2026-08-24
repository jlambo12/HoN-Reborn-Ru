#!/usr/bin/env python3
"""Transactionally install the validated merged Russian 0.1.0 overlay."""

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
    build = project / "build" / "merged-ru-v0.1.0" / "resources0.jz"
    report_path = project / "translation" / "reports" / "merged_ru_v0.1.0.json"
    extension_dir = juvio / "extensions"
    installed = extension_dir / "resources0.jz"
    if extension_dir.resolve() != (juvio / "extensions").resolve():
        raise SystemExit("Unsafe extension path")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    build_sha = digest(build)
    if report.get("result") != "PASS" or report.get("version") != "0.1.0" or build_sha != report["output"]["sha256"]:
        raise SystemExit("Merged build is not validated")
    with zipfile.ZipFile(build) as archive:
        if corrupt := archive.testzip():
            raise SystemExit(f"Build CRC failed at {corrupt}")

    timestamp = datetime.now(timezone.utc)
    stamp = timestamp.astimezone().strftime("%Y%m%d-%H%M%S")
    backup = None
    old_sha = None
    if installed.is_file():
        old_sha = digest(installed)
        backup_dir = extension_dir / "backups" / "merged-ru-v0.1.0"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"resources0-before-v0.1.0-{stamp}.jz"
        shutil.copy2(installed, backup)
        if digest(backup) != old_sha:
            raise SystemExit("Backup verification failed")

    extension_dir.mkdir(parents=True, exist_ok=True)
    temporary = extension_dir / ".resources0-merged-v010-install.tmp"
    temporary.unlink(missing_ok=True)
    shutil.copy2(build, temporary)
    if digest(temporary) != build_sha:
        raise SystemExit("Temporary copy verification failed")
    os.replace(temporary, installed)
    if digest(installed) != build_sha:
        raise SystemExit("Installed file verification failed")

    state = {
        "result": "INSTALLED",
        "version": "0.1.0",
        "timestamp_utc": timestamp.isoformat(),
        "previous_extension": {"sha256": old_sha, "backup": str(backup) if backup else None},
        "installed_extension": {"path": str(installed), "sha256": build_sha, "size_bytes": installed.stat().st_size},
        "runtime_verified": False,
    }
    state_path = project / "translation" / "reports" / "merged_ru_v0.1.0_install_state.json"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
