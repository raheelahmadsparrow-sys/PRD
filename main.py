"""Production launcher.

Local development:
    uv run uvicorn app.main:app --reload

Production / Railway:
    uv run python main.py            # respects $PORT, binds 0.0.0.0
    uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT   (Procfile path)
"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("UVICORN_RELOAD", "0") == "1"
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
