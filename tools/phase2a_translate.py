#!/usr/bin/env python3
"""Select and translate the Phase 2A user vertical into source-of-truth catalogs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path


TOKEN_RE = re.compile(r"%(?:\d+\$)?[-+#0 ]*(?:\d+|\*)?(?:\.\d+)?[A-Za-z%](?![A-Za-z])|\$\{[^{}\r\n]+\}|\{[^{}\r\n]+\}|<[^<>\r\n]+>|\^(?:[0-9]{3}|[^\s])|\\[rnt]")
PREFIXES = {
    "options", "main", "general", "game", "mm", "mm3", "create", "mainlobby",
    "match", "matchmaker", "tmm", "amm", "globby", "lobby", "gamelobby", "custom",
    "hselect", "rolepick", "loading", "notify", "confirm", "sysmessage", "ui", "tooltip",
    "player", "scoreboard", "gamechat", "smartcasting", "cc", "ccpanel", "ccserverlist",
    "social", "chat", "account", "local", "region", "filter", "map", "specui", "endstats",
}
NATIVE_FILES = {
    "ui/avoid_player.interface", "ui/fe3/sections/bottom_bar.package",
    "ui/fe3/sections/game_lobby.package", "ui/fe3/sections/lobby_communicator.package",
    "ui/fe3/sections/notifications_v2.package", "ui/fe3/sections/social_panel.package",
    "ui/fe3/sections/system_bar.package", "ui/fe3/sections/team_builder.package",
    "ui/fe3/templates/ban_select_templates.package", "ui/fe3/templates/fe3_templates.package",
    "ui/fe3/templates/matchmaking_templates.package", "ui/scripts/fe3/matchmaking.lua",
    "ui/scripts/game/game.lua", "ui/scripts/shared/avoid_player.lua",
    "ui/scripts/shared/report_player.lua", "ui/specui/caster.package",
    "ui/specui/specui_info_tabs.package", "ui/stash.package",
}
PREACT_LAYERS = {"lobby-customization", "shared_component", "match-stats"}

MANUAL = {
    "Play": "Играть", "PLAY": "ИГРАТЬ", "Apply": "Применить", "Cancel": "Отмена",
    "Reset": "Сбросить", "Search": "Поиск", "Options": "Настройки", "Settings": "Настройки",
    "Game": "Игра", "Graphics": "Графика", "Sound": "Звук", "Social": "Общение",
    "Controls": "Управление", "Friends": "Друзья", "Messages": "Сообщения",
    "Notifications": "Уведомления", "Confirm": "Подтвердить", "Yes": "Да", "No": "Нет",
    "OK": "ОК", "Close": "Закрыть", "Back": "Назад", "Next": "Далее", "Previous": "Назад",
    "Continue": "Продолжить", "Exit": "Выйти", "Logout": "Выйти из аккаунта",
    "Disconnect": "Отключиться", "Reconnect": "Подключиться снова", "Retry": "Повторить",
    "Try Again": "Попробовать снова", "Accept": "Принять", "Decline": "Отклонить",
    "Create Game": "Создать игру", "Custom Games": "Свои игры", "Matchmaking": "Поиск матча",
    "Find Match": "Найти матч", "Lobby": "Лобби", "Team": "Команда", "Spectator": "Зритель",
    "Hero Select": "Выбор героя", "Random Hero": "Случайный герой", "Ready": "Готов",
    "Loading": "Загрузка", "Victory": "Победа", "Defeat": "Поражение", "Alive": "Жив",
    "Dead": "Мёртв", "Scoreboard": "Таблица счёта", "Resume Game": "Продолжить игру",
    "Leave Game": "Покинуть игру", "Quit Game": "Выйти из игры", "Main Menu": "Главное меню",
    "Language": "Язык", "Resolution": "Разрешение", "Fullscreen": "Полный экран",
    "Windowed": "В окне", "Brightness": "Яркость", "Quality": "Качество", "Low": "Низкое",
    "Medium": "Среднее", "High": "Высокое", "Very High": "Очень высокое", "Off": "Выкл.",
    "On": "Вкл.", "Enabled": "Включено", "Disabled": "Отключено", "Volume": "Громкость",
    "Music Volume": "Громкость музыки", "Voice Volume": "Громкость голоса",
    "Master Volume": "Общая громкость", "Mouse Sensitivity": "Чувствительность мыши",
    "Default": "По умолчанию", "None": "Нет", "All": "Все", "Auto": "Авто",
    "Error": "Ошибка", "Warning": "Предупреждение", "Success": "Готово",
    "Username": "Имя пользователя", "Password": "Пароль", "Login": "Войти",
    "Server": "Сервер", "Region": "Регион", "Ping": "Пинг", "Refresh": "Обновить",
    "Invite": "Пригласить", "Kick": "Исключить", "Host": "Хост", "Players": "Игроки",
    "Player": "Игрок", "Bots": "Боты", "Add Bot": "Добавить бота", "Remove": "Удалить",
    "Save": "Сохранить", "Load": "Загрузить", "Clear": "Очистить", "Copy": "Копировать",
    "Match History": "История матчей", "Kills": "Убийства", "Deaths": "Смерти",
    "Assists": "Помощь", "Gold": "Золото", "Experience": "Опыт", "Level": "Уровень",
    "Customize Loadout": "Настроить комплект", "Queue Cooldown:": "Задержка очереди:",
    "Play a Matchmaking Game": "Играть в рейтинговый матч", "Find Our Match": "Найти матч",
    "BEST BALANCE": "ЛУЧШИЙ БАЛАНС", "FAST QUEUE": "БЫСТРАЯ ОЧЕРЕДЬ",
    "Sets event announcer volume. 100% is the base level.": "Громкость комментатора событий. 100% — базовый уровень.",
    "Wins\\nLosses\\nK:D\\nA:D\\nK+A:D\\nWards\\nXPM\\nGPM": "Победы\\nПоражения\\nK:D\\nA:D\\nK+A:D\\nВарды\\nXPM\\nGPM",
    "Unavoid": "Не избегать", "Avoid Player": "Избегать игрока", "Avoid List": "Список избегаемых",
    "Report Player": "Пожаловаться на игрока", "Reporting:": "Жалоба на:",
    "Reports are reviewed by our moderation team. False reports may result in penalties for the reporter.": "Жалобы рассматривает команда модераторов. За ложные жалобы можно получить наказание.",
    "Submit Report": "Отправить жалобу", "Reason:": "Причина:",
    "5% Leaves": "5% покинутых матчей",
}


def source_text(row: dict) -> str:
    return row.get("english", row.get("literal", ""))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


def main_in_scope(row: dict) -> bool:
    if row.get("status") != "TRANSLATE" or row.get("runtime_role") != "DISPLAY_TEXT":
        return False
    if row.get("category") == "settings_ui":
        return True
    if row.get("namespace") in {"game_messages", "client_messages"}:
        return row.get("category") not in {"chat_command_help"}
    if row.get("namespace") == "entities":
        return row.get("key") in {"ImmunityType_BarrierImmunity", "Popup_EmeraldWarden1", "Popup_EmeraldWarden2", "Popup_EmeraldWarden3", "Option_RapidFire"}
    if row.get("namespace") != "interface":
        return False
    key = row["key"].lower()
    prefix = key.split("_", 1)[0]
    return prefix in PREFIXES or row.get("category") == "profile_competitive_ui"


def mask_text(row: dict) -> tuple[str, dict[str, str]]:
    value = source_text(row)
    replacements: dict[str, str] = {}
    protected = [span["canonical_text"] for span in row.get("locked_spans", [])]
    protected += row.get("protected_terms", []) if not row.get("locked_spans") else []
    parts = sorted(set(protected), key=len, reverse=True)
    counter = 0
    for term in parts:
        pattern = re.compile(re.escape(term))
        while pattern.search(value):
            marker = f"[[ZXQLOCK{counter:04d}QXZ]]"
            value = pattern.sub(marker, value, count=1)
            replacements[marker] = term
            counter += 1
    def token_sub(match: re.Match[str]) -> str:
        nonlocal counter
        marker = f"[[ZXQTOK{counter:04d}QXZ]]"
        replacements[marker] = match.group(0)
        counter += 1
        return marker
    return TOKEN_RE.sub(token_sub, value), replacements


def restore_text(value: str, replacements: dict[str, str]) -> str:
    for marker, original in replacements.items():
        value = value.replace(marker, original)
    return value.strip()


def google_translate(values: list[str]) -> list[str]:
    separator = "ZXQSEP000QXZ"
    query = ("\n" + separator + "\n").join(values)
    url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ru&dt=t&q=" + urllib.parse.quote(query)
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=45) as response:
                payload = json.loads(response.read())
            translated = "".join(part[0] for part in payload[0])
            parts = re.split(r"\s*" + separator + r"\s*", translated)
            if len(parts) != len(values):
                raise ValueError(f"batch split mismatch: {len(parts)} != {len(values)}")
            return [part.strip() for part in parts]
        except Exception as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"translation request failed: {last_error}")


def translate_unique(entries: list[dict], cache: dict[str, str]) -> dict[str, str]:
    pending: list[tuple[str, str, dict[str, str]]] = []
    protected_rows: list[tuple[str, list[str | tuple[str, str, str]]]] = []
    for row in entries:
        english = source_text(row)
        if english in MANUAL:
            cache[english] = MANUAL[english]
            continue
        if english in cache:
            continue
        masked, replacements = mask_text(row)
        if replacements:
            marker_re = re.compile(r"(\[\[ZXQ(?:LOCK|TOK)\d{4}QXZ\]\])")
            parts: list[str | tuple[str, str, str]] = []
            for part in marker_re.split(masked):
                if not part:
                    continue
                if part in replacements:
                    parts.append(replacements[part])
                elif re.search(r"[A-Za-z]", part):
                    lead = re.match(r"^\s*", part).group(0)
                    trail = re.search(r"\s*$", part).group(0)
                    core = part[len(lead):len(part) - len(trail) if trail else None]
                    parts.append((lead, core, trail))
                else:
                    parts.append(part)
            protected_rows.append((english, parts))
        else:
            pending.append((english, masked, replacements))
    completed = 0
    while pending:
        batch, chars = [], 0
        while pending and len(batch) < 30:
            size = len(pending[0][1]) + 20
            if batch and chars + size > 2800:
                break
            batch.append(pending.pop(0)); chars += size
        translated = google_translate([item[1] for item in batch])
        for (english, _, replacements), russian in zip(batch, translated):
            cache[english] = restore_text(russian, replacements)
        completed += len(batch)
        if completed % 300 == 0:
            print(f"translated_unique={completed}")
    tasks: list[tuple[int, int, str]] = []
    mutable = [[english, list(parts)] for english, parts in protected_rows]
    for row_index, (_, parts) in enumerate(mutable):
        for part_index, part in enumerate(parts):
            if isinstance(part, tuple):
                tasks.append((row_index, part_index, part[1]))
    while tasks:
        batch, chars = [], 0
        while tasks and len(batch) < 30:
            size = len(tasks[0][2]) + 20
            if batch and chars + size > 2800:
                break
            batch.append(tasks.pop(0)); chars += size
        translated = google_translate([item[2] for item in batch])
        for (row_index, part_index, _), russian in zip(batch, translated):
            lead, _, trail = mutable[row_index][1][part_index]
            mutable[row_index][1][part_index] = lead + russian + trail
    for english, parts in mutable:
        cache[english] = "".join(parts).strip()
    return cache


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--manual-only", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve()
    paths = {
        "catalog": root / "catalog" / "strings.jsonl",
        "native": root / "catalog" / "native_extended_ui.jsonl",
        "preact": root / "catalog" / "preact_ui.jsonl",
    }
    groups = {name: read_jsonl(path) for name, path in paths.items()}
    selected = {
        "catalog": [row for row in groups["catalog"] if main_in_scope(row)],
        "native": [row for row in groups["native"] if row["status"] == "TRANSLATE" and row["source_file"] in NATIVE_FILES],
        "preact": [row for row in groups["preact"] if row["status"] == "TRANSLATE" and row.get("layer") in PREACT_LAYERS],
    }
    all_selected = [row for rows in selected.values() for row in rows]
    representative: dict[str, dict] = {}
    for row in all_selected:
        representative.setdefault(source_text(row), row)
    memory_path = root / "translations" / "phase2a_memory.jsonl"
    cache = {row["english"]: row["russian"] for row in read_jsonl(memory_path)} if memory_path.is_file() else {}
    for english in representative:
        if english in MANUAL:
            cache[english] = MANUAL[english]
    # Phase 2A safety: tokenized/protected values are regenerated whenever the
    # masking implementation changes; plain translations remain cached.
    if not args.manual_only:
        for english, row in representative.items():
            if mask_text(row)[1]:
                cache.pop(english, None)
        cache = translate_unique(list(representative.values()), cache)
    memory_rows = [{"english": english, "russian": cache[english], "english_hash": hashlib.sha256(english.encode()).hexdigest()} for english in sorted(cache, key=str.casefold)]
    write_jsonl(memory_path, memory_rows)
    selected_ids = {name: {row["id"] for row in rows} for name, rows in selected.items()}
    for name, rows in groups.items():
        for row in rows:
            if row["id"] in selected_ids[name]:
                row["russian"] = cache[source_text(row)]
                row["translation_phase"] = "2A"
        write_jsonl(paths[name], rows)
    manifest = {
        "version": 1, "scope": "Phase 2A first Russian user vertical",
        "selection": {name: sorted(ids) for name, ids in selected_ids.items()},
        "counts": {name: len(ids) for name, ids in selected_ids.items()},
        "unique_english": len(representative),
        "excluded_large_arrays": ["ability descriptions", "item descriptions", "hero lore", "full Help", "Patch Notes history"],
    }
    (root / "catalog" / "phase2a_scope.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"] | {"unique_english": len(representative)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
