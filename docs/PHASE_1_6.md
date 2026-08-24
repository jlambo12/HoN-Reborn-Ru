# Phase 1.6 — final localization hardening

Phase 1.6 является последним foundation-pass перед переводом. Он не заполняет
массово `russian`, не внедряет Preact i18n и не устанавливает archive в игру.

## Воспроизводимый pipeline

1. `scripts/build_preact_baseline.ps1` подготавливает неизменённый frontend.
2. `scripts/run_phase16.ps1` повторяет read-only audit, AST scan и policy-pass.
3. `scripts/run_tests.ps1` проверяет policy regressions и locked-span QA.
4. `scripts/build_probe.ps1` проверяет builder с English fallback только в
   локальной папке `build/`.

## Артефакты

- `catalog/canonical_dictionary.json` — heroes, abilities, items, bosses,
  cosmetics, announcer events и technical tokens с source keys и strength.
- `catalog/native_extended_ui.jsonl` — классификация всех native hardcoded
  candidates и будущая integration strategy.
- `catalog/preact_ui.jsonl` — production Preact catalog после final policy pass.
- `reports/state_protection_audit.jsonl` — удалённые State-only false locks.
- `reports/markup_protection_audit.json` — повторная проверка canonical names
  внутри HoN control markup.
- `reports/game_messages_classification.jsonl` — reason для каждого сообщения.
- `reports/completion_metrics.json` — Russian Release Translation Coverage.
- `reports/review_queue.csv` — P0/P1/P2/P3 очередь ручного review.
- `reports/phase16_summary.json` — итоговые counts.

## Upstream archive transition

Во время Phase 1.6 установленный read-only archive уже имел новое upstream
состояние `a518f760…` вместо snapshot Phase 1.5 `58fbed1e…`. Финальные counts
построены по текущему архиву; инструменты проекта не открывают его на запись.
Existing extension остался без изменений.
