#!/usr/bin/env bash
# Refresh the Big 12 scouting dashboard.
#
#   ./refresh.sh              # re-scrape the current season and rebuild everything
#   ./refresh.sh --skip-fetch # rebuild from the cached scrape (fast; for UI/data edits)
#   ./refresh.sh --both       # also re-scrape the 2025 season
#
# Requires: curl, python3 (standard library only). Run from anywhere.
set -euo pipefail
cd "$(dirname "$0")"

SEASON=2026
TODAY=$(date +%F)
SKIP_FETCH=0
BOTH=0
for arg in "$@"; do
  case "$arg" in
    --skip-fetch) SKIP_FETCH=1 ;;
    --both) BOTH=1 ;;
    *) echo "unknown option: $arg"; exit 1 ;;
  esac
done

step() { printf '\n\033[1m▸ %s\033[0m\n' "$*"; }
mkdir -p .cache

# ---------------------------------------------------------------- 1. official season data
if [ "$SKIP_FETCH" = "0" ]; then
  step "Pulling official $SEASON Big 12 statistics"
  curl -s -A "Mozilla/5.0" "https://big12sports.com/stats.aspx?path=soc&year=$SEASON"        -o stats2026.html
  curl -s -A "Mozilla/5.0" "https://big12sports.com/stats.aspx?path=soc&year=$SEASON&conf=true" -o stats2026conf.html
  ls -lh stats2026.html stats2026conf.html | awk '{print "  " $9, $5}'
fi

step "Parsing official team statistics + results list"
python3 official.py  | tail -3
python3 results.py   | tail -3

# ---------------------------------------------------------------- 2. box scores
if [ "$SKIP_FETCH" = "0" ]; then
  step "Collecting $SEASON schedules and box scores (this is the slow part, ~2–4 min)"
  python3 fetch_scheds.py | tail -3
  rm -rf /tmp/boxes /tmp/wmt
  FRESH=1 python3 fetch_boxes.py 400 | tail -2
  python3 fetch_wmt.py | tail -2
fi

step "Parsing box scores"
BOX_DIRS="/tmp/boxes/*.html:/tmp/wmt/w_*.html" python3 parse2.py | tail -2

step "Matching box scores to official results and reconciling totals"
python3 build3.py | tail -4
python3 merge_games.py games_clean.json results_games.json games_clean.json official.json

# ---------------------------------------------------------------- 3. 2025 season (static unless --both)
if [ "$BOTH" = "1" ]; then
  step "Refreshing the 2025 season"
  python3 y25/fetch25.py    | tail -2
  python3 y25/fetch_boxes25.py | tail -2
  python3 y25/parse25.py    | tail -2
  python3 y25/official25.py | tail -2
  python3 y25/results25.py  | tail -3
  python3 y25/build25.py    | tail -4
  python3 merge_games.py y25/games_clean25.json y25/results_games25.json y25/games_clean25.json y25/official25.json
  python3 season_build.py y25/games_clean25.json y25/official25.json season2025.json 2025 2025-12-08
elif [ ! -f season2025.json ]; then
  echo "  (2025 season data missing — run with --both)"; exit 1
fi

# ---------------------------------------------------------------- 4. season metrics
step "Building team metrics, logs and player tables"
python3 season_build.py games_clean.json official.json season2026.json "$SEASON" "$TODAY"

# ---------------------------------------------------------------- 5. projections
step "Recomputing the 2027 projection and roster minutes"
python3 projection.py | head -2
python3 rosters.py   | tail -1
python3 compose.py

# ---------------------------------------------------------------- 6. audit + render
step "Building the scrape report"
python3 report.py

step "Rendering the single-file dashboard"
python3 render.py

printf '\n\033[1m✓ Done\033[0m — files/big12-womens-soccer-2026-dashboard.html is current as of %s.\n' "$TODAY"
printf '  Publish: copy it to index.html in your repo, or drag the folder onto app.netlify.com/drop\n'
printf '  Bundle:  cd /tmp/staffpack && cp <dashboard> index.html && zip -r ..\n'
