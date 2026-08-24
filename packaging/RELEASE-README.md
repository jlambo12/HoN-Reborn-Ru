# HoN Reborn RU v@@VERSION@@

Неофициальная русская локализация HoN Reborn / Juvio для Windows.

## Установка

1. Убедитесь, что Juvio / HoN Reborn уже установлен и хотя бы раз запускался.
2. Откройте PowerShell в этой папке.
3. Выполните:

```powershell
powershell -ExecutionPolicy Bypass -File .\Install.ps1 -Launch
```

Параметр `-Launch` можно убрать, если игру пока не нужно запускать.

Установщик проверит SHA-256 архива и сохранит существующий extension в `%LOCALAPPDATA%\Juvio\extensions\backups\HoN-Reborn-RU`.

## Удаление

```powershell
powershell -ExecutionPolicy Bypass -File .\Uninstall.ps1
```

Скрипт восстановит extension, который был активен до установки. Если extension после установки изменился, удаление остановится, чтобы не потерять пользовательские данные.

## Целостность

SHA-256 файла `resources0.jz`:

```text
@@SHA256@@
```

Контрольные суммы всех файлов пакета находятся в `SHA256SUMS.txt`.

Проект: https://github.com/jlambo12/HoN-Reborn-Ru

