import sys,json,re,collections
sys.path.insert(0,'.')
from parse_tables import tables
from names import norm
ts=tables('y25/stats2025.html')
rows=[r for r in ts[20]['rows'] if r][1:]
games={}
for r in rows:
    if len(r)<3: continue
    date=r[0].strip(); loc=r[1].strip(); line=r[2].strip()
    conf = line.startswith('*')
    line=line.lstrip('*').strip()
    m=re.match(r'^(.*?)\s+(\d+)\s*-\s*(\d+)\s+(.*)$', line)
    if not m: print('FAIL',line); continue
    away,as_,hs,home=m.group(1).strip(),int(m.group(2)),int(m.group(3)),m.group(4).strip()
    away,home=norm(away),norm(home)
    md=re.match(r'(\d{2})/(\d{2})/(\d{4})',date)
    iso=f"{md.group(3)}-{md.group(1)}-{md.group(2)}"
    k=(iso,frozenset([home,away]),tuple(sorted([hs,as_])))
    if k in games:
        games[k]['conf']=games[k]['conf'] or conf
        continue
    games[k]={'date':iso,'home':home,'away':away,'hs':hs,'as':as_,'conf':conf,'loc':loc}
print('unique games',len(games))
gl=list(games.values())
c=collections.Counter()
for g in gl: c[g['home']]+=1; c[g['away']]+=1
off=json.load(open('y25/official25.json'))['all']
for t,o in off.items():
    print(f"{t:16} gp {c[t]:3} official {o['gp']}")
json.dump(gl,open('y25/results_games25.json','w'))
