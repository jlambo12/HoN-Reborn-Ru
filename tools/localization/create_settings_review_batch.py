#!/usr/bin/env python3
"""Create the reviewed settings correction batch from explicit human choices."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog" / "strings.jsonl"
OUTPUT = ROOT / "translation" / "human" / "batch_220_settings_human_review.json"


REVIEWED = {
    "interface:options_slider_max_menu_framerate_tip": "Ограничивает частоту кадров в главном меню. Высокие значения делают анимацию и движение курсора плавнее, а низкие снижают нагрузку и энергопотребление. Если меню подтормаживает или сильно загружает GPU, уменьшите это значение.",
    "interface:options_slider_max_ingame_framerate_tip": "Ограничивает частоту кадров во время игры. Высокие значения делают анимацию и движение курсора плавнее, а низкие снижают нагрузку и энергопотребление. Если игра подтормаживает или сильно загружает GPU, уменьшите это значение.",
    "interface:options_slider_max_ui_framerate": "Максимальная частота кадров интерфейса",
    "interface:options_slider_max_ui_framerate_tip": "Ограничивает частоту кадров интерфейса. Высокие значения делают анимацию и HTML-панели плавнее, а низкие уменьшают нагрузку на поток интерфейса.",
    "interface:options_checkbox_show_client_info": "Показывать FPS и пинг",
    "interface:options_checkbox_show_client_info_tip": "Показывает текущие FPS и пинг в правом верхнем углу экрана.",
    "interface:options_shadow_quality_tip": "Чем выше качество теней, тем чётче они выглядят, но тем больше видеопамяти требуется. Производительность зависит и от GPU, и от CPU.",
    "interface:options_rim_lighting_tip": "Контурное освещение повышает контраст моделей с фоном, имитируя яркий источник света позади модели и создавая светлый контур по её верхним краям.",
    "interface:options_spec_skybox": "Показывать небо в режиме наблюдателя",
    "interface:options_label_voice_chat_volume": "Громкость голосового чата и комментатора ^w",
    "interface:options_voice_chat_volume_tip_header": "Громкость голосового чата и комментатора",
    "interface:options_voice_chat_volume_tip": "Настраивает громкость голосового чата других игроков и комментария при просмотре повторов.",
    "interface:options_disable_input_background_tip": "Когда игра находится в фоне, курсор продолжает двигаться, но прокрутка у края экрана отключается, а элементы интерфейса не подсвечиваются и не воспроизводят звуки при наведении.",
    "interface:options_checkbox_display_xp_rewards": "Показывать полученный опыт",
    "interface:options_override_conflict_confirm_body": "^yОбнаружен конфликт:^* выбранная клавиша уже назначена действию ^o'{bind}'^*.\\nПрежняя привязка действия ^o'{bind}'^* будет удалена.",
    "interface:options_label_chat_controls": "Управление вкладками чата",
    "interface:options_label_shift_keybind": "Модификатор Shift",
    "interface:options_label_shiftmod_keybind_tooltip": "Модификатор Shift позволяет ставить команды в очередь.",
    "interface:options_label_ctrl_keybind": "Модификатор Ctrl",
    "interface:options_label_ctrlmod_keybind_tooltip": "Модификатор Ctrl используется вместе с различными игровыми командами.",
    "interface:options_simple_on-screen_info_toggle_text": "Горячая клавиша для показа и скрытия элементов игрового интерфейса, например полос здоровья",
    "interface:options_label_chat_show_tab_1": "Показать вкладку чата 1",
    "interface:options_label_chat_show_tab_2": "Показать вкладку чата 2",
    "interface:options_label_chat_show_tab_3": "Показать вкладку чата 3",
    "interface:options_label_chat_sel_tab_1": "Выбрать вкладку чата 1",
    "interface:options_label_chat_sel_tab_2": "Выбрать вкладку чата 2",
    "interface:options_label_chat_sel_tab_3": "Выбрать вкладку чата 3",
    "interface:options_keybind_showtab_1": "Показать вкладку 1",
    "interface:options_keybind_showtab_2": "Показать вкладку 2",
    "interface:options_keybind_showtab_3": "Показать вкладку 3",
    "interface:options_keybind_showtab_4": "Показать вкладку 4",
    "interface:options_keybind_showtab_5": "Показать вкладку 5",
    "interface:options_keybind_showtab_6": "Показать вкладку 6",
    "interface:options_keybind_showtab_7": "Показать вкладку 7",
    "interface:options_keybind_showtab_8": "Показать вкладку 8",
    "interface:options_label_smart_casting_type_tip": "Позволяет применять способности в точке курсора без дополнительного щелчка мышью.\\n- В режиме «При отпускании» способность применяется при отпускании горячей клавиши.\\n- В режиме «При нажатии» способность применяется при нажатии горячей клавиши.",
    "interface:options_checkbox_inventory_dragdrop_tip": "Позволяет перетаскивать предметы между ячейками инвентаря или на землю. Отключите, чтобы случайно не перемещать и не выбрасывать предметы в бою. Предмет всё ещё можно взять правой кнопкой мыши и выбросить сочетанием Ctrl+Shift+щелчок.",
    "interface:options_simple_self_activate_tp_text": "Горячая клавиша для применения Teleportation Stone на себя",
    "interface:options_double_activate_abilities_tip": "Двойной щелчок по некоторым предметам и способностям автоматически применяет их на вашего героя без выбора цели. Например, Homecoming Stone телепортирует героя на базу, а зелье здоровья применяется на него самого.",
    "interface:options_enable_hide_expanded_altinfo": "Скрывать расширенную дополнительную информацию",
    "interface:options_trouble_faq_intro": "Ниже приведены ответы на частые вопросы. Более подробные сведения и прямое обращение в ^yслужбу поддержки^* доступны по адресу ^y{value}^*.",
    "interface:options_trouble_faq1_a": "Откройте ^y{value}^* и измените пароль в левой части страницы.",
    "interface:multi_unit_control_disabled_tip": "Управление группой юнитов сейчас недоступно.",
    "interface:replay_viewer_game_options": "Параметры игры: {options}",
    "interface:game_lobby_options": "^555Параметры игры:^* {options}",
    "interface:specui_options_showHotkeys_txt": "Показывает горячие клавиши в интерфейсе наблюдателя.",
    "interface:specui_options_miniMode_txt": "Уменьшает размер элементов на экране. Требуется перезапуск HoN.",
    "interface:specui_options_miniMode1_txt": "Уменьшает размер элементов на экране. Требуется перезапуск HoN.",
    "interface:specui_options_miniMode2_txt": "Уменьшает размер элементов на экране. Требуется перезапуск HoN.",
    "interface:specui_options_miniMode3_txt": "Уменьшает размер элементов на экране. Требуется перезапуск HoN.",
    "interface:specui_options_popupCD": "Всплывающий индикатор перезарядки",
    "interface:options_hdr_paperwhite_tip": "Задаёт яркость рассеянного белого и интерфейса. Увеличьте значение, если HUD выглядит тусклым, и уменьшите, если он слишком яркий.",
    "interface:options_hdr_tonemap_tip": "Filmic плавно сжимает яркие области к пиковому значению; Clamp жёстко ограничивает их на пике; Reinhard сжимает весь диапазон.",
    "interface:options_hdr_tonemap_ui": "Тональная компрессия интерфейса",
    "interface:options_hdr_tonemap_ui_tip": "Применяет тональную компрессию не только к сцене, но и к интерфейсу. Если отключено, интерфейс отображается без неё поверх обработанной сцены.",
    "interface:options_hdr_sdr_grade": "Цветокоррекция сцены (SDR)",
    "interface:options_hdr_sdr_grade_tip": "Применяет настройки HDR-цветокоррекции — контраст, насыщенность и тональную компрессию — также на обычном дисплее. Если отключено, сохраняется исходный вид SDR.",
    "interface:options_simple_constraincur": "Когда окно HoN активно, курсор не выходит за его пределы",
    "interface:options_show_death_summary_button": "Всегда показывать кнопку «Сводка смерти»",
    "interface:options_label_center_screen_keybind_tooltip": "Центрирует камеру на основном выбранном юните, которым вы обычно управляете в данный момент.",
    "interface:options_slider_creep_health_bar_transparency_tip": "Задаёт прозрачность полосы здоровья крипа, пока его здоровье не достигнет указанного порога.",
    "interface:options_simple_unitreact": "Юнит реагирует на взаимодействие",
    "interface:multi_unit_control_on": "Управление группой юнитов включено",
    "interface:multi_unit_control_off": "Управление группой юнитов отключено",
    "interface:multi_unit_control_disabled": "Управление группой юнитов недоступно",
    "interface:options_altportraits": "Показывать портреты альтернативных обликов",
    "interface:options_auto_dampen_tip": "При использовании голосового чата громкость остальных звуков игры можно автоматически снижать. Настройте степень приглушения ползунком.",
    "interface:options_auto_region_max_ping_sub_text2": "Максимально допустимый пинг при поиске матча с автоматическим выбором региона.",
    "interface:options_auto_region_max_ping_tip_text1": "Задаёт максимально допустимый пинг сервера при поиске матча с автоматическим выбором региона.",
    "interface:options_bind_instructions_button": "Чтобы выбрать новую привязку, ^yнажмите^* клавишу или кнопку мыши.",
    "interface:options_bind_instructions_impulse": "Чтобы выбрать новую привязку, ^yнажмите^* нужную комбинацию клавиш.",
    "interface:options_brightMax_tip": "Настраивает максимальную яркость сцены и порог яркости для эффекта свечения. (По умолчанию: 2.0)",
    "interface:options_brightMin_tip": "Настраивает минимальную яркость сцены и порог яркости для эффекта свечения. (По умолчанию: 1.0)",
    "interface:options_brightScale_tip": "Настраивает масштаб яркости сцены и интенсивность эффекта свечения. (По умолчанию: 1.0)",
    "interface:options_btn_restart_tutorial_tip": "Повторно открывает обучающие слайды для новых игроков.",
    "interface:options_button_ok": "ОК",
    "interface:options_button_voice": "Голосовой чат",
    "interface:options_checkbox_animated_portraits": "Анимированные портреты",
    "interface:options_checkbox_animated_portraits_tip": "Включает анимацию портретов на нижней панели интерфейса.",
    "interface:options_checkbox_banjo_sound": "Звук банджо при выходе",
    "interface:options_checkbox_banjo_sound_tip": "Воспроизводит классический звук банджо при выходе из клиента HoN.",
    "interface:options_checkbox_cg_toolPersistantTargetIndicatorEnable": "Сохранять индикатор применения",
    "interface:options_checkbox_cg_toolPersistantTargetIndicatorEnable_tip": "Индикатор применения остаётся в выбранной области, пока герой не сможет начать применение способности.",
    "interface:options_checkbox_ff_health": "Деления на полосах здоровья",
    "interface:options_checkbox_ff_health_per_pip": "Здоровья на деление",
    "interface:options_checkbox_ff_health_per_pip_tip": "Количество здоровья, соответствующее одному крупному делению. Значение по умолчанию: 1000.",
    "interface:options_checkbox_ff_health_per_sub_pip": "Здоровья на малое деление",
    "interface:options_checkbox_ff_health_per_sub_pip_tip": "Количество здоровья, соответствующее одному малому делению. Значение по умолчанию: 200.",
    "interface:options_checkbox_ff_health_pip": "Показывать крупные деления",
    "interface:options_checkbox_ff_health_sub_pip": "Показывать малые деления",
    "interface:options_checkbox_frame_queuing_disabled_flush_frame_end": "Отключено (сброс в конце кадра)",
    "interface:options_checkbox_frame_queuing_disabled_flush_frame_start": "Отключено (сброс в начале кадра)",
    "interface:options_checkbox_goldlerp": "Плавное изменение количества золота",
    "interface:options_checkbox_goldlerp_tip": "Плавно изменяет отображаемое количество золота до текущего значения за 350 мс.",
    "interface:options_checkbox_graphics_triple_buffering_tip": "Использует дополнительный кадровый буфер видеокарты. Это может повысить плавность, но потребует больше видеопамяти.",
    "interface:options_checkbox_ground_sprite": "Показывать наземные спрайты",
    "interface:options_checkbox_hero_holdaftermove_tip": "После выполнения всех команд герой удерживает позицию и не начинает автоматически атаковать ближайших врагов.",
    "interface:options_checkbox_hovershowselectionring": "Контур при наведении",
    "interface:options_checkbox_hovershowselectionring_tip": "Подсвечивает контуром юнита, на которого наведён курсор.",
    "interface:options_checkbox_no_switch_to_hidden_hero": "Не переключаться на героя вне экрана",
    "interface:options_checkbox_portrait_overlay": "Индикатор юнитов вне экрана",
    "interface:options_checkbox_reverse_minimap": "Переместить мини-карту вправо",
    "interface:options_checkbox_right_click_deny": "Добивание союзников правой кнопкой",
    "interface:options_checkbox_right_click_deny_tooltip": "Позволяет атаковать союзных крипов с низким запасом здоровья правой кнопкой мыши, чтобы добить их.",
    "interface:options_checkbox_safe_channel": "Защита прерываемых способностей",
    "interface:options_checkbox_safe_channel_tip": "Движение или применение другой способности не прерывает уже выполняемую поддерживаемую способность.",
    "interface:options_checkbox_show_crit": "Показывать критический урон",
    "interface:options_checkbox_show_death_recap_on_death_tip": "Автоматически открывает сводку после смерти. Отключите, чтобы открывать её вручную кнопкой «Сводка смерти».",
    "interface:options_checkbox_show_deny": "Показывать эффект добивания",
    "interface:options_checkbox_show_exp": "Показывать полученный опыт",
    "interface:options_checkbox_show_gold": "Показывать полученное золото",
    "interface:options_screen_show_gold_tip": "Показывает количество полученного золота.",
    "interface:options_checkbox_showplayerring": "Контур своего героя",
    "interface:options_checkbox_smart_unit_selection": "Умный выбор юнитов",
    "interface:options_checkbox_smart_unit_selection_tip": "Выбирает ближайшего к курсору юнита, а не ближайшего к камере, и упрощает выбор юнитов, особенно у их ног.",
    "interface:options_checkbox_sound_muteMusic": "Отключить музыку",
    "interface:options_checkbox_sound_mutePings": "Отключить голосовые оповещения пингов",
    "interface:options_checkbox_team_or_player_color": "Использовать индивидуальные цвета игроков",
    "interface:options_checkbox_view_operation": "Управление обзором",
    "interface:options_classic_login_tip_text": "Включает классический экран входа и его анимацию. Требуются перезапуск игры и классический интерфейс (отключите «Новый основной интерфейс»).",
    "interface:options_disable_all_sounds_tip": "Полностью отключает звуковую систему. Это может улучшить работу на компьютерах с небольшим объёмом оперативной памяти. (Требуется перезапуск)",
    "interface:options_dropdown_show_combat_log_always": "Показывать в реальном времени",
    "interface:options_hoverhighlightstrength": "Интенсивность подсветки при наведении",
    "interface:options_label_self_cast_keybind": "Модификатор применения на себя",
    "interface:options_slider_creep_health_bar_transparency": "Прозрачность полос здоровья крипов",
    "interface:options_slider_creep_health_bar_threshold": "Порог прозрачности полос здоровья крипов",
    "interface:options_checkbox_mute_announcer": "Отключить диктора",
    "interface:options_checkbox_mute_announcer_tip": "Отключает голос диктора.",
    "interface:options_time_between_announcer_callouts": "Интервал между репликами диктора",
    "interface:options_time_between_announcer_callouts_tip": "Интервал между репликами диктора в миллисекундах.",
    "interface:options_newannouncervolume": "Громкость событийного диктора (%)",
    "interface:options_newannouncervolume_tip": "Настраивает громкость событийного диктора. Базовый уровень — 100%.",
    "interface:options_mutenewannouncer": "Отключить событийного диктора",
    "interface:options_mutenewannouncer_tip": "Отключает все реплики событийного диктора.",
    "interface:options_muteautomissingannouncer": "Отключить оповещения об исчезновении героев",
    "interface:options_muteautomissingannouncer_tip": "Отключает реплики диктора об исчезновении вражеских героев с линии.",
    "interface:options_mutekillcalloutannouncer": "Отключить оповещения об убийствах героев",
    "interface:options_mutekillcalloutannouncer_tip": "Отключает реплики диктора об убийствах героев.",
    "interface:options_muteherospottedcalloutannouncer": "Отключить оповещения об обнаружении героев",
    "interface:options_muteherospottedcalloutannouncer_tip": "Отключает реплики диктора об обнаружении героев.",
    "interface:options_muteruneinfocalloutannouncer": "Отключить оповещения о рунах",
    "interface:options_muteruneinfocalloutannouncer_tip": "Отключает реплики диктора с информацией о рунах.",
    "interface:options_simple_reactdelay": "Задержка между реакциями юнитов",
    "entities:TargetScheme_all_heroes": "Все герои",
    "entities:Option_AllHeroes": "Все герои",
}


def main() -> int:
    rows = [json.loads(line) for line in CATALOG.read_text(encoding="utf-8-sig").splitlines() if line]
    by_id = {row["id"]: row for row in rows}
    missing = sorted(set(REVIEWED) - set(by_id))
    if missing:
        raise SystemExit(f"Unknown catalog keys: {missing}")
    existing = set()
    for path in (ROOT / "translation" / "human").glob("batch_*.json"):
        if path == OUTPUT:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for entry in payload.get("entries", []):
            existing.update(entry.get("keys", []))
    duplicate = sorted(set(REVIEWED) & existing)
    if duplicate:
        raise SystemExit(f"Keys already reviewed in earlier batches: {duplicate}")
    payload = {
        "schema_version": 1,
        "batch_id": "HUMAN_RU_220_SETTINGS_REVIEW",
        "catalog_apply": True,
        "reviewed_by": "Codex full settings semantic review",
        "entries": [
            {"keys": [logical_key], "english_hash": by_id[logical_key]["english_hash"], "ru": ru}
            for logical_key, ru in REVIEWED.items()
        ],
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(payload['entries'])} reviewed entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
