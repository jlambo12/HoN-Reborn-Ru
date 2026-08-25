# HoN Reborn — русская локализация

[![CI](https://github.com/jlambo12/HoN-Reborn-Ru/actions/workflows/ci.yml/badge.svg)](https://github.com/jlambo12/HoN-Reborn-Ru/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/jlambo12/HoN-Reborn-Ru?include_prereleases)](https://github.com/jlambo12/HoN-Reborn-Ru/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Неофициальная русская локализация HoN Reborn / Juvio. Проект переводит интерфейс, системные сообщения, описания героев, способностей и предметов, сохраняя игровые токены, разметку и имена, которые должны оставаться на английском.

> Версия `v0.1.0-beta.6` упрощает работу с GearUP: Launcher больше не открывает ускоритель и всегда запускает игру с русскими параметрами. Подробности — в [заметках к релизу](docs/release-notes/v0.1.0-beta.6.md).

## Установка

1. Установите и хотя бы один раз запустите Juvio / HoN Reborn.
2. Скачайте `HoNRebornRU-Setup.exe` со страницы [Releases](https://github.com/jlambo12/HoN-Reborn-Ru/releases).
3. Установите и запустите **HoN Reborn RU**.
4. Нажмите «Установить перевод», затем запускайте игру ярлыком **HoN Reborn RU — Играть** или из Launcher.

Если используете GearUP, сначала откройте его и нажмите «Бустить». После включения буста запускайте игру ярлыком **HoN Reborn RU — Играть**. Кнопку запуска игры внутри GearUP использовать не нужно: она не передаёт параметры русского языка.

Launcher и Updater собраны как автономные Windows x64-приложения: пользователю не нужны .NET, Python, PowerShell, Git, архиваторы или другие компоненты. Обновления загружаются из GitHub Releases, проверяются по SHA-256 и устанавливаются с резервной копией. Удаление через стандартные параметры Windows восстанавливает предыдущий extension и настройки языка. Пароли и данные аккаунта проект не читает и не сохраняет.

## Что входит в v0.1.0-beta.6

- русский Native UI и современный Preact-интерфейс;
- основные меню, настройки, социальные и матчевые экраны;
- сообщения клиента и игры;
- переведённые описания героев, способностей, предметов и боссов;
- локальные новости и заметки к патчам;
- безопасная установка с резервной копией и проверкой целостности.

## Разработка

Требуется Windows и Python 3.14: его стандартный модуль `zipfile` поддерживает ZIP Zstandard (method 93), используемый архивами Juvio.

Создайте локальный `project.json` на основе примера:

```powershell
Copy-Item project.example.json project.json
py -3.14 -m unittest discover -s tests -p "test_*.py" -v
```

Сборка сайта:

```powershell
Set-Location website
npm ci
npm run build
```

Проверка и упаковка релизного артефакта:

```powershell
py -3.14 tools/verify_release.py --version 0.1.0-beta.6
.\scripts\package_release.ps1 -Version 0.1.0-beta.6 -PythonCommand "py"
```

Архитектура, правила локализации и стратегия обновления описаны в [документации](docs/ARCHITECTURE.md), [policy](docs/LOCALIZATION_POLICY.md) и [стратегии обновлений](docs/UPDATE_STRATEGY.md).

## Безопасность и ограничения

- оригинальный архив `heroes of newerth/resources0.jz` используется только для чтения;
- локализация устанавливается отдельным архивом в `Juvio/extensions/`;
- существующий extension не заменяется без проверенной резервной копии;
- сторонние исходники и оригинальные игровые архивы не входят в репозиторий;
- это неофициальный фанатский проект, не связанный с правообладателями HoN Reborn / Heroes of Newerth или Juvio.

Сообщения об ошибках приветствуются в [Issues](https://github.com/jlambo12/HoN-Reborn-Ru/issues). Пожалуйста, не прикладывайте логи или скриншоты с логином, токенами либо другими личными данными.

## Лицензия

Код проекта распространяется по лицензии [MIT](LICENSE). Сведения о сторонних компонентах находятся в [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Названия и игровые материалы принадлежат их соответствующим правообладателям.
