# Font/UI readability pass

Дата аудита: 2026-08-16. Базовый игровой архив исследован только на чтение. Его SHA-256 до и после работы: `a518f760c7bdebcfb2f9258dbfcfe7e2bf81881938e4653b0b1c725e04099762`.

## Итог

Основная причина «мыльности» нативного русского текста находится не в bitmap-atlas и не в постобработке. HoN использует динамические TTF fontmap, причём HoN Regular/Bold/Condensed содержат полный русский алфавит и TrueType hinting, но во всех 56 HoN fontmap этот hinting принудительно отключён через `nohinting="true"`. Наиболее заметен дефект на размерах 7–16 px, которые дополнительно вычисляются от высоты экрана через `dynamic_fontsize`, `baseresolution="768"`, `axis="y"` и могут попадать на дробный масштаб.

Вторая независимая причина — ложный/неполный fallback:

- `system.ttf` (Bitstream Vera Sans Mono) и `game.ttf` (FrizQuaReg) не содержат ни одного кириллического glyph, хотя соответствующие fontmap объявляют `cyrillic`;
- bundled Inter Regular/SemiBold/Bold в Preact содержит 0 кириллических glyph. Русский текст в Inter-панелях поэтому уходил в неуправляемый системный fallback, отличающийся от English по метрикам, весу и rasterization;
- HoN Regular/Bold/Condensed содержат 275 Cyrillic codepoints и весь русский алфавит. Отдельного Cyrillic atlas или Cyrillic bitmap font в UI нет.

Тестовый вариант устраняет две подтверждённые первопричины: включает штатный hinting HoN TTF и задаёт для кириллического диапазона Inter существующий HoN Regular/Bold. Новый шрифт не добавлялся. Глобальный sharpen/post-processing не применялся.

## Источники шрифтов

| Ресурс | Реальное семейство | Кириллица | Hint tables | Использование |
|---|---|---:|---:|---|
| `/core/fonts/hon_intl.ttf` | HoN Regular | 275, русский полный | есть | основной native UI `dyn_10..48`; Preact HON 400/500 |
| `/core/fonts/hon_bold_intl.ttf` | HoN Bold | 275, русский полный | есть | native `dyn_bold_*`, `heading_*`; Preact HON 600–800 |
| `/core/fonts/hon_cond_intl.ttf` | Roboto Condensed Regular, HoN asset | 275, русский полный | есть | native `dyn_7..9`, `dyn_con_10..11`; Preact condensed |
| `/core/fonts/system.ttf` | Bitstream Vera Sans Mono | 0 | есть | `system_small/medium/large`; риск fallback для кириллицы |
| `/core/fonts/game.ttf` | FrizQuaReg | 0 | есть | `littletextpopup`; риск fallback для кириллицы |
| `preact/**/inter-*.woff2` | Inter 4.001 Latin subset | 0 | `prep/gasp`, без полного TT hinting | Patch Notes/MOTD-подобные панели |

Файлы в `preact/public`, `preact/dist` и `preact/src/assets` являются копиями тех же семейств. Icon font `bootstrap-icons.woff2` не является текстовым шрифтом.

Метрики HoN показывают дополнительный fit-риск для длинных русских строк: средний advance русского набора примерно на 14% больше Latin (`1340.52` против `1175.96` для Regular; `1353.62` против `1178.27` для Bold). Поэтому исправление не меняет размеры панелей и не уменьшает шрифт глобально: переполнение нужно проверять по конкретным экранам.

Полные таблицы glyph/метрик/SHA находятся в `reports/font_resource_inventory.json`.

## Рендеринг, scaling и эффекты

Native fontmap:

