"""SACS (Simple Automated Cash Flow) PDF generator.

Page 1: Inflow → Outflow → Private Reserve cashflow diagram.
Page 2: Private Reserve balance, investment balance, and target.

Layout is fixed (Rebecca, 13:57: "We want the form set so nothing can move").
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont  # noqa: F401  (kept for future custom font)
from reportlab.pdfgen import canvas

from app.calculations import fmt_money

PAGE_W, PAGE_H = LETTER

NAVY = HexColor("#1c2128")  # charcoal — chrome/header color (PRD-mandated bubble blue stays as BLUE below)
BLUE = HexColor("#2c6fb5")
LIGHT_BLUE = HexColor("#dbeafe")
GREEN = HexColor("#2e7d32")
RED = HexColor("#c62828")
LIGHT_GRAY = HexColor("#f3f4f6")
MID_GRAY = HexColor("#9ca3af")
DARK_GRAY = HexColor("#4b5563")
TEXT = HexColor("#1f2937")


def _stat_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    value: str,
    sub: str,
    accent: HexColor,
) -> None:
    c.setFillColor(LIGHT_GRAY)
    c.roundRect(x, y, w, h, 8, stroke=0, fill=1)
    c.setFillColor(accent)
    c.rect(x, y + h - 5, w, 5, stroke=0, fill=1)
    c.setFillColor(MID_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 14, y + h - 22, label.upper())
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(x + 14, y + 32, value)
    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica", 9)
    c.drawString(x + 14, y + 16, sub)


def _header(c: canvas.Canvas, household: str, subtitle: str, label: str) -> None:
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 70, PAGE_W, 70, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, PAGE_H - 40, "Simple Automated Cash Flow System")
    c.setFont("Helvetica", 11)
    c.drawString(40, PAGE_H - 58, subtitle)
    c.setFont("Helvetica-Bold", 12)
    right = f"{household}   |   {label}"
    c.drawRightString(PAGE_W - 40, PAGE_H - 40, right)


def _footer(c: canvas.Canvas) -> None:
    c.setFillColor(MID_GRAY)
    c.setFont("Helvetica", 8)
    c.drawString(40, 25, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.drawRightString(PAGE_W - 40, 25, "EF Financial Planning  •  Windbrook Solutions")


def _bubble(
    c: canvas.Canvas,
    cx: float,
    cy: float,
    radius: float,
    fill: HexColor,
    title: str,
    amount: str,
    sub: str = "",
) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(fill)
    c.circle(cx, cy, radius, stroke=0, fill=1)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(cx, cy + 18, title)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(cx, cy - 4, amount)
    if sub:
        c.setFont("Helvetica", 9)
        c.drawCentredString(cx, cy - 22, sub)


def _arrow(c: canvas.Canvas, x1: float, y: float, x2: float, color: HexColor, label: str = "") -> None:
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(3)
    c.line(x1, y, x2 - 8, y)
    # Arrowhead
    p = c.beginPath()
    p.moveTo(x2, y)
    p.lineTo(x2 - 10, y + 6)
    p.lineTo(x2 - 10, y - 6)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    if label:
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString((x1 + x2) / 2, y + 12, label)


def _kv_row(c: canvas.Canvas, x: float, y: float, label: str, value: str, w: float = 480) -> None:
    c.setFillColor(LIGHT_GRAY)
    c.roundRect(x, y - 6, w, 38, 6, stroke=0, fill=1)
    c.setFillColor(TEXT)
    c.setFont("Helvetica", 11)
    c.drawString(x + 16, y + 14, label)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(x + w - 16, y + 10, value)


def render(client: dict[str, Any], sacs: dict[str, float], label: str = "") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)

    household = client.get("household_name") or "Client"
    inflow = sacs["inflow"] or 0
    outflow = sacs["outflow"] or 0
    excess = sacs["excess"] or 0
    target = sacs["private_reserve_target"] or 0
    balance = sacs["private_reserve_balance"] or 0

    # ─────────────────────────────────────────────────────────────────
    # Page 1 — Cashflow Diagram
    # ─────────────────────────────────────────────────────────────────
    _header(c, household, "Monthly Cash Flow Overview", label)

    # Subtitle band (intro just below header)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, PAGE_H - 100, "Monthly Cash Flow")
    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica", 10)
    c.drawString(
        40,
        PAGE_H - 116,
        f"How {fmt_money(inflow)} of monthly take-home pay moves through the household.",
    )

    # Diagram — moved higher into the page
    diagram_y = PAGE_H - 280
    radius = 65

    inflow_x = 110
    outflow_x = PAGE_W / 2
    reserve_x = PAGE_W - 110

    _bubble(c, inflow_x, diagram_y, radius, GREEN, "Inflow", fmt_money(inflow), "per month")
    _bubble(c, outflow_x, diagram_y, radius, RED, "Outflow", fmt_money(outflow), "expense budget")
    _bubble(c, reserve_x, diagram_y, radius, BLUE, "Private Reserve", fmt_money(excess), "excess / month")

    _arrow(c, inflow_x + radius + 6, diagram_y, outflow_x - radius - 6, RED, "expenses")
    _arrow(c, outflow_x + radius + 6, diagram_y, reserve_x - radius - 6, BLUE, "excess")

    # Caption directly under diagram
    cap_y = diagram_y - radius - 40
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, cap_y, "How this works")
    c.setFont("Helvetica", 10)
    lines = [
        f"• Take-home pay of {fmt_money(inflow)} per month flows into the primary account.",
        f"• {fmt_money(outflow)} per month is transferred to the spending account for agreed expenses.",
        f"• The {fmt_money(excess)} difference accumulates in the high-yield Private Reserve.",
    ]
    for i, line in enumerate(lines):
        c.drawString(50, cap_y - 18 - 14 * i, line)

    # Insight callout (mid-bottom)
    months_to_target = (target - balance) / excess if (excess > 0 and balance < target) else 0
    ins_y = 230
    ins_h = 56
    c.setFillColor(LIGHT_BLUE)
    c.roundRect(40, ins_y, PAGE_W - 80, ins_h, 8, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(56, ins_y + ins_h - 20, "Key insight")
    c.setFillColor(TEXT)
    c.setFont("Helvetica", 10)
    if balance >= target and target > 0:
        msg = f"Private Reserve is fully funded — {fmt_money(balance - target)} above the {fmt_money(target)} target."
    elif months_to_target > 0:
        savings_rate = (excess / inflow * 100) if inflow else 0
        msg = (
            f"At {fmt_money(excess)}/mo ({savings_rate:.0f}% of inflow), the household reaches the "
            f"{fmt_money(target)} Private Reserve target in ~{months_to_target:.0f} months."
        )
    else:
        msg = f"Excess of {fmt_money(excess)}/mo is below target pace — review the expense budget."
    c.drawString(56, ins_y + 18, msg)

    # Bottom stat strip — 3 colored cards
    strip_y = 80
    strip_h = 130
    gap = 12
    card_w = (PAGE_W - 80 - 2 * gap) / 3
    savings_pct = (excess / inflow * 100) if inflow else 0
    cards = [
        ("Take-home / Inflow", fmt_money(inflow), "per month", GREEN),
        ("Expense Budget / Outflow", fmt_money(outflow), "per month", RED),
        ("Excess to Reserve", fmt_money(excess), f"{savings_pct:.0f}% of inflow", BLUE),
    ]
    for i, (lbl, val, sub, accent) in enumerate(cards):
        _stat_card(c, 40 + i * (card_w + gap), strip_y, card_w, strip_h, lbl, val, sub, accent)

    _footer(c)
    c.showPage()

    # ─────────────────────────────────────────────────────────────────
    # Page 2 — Reserve & Investment Snapshot
    # ─────────────────────────────────────────────────────────────────
    _header(c, household, "Private Reserve & Investment Snapshot", label)

    # Subtitle band (consistent with page 1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, PAGE_H - 100, "Reserve Status")
    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica", 10)
    c.drawString(
        40,
        PAGE_H - 116,
        "Current balances and progress toward the 6-month expense buffer.",
    )

    bar_w = PAGE_W - 80
    pct = min(1.0, (balance / target) if target else 0)
    gap_to_go = max(0, target - balance)

    # ── Stat strip — 3 cards (mirrors page 1 for visual rhythm) ───────
    strip_top_y = PAGE_H - 165  # 627
    strip_h = 110
    strip_y = strip_top_y - strip_h  # 517
    gap = 12
    card_w = (PAGE_W - 80 - 2 * gap) / 3
    cards2 = [
        ("PRIVATE RESERVE", fmt_money(balance), "current balance", BLUE),
        ("INVESTMENT BALANCE", fmt_money(sacs["investment_balance"]), "non-retirement", GREEN),
        ("RESERVE TARGET", fmt_money(target), "6-month buffer", NAVY),
    ]
    for i, (lbl, val, sub, accent) in enumerate(cards2):
        _stat_card(c, 40 + i * (card_w + gap), strip_y, card_w, strip_h, lbl, val, sub, accent)

    # ── Progress to Target ────────────────────────────────────────────
    y = strip_y - 36  # 481
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Progress to Target")

    bar_h = 32
    bar_x, bar_y = 40, y - 46
    c.setFillColor(LIGHT_GRAY)
    c.roundRect(bar_x, bar_y, bar_w, bar_h, 6, stroke=0, fill=1)
    c.setFillColor(BLUE)
    c.roundRect(bar_x, bar_y, max(2, bar_w * pct), bar_h, 6, stroke=0, fill=1)

    # Inside-bar percentage if there's room, else outside
    pct_text = f"{int(pct * 100)}%"
    if pct >= 0.10:
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(bar_x + 14, bar_y + 11, pct_text)
    else:
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(bar_x + max(2, bar_w * pct) + 8, bar_y + 11, pct_text)

    # Right-side annotation under the bar
    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica", 10)
    if gap_to_go > 0:
        c.drawRightString(bar_x + bar_w, bar_y - 14, f"{fmt_money(gap_to_go)} to go")
    else:
        c.drawRightString(bar_x + bar_w, bar_y - 14, "Target fully funded")

    # ── How the target is calculated ─────────────────────────────────
    y = bar_y - 50
    box_h = 130
    c.setFillColor(LIGHT_GRAY)
    c.roundRect(40, y - box_h, bar_w, box_h, 8, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(56, y - 26, "How the target is calculated")

    six_months = 6 * outflow
    deductibles = max(0, target - six_months)
    c.setFillColor(TEXT)
    c.setFont("Helvetica", 11)
    c.drawString(56, y - 52, f"6 × {fmt_money(outflow)} monthly expenses")
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(40 + bar_w - 16, y - 52, fmt_money(six_months))

    c.setFillColor(TEXT)
    c.setFont("Helvetica", 11)
    c.drawString(56, y - 70, f"+ {fmt_money(deductibles)} insurance deductibles")
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(40 + bar_w - 16, y - 70, fmt_money(deductibles))

    # Divider line
    c.setStrokeColor(MID_GRAY)
    c.setLineWidth(0.5)
    c.line(56, y - 82, 40 + bar_w - 16, y - 82)

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(56, y - 100, "Private Reserve target")
    c.drawRightString(40 + bar_w - 16, y - 100, fmt_money(target))

    # Plain-English footnote inside the box
    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(
        56,
        y - 118,
        "A 6-month buffer that covers the household if income stops temporarily.",
    )

    _footer(c)
    c.showPage()

    c.save()
    return buf.getvalue()
