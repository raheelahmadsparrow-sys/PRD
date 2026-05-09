# AW Client Report Portal — Loom Script

**Length:** ~3:30–4:00
**URL:** `https://<your-railway-domain>.up.railway.app`
**Audience:** Andrew, Rebecca, Maryann (EF Financial Planning)

---

## Pre-flight (5 min before recording)

- [ ] Live URL opens; you're **signed out** (so you can demo login).
- [ ] Browser zoom **115%**, window 1280×800+, no bookmarks bar.
- [ ] **The Hartwells** seed visible on `/clients`.
- [ ] One SACS PDF and one TCC PDF already downloaded — flip to them mid-recording without waiting on the download dialog.
- [ ] Slack / email / notifications muted.

**Two manager calls before you start:**
1. **Login on-camera, or off-camera?** If on-camera, the credentials show briefly. Either rotate them after, or pre-sign-in and start the Loom on the dashboard.
2. **Mobile demo style?** Easiest: Chrome DevTools → toggle Device Toolbar (`Ctrl+Shift+M`). Or simply drag the window narrow.

---

## SCENE 1 — Intro (0:00–0:20)

> *[ON SCREEN: login page]*

> "Hi Andrew, Rebecca, and Maryann. This is the AW Client Report Portal we built from your brief. Goal — straight from your call — turn the full day of quarterly meeting prep into a few minutes per client. Quick walkthrough."

> *[ACTION: sign in]*

> "Sign-in is gated since this holds client financial data."

---

## SCENE 2 — Dashboard (0:20–0:35)

> *[ON SCREEN: `/clients`]*

> "Here's the dashboard. Each row is a household — name, members, account counts, last report date. We've seeded one fictional family, the Hartwells, so the demo isn't empty."

> *[ACTION: click "The Hartwells"]*

---

## SCENE 3 — Client Profile (0:35–1:10)

> *[ON SCREEN: client form]*

> "This is the static profile, entered once. Names, DOB with auto-calculated age, last four SSN, salary, expense budget. The trust section is the primary residence — address plus Zillow value, updated quarterly. Account structure is variable — retirement tagged per spouse because totals are per spouse, non-retirement, and liabilities with interest rates. Add or remove rows for any of them, up to six per section. Save once and this is the source of truth."

---

## SCENE 4 — Quarterly Form  *(the time-saver)*  (1:10–2:15)

> *[ACTION: click **Generate Quarterly Report**]*

> "Now quarterly prep. Static data is pre-filled. Each balance shows last quarter's value underneath with a **'↺ use last'** button. If nothing changed, one click and you're done. If it changed, type the new number."

> *[ACTION: click "↺ use last" on one row, then change another balance to a new number]*

> *[POINT to the strip pinned at the bottom of the screen]*

> "Rebecca, this part is specifically for you. Watch the strip at the bottom. As I edit a balance, the per-spouse retirement totals, non-retirement, trust, **Grand Total Net Worth**, and liabilities all recompute **live** — before I generate anything. The math you do by hand today happens automatically here."

> *[ACTION: bump one retirement balance up by $20,000. Pause. Point at the spouse total moving, then point at the Grand Total moving.]*

> *Manager note: this is the strongest beat in the whole video. Don't rush it. Type slowly, let the eye catch the totals updating, and pause for a second before continuing.*

> "Notice liabilities sit on the right end — red, marked separate. They never affect the Grand Total. That's your rule."

> "Form also blocks submit until every required field is filled."

> *[ACTION: clear one balance briefly to show the disabled button + missing-count message, then restore]*

> *[ACTION: click **Generate Reports**]*

---

## SCENE 5 — SACS PDF (2:15–2:55)

> *[ACTION: open the pre-downloaded SACS PDF]*

> "SACS, page 1: green Inflow, red Outflow, blue Private Reserve — same structure you have today. Three stat cards at the bottom mirror the bubbles."

> *[ACTION: flip to page 2]*

> "Page 2 — Reserve Status. Current balance, investment balance, target. Progress bar — the Hartwells are 59% of target, $29,000 to go. And the formula box: 6 × $11,000 monthly expenses + $5,000 deductibles = $71,000. The math is right there for the client."

---

## SCENE 6 — TCC PDF (2:55–3:35)

> *[ACTION: open the pre-downloaded TCC PDF]*

> "TCC — net worth overview. Two client info cards up top. Retirement split per spouse. Non-retirement — and importantly, the trust is **no`t** in this number, it's separate. Trust card with the property address and Zillow value, gold edge marking it as the residence."

> *[POINT to liabilities at bottom]*

> "Liabilities last, red edge, caption *'shown separately, not subtracted from net worth.'* Your exact wording, Rebecca."

> *[POINT to right summary panel]*

> "Right panel — the totals. Per-spouse retirement, non-retirement, trust, then **Grand Total Net Worth** in the highlight: $1,468,000 for the Hartwells. Liabilities last, marked '(separate)' — $413,000 of debt that does **not** get subtracted from the $1.46M."

---

## SCENE 7 — Mobile (3:35–3:50)

> *[ACTION: open DevTools device view, or drag window narrow]*

> "Mobile — top bar tightens, tables stack as cards or scroll, forms full-width. Works on a phone before a meeting."

---

## SCENE 8 — Wrap + What's Out of Scope (3:50–4:15)

> *[ACTION: back to dashboard]*

> "Deliberately not in V1: Canva export — Rebecca, you said no Canva on the call. RightCapital, Schwab, Pinnacle, Zillow auto-pulls — V2, because of the compliance and reliability concerns Maryann and Rebecca flagged. Data lives in a single file today — for production we'd add a database or a Railway volume so records survive deploys."

> "But the core ask — enter balances once, polished SACS and TCC in minutes — that's all here. Take it for a spin and tell us what to tweak."

> *[END]*

---

## Speaker notes — what to land slowly

| Moment | Why it matters |
|---|---|
| **The live-totals strip moves as you type** (Scene 4) | Direct answer to Rebecca's *"all of that math is done manually, so even just automating that would be great"* (25:36). Strongest beat in the video. |
| **"Liabilities never subtract from net worth"** (Scene 6) | Quotes Rebecca verbatim from 26:15. Shows we listened. |
| **"Trust is not in the non-retirement total"** (Scene 6) | Her other hard rule (24:28). |
| **"A full day → a few minutes"** (Scenes 1 + 8) | The value prop. Bookend the video with it. |

If you mis-click, don't restart — Loom lets you trim afterwards. Just pause and continue.

---

## Send with the Loom

1. The Loom link.
2. The live Railway URL.
3. Login credentials.
4. **One disclaimer:** *"Anything you create on this URL resets when we push the next update — production version will use persistent storage."*
