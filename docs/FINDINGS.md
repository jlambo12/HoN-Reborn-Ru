# Результаты первого прохода

Дата аудита: 2026-08-15. Установка игры не изменялась.

## Текущий билд

- Архив: `%LOCALAPPDATA%\Juvio\heroes of newerth\resources0.jz`
- Размер: 5 289 891 314 байт
- SHA-256: `58fbed1ed7e5507a72c4ab718b757187395e59e75ca5d9a47d3a89e2fa398364`
- SHA совпадает с ранее известным.
- Файлов: 50 909.
- Compression method 0: 4 929 entries.
- Compression method 93 (Zstandard): 45 980 entries.

Существующий тестовый extension также только прочитан: 476 617 байт, 8 entries,
SHA-256 `1391aa8551180b7a7146556ff016e0ef092bacbf9eb6134b3ddcd0adacc22483`.

## String tables

Upstream содержит 20 060 EN-записей и 19 994 уникальных эффективных строк.

| Namespace | EN unique | TH unique | EN keys missing in TH |
|---|---:|---:|---:|
| bot_messages | 155 | 155 | 0 |
| client_messages | 654 | 654 | 0 |
| entities | 10 333 | 10 286 | 145 |
| game_messages | 710 | 704 | 6 |
| interface | 7 662 | 7 615 | 58 |
| interface_test_suite | 480 | 480 | 0 |
| **Итого** | **19 994** | **19 894** | **209** |

Thai-only keys существуют: 98 в `entities` и 11 в `interface`. Они не входят в
EN-based source of truth, но сохранены в статистике для исследования legacy
regional content.

Диагностический `options_slider_max_ui_framerate` найден в EN на строке 593,
отсутствует в TH и классифицирован как `settings_ui / TRANSLATE`.

## Первичная классификация

| Status | Количество |
|---|---:|
| TRANSLATE | 14 537 |
| KEEP_EN | 2 756 |
| REVIEW | 1 494 |
| DEPRECATED | 1 205 |
| DYNAMIC | 2 |

Крупные категории: functional UI — 7 036; ability descriptions — 4 401;
ability names — 1 559; settings UI — 1 239; item descriptions — 947;
game event feed — 682; help/tutorial — 344; item names — 228; gameplay
descriptions — 232; hero descriptions — 181; profile/competitive UI — 157;
hero names — 145; announcer content — 103; cosmetic names — 39.

Классификация консервативна: 1 494 неоднозначные entity-строки оставлены REVIEW.
Весь `game_messages` на первом проходе оставлен EN как безопасный event-feed
clone; дальнейший контекстный разбор может разрешить перевод отдельных ключей.

## Что покрывается штатно

Native tables покрывают старый функциональный UI, настройки, lobby/hero select,
HUD, gameplay descriptions, сообщения клиента и ботов. `lang_ru`, RU flag,
international fonts, `SetHostLocale` и runtime-loading RU уже существуют или
подтверждены. Для этого слоя не нужна подмена English.

## Что требует Extended RU

В исходниках Preact найдено 4 697 консервативных hardcoded-кандидатов. Из них
4 174 относятся к встроенному корпусу Patch Notes v2; остальные распределены
между Profile, Match Stats, Leaderboard, Honor System, Lobby Customization,
Jade Buy, shared components и app shell. В исходниках не найден рабочий общий
localization API.

Подтверждены изображения с английским UI-текстом внутри bundled Patch Notes:
`cosmetics-store.webp`, `keybindings-toggle.webp`, `npe-2.webp`. Это скриншоты,
а не живые controls, и они требуют `IMAGE_TEXT` решения (замена, локализованная
подпись или осознанное сохранение оригинала).

## Риски

- Игра обновляется: EN hash и frontend source/dist могут измениться независимо.
- Upstream имеет duplicate keys; silent merge без отчёта недопустим.
- Preact пока не имеет i18n abstraction, глобальная замена литералов опасна.
- MOTD UI и payload удалённые; extension не контролирует серверный язык.
- API возвращает profile, product, patch-note и vanity data; часть полей должна
  оставаться EN по policy.
- Patch Notes v2 содержит большой статический исторический корпус и screenshots.
- Штатный `Restart()` может потерять `-mod`; launcher должен владеть restart flow.
- Основной архив ZIP64 >4 GiB и method 93 требуют Python 3.14+ или эквивалентный
  Zstandard-aware writer.

## Следующий шаг

Phase 1.6 формирует `reports/review_queue.csv` и корректный denominator release
coverage. Phase 2 должен начинаться только после принятия этой очереди и
canonical dictionaries: затем можно переводить приоритетный release UI и
проектировать Preact i18n, не включая historical Patch Notes corpus.
