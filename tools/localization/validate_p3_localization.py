#!/usr/bin/env python3
"""Fast static validator for P3 menu, settings and bundled patch-note UI."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NATIVE_CATALOG = ROOT / "catalog" / "strings.jsonl"
PREACT_CATALOG = ROOT / "catalog" / "preact_ui.jsonl"
QUEUE = ROOT / "translation" / "priority" / "live_p3_work.jsonl"
REPORT = ROOT / "translation" / "reports" / "live_p3_validation.json"
LIVE_SNAPSHOT = ROOT / "translation" / "priority" / "live_scope_snapshot.json"

TOKEN_RE = re.compile(
    r"\$\{[^{}]+\}|\{[A-Za-z_][A-Za-z0-9_.]*\}|%\d*\$?[a-zA-Z]|\^(?:[0-9]{3}|[A-Za-z]|\*)"
)

# Runtime-visible literal translations found during the settings screenshot
# audit.  These are exact anti-regressions, not a general language detector.
SETTINGS_MACHINE_TRANSLATION_ANTIPATTERNS = (
    "Ползучесть HP",
    "уровень увлажнения",
    "Беззвучный диктор",
    "Немой диктор",
    "выноска с информацией о руне",
    "отсутствует выноска",
    "умный выбор устройства",
    "золотые номера",
    "Схема самогероя",
    "Показать, как это происходит",
    "При наведении курсора на выделение Интенсивность цвета",
    "Резюме смерти",
    "шкалы здоровья ползучего",
    "Устройство реагирует",
    "Многоблочное управление",
    "повышенное GPU использования",
    "UI работа с нитками",
    "UI untonemapped",
)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def tokens(value: str) -> Counter[str]:
    return Counter(TOKEN_RE.findall(value or ""))


def p3_rows() -> list[dict]:
    rows: list[dict] = []
    snapshot = json.loads(LIVE_SNAPSHOT.read_text(encoding="utf-8"))
    current_source_root = ROOT / "src" / "upstream" / snapshot["upstream"]["sha256"][:12]
    for row in read_jsonl(NATIVE_CATALOG):
        key = row.get("key", "")
        category = row.get("category", "")
        if category == "settings_ui":
            area = "settings"
        elif key.startswith(("main_menu_", "main_button_", "social_panel_")):
            area = "main_menu"
        else:
            continue
        rows.append({
            "id": f"{row.get('namespace', '')}:{key}",
            "area": area,
            "source": "native",
            "english": row.get("english", ""),
            "russian": row.get("russian", ""),
            "catalog_status": row.get("status", ""),
        })

    for row in read_jsonl(PREACT_CATALOG):
        source_file = row.get("source_file", "")
        if "patch-notes" not in source_file:
            continue
        rows.append({
            "id": row["id"],
            "area": "patch_notes",
            "source": "preact",
            "english": row.get("english", ""),
            "russian": row.get("russian", ""),
            "catalog_status": row.get("status", ""),
            "source_file": source_file,
            "current_source_present": (current_source_root / source_file).is_file(),
        })
    return rows


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

    errors: list[str] = []
    queue: list[dict] = []
    counts: Counter[str] = Counter()
    area_counts: dict[str, Counter[str]] = {}

    for row in p3_rows():
        english = row["english"]
        russian = row["russian"]
        catalog_status = row["catalog_status"]
        structural_ok = tokens(english) == tokens(russian)
        if row["source"] == "preact" and not row.get("current_source_present", True):
            status = "EXCLUDED"
        elif catalog_status in {"TRANSLATE", "KEEP_EN"} and russian.strip() and structural_ok:
            status = "DONE"
        elif catalog_status in {"TECHNICAL", "DEPRECATED", "DYNAMIC"}:
            status = "EXCLUDED"
        elif not russian.strip():
            status = "TODO"
        else:
            status = "INVALID_REVIEW"
        out = {**row, "priority": "P3", "status": status, "structural_tokens_ok": structural_ok}
        queue.append(out)
        counts[status] += 1
        area_counts.setdefault(row["area"], Counter())[status] += 1
        if status in {"TODO", "INVALID_REVIEW"}:
            errors.append(f"{status}: {row['id']}")
        if row["area"] == "settings":
            for phrase in SETTINGS_MACHINE_TRANSLATION_ANTIPATTERNS:
                if phrase.casefold() in russian.casefold():
                    errors.append(f"MACHINE_TRANSLATION_ANTIPATTERN: {row['id']}: {phrase}")

    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in queue), encoding="utf-8", newline="\n")
    result = "PASS" if not errors else "FAIL"
    report = {
        "schema_version": 1,
        "result": result,
        "priority": "P3",
        "scope": ["main_menu", "settings", "patch_notes"],
        "rows": len(queue),
        "status_counts": dict(sorted(counts.items())),
        "areas": {area: dict(sorted(values.items())) for area, values in sorted(area_counts.items())},
        "errors": errors,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
