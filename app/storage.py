"""JSON-file storage for clients and quarterly reports.

Single-writer assumption: the EF team is 3 people and traffic is trivial,
so a process-local lock is enough — no DB needed.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_FILE = DATA_DIR / "clients.json"

_lock = threading.Lock()


def _empty_db() -> dict[str, Any]:
    return {"clients": []}


def _ensure_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps(_empty_db(), indent=2), encoding="utf-8")


def load() -> dict[str, Any]:
    _ensure_file()
    with _lock:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save(db: dict[str, Any]) -> None:
    _ensure_file()
    with _lock:
        DATA_FILE.write_text(json.dumps(db, indent=2), encoding="utf-8")


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def list_clients() -> list[dict[str, Any]]:
    return load()["clients"]


def get_client(client_id: str) -> dict[str, Any] | None:
    for c in list_clients():
        if c["id"] == client_id:
            return c
    return None


def upsert_client(client: dict[str, Any]) -> dict[str, Any]:
    db = load()
    if not client.get("id"):
        client["id"] = new_id()
        client["created_at"] = now_iso()
        db["clients"].append(client)
    else:
        for i, existing in enumerate(db["clients"]):
            if existing["id"] == client["id"]:
                client.setdefault("created_at", existing.get("created_at", now_iso()))
                client.setdefault("reports", existing.get("reports", []))
                db["clients"][i] = client
                break
        else:
            db["clients"].append(client)
    client["updated_at"] = now_iso()
    save(db)
    return client


def delete_client(client_id: str) -> bool:
    db = load()
    before = len(db["clients"])
    db["clients"] = [c for c in db["clients"] if c["id"] != client_id]
    save(db)
    return len(db["clients"]) < before


def add_report(client_id: str, report: dict[str, Any]) -> dict[str, Any] | None:
    db = load()
    for client in db["clients"]:
        if client["id"] == client_id:
            report.setdefault("id", new_id())
            report.setdefault("created_at", now_iso())
            client.setdefault("reports", []).append(report)
            client["updated_at"] = now_iso()
            save(db)
            return report
    return None


def get_report(client_id: str, report_id: str) -> dict[str, Any] | None:
    client = get_client(client_id)
    if not client:
        return None
    for r in client.get("reports", []):
        if r["id"] == report_id:
            return r
    return None


def latest_report(client_id: str) -> dict[str, Any] | None:
    client = get_client(client_id)
    if not client:
        return None
    reports = client.get("reports", [])
    return reports[-1] if reports else None
