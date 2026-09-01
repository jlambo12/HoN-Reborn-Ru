# honreborn.ru

Одностраничный статический сайт русской локализации HoN Reborn.

## Разработка

```bash
npm install
npm run dev
```

## Production-сборка

```bash
npm run build
```

Готовые статические файлы создаются в `dist/`.

## Ссылка на релиз

По умолчанию кнопка ведёт прямо на актуальный автономный установщик в GitHub Release. При необходимости ссылку можно переопределить через `.env`:

```dotenv
PUBLIC_DOWNLOAD_URL=https://github.com/jlambo12/HoN-Reborn-Ru/releases/download/v0.1.0-beta.18/HoNRebornRU-Setup.exe
```

При нажатии GitHub сразу отдаёт файл `HoNRebornRU-Setup.exe`, без промежуточного перехода на страницу релиза.

## Слои главного экрана

Активные фоновые изображения описаны в `src/config/heroLayers.ts`. Когда появятся прозрачные слои финального арта, положите их в `public/hero/` и добавьте в массив `heroImageLayers`. Запросы к отсутствующим файлам не создаются.

## Размещение

Содержимое `dist/` публикуется в `/var/www/honreborn.ru` на VDS. Конфигурация Nginx находится в `honreborn.ru.nginx.conf`; HTTPS управляется Certbot.
