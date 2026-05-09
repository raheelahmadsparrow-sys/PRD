# AW Client Report Portal

A small internal portal for the EF Financial Planning team to enter client
financial data once, fill in current balances quarterly, and generate
polished **SACS** (cashflow) and **TCC** (net worth) PDF reports — turning a
full day of meeting prep into a few minutes.

Built per `AW Client Report Portal — PRD v1.0`.

## Stack

- Python 3.12 with [`uv`](https://docs.astral.sh/uv/) as the package manager
- **FastAPI** + **Jinja2Templates** for HTML rendering
- **python-multipart** for form handling
- **ReportLab** for pixel-stable PDF generation
- A single JSON file (`data/clients.json`) for storage — no DB

## Project layout

```
aw-client-portal/
├── pyproject.toml
├── README.md
├── main.py                  # convenience launcher (uvicorn)
├── app/
│   ├── main.py              # FastAPI app & routes
│   ├── calculations.py      # SACS / TCC math
│   ├── pdf_sacs.py          # SACS PDF generator
│   ├── pdf_tcc.py           # TCC PDF generator
│   └── storage.py           # JSON read/write
├── templates/
│   ├── base.html
│   ├── clients_list.html
│   ├── client_form.html
│   ├── quarterly_form.html
│   └── report_view.html
├── static/
│   └── style.css
├── data/
│   └── clients.json
└── output/                  # generated PDFs (currently streamed inline)
```

## Run

```sh
uv sync
uv run uvicorn app.main:app --reload   # local development with hot reload
```

Open http://127.0.0.1:8000 — you'll be redirected to `/clients`.

`uv run python main.py` is also available — it reads `$PORT` (defaults to
8000), binds `0.0.0.0`, and runs without `--reload`. That's the production
path used by the `Procfile` on Railway.

## Deploy to Railway

1. Push this repo to GitHub.
2. On [railway.app](https://railway.app), create a **New Project →
   Deploy from GitHub repo** and pick this repo.
3. Railway's Nixpacks builder auto-detects the Python project from
   `pyproject.toml` + `uv.lock`, installs dependencies via `uv`, and starts
   the app using the [`Procfile`](./Procfile):
   ```
   web: uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. No environment variables are required for V1.
5. Once the first deploy is green, the public URL is on the service's
   **Settings → Networking** tab.

### Authentication

The portal is gated by a single shared username + password. Defaults are
`admin` / `demo2026`. Override on Railway by setting environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `PORTAL_USER` | Login username | `admin` |
| `PORTAL_PASSWORD` | Login password | `demo2026` |
| `SESSION_SECRET` | HMAC key for session cookies | random per restart |

Set `SESSION_SECRET` to a stable 32+ character random string in production —
otherwise every restart invalidates existing sessions and forces all users to
re-login.

### Persistence note

`data/clients.json` lives on the container's local disk. Railway provisions
no volume by default, so **every deploy/restart resets the file to whatever
is committed in git** — i.e., the seeded "Hartwells" household. Anything
created during a live session survives until the next deploy.

For production, mount a Railway Volume at `/data` and point
[`app/storage.py`](app/storage.py)'s `DATA_DIR` at it (e.g.
`DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))`), or move
to a real database. This is intentionally deferred to V2 — the demo's value
comes from the form + math + PDF flow, not the storage layer.

## How it's used

1. **Create a client** (`/clients/new`)
   - Household name, married flag, Client 1/2 demographics, salary, expense budget.
   - Add retirement, non-retirement, and liability rows. Add as many as the client has.
   - Trust = primary residence (address + Zillow value).
2. **Generate a quarterly report** (`Generate Quarterly Report` button)
   - All static data is pre-filled. Just enter current balances per account, the
     Private Reserve balance, and the latest Zillow value.
   - On save, the system snapshots the entire state and updates the client's
     last-known balances so next quarter pre-fills with these.
3. **Download PDFs**
   - From the report view, click `Download SACS PDF` or `Download TCC PDF`.
   - History of all reports lives on the client profile.

## Calculation rules (per the PRD — these are non-negotiable)

- `Excess = Inflow − Outflow`
- `Private Reserve target = 6 × monthly expenses + Σ insurance deductibles`
- Retirement totals are computed **per spouse**.
- **Trust is NOT included** in the non-retirement total (Rebecca, 24:28).
- **Liabilities are NOT subtracted** from net worth — they render in their
  own box (Rebecca, 26:15).

## V1 scope notes

- **No API integrations.** All financial data is entered manually. Schwab,
  Pinnacle, RightCapital, Zillow auto-pulls are explicit V2 work.
- **No Canva export** in V1. The portal PDF is the deliverable. Easy to add later.
- **No auth** in V1 — internal tool, 3 users. Add Basic Auth or a single shared
  password before exposing publicly.
