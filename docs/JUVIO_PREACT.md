# Juvio / Preact

## Точки подключения

Native packages подключают `/preact/dist/index.html` с `ViewScope`:

| Native host | ViewScope |
|---|---|
| `ui/confirmations.interface` | `jade-buy` |
| `ui/fe3/sections/game_lobby.package` | `lobby-customization` |
| `ui/fe3/sections/ladder.package` | `leaderboard` |
| `ui/fe3/sections/match_stats.package` | `match-stats` |
| `ui/fe3/sections/patch_notes.package` | `patch-notes` |
| `ui/fe3/sections/profilev2.package` | `profile` |

Router также содержит `honor-system`, `patch-notes-v2` и shared dialogs. Jade
Buy переводится на route из `Engine.ViewScope` в `app.tsx`.

Исходники и compiled dist находятся внутри основного archive, поэтому extension
может переопределить конкретные `preact/dist/*` paths. Надёжная схема — добавить
i18n в source, собрать согласованный dist и публиковать его целиком в Extended
RU, а не менять строки в minified JS.

## Hardcoded client strings

Отчёт `reports/preact_string_candidates.jsonl` содержит 4 697 кандидатов:
3 000 JSX text nodes, 1 419 string literals и 278 UI attributes. Scanner
консервативный; это очередь review, а не готовый translation catalog.

Основные живые слои без Patch Notes v2: app shell 83, shared components 58,
Profile 80, Match Stats 67, API/error paths 63, Lobby Customization 55, Honor
System 49, Leaderboard 31, Jade Buy 16, MOTD reference source 14, Patch Notes
API view 7.

## Dynamic/API data

Frontend делает сетевые запросы для profile, leaderboard, match stats, vanity,
Jade packages и patch notes. Hero/item API types содержат `translatedName`, но
для protected names runtime должен предпочитать canonical English name.

Patch Notes имеют две модели: API-based слой и большой bundled static corpus
`patch-notes-v2/patches`. Последний содержит 4 174 hardcoded candidates и много
image references.

## MOTD / News

Активный `ui/fe3/sections/motd.package` загружает:

`https://hon-public.juvio.com/motd/remote-ul.zip`

с root `:/remote/cdn/`. Закомментированный local path указывает на
`/preact-remote/dist/index.html`. Bundled reference source затем запрашивает
`/v1/community/motd`; title/body/CTA приходят с сервера. Следовательно:

- shell/error/quick-link labels можно локализовать client-side;
- title/body/CTA — DYNAMIC и требуют серверного RU либо EN fallback;
- MITM не нужен и не рассматривается;
- возможный native extension point — override `motd.package` на локально
  собранный shell, который продолжает использовать официальный API.

Этот override нужно сначала проверить отдельно: он меняет trust/update model
удалённого UI, поэтому в первый build не включён.

## Image text

Визуально подтверждён English text внутри bundled screenshots:

- `patch-0-10-0/cosmetics-store.webp`;
- `patch-0-10-0/keybindings-toggle.webp`;
- `patch-0-10-0/npe-2.webp`.

Это содержимое Patch Notes, а не доказательство hardcoded text в соответствующем
живом UI. Для таких assets нужен отдельный IMAGE_TEXT registry. Автоматическая
OCR-замена недопустима; предпочтительны локализованные screenshots или captions.

## Phase 1.5 AST catalog и baseline

Production-oriented каталог строится TypeScript Compiler API отдельно от raw
discovery: `catalog/extended_ui.jsonl`. AST-проход берёт JSXText, видимые JSX
attributes, известные user messages и display configuration values, исключая
CSS, SVG path data, routes, URLs, resource paths, mocks и историю
`patch-notes-v2/patches`. Phase 1.5 дал 744 кандидата; текущий upstream и
поддержка conditional JSX literals дают 766 production candidates без истории.

`scripts/build_preact_baseline.ps1` создаёт изолированный workspace из snapshot,
включая `preact-qjs/**`, `public/**`, `bun.lock` и bundled Bun 1.2.17. Исходный
`package-lock.json` рассинхронизирован с `package.json`, поэтому канонический
путь — `bun install --frozen-lockfile` и `bun run build`. Baseline без наших
изменений успешно создаёт тот же набор из 723 relative dist paths, что и
shipped frontend. Доказательства находятся в
`reports/preact_baseline_build.json`; результат не устанавливается в игру.
