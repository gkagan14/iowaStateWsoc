import json, re, collections

B12=["Arizona","Arizona State","Baylor","BYU","Cincinnati","Colorado","Houston","Iowa State","Kansas","Kansas State","Oklahoma State","TCU","Texas Tech","UCF","Utah","West Virginia"]
ABBR={"Arizona":"ARIZ","Arizona State":"ASU","Baylor":"BAY","BYU":"BYU","Cincinnati":"CIN","Colorado":"CU","Houston":"HOU",
"Iowa State":"ISU","Kansas":"KU","Kansas State":"KSU","Oklahoma State":"OSU","TCU":"TCU","Texas Tech":"TTU","UCF":"UCF",
"Utah":"UTAH","West Virginia":"WVU"}

def clean_name(s):
    s=re.sub(r'\s+',' ',s or '').strip()
    if not s: return s
    if ',' in s:
        parts=[p.strip() for p in s.split(',')]
        s=' '.join([p for p in parts[1:]]+[parts[0]])
    s=re.sub(r'\s+',' ',s).strip()
    return ' '.join(w[:1].upper()+w[1:] if w.isupper() and len(w)>1 else w for w in s.split()) if s.isupper() else s

def norm(s):
    return re.sub(r'\s+',' ',s or '').strip().lower()

# official result set for filtering exhibitions
res=json.load(open('y25/results_games25.json'))
resset={}
for r in res:
    resset.setdefault((r['date'],frozenset([r['home'],r['away']])),[]).append(r)

old=json.load(open('y25/games_raw25.json')); wmt=[]
seen={}
for r in old:
    if not r['date']: continue
    k=(r['date'],frozenset([r['home'],r['away']]),tuple(sorted([r['hs'],r['as']])))
    score=len(r.get('stats') or {})*2 + (1 if r.get('goals') else 0)
    # prefer a school's own sidearm box score (full line-ups, clean goal text) over a widget
    if '/boxes/' in (r.get('src') or '') or '/pages/' in (r.get('src') or ''): score += 3
    if k in seen and score<=seen[k][0]: continue
    seen[k]=(score,r)
games=[]
for k,(_,r) in seen.items():
    key=(r['date'],k[1])
    if key not in resset: continue
    # orientation check against a results row that agrees
    games.append(r)
games.sort(key=lambda g:g['date'])
print('canonical games',len(games))

# fix goal team attribution where missing, via lineup name matching
def last(n):
    n=clean_name(n).lower()
    return n.split()[-1] if n else ''
out=[]
for g in games:
    lineups=g.get('lineups') or []
    maps={}
    if len(lineups)>=2:
        maps[g['away']]=[last(p['name']) for p in lineups[0]]
        maps[g['home']]=[last(p['name']) for p in lineups[1]]
    goals=[]
    prev_h=prev_a=0
    for ev in g.get('goals') or []:
        ev=dict(ev)
        team=ev.get('team')
        sc=clean_name(re.sub(r'\s*\(\d+\)\s*$','',ev.get('scorer') or ''))
        raw_as=re.sub(r'Assisted by:\s*','',ev.get('assist') or '')
        asst=[]
        for a in re.split(r',|\band\b', raw_as):
            a=re.sub(r'\s*\(\d+\)\s*$','',a.strip())
            if a and a.lower()!='unassisted': asst.append(clean_name(a))
        raw_as=re.sub(r'Assisted by:\s*','',ev.get('assist') or '')
        asst=[]
        for _a in re.split(r',|\band\b', raw_as):
            _a=re.sub(r'\s*\(\d+\)\s*$','',_a.strip())
            if _a and _a.lower()!='unassisted': asst.append(clean_name(_a))
        if not team and ev.get('h') is not None:
            try:
                ch=int(str(ev['h']).strip()); ca=int(str(ev['a']).strip())
                if ca>prev_a and ch==prev_h: team=g['home']
                elif ch>prev_h and ca==prev_a: team=g['away']
                prev_h, prev_a = ch, ca
            except Exception: pass
        if not team:
            ln=last(sc)
            cands=[t for t,names in maps.items() if ln and ln in names]
            if len(cands)==1: team=cands[0]
            else:
                m=re.search(r'GOAL by\s+([A-Za-z&\.\']{2,6})\s', ev.get('desc') or '')
                if m:
                    ab=m.group(1).upper().replace('.','')
                    for t in (g['home'],g['away']):
                        if ABBR.get(t,'').upper()==ab: team=t
        goals.append({'min':ev.get('min'),'team':team,'scorer':sc,'assist':asst})
    cards=[]
    for c in g.get('cards') or []:
        cards.append({'type':c.get('type') or 'Card','min':c.get('min'),'team':c.get('team'),'player':clean_name(c.get('player') or '')})
    players=[]
    for i,lu in enumerate(lineups):
        t=g['away'] if i==0 else g['home']
        for p in lu:
            players.append({'team':t,'name':clean_name(p['name']),'pos':p['pos'],'sh':p['sh'],'sog':p['sog'],'g':p['g'],'a':p['a'],'min':p['min'],'starter':True})
    gk=[]
    for i,gs in enumerate(g.get('gks') or []):
        t=g['away'] if i==0 else g['home']
        for p in gs:
            gk.append({'team':t,'name':clean_name(p['name']),'min':p['min'],'ga':p['ga'],'sv':p['sv']})
    out.append({'date':g['date'],'home':g['home'],'away':g['away'],'hs':g['hs'],'as':g['as'],
                'stats':g.get('stats') or {},'goals':goals,'cards':cards,'players':players,'gk':gk})
json.dump(out,open('y25/games_clean25.json','w'))

# validation
off=json.load(open('y25/official25.json'))['all']
bad=0
for t in B12:
    n=gf=ga=0
    for g in out:
        if g['home']==t: n+=1; gf+=g['hs']; ga+=g['as']
        elif g['away']==t: n+=1; gf+=g['as']; ga+=g['hs']
    o=off[t]
    if (n,gf,ga)!=(o['gp'],o['gf'],o['ga']): bad+=1; print('MISMATCH',t,(n,gf,ga),(o['gp'],o['gf'],o['ga']))
print('mismatches',bad)
