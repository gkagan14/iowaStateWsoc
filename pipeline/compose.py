import json, os
_B=os.path.dirname(os.path.abspath(__file__))
P=lambda n: os.path.join(_B,n)
s26=json.load(open(P('season2026.json')))
s25=json.load(open(P('season2025.json')))
proj=json.load(open(P('projection.json')))
ros=json.load(open(P('rosters.json')))
out={'generated':__import__('datetime').date.today().isoformat(),'seasons':{'2026':s26,'2025':s25},'projection':proj,'rosters':ros}
json.dump(out,open(P('dashboard_data.json'),'w'),separators=(',',':'))
import os
print('composed', round(os.path.getsize(P('dashboard_data.json'))/1024),'KB')
for y,s in out['seasons'].items():
    print(y, s['generated'], 'teams', len(s['teams']))
