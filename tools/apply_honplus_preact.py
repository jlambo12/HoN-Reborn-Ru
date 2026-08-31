#!/usr/bin/env python3
"""Apply the tracked HoN Plus panel to a prepared Preact workspace."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    workspace = args.workspace.resolve()
    expected_parent = (root / "build").resolve()
    if workspace.parent != expected_parent:
        raise SystemExit(f"Unsafe workspace: {workspace}")

    layer = workspace / "preact" / "src" / "layers" / "match-stats"
    source = root / "src" / "honplus_preact"
    shutil.copy2(source / "HoNPlusPanel.tsx", layer / "HoNPlusPanel.tsx")
    shutil.copy2(source / "honplus.css", layer / "honplus.css")

    matchstats = layer / "matchstats.tsx"
    text = matchstats.read_text(encoding="utf-8")
    if 'import HoNPlusPanel from "./HoNPlusPanel";' not in text:
        text = text.replace(
            'import MatchStatsGraphs from "./components/MatchStatsGraphs/MatchStatsGraphs";',
            'import MatchStatsGraphs from "./components/MatchStatsGraphs/MatchStatsGraphs";\nimport HoNPlusPanel from "./HoNPlusPanel";',
        )
    tab = '  {\n    title: "HoN Plus",\n    getComponent: (matchId) =>\n      matchId ? <HoNPlusPanel matchId={matchId} /> : undefined,\n    icon: <StatsIcon />,\n  },\n'
    if 'title: "HoN Plus"' not in text:
        gift_icon = text.find("    icon: <GiftIcon />,")
        marker_at = text.rfind("  {\n", 0, gift_icon)
        if gift_icon < 0 or marker_at < 0:
            raise SystemExit("Match Stats mastery tab marker was not found")
        text = text[:marker_at] + tab + text[marker_at:]
    if '"hon-plus": 2' not in text:
        text = text.replace('  "mastery": 2,\n  "awards": 3,', '  "hon-plus": 2,\n  "mastery": 3,\n  "awards": 4,')
    matchstats.write_text(text, encoding="utf-8")
    print(f"Applied HoN Plus Preact panel to {workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
