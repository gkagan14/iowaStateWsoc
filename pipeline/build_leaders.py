"""Per-player leaderboards for both seasons and both scopes.

goals/assists come from the goal logs (they reconcile exactly to team totals);
shots/SOG/minutes come from published line-ups; keeper data from the GK rows;
cards from the box-score card tables (the box scores do not reliably split colour,
so the dashboard shows exact team yellow/red cards alongside player 'cards').
"""
import json, os, collections, re

B = os.path.dirname(os.path.abspath(__file__))
P = lambda n: os.path.join(B, n)

SOURCES = [('2026', 'games_clean.json'), ('2025', 'y25/games_clean25.json')]


def blank():
    return {'g': 0, 'a': 0, 'sh': 0, 'sog': 0, 'min': 0, 'apps': 0, 'cards': 0,
            'gk_min': 0, 'gk_ga': 0, 'gk_sv': 0, 'gk_so': 0, 'gk_apps': 0}


out = {}
for season, path in SOURCES:
    games = json.load(open(P(path)))
    players = collections.defaultdict(lambda: {'pos': '', 'all': blank(), 'conf': blank(), 'name': '', 'from_lineup': False})

    def key_of(name):
        return re.sub(r'[^a-z ]', '', name.lower()).strip()

    def add(team, name, scope, key, val):
        if not name or re.fullmatch(r'[\d\s#.]+', name):
            return          # jersey numbers and blank entries are not players
        d = players[(team, key_of(name))]
        if not d['name']:
            d['name'] = name
        elif name != d['name']:
            d['alt'] = name
        d['all'][key] += val
        if scope:
            d['conf'][key] += val

    for g in games:
        conf = bool(g.get('conf'))
        # goals + assists from the goal log
        for ev in g.get('goals') or []:
            team = ev.get('team')
            if not team:
                continue
            add(team, ev.get('scorer'), conf, 'g', 1)
            for a_ in ev.get('assist') or []:
                add(team, a_, conf, 'a', 1)
        # line-ups: shots, SOG, minutes, appearances
        for p in g.get('players') or []:
            team = p['team']
            nm = p['name']
            if not nm:
                continue
            d = players[(team, key_of(nm))]
            if p.get('pos'):
                d['pos'] = p['pos']
            if not d['from_lineup']:
                d['from_lineup'] = True
                d['name'] = nm
            for key, src in (('sh', 'sh'), ('sog', 'sog'), ('min', 'min')):
                d['all'][key] += p.get(src) or 0
                if conf:
                    d['conf'][key] += p.get(src) or 0
            add(team, nm, conf, 'apps', 1)
        # cards
        for c in g.get('cards') or []:
            nm = re.sub(r'^#\s*\d+\s*', '', (c.get('player') or '').strip())
            nm = re.sub(r'\s+', ' ', nm).strip()
            if nm in ('', '0', '-', '—'):
                continue                      # bench/team card with no player attached
            add(c.get('team'), nm, conf, 'cards', 1)
        # keepers
        team_ga = {}
        for t, ga in ((g['home'], g['as']), (g['away'], g['hs'])):
            team_ga[t] = ga
        for k in g.get('gk') or []:
            team, nm = k['team'], k['name']
            if not nm:
                continue
            d = players[(team, key_of(nm))]
            shutout = 1 if team_ga.get(team) == 0 and (k.get('min') or 0) > 0 else 0
            for key, val in (('gk_min', k.get('min') or 0), ('gk_ga', k.get('ga') or 0),
                             ('gk_sv', k.get('sv') or 0), ('gk_so', shutout), ('gk_apps', 1)):
                d['all'][key] += val
                if conf:
                    d['conf'][key] += val

    b12 = set(json.load(open(P('dashboard_data.json')))['seasons'][season]['teams'].keys())
    rows = []
    for (team, _key), d in players.items():
        name = d.get('name') or _key
        alt = d.get('alt')
        if alt and sum(c.isupper() for c in alt[1:]) > sum(c.isupper() for c in name[1:]):
            name = alt
        if team not in b12:
            continue                          # league leaders are Big 12 players only
        a = d['all']
        if (a['g'] + a['a'] + a['sh'] + a['cards'] + a['gk_min']) == 0:
            continue                          # never appeared in a published box score
        row = {'n': name, 't': team, 'p': d['pos'] or ''}
        for sc, tag in (('all', 'a'), ('conf', 'c')):
            s = d[sc]
            compact = {}
            for k, v in (('g', s['g']), ('as', s['a']), ('sh', s['sh']), ('sog', s['sog']),
                         ('min', s['min']), ('apps', s['apps']), ('cards', s['cards']),
                         ('gk_min', s['gk_min']), ('gk_ga', s['gk_ga']), ('gk_sv', s['gk_sv']),
                         ('gk_so', s['gk_so'])):
                if v:
                    compact[k] = v
            if compact.get('gk_sv') is not None and (s['gk_sv'] + s['gk_ga']) > 0:
                compact['sv_pct'] = round(100 * s['gk_sv'] / (s['gk_sv'] + s['gk_ga']), 1)
                compact['ga90'] = round(s['gk_ga'] / (s['gk_min'] / 90), 2) if s['gk_min'] >= 90 else None
            if compact:
                row[tag] = compact
        if 'a' in row:
            rows.append(row)
    out[season] = rows
    nk = sum(1 for r in rows if r['a'].get('gk_min'))
    print(f"{season}: {len(rows)} players tracked, {nk} keepers, "
          f"{sum(r['a'].get('g', 0) for r in rows)} goals, {sum(r['a'].get('as', 0) for r in rows)} assists, "
          f"{sum(r['a'].get('cards', 0) for r in rows)} cards")

json.dump(out, open(P('leaders.json'), 'w'), separators=(',', ':'))
print('wrote leaders.json', round(os.path.getsize(P('leaders.json')) / 1024), 'KB')
