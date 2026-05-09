"""FastAPI app for the AW Client Report Portal."""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import calculations, pdf_sacs, pdf_tcc, storage


def quarter_label(d: datetime | None = None) -> str:
    """Format a datetime as 'YYYY QN' (e.g. '2026 Q2')."""
    d = d or datetime.now()
    return f"{d.year} Q{(d.month - 1) // 3 + 1}"


def _period_for(report: dict[str, Any]) -> str:
    """Resolve the period label for a stored report (back-compat with old data)."""
    snap = report.get("snapshot", {})
    if snap.get("period"):
        return snap["period"]
    raw = report.get("created_at") or ""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return quarter_label(dt)
    except (ValueError, AttributeError):
        return snap.get("label", "")

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "output"


def _safe_slug(s: str, fallback: str = "client") -> str:
    s = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (s or "").strip())
    s = s.strip("_") or fallback
    return s[:50]

app = FastAPI(title="AW Client Report Portal", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals["fmt_money"] = calculations.fmt_money
templates.env.globals["age_from_dob"] = calculations.age_from_dob


def _form_list(form: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    """Reassemble repeated form fields like `acc[0][type]` into list-of-dicts."""
    rows: dict[int, dict[str, str]] = {}
    for key, value in form.items():
        if not key.startswith(prefix + "["):
            continue
        try:
            rest = key[len(prefix) + 1 :]
            idx_str, _, field = rest.partition("][")
            idx = int(idx_str)
            field = field.rstrip("]")
        except (ValueError, IndexError):
            continue
        rows.setdefault(idx, {})[field] = (value or "").strip()
    return [rows[i] for i in sorted(rows) if any(rows[i].values())]


def _parse_client_form(form: dict[str, Any], client_id: str | None = None) -> dict[str, Any]:
    is_married = form.get("is_married") == "on"

    def person(prefix: str) -> dict[str, Any]:
        return {
            "name": (form.get(f"{prefix}_name") or "").strip(),
            "dob": (form.get(f"{prefix}_dob") or "").strip(),
            "ssn_last4": (form.get(f"{prefix}_ssn_last4") or "").strip(),
            "monthly_salary": form.get(f"{prefix}_monthly_salary") or 0,
        }

    retirement = _form_list(form, "ret")
    non_ret = _form_list(form, "nonret")
    liabilities = _form_list(form, "liab")

    for row in retirement + non_ret:
        row.setdefault("id", storage.new_id())
        row.setdefault("balance", "0")
        row.setdefault("cash_balance", "0")
    for row in liabilities:
        row.setdefault("id", storage.new_id())
        row.setdefault("balance", "0")
        row.setdefault("interest_rate", "0")

    return {
        "id": client_id,
        "household_name": (form.get("household_name") or "").strip(),
        "is_married": is_married,
        "client1": person("client1"),
        "client2": person("client2") if is_married else None,
        "monthly_expense_budget": form.get("monthly_expense_budget") or 0,
        "insurance_deductibles_total": form.get("insurance_deductibles_total") or 0,
        "private_reserve_balance": form.get("private_reserve_balance") or 0,
        "trust": {
            "property_address": (form.get("trust_property_address") or "").strip(),
            "current_value": form.get("trust_current_value") or 0,
        },
        "retirement_accounts": retirement,
        "non_retirement_accounts": non_ret,
        "liabilities": liabilities,
    }


def _empty_client() -> dict[str, Any]:
    return {
        "id": None,
        "household_name": "",
        "is_married": True,
        "client1": {"name": "", "dob": "", "ssn_last4": "", "monthly_salary": 0},
        "client2": {"name": "", "dob": "", "ssn_last4": "", "monthly_salary": 0},
        "monthly_expense_budget": 0,
        "insurance_deductibles_total": 0,
        "private_reserve_balance": 0,
        "trust": {"property_address": "", "current_value": 0},
        "retirement_accounts": [],
        "non_retirement_accounts": [],
        "liabilities": [],
        "reports": [],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse("/clients", status_code=302)


@app.get("/clients", response_class=HTMLResponse)
def clients_list(request: Request):
    clients = storage.list_clients()
    return templates.TemplateResponse(
        request,
        "clients_list.html",
        {"clients": clients},
    )


@app.get("/clients/new", response_class=HTMLResponse)
def client_new(request: Request):
    return templates.TemplateResponse(
        request,
        "client_form.html",
        {"client": _empty_client(), "is_new": True},
    )


@app.post("/clients/new")
async def client_create(request: Request):
    form = dict(await request.form())
    data = _parse_client_form(form, client_id=None)
    data["reports"] = []
    saved = storage.upsert_client(data)
    return RedirectResponse(f"/clients/{saved['id']}", status_code=303)


@app.get("/clients/{client_id}", response_class=HTMLResponse)
def client_detail(request: Request, client_id: str):
    client = storage.get_client(client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    return templates.TemplateResponse(
        request,
        "client_form.html",
        {"client": client, "is_new": False},
    )


@app.post("/clients/{client_id}")
async def client_update(request: Request, client_id: str):
    if not storage.get_client(client_id):
        raise HTTPException(404, "Client not found")
    form = dict(await request.form())
    data = _parse_client_form(form, client_id=client_id)
    storage.upsert_client(data)
    return RedirectResponse(f"/clients/{client_id}", status_code=303)


@app.post("/clients/{client_id}/delete")
def client_delete(client_id: str):
    storage.delete_client(client_id)
    return RedirectResponse("/clients", status_code=303)


@app.get("/clients/{client_id}/report/new", response_class=HTMLResponse)
def quarterly_form(request: Request, client_id: str):
    client = storage.get_client(client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    return templates.TemplateResponse(
        request,
        "quarterly_form.html",
        {"client": client},
    )


@app.post("/clients/{client_id}/report/new")
async def quarterly_save(request: Request, client_id: str):
    client = storage.get_client(client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    form = dict(await request.form())

    # Update balances on the client record (so next quarter pre-fills with these)
    for acc in client.get("retirement_accounts", []) + client.get("non_retirement_accounts", []):
        acc_id = acc["id"]
        bal_key = f"balance_{acc_id}"
        cash_key = f"cash_{acc_id}"
        if bal_key in form:
            acc["balance"] = form[bal_key] or 0
        if cash_key in form:
            acc["cash_balance"] = form[cash_key] or 0
    for li in client.get("liabilities", []):
        bal_key = f"balance_{li['id']}"
        if bal_key in form:
            li["balance"] = form[bal_key] or 0

    if "private_reserve_balance" in form:
        client["private_reserve_balance"] = form["private_reserve_balance"] or 0
    if "trust_current_value" in form:
        client["trust"]["current_value"] = form["trust_current_value"] or 0
    if "insurance_deductibles_total" in form:
        client["insurance_deductibles_total"] = form["insurance_deductibles_total"] or 0

    storage.upsert_client(client)

    # Snapshot under reports[]. The period (YYYY QN) is auto-derived from the
    # generation date — that's what shows on the PDF header. The free-text
    # label is for the team's internal filing and can be empty.
    period = quarter_label()
    user_label = (form.get("report_label") or "").strip()
    snapshot = {
        "client": client,
        "sacs": calculations.sacs_summary(client),
        "tcc": calculations.tcc_summary(client),
        "period": period,
        "label": user_label or period,
    }
    report = storage.add_report(client_id, {"snapshot": snapshot})

    # Write PDFs to output/ on disk so they're inspectable / archivable.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sacs_bytes = pdf_sacs.render(client, snapshot["sacs"], label=period)
    tcc_bytes = pdf_tcc.render(client, snapshot["tcc"], label=period)
    name = _safe_slug(client.get("household_name"))
    file_label = _safe_slug(period, fallback="report")
    (OUTPUT_DIR / f"SACS_{name}_{file_label}.pdf").write_bytes(sacs_bytes)
    (OUTPUT_DIR / f"TCC_{name}_{file_label}.pdf").write_bytes(tcc_bytes)

    return RedirectResponse(f"/clients/{client_id}/report/{report['id']}", status_code=303)


@app.get("/clients/{client_id}/report/{report_id}", response_class=HTMLResponse)
def report_view(request: Request, client_id: str, report_id: str):
    client = storage.get_client(client_id)
    report = storage.get_report(client_id, report_id)
    if not client or not report:
        raise HTTPException(404, "Report not found")
    snapshot = report["snapshot"]
    return templates.TemplateResponse(
        request,
        "report_view.html",
        {
            "client": client,
            "report": report,
            "snapshot": snapshot,
        },
    )


@app.get("/clients/{client_id}/report/{report_id}/sacs.pdf")
def report_sacs_pdf(client_id: str, report_id: str):
    report = storage.get_report(client_id, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    snap = report["snapshot"]
    period = _period_for(report)
    pdf_bytes = pdf_sacs.render(snap["client"], snap["sacs"], label=period)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'inline; filename="SACS_{_safe_slug(snap["client"]["household_name"])}_{_safe_slug(period)}.pdf"'
            )
        },
    )


@app.get("/clients/{client_id}/report/{report_id}/tcc.pdf")
def report_tcc_pdf(client_id: str, report_id: str):
    report = storage.get_report(client_id, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    snap = report["snapshot"]
    period = _period_for(report)
    pdf_bytes = pdf_tcc.render(snap["client"], snap["tcc"], label=period)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'inline; filename="TCC_{_safe_slug(snap["client"]["household_name"])}_{_safe_slug(period)}.pdf"'
            )
        },
    )
