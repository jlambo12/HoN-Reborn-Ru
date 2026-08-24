# Phase 2A — первый русский вертикальный срез

Статус: **PASS**.

Phase 1.7 точечно исправляет policy для announcer/combat/leave feed, контролируемых морфологических aliases, Preact branded stats, English-changed merge и перечисленных P0-сущностей. Широкий discovery повторно не запускался.

Phase 2A переводит 6000 scoped-строк: 5764 stringtable, 79 native hardcoded и 157 Preact. В охват входят settings, startup/main navigation, основные dialogs/notifications, matchmaking/custom games/lobby/hero select, базовый HUD/scoreboard/ESC/loading и соответствующие Preact lobby/shared/match-stats слои. Огромные массивы ability/item descriptions, hero lore, полный Help и Patch Notes не входят.

Source of truth: `catalog/strings.jsonl`, `catalog/native_extended_ui.jsonl`, `catalog/preact_ui.jsonl`, `translations/phase2a_memory.jsonl`; точный scope находится в `catalog/phase2a_scope.json`.

Сборка находится отдельно в `build/phase2a/resources0.jz`. Основной игровой архив и существующее probe extension не менялись. `scripts/install_phase2a_test.ps1` при ручном запуске сначала сохраняет установленный extension в `backups/phase2a-installer`, затем использует mod stack `heroes of newerth;extensions`.

Полные метрики и QA: `reports/phase2a_final_report.json`.
