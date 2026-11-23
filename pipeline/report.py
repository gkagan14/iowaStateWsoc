"""Build a machine-readable scrape report so a CI run can be audited without the raw log.

Written after the fetch + build steps: per-school page counts, per-season box-score coverage,
and the reconciliation result against the official Big 12 totals.
"""
import json, os, collections, datetime

B = os.path.dirname(os.path.abspath(__file__))
P = lambda n: os.path.join(B, n)


def load(n, default=None):
    try:
        return json.load(open(P(n)))
    except Exception:
        return default


def school_rollup(reports, seasons):
    """reports: list of {school, url, ok} rows -> per school counts (de-duplicated by url)."""
    seen = {}
    for season, rows in seasons:
        for r in rows or []:
            key = r['url']
            if key in seen:
                continue
            seen[key] = {'school': r.get('school', '?'), 'season': season, 'ok': bool(r.get('ok'))}
    per = collections.defaultdict(lambda: {'requested': 0, 'ok': 0, 'failed': [], 'seasons': set()})
    for url, v in seen.items():
        d = per[v['school']]
        d['requested'] += 1
        d['seasons'].add(v['season'])
        if v['ok']:
            d['ok'] += 1
        else:
            d['failed'].append(url)
    out = []
    for school, d in sorted(per.items()):
        out.append({'school': school, 'requested': d['requested'], 'ok': d['ok'],
                    'failed': len(d['failed']), 'seasons': sorted(d['seasons']),
                    'failedUrls': d['failed'][:5]})
    return out


def season_summary(label, games_file, official_file):
    games = load(games_file, [])
    off = load(official_file, {}).get('all', {})
    if not games:
        return {'season': label, 'error': 'no games file'}
    box = sum(1 for g in games if g.get('stats'))
    cov = {}
    for g in games:
        for t in (g['home'], g['away']):
            if t in off:
                d = cov.setdefault(t, {'gp': 0, 'box': 0})
                d['gp'] += 1
                if g.get('stats'):
                    d['box'] += 1
    teams = []
    for t, d in sorted(cov.items()):
        teams.append({'school': t, 'gp': d['gp'], 'boxScoreGames': d['box'],
                      'coverage': round(d['box'] / d['gp'], 2) if d['gp'] else 0})
    # reconciliation
    bad = []
    for t, o in off.items():
        n = gf = ga = 0
        for g in games:
            if g['home'] == t:
                n += 1; gf += g['hs']; ga += g['as']
            elif g['away'] == t:
                n += 1; gf += g['as']; ga += g['hs']
        if (n, gf, ga) != (o['gp'], o['gf'], o['ga']):
            bad.append({'school': t, 'dashboard': [n, gf, ga], 'official': [o['gp'], o['gf'], o['ga']]})
    return {'season': label, 'games': len(games), 'withBoxScore': box,
            'teams': teams, 'reconciliationMismatches': bad}


rep = {
    'generatedUtc': datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z',
    'schools': school_rollup(None, [('2026', load('fetch_report.json', [])),
                                    ('2025', load('y25/fetch_report.json', []))]),
    'seasons': [season_summary('2026', 'games_clean.json', 'official.json'),
                season_summary('2025', 'y25/games_clean25.json', 'y25/official25.json')],
}
json.dump(rep, open(P('scrape-report.json'), 'w'), indent=1)

bad_schools = [s for s in rep['schools'] if s['failed']]
print(f"scrape report: {len(rep['schools'])} schools, {sum(s['failed'] for s in rep['schools'])} failed fetches")
for s in rep['schools']:
    s25 = next((x for x in rep['seasons'] if x['season'] == '2025'), {})
    print(f"  {s['school']:16} pages {s['ok']:3}/{s['requested']:3} ok" + (f"  FAILED {s['failed']}" if s['failed'] else ''))
for seasons in rep['seasons']:
    if 'error' in seasons:
        print(f"  {seasons['season']}: {seasons['error']}"); continue
    worst = min(seasons['teams'], key=lambda x: x['coverage'])
    print(f"  {seasons['season']}: {seasons['games']} games, {seasons['withBoxScore']} with box scores, "
          f"lowest coverage {worst['school']} {worst['coverage']*100:.0f}%, "
          f"{len(seasons['reconciliationMismatches'])} mismatches")
