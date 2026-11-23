import json, collections

import os
_B=os.path.dirname(os.path.abspath(__file__))
P=lambda n: os.path.join(_B,n)
D = json.load(open(P('season2026.json')))
GAMES = json.load(open(P('games_clean.json')))
B12 = list(D['teams'])

acc = {t: collections.defaultdict(lambda: {'name': '', 'pos': '', 'min': 0, 'g': 0, 'a': 0, 'sh': 0, 'apps': 0}) for t in B12}

for g in GAMES:
    for p in g.get('players') or []:
        t = p['team']
        if t not in acc:
            continue
        d = acc[t][p['name']]
        d['name'] = p['name']
        d['pos'] = p.get('pos') or d['pos']
        d['min'] += p.get('min') or 0
        d['sh'] += p.get('sh') or 0
        d['apps'] += 1
    # goal-log scorers who never appear in a published lineup
    for ev in g.get('goals') or []:
        t = ev.get('team')
        if t not in acc or not ev.get('scorer'):
            continue
        nm = ev['scorer']
        d = acc[t][nm]
        d['name'] = nm
        d['g'] += 1
        for a_ in ev.get('assist') or []:
            if a_:
                acc[t][a_]['name'] = a_
                acc[t][a_]['a'] += 1

rosters = {}
for t in B12:
    gp = D['teams'][t]['metrics']['all']['gp']
    players = []
    for nm, d in acc[t].items():
        g_ = d['g']
        players.append({'name': nm, 'pos': d['pos'], 'min': d['min'], 'g': g_, 'a': d['a'],
                        'sh': d['sh'], 'apps': d['apps']})
    players.sort(key=lambda x: (-x['min'], -x['g'], -x['sh'], x['name']))
    tracked = sum(p['min'] for p in players)
    expected = gp * 990.0
    rosters[t] = {'players': players, 'trackedMin': tracked,
                  'coverage': round(min(1.0, tracked / expected), 2) if expected else 0,
                  'trackedGoals': sum(p['g'] for p in players),
                  'teamGoals': D['teams'][t]['metrics']['all']['gf'],
                  'gp': gp}

D['rosters'] = rosters
json.dump(D['rosters'], open(P('rosters.json'), 'w'), separators=(',', ':'))
for t in B12:
    r = rosters[t]
    print(f"{t:16} players {len(r['players']):3} tracked_min {r['trackedMin']:6} coverage {r['coverage']*100:5.1f}% goals {r['trackedGoals']}/{r['teamGoals']}")
