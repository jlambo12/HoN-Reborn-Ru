# Журнал решений

## 2026-08-15 — основной архив read-only

Все анализаторы открывают game `resources0.jz` только в режиме `r`. Builder
пишет только `build/resources0.jz`. Существующий extension не изменён.

## 2026-08-15 — JSONL как canonical catalog

JSONL устойчив к tabs/newlines в значениях, удобно diff/stream обрабатывать и
не теряет типизированные поля. CSV генерируется как представление для человека.

## 2026-08-15 — last duplicate wins, но duplicate всегда отчётный

Upstream содержит 66 повторных EN key occurrences. Каталог хранит последнее
эффективное значение, а `stringtable_stats.json` сохраняет полный список.
Созданный вручную duplicate ID builder блокирует.

## 2026-08-15 — safe clone game_messages

До key-level контекстного анализа весь namespace получает KEEP_EN. Это сохраняет
announcer/event feed и исключает ошибочную глобальную защиту слова `Victory` в
других namespaces.

## 2026-08-15 — Preact переводится через source build

Minified dist и глобальная замена литералов не используются. Extended RU должен
ввести i18n adapter в source и публиковать согласованный dist override.

## 2026-08-15 — MOTD не переопределяется в первом build

Текущий host загружает официальный remote ZIP. Локальный shell является
возможной точкой расширения, но требует отдельного runtime-теста и решения о
server-delivered тексте.

## 2026-08-15 — audit сохраняет translator state

Повторный inventory merge выполняется по `id` и `english_hash`. Неизменные
translator fields сохраняются, изменённый EN требует REVIEW, removed IDs
попадают в отдельный отчёт. Protected rows всегда возвращаются к новому EN.