- 60 fontmap в `core_en.resources`;
- HoN maps: размеры 7–48, `dynamic_fontsize="true"`, baseline 768 по оси Y, `gamma="1.5"`, outline 0.04h–0.10h;
- `system_*`: fixed size + `highdpisize`, gamma 1.5, outline 2.0;
- `littletextpopup`: dynamic 16, outline 0.16h;
- явных font texture filtering/mipmap/atlas settings не найдено, потому что glyph rasterization выполняется из TTF динамически;
- отдельных настроек для Cyrillic, отдельного atlas resolution и отдельной плотности кириллического atlas нет;
- явной коррекции half-pixel для labels не найдено. Дробные `h`-координаты и responsive Y-scaling остаются возможным вторичным фактором, но массовое округление позиций изменило бы layout и не включено в pass.

Глобальные native styles в `ui/hd_ui/styles.package`:

- активные `h1..h5`, `text_base`, `sysbar_menu_label`, tutorial и tooltip styles были `.9 .9 .9 1` (примерно `#E6E6E6`);
- `text_muted` — `.7 .7 .7 1`; textbox active — `.8`; placeholder shop — `.3`;
- заголовки и base text часто используют чёрную тень (`shadow=1`, offset 1–2); tutorial headings используют outline;
- HoN semantic colors заданы отдельно: orange `#ffab01`, green `#6CDE8B`, red `#d82727`, а также отдельные gold/blue/attribute/resource colors.

Preact:

- корневой UI использует `HON, sans-serif`; Inter явно используется в Patch Notes/MOTD-подобных слоях;
- `--color-text-primary` уже `#FFFFFF`, secondary `#9FA5B2`, light gray `#CECECE/#D8D8D8`, muted `#686E7D`, placeholder `#D1D5DE`;
- Preact уже применяет `zoom` вместо `transform: scale()` для downscale, чтобы текст rasterize-ился в конечном размере. Это оставлено без изменения;
- имеются точечные тени 2/5 px и декоративные glow-эффекты. Они не заменялись глобально: gameplay/decorative hierarchy сохранена.

Полный частотный inventory font/color/alpha/shadow/outline/filter/scale: `reports/font_style_inventory.json`.

## Что изменено в тестовом build

Из Phase 2A изменены только три archive member:

1. `core_ru.resources`: удалены 56 `nohinting="true"`; размеры, DPI/Y-scaling, gamma и outline не изменены.
2. `ui/hd_ui/styles.package`: только 16 primary/active styles подняты с `.9` до `.95` (примерно `#F2F2F2`): `color-white`, `section_title`, `h1..h5`, `text_base`, `sysbar_menu_label`, `tutorial_h1/h2`, `tip_textSmaller..Bigger`.
3. `preact/dist/assets/index.css`: для Unicode Cyrillic ranges `U+0400-052F`, `U+2DE0-2DFF`, `U+A640-A69F` Inter получает существующие HoN Regular/Bold glyphs. Latin Inter не меняется.

Это RU extension override, поэтому оригинальный игровой archive и английские игровые ресурсы не переписаны.

## Что намеренно оставлено без изменений

- размеры окон, панелей, font sizes, line-height и общий UI scale;
- gamma 1.5, outline thickness и штатные тени — их изменение отложено до A/B visual QA после включения hinting;
- muted, disabled, secondary metadata, placeholder и inactive colors;
- orange/yellow/green/red gameplay markup и оригинальная цветовая иерархия заголовков;
- `system.ttf`/`game.ttf`: слепая замена изменила бы mono/Friz layout. Экраны с ними внесены в QA; при подтверждённом русском fallback-дефекте нужен отдельный узкий override;
- изображения tutorial/help и все localization strings;
- никакой sharpen, screen-space filter, material или shader post-processing.

## Поверхности и обязательная визуальная проверка

Проверять попарно English/Russian, минимум при 1280×720, 1920×1080 и high-DPI/device scale 2:

