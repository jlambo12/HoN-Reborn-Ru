#!/usr/bin/env python3
"""Fail when a translation microfix changes files outside its reviewed allowlist."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def member_hashes(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise SystemExit(f"CRC failure in {path}: {corrupt}")
        return {
            name: hashlib.sha256(archive.read(name)).hexdigest()
            for name in archive.namelist()
            if not name.endswith("/")
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--allow", action="append", default=[])
    args = parser.parse_args()

    base = member_hashes(args.base.resolve())
    candidate = member_hashes(args.candidate.resolve())
    allowed = set(args.allow)
    added = sorted(candidate.keys() - base.keys())
    removed = sorted(base.keys() - candidate.keys())
    changed = sorted(name for name in base.keys() & candidate.keys() if base[name] != candidate[name])
    actual = set(added) | set(removed) | set(changed)
    unexpected = sorted(actual - allowed)
    unused = sorted(allowed - actual)
    result = {
        "result": "PASS" if not unexpected and not removed and not unused else "FAIL",
        "added": added,
        "removed": removed,
        "changed": changed,
        "unexpected": unexpected,
        "allowed_but_unchanged": unused,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
