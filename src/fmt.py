from html import escape as _html_escape

from src.texts import get_text


def fmt_profile(client, lang: str = "ru") -> str:
    title = get_text("profile_title", lang)
    return (
        "┌─────────────────────────┐\n"
        f"│        {title}        │\n"
        "├─────────────────────────┤\n"
        f"│ 🆔  {client.tps_code}\n"
        f"│ 👤  {client.full_name}\n"
        f"│ 📱  {client.phone}\n"
        "└─────────────────────────┘"
    )


def fmt_welcome(tps_code: str, lang: str = "ru") -> str:
    if lang == "tj":
        return (
            "╔══════════════════════════╗\n"
            "║   🎉  ХУШ ОМАДЕД!         ║\n"
            "╠══════════════════════════╣\n"
            "║                          ║\n"
            "║  Сабти ном анҷом ёфт!    ║\n"
            "║                          ║\n"
            f"║  ID-и шумо:  {tps_code}     \n"
            "║                          ║\n"
            "║  📌 Ин рамзро ҳангоми    ║\n"
            "║  фиристодани посылкаҳо    ║\n"
            "║  нишон диҳед              ║\n"
            "║                          ║\n"
            "╚══════════════════════════╝"
        )
    return (
        "╔══════════════════════════╗\n"
        "║   🎉  ДОБРО ПОЖАЛОВАТЬ!   ║\n"
        "╠══════════════════════════╣\n"
        "║                          ║\n"
        "║  Регистрация завершена!   ║\n"
        "║                          ║\n"
        f"║  Ваш ID:  {tps_code}     \n"
        "║                          ║\n"
        "║  📌 Укажите этот код при  ║\n"
        "║  отправке посылок         ║\n"
        "║                          ║\n"
        "╚══════════════════════════╝"
    )


def _status_text(
    status: str, lang: str = "ru",
) -> str:
    if status == "issued":
        return get_text("status_received", lang)
    if status == "ready_to_issue":
        return get_text("status_ready", lang)
    if status == "problem":
        return get_text("status_problem", lang)
    return get_text("status_waiting", lang)


def _format_date(dt) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d.%m.%Y")


def fmt_parcel_arrived(
    track_id: str, lang: str = "ru",
) -> str:
    title = get_text("parcel_arrived_title", lang)
    body = get_text("parcel_arrived_body", lang)
    return (
        "┌─────────────────────────┐\n"
        f"│   {title}   │\n"
        "├─────────────────────────┤\n"
        f"│ 📦  Трек: {track_id}\n"
        "│ 📍  Склад: Душанбе\n"
        "│\n"
        f"│ {body}\n"
        "└─────────────────────────┘"
    )


def fmt_track_result_client(
    track_code: str,
    in_china: bool,
    dushanbe_info,
    lang: str = "ru",
    unresolved_info: dict | None = None,
) -> str:
    title = get_text("track_title", lang)
    lines = [
        "┌─────────────────────────┐",
        f"│   {title}   │",
        "├─────────────────────────┤",
        f"│ 📦  Трек: {track_code}",
    ]
    if dushanbe_info:
        if dushanbe_info.status == "issued":
            lines.append(
                "│ "
                + get_text(
                    "track_in_dushanbe_received", lang
                )
            )
        else:
            lines.append(
                "│ "
                + get_text("track_in_dushanbe", lang)
            )
            lines.append(
                "│ "
                + get_text("track_can_pickup", lang)
            )
    elif unresolved_info:
        lines.append(
            "│ "
            + get_text(
                "track_in_dushanbe_processing", lang
            )
        )
        info = unresolved_info
        if info.get("china_at"):
            lines.append(
                "│   "
                f"{get_text('parcel_field_china', lang)}: "
                f"{_format_date(info['china_at'])}"
            )
        if info.get("arrived_at"):
            lines.append(
                "│   "
                f"{get_text('parcel_field_arrived', lang)}: "
                f"{_format_date(info['arrived_at'])}"
            )
        if info.get("weight_kg"):
            lines.append(
                "│   "
                f"{get_text('parcel_field_weight', lang)}: "
                f"{_fmt_kg(info['weight_kg'])} кг"
            )
        if info.get("amount_estimated"):
            lines.append(
                "│   "
                f"{get_text('parcel_field_amount_est', lang)}"
                f": {_fmt_amount(info['amount_estimated'])}"
            )
    elif in_china:
        lines.append(
            "│ " + get_text("track_in_china", lang)
        )
        lines.append(
            "│ "
            + get_text("track_wait_delivery", lang)
        )
    else:
        lines.append(
            "│ " + get_text("track_not_found", lang)
        )
    lines.append("└─────────────────────────┘")
    return "\n".join(lines)


