import json, collections, math

B12=["Arizona","Arizona State","Baylor","BYU","Cincinnati","Colorado","Houston","Iowa State","Kansas","Kansas State","Oklahoma State","TCU","Texas Tech","UCF","Utah","West Virginia"]
ABBR={"Arizona":"ARIZ","Arizona State":"ASU","Baylor":"BAY","BYU":"BYU","Cincinnati":"CIN","Colorado":"CU","Houston":"HOU","Iowa State":"ISU","Kansas":"KU","Kansas State":"KSU","Oklahoma State":"OSU","TCU":"TCU","Texas Tech":"TTU","UCF":"UCF","Utah":"UTAH","West Virginia":"WVU"}
import sys
GAMES_FILE, OFF_FILE, OUT_FILE, SEASON, GENERATED = sys.argv[1:6]
games=json.load(open(GAMES_FILE))
official=json.load(open(OFF_FILE))
ISB12=set(B12)

def mins(m):
    try:
        a,b=str(m).split(':'); return int(a)+int(b)/60
    except: return None

# scope "all" and "conf"
def agg(scope):
    out={}
    for t in B12:
        gs=[g for g in games if t in (g['home'],g['away']) and (not scope=='conf' or g['conf'])]
        d={'gp':0,'w':0,'l':0,'t':0,'gf':0,'ga':0,'hw':0,'hl':0,'ht':0,'aw':0,'al':0,'at':0,
           'shots':0,'sog':0,'corners':0,'fouls':0,'saves':0,'offsaves':0,
           'oppshots':0,'oppsog':0,'oppcorners':0,'oppfouls':0,'boxgp':0,
           'cs':0,'fts':0,'otg':0,'pk':0,'pka':0,'cards':0,
           'gtime':collections.Counter(),'otime':collections.Counter(),
           'scored_first':0,'conceded_first':0,'both':0,'gfh':0,'gfa':0,'gah':0,'gaa':0}
        for g in gs:
            home=g['home']==t
            f,a=(g['hs'],g['as']) if home else (g['as'],g['hs'])
            d['gp']+=1; d['gf']+=f; d['ga']+=a
            if f>a: d['w']+=1
            elif f<a: d['l']+=1
            else: d['t']+=1
            if home:
                if f>a: d['hw']+=1
                elif f<a: d['hl']+=1
                else: d['ht']+=1
            else:
                if f>a: d['aw']+=1
                elif f<a: d['al']+=1
                else: d['at']+=1
            if a==0: d['cs']+=1
            if f==0: d['fts']+=1
            s=g.get('stats') or {}
            if s and t in s and 'shots' in s[t]:
                so=s[t]; op=s.get(g['away'] if home else g['home'],{})
                d['boxgp']+=1
                d['shots']+=so.get('shots') or 0; d['sog']+=so.get('sog') or 0
                d['corners']+=so.get('corners') or 0; d['fouls']+=so.get('fouls') or 0
                d['saves']+=so.get('saves') or 0
                d['oppshots']+=op.get('shots') or 0; d['oppsog']+=op.get('sog') or 0
                d['oppcorners']+=op.get('corners') or 0; d['oppfouls']+=op.get('fouls') or 0
            for c in g.get('cards') or []:
                if c.get('team')==t: d['cards']+=1
            # goal timing / first goal
            evs=[]
            for ev in g.get('goals') or []:
                if not ev.get('team'): continue
                mm=mins(ev['min'])
                if mm is None: continue
                evs.append((mm,ev['team']))
            evs.sort()
            if evs:
                first=evs[0][1]
                if first==t: d['scored_first']+=1
                else: d['conceded_first']+=1
            for mm,team in evs:
                b='0-15' if mm<15 else '16-30' if mm<30 else '31-45' if mm<=45 else '46-60' if mm<60 else '61-75' if mm<75 else '76-90' if mm<=90 else '90+'
                if team==t:
                    d['gtime'][b]+=1
                    if mm<=45: d['gfh']+=1
                    if mm>90: d['otg']+=1
                else:
                    d['otime'][b]+=1
                    if mm<=45: d['gah']+=1
                    if mm>90: d['otg']+=1
        out[t]=d
    return out

A=agg('all'); C=agg('conf')

def per(d,key,den=None):
    n=den if den else d['gp']
    return round(d[key]/n,2) if n else 0

metrics={}
for t in B12:
    m={}
    for scope,D in (('all',A[t]),('conf',C[t])):
        boxgp=D['boxgp'] or 1
        m[scope]={
          'gp':D['gp'],'w':D['w'],'l':D['l'],'t':D['t'],
          'gf':D['gf'],'ga':D['ga'],'gpg':round(D['gf']/(D['gp'] or 1),2),'gapg':round(D['ga']/(D['gp'] or 1),2),
          'cs':D['cs'],'fts':D['fts'],'sf':D['scored_first'],'cf':D['conceded_first'],
          'shots':D['shots'],'sog':D['sog'],'shpg':round(D['shots']/boxgp,1),'sogpg':round(D['sog']/boxgp,1),
          'acc':round(100*D['sog']/D['shots'],1) if D['shots'] else 0,
          'conv':round(100*D['gf']/D['shots'],1) if D['shots'] else 0,
          'corners':D['corners'],'cpg':round(D['corners']/boxgp,1),
          'fouls':D['fouls'],'fpg':round(D['fouls']/boxgp,1),
          'saves':D['saves'],'svpg':round(D['saves']/boxgp,1),
          'savepct':round(100*D['saves']/(D['saves']+D['ga']),1) if (D['saves']+D['ga']) else 0,
          'oppshots':D['oppshots'],'oppshpg':round(D['oppshots']/boxgp,1),
          'oppsog':D['oppsog'],'oppsogpg':round(D['oppsog']/boxgp,1),
          'oppcpg':round(D['oppcorners']/boxgp,1),
          'shotshare':round(100*D['shots']/(D['shots']+D['oppshots']),1) if (D['shots']+D['oppshots']) else 50,
          'sogshare':round(100*D['sog']/(D['sog']+D['oppsog']),1) if (D['sog']+D['oppsog']) else 50,
          'cards':D['cards'],'cpg_cards':round(D['cards']/(D['gp'] or 1),2),
          'gtime':dict(D['gtime']),'otime':dict(D['otime']),
          'g1h':D['gfh'],'ga1h':D['gah'],
          'boxgp':D['boxgp'],
        }
    # official extras
    o=official['all'].get(t,{}); oc=official['conf'].get(t,{})
    for scope,od in (('all',o),('conf',oc)):
        m[scope]['shutouts']=od.get('shutouts')
        m[scope]['offsides']=od.get('offsides')
        m[scope]['pk']=od.get('pk'); m[scope]['pka']=od.get('pka')
        m[scope]['yc']=od.get('yc'); m[scope]['rc']=od.get('rc')
        m[scope]['svpct_off']=round(100*(od.get('savepct') or 0),1)
        m[scope]['assists']=od.get('assists')
    m['rank']={}
    metrics[t]=m

