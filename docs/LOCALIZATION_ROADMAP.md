# HoN Reborn RU — Localization Roadmap

Последнее обновление: 2026-08-18.

## Текущая контрольная точка

- Установленный baseline: **Pass C**, SHA-256 `3d5ee66b9507c342d92b0be886d2918ea959e9beffb2126e6a7f77604142e301`.
- Основной upstream archive не изменён, SHA-256 `a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762`.
- PRE-D Existing Translation Audit: **завершён**.
- DONOR TEST 0: **COMPLETE**;
  donor не утверждён и не объединён с проектом.
- Hybrid Multi-Source Localization Base: **реализована**, переводческий batch
  workflow активен.
- Controlled Batch 001 — Modern UI: **TARGETED RUNTIME PASS / FULL BATCH STILL PENDING**.
  `СПРАВКА`, `РЕЙТИНГ` и исправление raw `game_menu_*` подтверждены в живом
  клиенте. Остальные решения из 39 строк не получают автоматический статус
  runtime-verified.
- Development test: `controlled_001_test` (изолированный `Pass C + Controlled 001`).
- Первый runtime QA: **FAILED (locale profile resolved to `en`)**; Batch 001 не
  помечен runtime-verified. Pipeline исправлен для явной фиксации `ru` только в
  изолированном профиле перед повторным запуском.
- Второй runtime QA: **PARTIAL PASS**. Locale и loading labels подтверждены;
  main-navigation оказался hardcoded в `system_bar.package`, а raw `game_menu_*`
  вызван переводом технического `_button` в package-шаблоне. Выполняется только
  controlled live-key resolution fix; весь batch остаётся runtime-pending.
- Третий runtime QA: **TARGETED PASS**. Hardcoded main-navigation literals
  `СПРАВКА`/`РЕЙТИНГ` и восстановленный `game_menu_{btnName}_button` реально
  работают. Это не является подтверждением всех 39 строк Batch 001.
- Controlled Batch 002 — terminology: **BUILT / ISOLATED RUNTIME QA STARTED**.
  Pass C и upstream не изменялись; полный результат ручной проверки не
  зафиксирован как runtime-verified.
- Controlled Batch 003 — large-scale player-facing: **CANDIDATE + ONE
  CONTROLLED BUILD / NOT INSTALLED**. Все 19 538 CURRENT-ключей получили
  явное решение; одиночные donor-предложения запрещены после выявления
  семантических ошибок, механические описания оставлены в REVIEW.
- Pass D1: **не начат**.

## PRE-D — Existing Translation Audit

Источник-кандидат `HoN_RU_Pack` проверен в read-only режиме на закреплённом commit
`9f276bf86037bffe9e6d208dacd99d19b4e666eb`. Автоматический merge/import не
выполнялся. Результаты находятся в
`translation/reports/PRE_D_DONOR_AUDIT.md` и связанных машиночитаемых отчётах.

Следующее действие: ручное ревью групп `DONOR_PREFERRED_CANDIDATE`,
`MANUAL_REVIEW`, известных проблем и конфликтов KEEP_EN. Значение может попасть
в проект только после проверки смысла, entity context, placeholders/markup и
естественности русского.

## DONOR TEST 0 — Runtime Preview

Минимальный donor-only overlay запущен с `host_locale en` и mod list
`heroes of newerth;donor_test`. `extensions` не загружался. Pass C остаётся
стабильным baseline; результат preview предназначен только для визуального
сравнения и не означает одобрение donor-перевода.

Runtime-выводы:

- donor ценен как secondary/human candidate source;
- donor заметно сильнее покрывает legacy/gameplay descriptions;
- modern Reborn UI у donor покрыт слабо;
- gameplay descriptions могут быть семантически устаревшими;
- прямой merge donor запрещён.

## Hybrid Multi-Source Localization Base

Current game source определяет актуальный смысл. Project-approved memory,
pinned donor и Pass C предоставляют независимые candidates. Donor и Pass C не
становятся approved автоматически; mechanic text требует current entity
context и semantic review.

Текущий следующий шаг: **ручной runtime QA изолированной Controlled 003
сборки**. Stable runtime baseline остаётся Pass C; Controlled 003 не установлен.

## Future distribution / launcher requirements

Некоторые игроки запускают HoN через GearUP или аналогичные сетевые
ускорители, которым нужен стабильный путь к executable/shortcut. Будущий
launcher русификатора должен иметь стабильный executable path и запускать
реальный `juvio.exe` с нужными localization mod arguments. Он должен оставаться
совместимым с внешними accelerator/VPN tools, но не реализовывать и не изменять
сетевую маршрутизацию самостоятельно. Это только документированное будущее
требование; launcher work не начата.

## Ограничитель этапа

Не изменять Pass C или upstream. Controlled-сборки устанавливаются только в
отдельный mod-каталог после явной команды; любой непроверенный смысл остаётся
в REVIEW.