def _fmt_amount(value) -> str:
    """Сумма к оплате без лишних нулей: 120, 99.5, 12.34."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _fmt_kg(value) -> str:
    """Вес без лишних нулей: 2.5, 2.55, 3 (макс. 2 знака)."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


PARCELS_PER_PAGE = 15  # средняя длина 1 посылки ~200 байт, запас от лимита 4096


def _fmt_one_parcel(p: dict, lang: str) -> str:
    lines = ["│", f"│ 📦  {p['track_id']}"]
    # 2) Принято в Китае — только если зарегистрировано.
    if p.get("china_at"):
        lines.append(
            f"│   {get_text('parcel_field_china', lang)}: "
            f"{_format_date(p['china_at'])}"
        )
    # 3) Статус.
    lines.append(
        f"│   {get_text('parcel_field_status', lang)}: "
        f"{_status_text(p['status'], lang)}"
    )
    # 4) Прибыло в Душанбе.
    if p.get("arrived_at"):
        lines.append(
            f"│   "
            f"{get_text('parcel_field_arrived', lang)}: "
            f"{_format_date(p['arrived_at'])}"
        )
    # Полка на складе в Душанбе.
    if p.get("shelf"):
        lines.append(
            f"│   {get_text('parcel_field_shelf', lang)}: "
            f"{p['shelf']}"
        )
    # 5) Вес.
    if p.get("weight_kg"):
        lines.append(
            f"│   {get_text('parcel_field_weight', lang)}: "
            f"{_fmt_kg(p['weight_kg'])} кг"
        )
    # 6) Сумма к оплате: зафиксированная либо ориентировочная.
    if p.get("amount_due"):
        lines.append(
            f"│   {get_text('parcel_field_amount', lang)}: "
            f"{_fmt_amount(p['amount_due'])}"
        )
    elif p.get("amount_estimated"):
        lines.append(
            "│   "
            f"{get_text('parcel_field_amount_est', lang)}: "
            f"{_fmt_amount(p['amount_estimated'])}"
        )
    # 7) Дата выдачи — для выданных.
    if p["status"] == "issued" and p.get("issued_at"):
        lines.append(
            f"│   {get_text('parcel_field_issued', lang)}: "
            f"{_format_date(p['issued_at'])}"
        )
    return "\n".join(lines)


def fmt_my_parcels_pages(
    tps_code: str,
    parcels: list,
    lang: str = "ru",
) -> list[str]:
    title = get_text("my_parcels_title", lang)
    header_top = [
        "┌─────────────────────────┐",
        f"│     {title}      │",
        "├─────────────────────────┤",
        f"│ 🆔  {tps_code}",
    ]
    if not parcels:
        lines = list(header_top)
        lines.append("│")
        lines.append("│ " + get_text("no_parcels", lang))
        lines.append("└─────────────────────────┘")
        return ["\n".join(lines)]

    total_pages = (
        len(parcels) + PARCELS_PER_PAGE - 1
    ) // PARCELS_PER_PAGE
    pages = []
    for i in range(0, len(parcels), PARCELS_PER_PAGE):
        chunk = parcels[i:i + PARCELS_PER_PAGE]
        lines = list(header_top)
        if total_pages > 1:
            page_num = i // PARCELS_PER_PAGE + 1
            lines.append(
                f"│   {get_text('my_parcels_page', lang).format(page=page_num, total_pages=total_pages)}"
            )
        for p in chunk:
            lines.append(_fmt_one_parcel(p, lang))
        lines.append("└─────────────────────────┘")
        pages.append("\n".join(lines))
    return pages


def fmt_my_parcels(
    tps_code: str,
    parcels: list,
    lang: str = "ru",
) -> str:
    """Совместимость со старым кодом: одна строка со всеми страницами.
    Для длинных списков предпочитай fmt_my_parcels_pages, иначе можно
    превысить лимит Telegram в 4096 байт на сообщение."""
    return "\n\n".join(fmt_my_parcels_pages(tps_code, parcels, lang))


def fmt_warehouse_for_client(
    w, tps_code: str, name: str,
) -> str:
    # Телефон + регион + полный адрес (с TPS-кодом) внутри одного
    # <code>-блока: на мобильных клиентах тап по моноширинному тексту
    # копирует всю сущность сразу (и на iOS, и на Android). <pre>
    # копию по тапу не даёт — только long-press, поэтому остановились
    # на <code> с переносами.
    # ВАЖНО: parse_mode="HTML" при отправке (см. on_warehouse_select).
    full_address = f"{w.address}{tps_code}"
    copy_block = (
        f"{_html_escape(w.phone)}\n"
        f"{_html_escape(w.region)}\n"
        f"{_html_escape(full_address)}"
    )
    return (
        f"📍 {_html_escape(w.name)}\n"
        f"👤 {_html_escape(name)}\n\n"
        f"<code>{copy_block}</code>\n\n"
        "👆 нажмите чтобы скопировать"
    )
