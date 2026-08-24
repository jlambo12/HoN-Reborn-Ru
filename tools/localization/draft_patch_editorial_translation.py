#!/usr/bin/env python3
"""Create exact, source-pinned Russian drafts for the large editorial patch pages.

This helper is intentionally limited to the two current patch components.  It
uses the already audited AST report and a public Lingva endpoint, then leaves a
normal reviewed batch in translation/human for manual polishing.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path


SEPARATOR = " ||| "
KEEP_EXACT = {
    "Gameplay", "Visual", "Audio", "Tooltip", "Client", "Server",
    "Loki", "Jade", "Legendary", "Electric Tide", "Corrupted Conduit",
    "Static Discharge", "Overload", "Staff of the Master", "VRZO English Announcer",
    "GCash", "Maya", "TrueMoney Wallet", "Pix", "Boleto", "Card", "Alipay",
    "WeChat Pay", "Klarna", "Crypto", "Double Tap", "Quad Kill", "Smackdown",
    "Rage Quit", "Patch 0.12.5", "Patch 0.12.4", "0.12.5.0 - windows x64",
    "Art pending - drop this file in to replace.", "Clip pending", "Drop this file in to replace.",
}
MANUAL_0125 = {
    "Finish a Ranked Caldavar match you queued for with": "Завершите рейтинговый матч Caldavar, встав в очередь с",
    "both": "обеими",
    "Soft Support and Hard Support selected, and you are paid in Role Tokens. You are paid for the offer, not the outcome - it does not matter which role the draft actually handed you.": "выбранными ролями поддержки — и получите жетоны ролей. Награда выдаётся за готовность играть, а не за итог: какую роль вам назначил выбор героев, неважно.",
    "Balances cap at": "Можно накопить не более",
    ". One support role on its own earns nothing - it has to be both.": ". Одна выбранная роль поддержки жетонов не приносит — нужно выбрать обе.",
    "Queueing Ranked Caldavar with": "Поиск рейтингового матча Caldavar без",
    "neither": "ни одной",
    "support role selected costs": "выбранной роли поддержки стоит",
    "Role Token. Selecting either Soft Support or Hard Support is free entry, it just does not earn you anything. Spend a token and you can queue playing exactly what you want.": "жетон роли. Выбор хотя бы одной роли поддержки ничего не стоит, но и жетонов не приносит. Потратьте жетон — и ищите матч только на желаемых ролях.",
    "Both supports ticked": "Выбраны обе роли поддержки",
    "Neither support ticked": "Роли поддержки не выбраны",
    "Who is inside the economy.": "На кого действует система.",
    "A party of five neither earns nor spends - it brings its own team. Neither does a party queueing with a spread wide enough to slow its rating; a party already paying for its gap is not charged for its roles as well. Terminated matches settle nothing.": "Полная группа из пяти игроков не получает и не тратит жетоны — она уже собрала всю команду. То же относится к группе с такой разницей рейтинга, которая снижает влияние матча на MMR: дополнительной платы за роли нет. Прерванные матчи не учитываются.",
    "A four stack asks the matchmaker to find one specific player to complete your team, at your combined rating, in your region, right now. It is the hardest ask in the entire system. In practice it meant four stacks waited a long time for a game, and when the game finally formed it was frequently a worse match for all ten players.": "Группе из четырёх подбор должен найти одного строго подходящего игрока: для завершения команды, под общий рейтинг, в выбранном регионе и прямо сейчас. Это самая трудная задача для всей системы. На практике такие группы долго ждали, а найденный матч нередко оказывался хуже для всех десяти игроков.",
    "Better games when they do form": "Более качественные матчи",
    "Queue as carry + hard support, or offlane + soft support, and the matchmaker will actively try to put the two of you in the same lane. It can nudge other players&apos; role choices to make that happen, within limits. No more queueing as a duo and getting split across the map.": "Выберите связку керри + поддержка или оффлейн + роум, и подбор постарается поставить вас на одну линию. В допустимых пределах он может скорректировать роли других игроков. Дуэты больше не должны оказываться на разных концах карты.",
    "Told why, not just no": "Отказ с объяснением",
    "A party that stops qualifying for what it is queued for - the support cover leaves, someone&apos;s roles change, the party grows - now leaves the queue rather than riding out a game it is no longer eligible for.": "Если группа перестала соответствовать условиям очереди — вышел игрок поддержки, изменились роли или вырос состав, — она покидает очередь, а не продолжает ждать матч, для которого уже не подходит.",
    "Leaving a party of one is no longer possible, and leaving a party puts you straight into a fresh solo queue rather than into no party at all.": "Покинуть группу из одного игрока больше нельзя. После выхода из группы вы сразу становитесь отдельной группой, а не остаётесь без группы вовсе.",
    "Xsolla is now live as a payment provider on heroesofnewerth.com. That means local payment methods that actually work where you live.": "На heroesofnewerth.com подключена платёжная система Xsolla, а вместе с ней — местные способы оплаты, доступные в вашем регионе.",
    "Nothing about the game changes, and nothing is paywalled.": "Сама игра не меняется, а её содержимое не скрывается за оплатой.",
    "Go to the store": "Перейти в магазин",
    "Discord": "Discord",
    "Kill credit on wards was a coin flip whenever more than one thing damaged the ward on the same frame. It is decided by a rule now.": "Если в одном кадре вард повреждали несколько целей, награда за его уничтожение определялась случайно. Теперь действует однозначное правило.",
    "Corrupted Disciple &middot; not marketable": "Corrupted Disciple &middot; не продаётся на торговой площадке",
    "Green and gold, horned and gilded, wreathed in a sorcery that answers to nobody. A trickster reimagining of the Corrupted Disciple, built from the ground up rather than recoloured.": "Зелёный и золотой, рогатый и позолоченный, окутанный неподвластной никому магией. Образ трикстера для Corrupted Disciple, созданный с нуля, а не простой перекраской.",
    "Electric Tide (Q):": "Electric Tide (Q):",
    "Corrupted Conduit (W):": "Corrupted Conduit (W):",
    "Static Discharge (E):": "Static Discharge (E):",
    "Overload (R):": "Overload (R):",
    "Staff of the Master variant.": "отдельный вариант для Staff of the Master.",
    "A full voice set - selection, flavour, movement, attack, out-of-mana, cooldown and taunt lines.": "Полный набор реплик: выбор героя, особые фразы, движение, атака, нехватка маны, перезарядка и насмешки.",
    "The VRZO announcer arrives in English. Every call is delivered through a battered little CRT that flies apart on impact, so the pack is as much something you watch as something you hear.": "Добавлен англоязычный комментатор VRZO. Каждая реплика сопровождается старым ЭЛТ-телевизором, который разлетается от удара, поэтому этот набор интересно не только слушать, но и смотреть.",
    "Its own on-screen banner for every call, not just a voice line.": "Собственный экранный баннер для каждого события, а не только голосовая реплика.",
    "Its own marketplace stage.": "Собственная сцена в магазине.",
    "Five of the calls, with the announcer&apos;s own audio straight out of the game files. Press play - these ones have sound.": "Пять реплик с оригинальным звуком комментатора прямо из файлов игры. Нажмите воспроизведение — у этих примеров есть звук.",
    "Review reports for griefing, feeding, ability abuse, item abuse, role refusal and going AFK.": "Рассматривать жалобы на вредительство, намеренные смерти, злоупотребление способностями и предметами, отказ играть выбранную роль и бездействие.",
    "They cannot ban, suspend or mute anyone, and they cannot influence account standing. A verdict is an opinion on one case; the system works out the consequence from the player&apos;s own history.": "Они не могут блокировать, временно отстранять или заглушать игроков и не влияют на статус учётной записи. Вердикт — лишь решение по одной жалобе; последствия система определяет по истории игрока.",
    "Cheating, boosting and other serious cases go straight to Staff, never to the GM team.": "Жалобы на читы, бустинг и другие серьёзные нарушения сразу передаются сотрудникам проекта, а не игровым модераторам.",
    "The store used to freeze the entire client for over a minute the first time you opened it in a session, and could close the client outright on a reopen or after a logout. Both are fixed.": "Раньше при первом открытии магазина клиент зависал более чем на минуту, а повторное открытие или вход после выхода могли полностью закрыть игру. Обе проблемы исправлены.",
    "rather than just dimmed, so they no longer take hover and click input that did nothing.": ", а не просто затемняются, поэтому больше не перехватывают наведение и бесполезные щелчки.",
    "A short &quot;Preparing store previews&quot; notice covers the brief window while previews are still resolving.": "Пока миниатюры подготавливаются, ненадолго появляется сообщение «Подготовка изображений магазина».",
    "Every historical patch notes page carried a stand-in that opened the video in your system browser, because the old renderer could not host an embedded player. They are real YouTube players now, on all 15 spotlights across the archive.": "Раньше на страницах старых патчей стояла заглушка, открывавшая видео в системном браузере: прежний рендерер не поддерживал встроенный проигрыватель. Теперь во всех 15 обзорах архива работают настоящие проигрыватели YouTube.",
    "Panel video follows your master sound volume.": "Громкость видео подчиняется общей громкости игры.",
    "A clip in a panel used to play at whatever volume the page asked for, straight past the game&apos;s sound slider. As a side effect, changing the master volume multiplier now reaches the game&apos;s own audio too, which it previously did not.": "Раньше видео в панели воспроизводилось с громкостью, заданной страницей, игнорируя ползунок игры. Теперь общая громкость корректно влияет и на видео, и на собственные звуки игры.",
    "Modifier keys reach the page.": "Панель распознаёт клавиши-модификаторы.",
    "Ctrl+C arrived as a bare C and Shift+Right as a bare Right, so the caret moved instead of the selection extending.": "Раньше Ctrl+C распознавалось как обычная C, а Shift+Right — как Right, поэтому курсор перемещался вместо расширения выделения.",
}
SKIP_RE = re.compile(r"^(?:https?://|/|[\d\s.,:+%()\-/]+)$")


def translate(texts: list[str], endpoint: str) -> list[str]:
    masked = [text.replace("&apos;", "__APOS__").replace("&quot;", "__QUOT__").replace("&middot;", "__MDOT__") for text in texts]
    url = endpoint.rstrip("/") + "/" + urllib.parse.quote(SEPARATOR.join(masked), safe="")
    with urllib.request.urlopen(url, timeout=45) as response:
        payload = json.load(response)
    result = payload["translation"].split(SEPARATOR)
    if len(result) != len(texts):
        if len(texts) == 1:
            raise RuntimeError("translator changed the only string")
        midpoint = len(texts) // 2
        return translate(texts[:midpoint], endpoint) + translate(texts[midpoint:], endpoint)
    return [part.strip().replace("__APOS__", "&apos;").replace("__QUOT__", "&quot;").replace("__MDOT__", "&middot;") for part in result]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--patch", choices=("0124", "0125"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--exclude-batch", type=Path, action="append", default=[])
    parser.add_argument("--endpoint", default="https://lingva.lunar.icu/api/v1/en/ru")
    args = parser.parse_args()
    root = args.project_root.resolve()
    report = root / "translation" / "reports" / "patch_editorial_all.jsonl"
    source_file = f"preact/src/layers/patch-notes-v2/patches/patch{args.patch}.tsx"
    excluded: set[str] = set()
    for path in args.exclude_batch:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        excluded.update(row["english"] for row in payload.get("rows", []))

    ordered: list[str] = []
    counts: Counter[str] = Counter()
    first_line: dict[str, int] = {}
    for raw in report.read_text(encoding="utf-8-sig").splitlines():
        row = json.loads(raw)
        if not row["source_file"].endswith(f"patch{args.patch}.tsx"):
            continue
        english = html.unescape(row["english"]).replace("'", "&apos;").replace('"', "&quot;")
        # Keep the exact spelling from the report; html.unescape above is only
        # used to normalize scanner variants back to the source representation.
        english = row["english"]
        counts[english] += 1
        first_line.setdefault(english, int(row["source_line"]))
        if english not in ordered:
            ordered.append(english)

    pending = [text for text in ordered if text not in excluded and not SKIP_RE.fullmatch(text)]
    manual = MANUAL_0125 if args.patch == "0125" else {}
    translations: dict[str, str] = {text: manual.get(text, text) for text in pending if text in KEEP_EXACT or text in manual}
    translatable = [text for text in pending if text not in translations]
    chunks: list[list[str]] = []
    chunk: list[str] = []
    size = 0
    for text in translatable:
        added = len(text) + (len(SEPARATOR) if chunk else 0)
        if chunk and size + added > 850:
            chunks.append(chunk)
            chunk, size = [], 0
        chunk.append(text)
        size += added
    if chunk:
        chunks.append(chunk)
    for index, group in enumerate(chunks, 1):
        for source, target in zip(group, translate(group, args.endpoint), strict=True):
            translations[source] = target
        print(f"translated chunk {index}/{len(chunks)}")
        time.sleep(0.35)

    rows = []
    for english in pending:
        russian = translations[english]
        rows.append({
            "source_file": source_file,
            "english": english,
            "russian": russian,
            "expected_matches": counts[english],
            "source_line": first_line[english],
            "decision": "KEEP_EN" if russian == english else "MACHINE_DRAFT_REVIEWED_NEXT",
        })
    payload = {
        "schema_version": 1,
        "batch_id": f"PREACT_RUNTIME_PATCH_{args.patch}_DRAFT",
        "scope": f"Complete editorial text for patch 0.{args.patch[-2]}.{args.patch[-1]}",
        "reviewed_by": "Machine draft; requires manual review",
        "rows": rows,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "rows": len(rows), "chunks": len(chunks)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
