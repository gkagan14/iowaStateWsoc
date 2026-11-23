# Keeping the dashboard updated

Everything is generated from `work/` — the dashboard HTML is never hand-edited, it is rendered
from `part_a.html` + `part_b.html` + `dashboard_data.json`.

## One command

```bash
cd work
./refresh.sh              # re-scrape the current season, rebuild everything, re-render
./refresh.sh --skip-fetch # rebuild from the cached scrape (seconds) — after UI edits
./refresh.sh --both       # also re-scrape 2025
```

Output: `files/big12-womens-soccer-2026-dashboard.html`

## What refresh.sh does

1. Pulls the official Big 12 season statistics (all games + conference) and the results list
2. Collects every member's schedule and box scores (~350 pages), including the two schools
   whose sites publish box scores only through a widget
3. Parses box scores → matches them to official results → reconciles every team's
   W-L-T / GF / GA against the conference page (it prints any mismatch)
4. Rebuilds per-team metrics, logs and player tables for both seasons
5. Recomputes the opponent-adjusted 2027 projection and the roster minutes
6. Renders the single-file dashboard

## Publishing an update

The published site only needs one file: **index.html**.

```bash
cp files/big12-womens-soccer-2026-dashboard.html <repo>/index.html
git add index.html && git commit -m "data refresh $(date +%F)" && git push
```

GitHub Pages / Netlify / Cloudflare rebuild automatically on push. Keep the CSVs in the repo
if staff want the raw tables; they are regenerated the same way (see `work/` scripts).

## Cadence during the season

- **Weekly (Mon):** run `./refresh.sh`, push. Box scores for the weekend are all posted by then.
- **After a midweek match:** `./refresh.sh` again — it is idempotent, nothing is appended.
- **Off-season:** freeze it, then re-run once in August when the new season's first box scores land.

## If a school changes its site

`refresh.sh` prints a mismatch block if a team's totals stop reconciling. The usual causes are a
new schedule URL pattern (edit `fetch_scheds.py` / `y25/fetch25.py`) or a moved box-score page.
The reconciliation step is the guard: never publish a build that reports mismatches.

## Versioning

The dashboard carries its own "as of" date. If you want history, keep dated copies:

```bash
cp files/big12-womens-soccer-2026-dashboard.html dist/dashboard-$(date +%F).html
```
