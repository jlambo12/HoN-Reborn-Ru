# Политика локализации

## Переводим

Функциональный интерфейс, настройки, matchmaking, custom games, lobby, hero
select, HUD, магазин, scoreboard, ESC menu, help/tutorial, profile, match
history, ladder, store/vanity/plinko UI, replays, notifications, dialogs,
social/post-game UI, а также описания героев, способностей, предметов, боссов и
механик.

## Оставляем English

Имена героев, названия способностей, предметов, avatars/skins и конкретных
cosmetic products. Announcer audio, banners, фирменные event names/messages и
озвучиваемые leave/reconnect events не локализуются. Настройки announcer
переводятся.

## Контекст важнее слова

Запреты применяются по key/path/namespace/category. Само слово `Victory` не
является глобально защищённым: announcer preview остаётся EN, а Match History
переводится. Сомнительный контекст получает REVIEW.

## Статусы

- `TRANSLATE` — нужен русский текст.
- `KEEP_EN` — English является утверждённым runtime value.
- `REVIEW` — требуется ручное семантическое решение.
- `DYNAMIC` — значение приходит извне или вычисляется.
- `IMAGE_TEXT` — текст встроен в растровый asset.
- `DEPRECATED` — пустое/неактивное upstream-значение.

Массовый машинный перевод до контекстной ревизии запрещён.

## Правило точечных исправлений

Исправление по скриншоту оформляется отдельным проверяемым слоем поверх последнего
релиза. Перед публикацией новый архив сравнивается с предыдущим: разрешены только
заранее перечисленные файлы, удаление прежних файлов запрещено, а все остальные
члены архива должны совпадать побайтово. Нативные UI-файлы берутся только из
точной текущей версии Juvio; целые экраны из старых сборок не переносятся.

Проверка выполняется `tools/localization/verify_thin_patch.py` и закрепляется
регрессионным тестом релизного архива.

## Runtime role

Статус перевода не заменяет роль значения. `DISPLAY_TEXT` допускает перевод по
статусу; `COMMAND_TOKEN`, `INTERNAL_ID`, `RESOURCE_PATH`, `SEARCH_METADATA`,
`STRUCTURAL` и `DYNAMIC_DATA` не должны попадать в массовый перевод. Команды и
aliases остаются `REVIEW/COMMAND_TOKEN`, тогда как их help/usage/error prose
классифицируется отдельно как display text.

Thai используется только как сигнал (`DIFFERENT`, `SAME_AS_ENGLISH`, `EMPTY`,
`MISSING`), но не как источник истины.

## Утверждённая политика Phase 1.6

- Gameplay states/status labels (`Silenced`, `Stunned`, `Disarmed` и аналоги)
  переводятся; `State_*` не является источником canonical Ability names.
- MMR/KDA/GPM/XPM/DPM/FPS/HP/MP и контролируемые технические сокращения,
  region/currency codes остаются EN. Полные country display names переводятся.
- Физические keycaps (`Ctrl`, `Enter`, `F1`, `Mouse1`) копируются без перевода;
  названия действий переводятся.
- Kongor и Fluffylumps, а также boss ability names остаются EN; описания и
  характеристики переводятся.
- Non-text punctuation/number/markup values и test-suite corpus исключаются из
  release translation workload.

Контролируемые списки находятся в `catalog/technical_tokens.json`, starter
terminology — в `catalog/glossary.json`.
