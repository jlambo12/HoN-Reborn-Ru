# Phase 1.5 — foundation hardening

Phase 1.5 завершает только архитектурную основу. Массовый перевод, Preact i18n,
установка archive и изменение поведения клиента не выполнялись.

## Классификатор

- Announcer identity определяется только grammar `interface:announcement_*`;
  options/store/vanity UI с `announcer` переводится.
- Hero, Ability и Item name/name-variant grammar поддерживает `_name$` и
  `_name:`; hero roles/prose переводятся.
- Cosmetic matching использует token boundaries, а не substring.
- Item search terms и shop categories выделены как недисплейные metadata.
- Structural-only `\\r`, `\\n`, `\\t` и комбинации не требуют перевода.
- `runtime_role` отделяет display text от command/internal/path/metadata data.
- `thai_signal` является вспомогательной эвристикой.
- Inline `protected_terms` строятся из canonical entity rows longest-first и
  проверяются builder-ом как точный multiset.

Итоговые counts находятся в `reports/phase15_summary.json`. Переход всех 1 494
исходных REVIEW строк зафиксирован в
`reports/phase15_review_transition.json`.

## QA и inventory

- `scripts/run_tests.ps1` — regression suite classifier/builder.
- `reports/native_ui_string_candidates.jsonl` — hardcoded visible candidates из
  прямого read-only scan 161 package, 35 interface и 112 Lua.
- `reports/native_ui_integration_points.json` — localization integration points.
- `scripts/run_preact_ast_scan.ps1` — AST production catalog без Patch Notes
  history.
- `scripts/build_preact_baseline.ps1` — изолированный неизменённый baseline
  frontend build; ничего не устанавливает.
