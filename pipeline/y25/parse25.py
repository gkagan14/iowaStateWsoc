import re, glob, json, sys
sys.path.insert(0,'.')
from parse_tables import tables
from names import norm, num

TIME=re.compile(r'^\d{1,3}:\d{2}$')
recs=[]
FILES=json.load(open('y25/files.json'))
for f in FILES:
    try: h=open(f,encoding='utf-8',errors='ignore').read()
    except: continue
    tm=re.search(r'<title>(.*?)</title>',h,re.S)
    title=re.sub(r'&#x2F;','/',re.sub(r'&#x27;',"'",tm.group(1))) if tm else ''
    date=None
    dm=re.search(r'(\d{1,2})\s*[/\s]\s*(\d{1,2})\s*[/\s]\s*(\d{4})',title)
    if dm: date=f"{dm.group(3)}-{int(dm.group(1)):02d}-{int(dm.group(2)):02d}"
    ts=tables(f)
    if not ts: continue
    scores=None
    for t in ts:
        rows=[r for r in t['rows'] if r]
        if not rows: continue
        hd=rows[0]
        if len(rows)>=3 and len(hd)>=3 and ('Total' in hd[-1] or hd[-1]=='T'):
            if all(re.match(r'^\d+$',str(x).strip()) for x in rows[1][1:-1]) or True:
                names=[rows[1][0],rows[2][0]]
                if all(names):
                    scores=(names,[num(rows[1][-1])[0],num(rows[2][-1])[0]]); break
    if not scores or None in scores[1]: continue
    away,home=norm(scores[0][0]),norm(scores[0][1])
    as_,hs=scores[1][0],scores[1][1]
    goals=[];cards=[];st={};lineups=[];gks=[]
    for t in ts:
        rows=[r for r in t['rows'] if r]
        if len(rows)<1: continue
        hd=rows[0]
        # goals
        if any(TIME.match(str(r[0])) for r in rows[1:] if r) and len(hd)>=3 and not any('SH'==c for c in hd):
            for r in rows[1:]:
                if not r or not TIME.match(str(r[0])): continue
                if len(r)>=7:  # sidearm: min,'',scorer,assist,desc,hs,as
                    goals.append({'min':r[0],'team':None,'scorer':r[2],'assist':r[3],'desc':r[4],'h':r[-2],'a':r[-1]})
                elif len(r)>=3:  # wmt: min,team,scorer[,assist]
                    goals.append({'min':r[0],'team':norm(r[1]),'scorer':r[2],'assist':r[3] if len(r)>3 else '','desc':''})
            continue
        # cards
        if hd[:3]==['Team','Min','Player']:
            for r in rows[1:]:
                if len(r)>=3 and r[0]: cards.append({'type':'Card','min':r[1],'team':norm(r[0]),'player':r[2]})
            continue
        if len(rows)>1 and 'Card' in str(hd[0]):
            for r in rows:
                if len(r)>=4: cards.append({'type':r[0],'min':r[2],'team':norm(r[3]),'player':r[4] if len(r)>4 else ''})
            continue
        # team stats
        labels={r[0] for r in rows}
        if 'Shots' in labels and ('Fouls' in labels or 'Fouls ' in labels):
            cur=None
            for r in rows:
                if len([c for c in r if c])==1:
                    cur=r[0].strip(); continue
                if not r[0]: continue
                if r[0] in ('Shots','Saves','Corners Kicks','Corner Kicks','Offsides','Fouls'): cur=r[0]
                else:
                    v,sog=num(r[-1]); key={'Shots':'shots','Saves':'saves','Corners Kicks':'corners','Corner Kicks':'corners','Offsides':'offsides','Fouls':'fouls'}.get((cur or '').strip())
                    if key:
                        st.setdefault(norm(r[0]),{})[key]=v
                        if key=='shots': st[norm(r[0])]['sog']=sog
            continue
        if 'SH' in hd and 'SOG' in hd and 'MIN' in hd:
            ps=[]
            for r in rows[1:]:
                if len(r)<8 or not r[0].isdigit(): continue
                ps.append({'no':r[0],'name':r[1],'pos':r[2],'sh':num(r[3])[0] or 0,'sog':num(r[4])[0] or 0,'g':num(r[5])[0] or 0,'a':num(r[6])[0] or 0,'min':num(r[7])[0] or 0})
            lineups.append(ps); continue
        if 'GA' in hd and 'Saves' in hd and 'game' not in str(hd).lower():
            g=[]
            for r in rows[1:]:
                if len(r)<5 or not r[0]: continue
                g.append({'no':r[0],'name':r[1],'min':num(r[2])[0] or 0,'ga':num(r[3])[0] or 0,'sv':num(r[4])[0] or 0})
            gks.append(g)
    recs.append({'date':date,'home':home,'away':away,'hs':hs,'as':as_,'stats':st,'goals':goals,'cards':cards,
                 'lineups':lineups,'gks':gks,'title':title[:120],'src':f})
print('parsed',len(recs),'goals',sum(len(r['goals']) for r in recs),'withstats',sum(1 for r in recs if r['stats']))
json.dump(recs,open('y25/games_raw25.json','w'))
