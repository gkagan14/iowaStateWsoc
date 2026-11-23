import re, glob, json, sys
sys.path.insert(0,'.')
from parse_tables import tables

SHORT={'Arizona':'Arizona','Arizona St.':'Arizona State','Arizona State':'Arizona State','Kansas St.':'Kansas State',
'Kansas State':'Kansas State','Oklahoma St.':'Oklahoma State','Oklahoma State':'Oklahoma State','Iowa St.':'Iowa State',
'Iowa State':'Iowa State','West Virginia':'West Virginia','Texas Tech':'Texas Tech','TCU':'TCU','BYU':'BYU',
'Colorado':'Colorado','Kansas':'Kansas','Baylor':'Baylor','Houston':'Houston','Utah':'Utah','UCF':'UCF',
'Cincinnati':'Cincinnati','Cal St. Fullerton':'Cal State Fullerton','South Fla.':'South Florida','San Diego St.':'San Diego State',
'Colorado St.':'Colorado State','Utah St.':'Utah State','Seattle U':'Seattle U','Kansas City':'Kansas City','Grand Canyon':'Grand Canyon',
'Abilene Christian':'Abilene Christian','Eastern Ky.':'Eastern Kentucky','Utah Valley':'Utah Valley','New Mexico St.':'New Mexico State'}

def norm(s):
    s=s.strip()
    if s in SHORT: return SHORT[s]
    s=s.replace(' St.',' State').replace(' Fla.',' Florida').replace(' Ky.',' Kentucky')
    return s

def num(x):
    x=str(x).strip()
    m=re.match(r'^(\d+)(?:\s*\((\d+)\))?$',x)
    if m: return int(m.group(1)), (int(m.group(2)) if m.group(2) else None)
    if re.match(r'^-?\d+$',x): return int(x),None
    return None,None

