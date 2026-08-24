# Visible UI Localization Pass B

Статус test build: **PASS по структуре, builder, CRC и regression; не установлен**.

## Переведённый scope

| Раздел | Строк |
|---|---:|
| Help Topics (ранее пустые) | 236 |
| Описания героев | 276 |
| Описания способностей | 3740 |
| Описания предметов | 917 |
| Связанные state/tooltips | 1079 |
| Bosses UI | 41 |
| Hero encyclopedia labels | 76 |
| Settings/controls targeted fixes | 13 |
| Native hardcoded UI | 123 |
| MOTD local shell, подготовлено в каталоге | 17 |

Help Topics теперь не имеет пустых localizable strings в выбранном наборе.
Имена героев, способностей, предметов, Kongor и Fluffylumps не переводились.
Изображения Help/NPE, включая 23 подтверждённых IMAGE_TEXT assets, не менялись.

## Оставшийся visible English

- 0 пустых localizable rows в выбранном локальном runtime scope.
- 181 строка содержит English-token candidates и остаётся в `REVIEW`; полный
  построчный список находится в `reports/pass_b_review.jsonl`. Основные классы:
  не зарегистрированные в locked spans имена state/ability variants, технические
  термины и реальные mixed-language хвосты. Test build предназначен для визуального
  и лингвистического QA, а не для production promotion без закрытия этой очереди.
- Утверждённые KEEP_EN: 140 hero names, 998 ability names, 261 item names,
  5 boss names, 8 boss ability names и 12 keycap values.
- 23 Help/NPE изображения содержат baked English и намеренно оставлены без изменений.
- Активный MOTD загружается как официальный удалённый `remote-ul.zip`. 17 строк
  локального shell переведены в каталоге, но не подменяют remote package в этом
  build: изменение trust/update model без отдельного i18n слоя запрещено.
- `tagLabel`, `title`, `body` и `ctas[].label` являются динамическими API fields;
  количество runtime values заранее не ограничено, hardcode не применялся.

## Исправленные mixed/bad translations

Полный машинный список с English source и итоговым Russian:
`reports/pass_b_mixed_language_fixes.json`.

В частности исправлены:

- `Press {hotkey} to disassemble` → `Нажмите {hotkey}, чтобы разобрать.`;
- `All Heroes` → `Все герои` в aggregate UI labels;
- пять `Toggle Extra Ability … Autocast`;
- `Toggle Replay Controls Visibility`;
- `Toggle Sharing Courier With Team`;
- `Press {key} to show`;
- Help Quick Buy с сохранёнными keycaps `Shift`;
- пользовательский `Toggle` в описании эффекта;
- canonical/markup edge cases для Blacksmith, Gemini, Gauntlet, Pharaoh,
  Ophelia, Tempest и Behemoth's Heart.

## Readability minor pass

Отдельный override `src/pass_b_readability/ui/hd_ui/styles.package` меняет только
semantic `color-gray-light`: `#BFBFBF` → `#DBDBDB` (диапазон задания
`#D6D6D6–#DEDEDE`). Primary `#F2F2F2`, `text_muted`, disabled, placeholders,
font resources, hinting, fallback, gamma, размеры, layout и UI scale идентичны
принятому Font/Readability build. Откат — один archive member либо полный rollback.

## Build и безопасность

- Test build: `build/pass-b/resources0.jz`
- SHA-256: `d71f85e3321c3954e877f2ccfa516c1e87f2006371499d491c83fd565fb1cb3d`
- Размер: 226435950 bytes
- Members: 761; CRC: PASS; removed members: 0; image changes: 0.
- От принятого font-build изменены только `entities_ru.str`, `interface_ru.str`,
  semantic style и добавлены 11 native UI override members из проверенного scope.
- Основной upstream archive и установленный extension не изменены.
- Установка: `scripts/install_pass_b_test.ps1` (по умолчанию не запускает игру).
- Rollback: `scripts/restore_font_after_pass_b.ps1`.

Machine-readable итог: `reports/pass_b_final_report.json`.
