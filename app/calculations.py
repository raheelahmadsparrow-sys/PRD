"""All deterministic math for SACS and TCC reports.

The PRD is explicit on these rules — keep them faithful:
  - Liabilities are NOT subtracted from net worth. They render in a
    separate box (Rebecca, 26:15).
  - Trust is NOT included in the non-retirement total. The non-retirement
    total is accounts only (Rebecca, 24:28).
  - Excess = Inflow − Outflow.
  - Private Reserve target = 6 × monthly expenses + sum of insurance deductibles.
"""

from __future__ import annotations

from datetime import date
from typing import Any


def _f(v: Any) -> float:
    if v in (None, ""):
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def age_from_dob(dob: str | None) -> int | None:
    if not dob:
        return None
    try:
        d = date.fromisoformat(dob)
    except ValueError:
        return None
    today = date.today()
    years = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
    return years


def total_inflow(client: dict[str, Any]) -> float:
    return _f(client.get("client1", {}).get("monthly_salary")) + _f(
        client.get("client2", {}).get("monthly_salary") if client.get("is_married") else 0
    )


def outflow(client: dict[str, Any]) -> float:
    return _f(client.get("monthly_expense_budget"))


def excess_to_reserve(client: dict[str, Any]) -> float:
    return total_inflow(client) - outflow(client)


def private_reserve_target(client: dict[str, Any]) -> float:
    return 6 * outflow(client) + _f(client.get("insurance_deductibles_total"))


def retirement_total(client: dict[str, Any], owner: str) -> float:
    return sum(
        _f(a.get("balance"))
        for a in client.get("retirement_accounts", [])
        if a.get("owner") == owner
    )


def non_retirement_total(client: dict[str, Any]) -> float:
    return sum(_f(a.get("balance")) for a in client.get("non_retirement_accounts", []))


def trust_value(client: dict[str, Any]) -> float:
    return _f(client.get("trust", {}).get("current_value"))


def grand_total_net_worth(client: dict[str, Any]) -> float:
    return (
        retirement_total(client, "client1")
        + retirement_total(client, "client2")
        + non_retirement_total(client)
        + trust_value(client)
    )


def liabilities_total(client: dict[str, Any]) -> float:
    return sum(_f(li.get("balance")) for li in client.get("liabilities", []))


def sacs_summary(client: dict[str, Any]) -> dict[str, float]:
    return {
        "inflow": total_inflow(client),
        "outflow": outflow(client),
        "excess": excess_to_reserve(client),
        "private_reserve_balance": _f(client.get("private_reserve_balance")),
        "private_reserve_target": private_reserve_target(client),
        "investment_balance": non_retirement_total(client),
    }


def tcc_summary(client: dict[str, Any]) -> dict[str, float]:
    return {
        "client1_retirement": retirement_total(client, "client1"),
        "client2_retirement": retirement_total(client, "client2"),
        "non_retirement": non_retirement_total(client),
        "trust": trust_value(client),
        "grand_total": grand_total_net_worth(client),
        "liabilities": liabilities_total(client),
    }


def fmt_money(value: float | int | str | None) -> str:
    n = _f(value)
    sign = "-" if n < 0 else ""
    return f"{sign}${abs(n):,.0f}"
