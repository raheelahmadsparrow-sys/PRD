"""TCC (Total Client Chart) PDF generator — private-bank aesthetic.

One landscape page:
  Header (navy bar)
  Person cards (subtle green accent dot, otherwise plain white)
  Two columns:
    Left  — account detail sections (Retirement → Non-retirement → Trust → Liabilities)
    Right — TOTALS panel with Grand Total Net Worth visually dominant

Design rules:
  - White card backgrounds with thin LINE borders. No heavy fills.
  - Color is used only as a thin left-edge accent or a small dot.
  - Section titles: navy uppercase 12pt with a hairline underline.
  - Liabilities are rendered with a small "(shown separately)" caption,
    not a wall of red.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import landscape, LETTER
from reportlab.pdfgen import canvas

from app.calculations import age_from_dob, fmt_money

PAGE_W, PAGE_H = landscape(LETTER)  # 792 x 612

# ── Palette (intentionally restrained) ────────────────────────────────────
NAVY = HexColor("#1e3a5f")
TEXT = HexColor("#1f2937")
DARK_GRAY = HexColor("#4b5563")
MID_GRAY = HexColor("#9ca3af")
LINE = HexColor("#e5e7eb")  # subtle borders
LINE_STRONG = HexColor("#cbd5e1")  # section underlines
TINT = HexColor("#f8fafc")  # very subtle highlight (grand-total band)
HIGHLIGHT = HexColor("#eff6ff")  # gentle blue tint for emphasis

# Accents — used only as edges/dots, never as fills
GREEN = HexColor("#15803d")
BLUE = HexColor("#2c6fb5")
GOLD = HexColor("#b45309")
RED = HexColor("#b91c1c")


# ── Header / footer ───────────────────────────────────────────────────────


def _header(c: canvas.Canvas, household: str, period: str) -> None:
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 56, PAGE_W, 56, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(30, PAGE_H - 35, "Total Client Chart")
    c.setFont("Helvetica", 10)
    c.drawString(30, PAGE_H - 50, "Net Worth Overview")
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(PAGE_W - 30, PAGE_H - 35, household)
    c.setFont("Helvetica", 10)
    c.drawRightString(PAGE_W - 30, PAGE_H - 50, period)


def _footer(c: canvas.Canvas) -> None:
    c.setFillColor(MID_GRAY)
    c.setFont("Helvetica", 8)
    c.drawString(30, 18, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.drawRightString(PAGE_W - 30, 18, "EF Financial Planning  •  Windbrook Solutions")


# ── Building blocks ───────────────────────────────────────────────────────


def _section_title(c: canvas.Canvas, x: float, y: float, w: float, text: str, caption: str = "") -> None:
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, text.upper())
    if caption:
        title_w = c.stringWidth(text.upper(), "Helvetica-Bold", 11)
        c.setFillColor(MID_GRAY)
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(x + title_w + 8, y, caption)
    c.setStrokeColor(LINE_STRONG)
    c.setLineWidth(0.6)
    c.line(x, y - 5, x + w, y - 5)


def _person_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, person: dict[str, Any]) -> None:
    c.setFillColor(white)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, 6, stroke=1, fill=1)

    # Small green status dot
    c.setFillColor(GREEN)
    c.circle(x + 14, y + h - 14, 3.5, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 26, y + h - 16, person.get("name") or "—")

    bits: list[str] = []
    age = age_from_dob(person.get("dob"))
    if age is not None:
        bits.append(f"Age {age}")
    if person.get("dob"):
        bits.append(f"DOB {person['dob']}")
    if person.get("ssn_last4"):
        bits.append(f"SSN ****{person['ssn_last4']}")
    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica", 9)
    c.drawString(x + 14, y + h - 32, "  ·  ".join(bits) if bits else "—")

    sal = person.get("monthly_salary")
    if sal:
        try:
            sal_n = float(sal)
        except (TypeError, ValueError):
            sal_n = 0
        if sal_n:
            c.setFillColor(MID_GRAY)
            c.setFont("Helvetica", 9)
            c.drawString(x + 14, y + 10, f"Take-home: {fmt_money(sal_n)}/mo")


def _account_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, acc: dict[str, Any]) -> None:
    c.setFillColor(white)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.roundRect(x, y, w, h, 5, stroke=1, fill=1)

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 10, y + h - 14, (acc.get("type") or "Account")[:26])

    sub_bits: list[str] = []
    if acc.get("custodian"):
        sub_bits.append(acc["custodian"])
    if acc.get("account_last4"):
        sub_bits.append(f"****{acc['account_last4']}")
    if sub_bits:
        c.setFillColor(MID_GRAY)
        c.setFont("Helvetica", 8)
        c.drawString(x + 10, y + h - 26, "  ·  ".join(sub_bits))

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x + 10, y + 12, fmt_money(acc.get("balance")))

    if acc.get("cash_balance"):
        try:
            cash_n = float(acc["cash_balance"])
        except (TypeError, ValueError):
            cash_n = 0
        if cash_n:
            c.setFillColor(MID_GRAY)
            c.setFont("Helvetica", 8)
            c.drawString(x + 10, y + 2, f"cash {fmt_money(cash_n)}")


def _account_grid(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    width: float,
    accounts: list[dict[str, Any]],
    cols: int,
    h: float = 52,
    gap: float = 6,
) -> float:
    """Returns the y-coordinate at the bottom of the rendered grid."""
    if not accounts:
        c.setFillColor(MID_GRAY)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(x, y_top - 14, "(none)")
        return y_top - 22
    cols = min(cols, max(1, len(accounts)))
    card_w = (width - gap * (cols - 1)) / cols
    for i, acc in enumerate(accounts):
        row = i // cols
        col = i % cols
        bx = x + col * (card_w + gap)
        by = y_top - h - row * (h + gap)
        _account_card(c, bx, by, card_w, h, acc)
    rows = (len(accounts) + cols - 1) // cols
    return y_top - rows * (h + gap)


def _trust_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, trust: dict[str, Any]) -> None:
    c.setFillColor(white)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, 5, stroke=1, fill=1)
    # Thin gold left-edge accent
    c.setFillColor(GOLD)
    c.rect(x, y, 3, h, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x + 14, y + h - 16, trust.get("property_address") or "—")

    c.setFillColor(MID_GRAY)
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(x + 14, y + h - 28, "Primary residence  ·  Zillow Zestimate (updated quarterly)")

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(x + w - 14, y + h / 2 - 4, fmt_money(trust.get("current_value")))


def _liab_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, li: dict[str, Any]) -> None:
    c.setFillColor(white)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.roundRect(x, y, w, h, 5, stroke=1, fill=1)
    # Thin red left-edge accent
    c.setFillColor(RED)
    c.rect(x, y, 3, h, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 12, y + h - 14, (li.get("type") or "Liability")[:24])

    rate = li.get("interest_rate")
    if rate:
        c.setFillColor(MID_GRAY)
        c.setFont("Helvetica", 8)
        c.drawString(x + 12, y + h - 26, f"{rate}% interest")

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 13)
    c.drawRightString(x + w - 12, y + 14, fmt_money(li.get("balance")))


def _summary_panel(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    w: float,
    h: float,
    client: dict[str, Any],
    tcc: dict[str, float],
) -> None:
    """Right-side TOTALS panel. Grand Total is visually dominant."""
    is_married = bool(client.get("is_married") and client.get("client2"))

    # Build the row list — (label, value, is_grand)
    rows: list[tuple[str, str, bool]] = []
    if is_married:
        rows.append((f"{client['client1'].get('name') or 'Client 1'} retirement", fmt_money(tcc["client1_retirement"]), False))
        rows.append((f"{client['client2'].get('name') or 'Client 2'} retirement", fmt_money(tcc["client2_retirement"]), False))
    else:
        rows.append(("Retirement total", fmt_money(tcc["client1_retirement"]), False))
    rows.append(("Non-retirement total", fmt_money(tcc["non_retirement"]), False))
    rows.append(("Trust value", fmt_money(tcc["trust"]), False))
    rows.append(("Grand Total Net Worth", fmt_money(tcc["grand_total"]), True))
    rows.append(("Liabilities (separate)", fmt_money(tcc["liabilities"]), False))

    # Container card (white with thin border, full panel)
    c.setFillColor(white)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.roundRect(x, y_top - h, w, h, 8, stroke=1, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x + 14, y_top - 22, "TOTALS")
    c.setStrokeColor(LINE_STRONG)
    c.setLineWidth(0.6)
    c.line(x + 14, y_top - 28, x + w - 14, y_top - 28)

    # Distribute rows in remaining space
    y = y_top - 36
    avail = (y_top - 36) - (y_top - h + 16)  # bottom inner padding 16
    # Grand row gets 1.7x the height of a regular row
    n_regular = sum(1 for _, _, gr in rows if not gr)
    n_grand = sum(1 for _, _, gr in rows if gr)
    unit = avail / (n_regular + n_grand * 1.7)

    inner_pad_x = 16
    for label, value, is_grand in rows:
        row_h = unit * (1.7 if is_grand else 1.0)

        if is_grand:
            # Subtle blue-tint highlight band
            c.setFillColor(HIGHLIGHT)
            c.rect(x + 1, y - row_h + 4, w - 2, row_h, stroke=0, fill=1)

        # Label
        c.setFillColor(NAVY if is_grand else MID_GRAY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + inner_pad_x, y - 14, label.upper() if is_grand else label)

        # Value
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 22 if is_grand else 16)
        c.drawString(x + inner_pad_x, y - (row_h - 14), value)

        y -= row_h
        # Hairline divider between regular rows (skip after grand row)
        if not is_grand:
            c.setStrokeColor(LINE)
            c.setLineWidth(0.3)
            c.line(x + inner_pad_x, y + 2, x + w - inner_pad_x, y + 2)


# ── Main render ───────────────────────────────────────────────────────────


def render(client: dict[str, Any], tcc: dict[str, float], label: str = "") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(LETTER))

    household = client.get("household_name") or "Client"
    is_married = bool(client.get("is_married") and client.get("client2"))

    _header(c, household, label)

    # ── Layout columns ─────────────────────────────────────────────────
    margin = 30
    summary_w = 240
    col_gap = 18
    main_w = PAGE_W - 2 * margin - summary_w - col_gap
    main_x = margin
    summary_x = PAGE_W - margin - summary_w

    # Person cards row (sits below header)
    person_top = PAGE_H - 70
    person_h = 52

    if is_married:
        card_w = (main_w - 12) / 2
        _person_card(c, main_x, person_top - person_h, card_w, person_h, client["client1"])
        _person_card(c, main_x + card_w + 12, person_top - person_h, card_w, person_h, client["client2"])
    else:
        _person_card(c, main_x, person_top - person_h, main_w, person_h, client["client1"])

    body_top = person_top - person_h - 22  # spacing below person cards

    # ── Right column: TOTALS panel ────────────────────────────────────
    panel_top = person_top
    panel_h = panel_top - 60  # leaves room for footer
    _summary_panel(c, summary_x, panel_top, summary_w, panel_h, client, tcc)

    # ── Left column: account sections ─────────────────────────────────
    y = body_top

    # RETIREMENT ──────────────────────────────────────────────────────
    _section_title(c, main_x, y, main_w, "Retirement Accounts")
    y -= 12
    ret_accts = client.get("retirement_accounts", [])
    c1_ret = [a for a in ret_accts if a.get("owner") == "client1"]
    c2_ret = [a for a in ret_accts if a.get("owner") == "client2"]

    if is_married:
        col_w = (main_w - 12) / 2
        # Sub-headers (small, mid-gray)
        c.setFillColor(MID_GRAY)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(main_x, y, (client["client1"].get("name") or "Client 1").upper())
        c.drawString(main_x + col_w + 12, y, (client["client2"].get("name") or "Client 2").upper())
        y -= 10
        cols_c1 = min(2, max(1, (len(c1_ret) + 1) // 2)) if c1_ret else 1
        cols_c2 = min(2, max(1, (len(c2_ret) + 1) // 2)) if c2_ret else 1
        b1 = _account_grid(c, main_x, y, col_w, c1_ret, cols=cols_c1)
        b2 = _account_grid(c, main_x + col_w + 12, y, col_w, c2_ret, cols=cols_c2)
        y = min(b1, b2)
    else:
        cols = min(4, max(1, (len(c1_ret) + 1) // 2)) if c1_ret else 1
        y = _account_grid(c, main_x, y, main_w, c1_ret, cols=cols)

    # NON-RETIREMENT ──────────────────────────────────────────────────
    y -= 22
    _section_title(c, main_x, y, main_w, "Non-Retirement Accounts")
    y -= 12
    nonret = client.get("non_retirement_accounts", [])
    cols = min(4, max(1, (len(nonret) + 1) // 2)) if nonret else 1
    y = _account_grid(c, main_x, y, main_w, nonret, cols=cols)

    # TRUST ───────────────────────────────────────────────────────────
    y -= 22
    _section_title(c, main_x, y, main_w, "Trust  ·  Primary Residence")
    y -= 12
    _trust_card(c, main_x, y - 50, main_w, 50, client.get("trust") or {})
    y -= 50 + 4

    # LIABILITIES ─────────────────────────────────────────────────────
    y -= 22
    _section_title(c, main_x, y, main_w, "Liabilities", caption="shown separately, not subtracted from net worth")
    y -= 12
    liabs = client.get("liabilities", [])[:4]
    if liabs:
        gap = 10
        liab_w = (main_w - gap * (len(liabs) - 1)) / max(1, len(liabs))
        liab_w = min(liab_w, 220)
        for i, li in enumerate(liabs):
            _liab_card(c, main_x + i * (liab_w + gap), y - 48, liab_w, 48, li)
    else:
        c.setFillColor(MID_GRAY)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(main_x, y - 14, "(none)")

    _footer(c)
    c.showPage()
    c.save()
    return buf.getvalue()
