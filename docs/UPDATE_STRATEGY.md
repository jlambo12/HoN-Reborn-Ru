# Стратегия обновлений

## Pipeline после патча

1. Запустить `scripts/build_preact_baseline.ps1`, затем
   `scripts/run_phase16.ps1`; pipeline вычислит SHA-256 и новый snapshot.
2. Сопоставить новый `catalog/strings.jsonl` с предыдущим по `id`.
3. New IDs получают классификацию и пустой RU.
4. При том же ID и изменившемся `english_hash` сохранить RU, но перевести статус
   в REVIEW до проверки placeholders/смысла.
5. Исчезнувшие IDs отметить removed/deprecated, не теряя translation memory.
6. Повторно применить protected rules независимо от сохранённого RU.
7. Сравнить Preact source, host packages и compiled dist; пересобрать Extended RU.
8. Запустить regression validation и builder probe. Strict production builder и
   in-game smoke-tests остаются release gates после появления переводов.

Текущий audit уже выполняет базовый трёхсторонний merge
`old EN + old RU + new EN`: сохраняет translator fields для неизменного hash,
переводит изменившийся EN в REVIEW, обновляет protected English и записывает
removed IDs в `reports/catalog_update.json`. Перед первым production-update
нужно добавить regression tests на реальные исторические snapshots.

## Release gates

- SHA текущей игры записан в manifest релиза.
- Нет duplicate IDs, placeholder/tag/color mismatches.
- Нет изменённых KEEP_EN.
- Нет пустых TRANSLATE и raw localization keys.
- `regions.lua` patch применился ровно к ожидаемой структуре.
- Extension archive читается обратно и содержит manifest-ожидаемый список.
- In-game smoke-test выполняется с `-mod "heroes of newerth;extensions"`.

Installer обязан делать backup существующего extension перед заменой и хранить
достаточные данные для Repair, Restore и Uninstall. Основной game archive не
является install target.
