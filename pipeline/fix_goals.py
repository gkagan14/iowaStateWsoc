"""Repair goal text that a stats widget collapses into one cell.

The new-frontend widgets render a goal as a single string,
"Scorer [extra name] Assisted by: A, B". Split it, then segment any run-on
scorer text against the team's own roster names (longest match first).
"""
import json, sys, re, collections

B = __file__.rsplit('/', 1)[0]
path = sys.argv[1] if len(sys.argv) > 1 else f'{B}/games_clean.json'
games = json.load(open(path))

# rosters straight from the line-ups
roster = collections.defaultdict(set)
for g in games:
    for p in g.get('players') or []:
        if p.get('name'):
            roster[p['team']].add(p['name'])

def segment(text, names):
    """Longest-prefix match a run-on name string against known player names."""
    text = text.strip()
    found = []
    guard = 0
    while text and guard < 8:
        guard += 1
        hit = None
        for nm in sorted(names, key=len, reverse=True):
            if text.lower().startswith(nm.lower()):
                hit = nm; break
        if not hit:
            break
        found.append(hit)
        text = text[len(hit):].strip(' -,;')
    return found, text

fixed = 0
for g in games:
    new = []
    for ev in g.get('goals') or []:
        sc = (ev.get('scorer') or '').strip()
        assists = list(ev.get('assist') or [])
        if 'Assisted by' in sc:
            head, tail = re.split(r'Assisted by:\s*', sc, maxsplit=1)
            extras = [a.strip() for a in re.split(r',|;|\band\b', tail) if a.strip()]
            names = roster.get(ev.get('team'), set())
            matched, leftover = segment(head, names)
            if matched:
                sc = matched[0]
                assists = matched[1:] + extras + assists
            else:
                sc = head.strip()
                assists = extras + assists
            fixed += 1
        sc = re.sub(r'\s*\(\d+\)\s*$', '', sc).strip()
        ev['scorer'] = sc
        ev['assist'] = [a for a in dict.fromkeys(assists) if a and a != sc]
        new.append(ev)
    g['goals'] = new

json.dump(games, open(path, 'w'))
print(f'{path}: repaired {fixed} goal events')