# ranks within Big 12 for key metrics (1 = best)
RANKS={'w':1,'gpg':1,'gapg':-1,'gd':1,'shpg':1,'sogpg':1,'acc':1,'conv':1,'cpg':1,'shotshare':1,
       'oppshpg':-1,'savepct':1,'shutouts':1,'cards':-1,'fpg':-1,'sogshare':1,'svpg':1,'oppsogpg':-1}
for scope in ('all','conf'):
    for key,dirn in RANKS.items():
        vals=[]
        for t in B12:
            v=metrics[t][scope].get(key)
            if key=='gd': v=metrics[t][scope]['gf']-metrics[t][scope]['ga']
            if v is None: continue
            vals.append((v,t))
        vals.sort(reverse=(dirn==1))
        for i,(v,t) in enumerate(vals,1):
            metrics[t]['rank'].setdefault(scope,{})[key]=i

# players
pl=collections.defaultdict(lambda: collections.defaultdict(lambda: {'g':0,'a':0,'sh':0,'sog':0,'min':0,'apps':0,'pos':'','ga':0,'sv':0,'gkmin':0,'starts':0}))
for g in games:
    sc_team={}
    for ev in g.get('goals') or []:
        team=ev.get('team'); nm=ev.get('scorer')
        if not team or not nm: continue
        pl[team][nm]['g']+=1
        for a_ in ev.get('assist') or []:
            if a_: pl[team][a_]['a']+=1
    for p in g.get('players') or []:
        t=p['team']; d=pl[t][p['name']]
        d['sh']+=p['sh']; d['sog']+=p['sog']; d['min']+=p['min']; d['apps']+=1
        if p.get('pos'): d['pos']=p['pos']
    for p in g.get('gk') or []:
        t=p['team']; d=pl[t][p['name']]
        d['ga']+=p['ga']; d['sv']+=p['sv']; d['gkmin']+=p['min']
players={}
for t in B12:
    arr=[]
    for nm,d in pl[t].items():
        arr.append({'name':nm,'pos':d['pos'],'g':d['g'],'a':d['a'],'pts':2*d['g']+d['a'],'sh':d['sh'],'sog':d['sog'],
                    'min':d['min'],'apps':d['apps'],'ga':d['ga'],'sv':d['sv'],'gkmin':d['gkmin'],
                    'gk':d['gkmin']>0})
    arr.sort(key=lambda x:(-x['pts'],-x['g'],-x['sh'],-x['min']))
    players[t]=arr

# team game logs
logs={}
for t in B12:
    lg=[]
    for g in games:
        if t not in (g['home'],g['away']): continue
        home=g['home']==t; opp=g['away'] if home else g['home']
        f,a=(g['hs'],g['as']) if home else (g['as'],g['hs'])
        s=g.get('stats') or {}
        so=s.get(t,{}); op=s.get(opp,{})
        lg.append({'date':g['date'],'opp':opp,'ha':'H' if home else 'A','gf':f,'ga':a,
                   'r':'W' if f>a else ('L' if f<a else 'T'),'conf':g['conf'],
                   'sh':so.get('shots'),'sog':so.get('sog'),'osh':op.get('shots'),'osog':op.get('sog'),
                   'ck':so.get('corners'),'opck':op.get('corners'),'sv':so.get('saves'),'fls':so.get('fouls'),
                   'goals':[{'min':e['min'],'n':e['scorer'],'a':e.get('assist'),'t':e['team']} for e in (g.get('goals') or []) if e.get('team') in (t,opp)]})
    logs[t]=lg

data={'generated':GENERATED,'season':SEASON,'teams':{t:{'name':t,'abbr':ABBR[t],'metrics':metrics[t],'log':logs[t],'players':players[t],
        'sos':None} for t in B12}}

def wpct(t):
    m=metrics[t]['all']; n=m['gp'] or 1
    return (m['w']+0.5*m['t'])/n
for t in B12:
    opps=[g['away'] if g['home']==t else g['home'] for g in games if t in (g['home'],g['away'])]
    b=[o for o in opps if o in ISB12]
    data['teams'][t]['sos']=round(100*sum(wpct(o) for o in b)/len(b),1) if b else 0
json.dump(data,open(OUT_FILE,'w'),separators=(',',':'))
import os
print('teams', len(data['teams']), 'size', round(os.path.getsize(OUT_FILE)/1024), 'KB')

