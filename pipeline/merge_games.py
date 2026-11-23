"""Fill in result-only games (no box score) from the official results list and stamp conference flags."""
import json, sys

games_file = sys.argv[1] if len(sys.argv) > 1 else 'games_clean.json'
results_file = sys.argv[2] if len(sys.argv) > 2 else 'results_games.json'
out_file = sys.argv[3] if len(sys.argv) > 3 else games_file

g = json.load(open(games_file))
res = json.load(open(results_file))
have = {(x['date'], frozenset([x['home'], x['away']])) for x in g}

added = 0
for r in res:
    k = (r['date'], frozenset([r['home'], r['away']]))
    if k in have:
        continue
    g.append({'date': r['date'], 'home': r['home'], 'away': r['away'], 'hs': r['hs'], 'as': r['as'],
              'stats': {}, 'goals': [], 'cards': [], 'players': [], 'gk': [], 'result_only': True})
    added += 1

rmap = {(r['date'], frozenset([r['home'], r['away']])): r.get('conf', False) for r in res}
for x in g:
    x['conf'] = rmap.get((x['date'], frozenset([x['home'], x['away']])), False)
g.sort(key=lambda x: x['date'])
json.dump(g, open(out_file, 'w'))

off = json.load(open(sys.argv[4] if len(sys.argv) > 4 else 'official.json'))['all']
bad = 0
for t in off:
    n = gf = ga = 0
    for x in g:
        if x['home'] == t:
            n += 1; gf += x['hs']; ga += x['as']
        elif x['away'] == t:
            n += 1; gf += x['as']; ga += x['hs']
    o = off[t]
    if (n, gf, ga) != (o['gp'], o['gf'], o['ga']):
        bad += 1
        print(f'  MISMATCH {t}: mine {n} gp {gf}-{ga} vs official {o["gp"]} gp {o["gf"]}-{o["ga"]}')
print(f'{out_file}: {len(g)} games, {sum(1 for x in g if x["stats"])} with box scores, {added} added from results, {bad} mismatches')