- Juvio Options: вкладки, section headings, checkbox/radio/dropdown, active input, placeholder, Apply/Cancel;
- Settings и Controls: мелкие 7–12 px labels, keybind columns, длинные русские action names, конфликт/disabled state;
- HUD: stats, resource values, ability captions, quick buy, courier controls, notifications;
- tooltips: body, secondary metadata, colored markup, wrap и outline на тёмном/светлом фоне;
- scoreboard и post-match: headers, player rows, длинные имена/статусы, muted/disabled hierarchy;
- lobby/matchmaking и custom lobby: role priority, region/mode cards, queue metadata, длинные строки;
- shop: search, placeholder, item/guide headings, quick-buy instructions;
- main/in-game menus и confirmations;
- Preact: match stats, profile, leaderboard, honor, lobby customization, Patch Notes/MOTD; особо проверить кириллицу внутри Inter;
- console/system labels и `littletextpopup` — проверить отсутствие смешанного fallback до решения об узком fontface override;
- Learn → Help Topics: category/menu list, все article titles/body, navigation labels и длинные descriptions.

Критерий A/B: вертикальные/горизонтальные штрихи кириллицы должны быть стабильнее на 7–16 px без увеличения halo; English и Russian должны иметь сопоставимый вес. Если outline после hinting окажется чрезмерным, следующим безопасным экспериментом будет отдельное уменьшение outline только для small fontmap, не глобальный sharpen.

## Learn → Help Topics inventory

Runtime-цепочка:

`tutorial_library.package` → `Tutorial:PopulateMenuList()` → `ui/scripts/fe3/tutorial.lua` (`tutorialCategories`, `tutorialSlides`) → template по имени `tutorial_slide_*` в `tutorial_templates.package` → stringtable `interface_ru.str` и textures `/ui/fe3/npe/*`.

Результат полного аудита:

- 308 связанных UI/localization rows;
- 256 имеют прямую ссылку из tutorial package/Lua;
- 72 уже имеют Russian, 236 пока пусты;
- 65 NPE image assets зарегистрированы, 52 реально загружаются tutorial UI;
- в 23 assets визуально подтверждён baked English text; изображения не редактировались;
- полный список categories, titles, descriptions и UI strings: `reports/help_topics_inventory.jsonl`;
- полный IMAGE_TEXT registry с asset path, dimensions, SHA, runtime source и кратким baked-text inventory: `reports/help_image_assets.jsonl`.

Фраза `Each Hero has a built in teleportation stone...` не baked в изображение. Это stringtable key `tutorial_slide_teleport_desc` (`stringtables/interface_en.str`, строка 8577), который template выводит обычным `<label>`. Сопутствующий asset `/ui/fe3/npe/teleport.png` содержит другой baked English (`PlayerName`, `Teleportation Stone`) и зарегистрирован отдельно как `CONFIRMED_ENGLISH_TEXT`.

Изображения пока не менялись: перед их локализацией нужен отдельный image pass с сохранением композиции, arrows/highlights и исходного разрешения.

## Build, backup и rollback

- Test build: `build/font-readability/resources0.jz`
- SHA-256: `96e4d1c6d2b8a772322affbea3be367020a2bba07b89b80dd71b1752babd2868`
- Размер: 226261643 bytes
- Build verification: PASS, 750 members, CRC clean, ровно 3 изменённых member, удалённых member нет.
- Отдельный backup Phase 2A: `backups/font-readability/phase2a-resources0-before-font.jz`, SHA-256 `9d5d4176ff51f1799df50d9f7f61ba387ec7cdc54244cb7393e8c87f7143945c`.
- Безопасная установка: `scripts/install_font_readability_test.ps1` (откажется работать при запущенном Juvio, проверит main/Phase 2A SHA, создаст ещё одну timestamped backup).
- Rollback: `scripts/restore_phase2a_after_font_test.ps1` (принимает только известный установленный SHA и проверенную backup).

Test build не установлен, потому что Juvio/HoN был запущен. Установленный Phase 2A archive остался неизменным. Финальные machine-readable checks: `reports/font_readability_final_report.json`.
