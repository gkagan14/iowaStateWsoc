import sys, json
sys.path.insert(0,'.')
from parse_tables import tables

def f(x):
    try: return float(str(x).replace('%',''))
    except: return None

FIELDS={'GF':'gf','GA':'ga','ScoreAvg':'gf90','OppAvg':'ga90','Margin':'margin','PK':'pk','PKATT':'pka',
'Shots':'shots','Saves':'saves','Save%':'savepct','Corners':'corners','Fouls':'fouls','Fo':'fouls',
'Offside':'offsides','Off':'offsides','YC':'yc','RC':'rc','SOG':'sog','Assists':'assists','NO':'n_o',
'Avg/G':'avg','GW':'gwg','GT':'gt','1ST':'first','OT':'ot','GA Avg/G':'gaavg','Minutes':'minutes','Gaa Avg/G':'gaa',
'Sa/G':'sag','Sho':'shutouts','Sho/G':'shog','F/G':'fg','Off/G':'offg','C':'corners','C/G':'cg','YC/G':'ycg','RC/G':'rcg',
'PK/PKA':'pkstr','YC/RC':'ycrс'}
DROP={'Index','Team','#','Player','Game','Total'}
def build(path):
    ts=tables(path); out={}
    for t in ts[:10]:
        rows=[r for r in t['rows'] if r]
        if len(rows)<2: continue
        hdr=rows[0]
        for r in rows[1:]:
            if len(r)!=len(hdr): continue
            team=r[1]
            if not team or team in ('Team',): continue
            d=out.setdefault(team,{})
            for h,v in zip(hdr,r):
                if h in DROP or not v: continue
                if h=='GP': d['gp']=int(f(v)) if f(v) is not None else None
                elif h in FIELDS:
                    key=FIELDS[h]; val=f(v)
                    if key=='minutes': d[key]=v
                    elif key in ('pkstr','ycrс'): d[key]=v
                    elif val is not None and val==int(val): d[key]=int(val)
                    else: d[key]=val
    return out
allg=build('stats2026.html'); confg=build('stats2026conf.html')
json.dump({'all':allg,'conf':confg},open('official.json','w'),indent=1)
for t,v in allg.items(): print(f"{t:16}", v.get('gp'), v.get('gf'), v.get('ga'), v.get('shots'), v.get('sog'), v.get('corners'), v.get('shutouts'))
print('conf sample', confg.get('Colorado'))
