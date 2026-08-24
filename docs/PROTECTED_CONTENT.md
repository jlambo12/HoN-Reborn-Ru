# Защищённый контент

Builder считает `KEEP_EN` неизменяемым: `russian` обязан побайтово совпадать с
`english`. Нарушение блокирует сборку.

## Защищённые категории

- hero display names;
- ability display names;
- item display names;
- avatar/skin и cosmetic product names;
- announcer event names, messages, audio identity и banners;
- boss proper names и boss ability names;
- контролируемые technical abbreviations, codes и keycaps.

Автоклассификатор использует namespace и key patterns, а не blacklist обычных
слов. Его решения видны в `category`, `context` и `protected_reason`.

## Inline locked spans

Canonical dictionary строится только из структурных источников, а не из любого
`State_*`. Matcher удаляет HoN control tokens во временном visible view, хранит
mapping visible offsets к исходным offsets и выбирает longest non-overlapping
canonical match. `locked_spans` фиксирует фактический English span и прилегающий
markup, при этом русский термин разрешено естественно перемещать в предложении.

Builder проверяет multiset immutable visible terms, exact case и полностью
обрамляющий markup (`^oWebbed Shot^*`, `^494Arcane Bolts^*`).

## Обязательная ручная ревизия

Неоднозначные entity labels и server/API fields не решаются без runtime
доказательства. Gameplay state/status labels переводятся, а State fields,
которые точно повторяют canonical Ability/Item name, остаются EN как ссылки.

Cosmetic descriptions и UI controls переводим, product names оставляем EN.
`translatedName` в Preact/API нельзя автоматически считать разрешением на
перевод: для героев, предметов и cosmetics он должен следовать этой политике.
