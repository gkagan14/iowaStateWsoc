import json, subprocess, os, sys, re, glob, hashlib, time
from concurrent.futures import ThreadPoolExecutor
scheds=json.load(open('scheds2.json'))
uj=[]; seen=set()
for team,d in scheds.items():
    for l in d['links']:
        u=f"https://{d['dom']}{l}"
        if u in seen: continue
        seen.add(u); uj.append((team,u))
done=set()
for f in glob.glob('done-*.txt'):
    done |= set(open(f).read().split())
todo=[j for j in uj if j[1] not in done]
n=int(sys.argv[1]) if len(sys.argv)>1 else 100
batch=todo[:n]
os.makedirs('/tmp/boxes', exist_ok=True)
def fetch(item):
    t,u=item
    fn='/tmp/boxes/'+hashlib.md5(u.encode()).hexdigest()+'.html'
    if os.path.exists(fn) and os.path.getsize(fn)>20000: return (u,fn,'200')
    r=subprocess.run(["curl","-sL","-A","Mozilla/5.0","--max-time","60","-o",fn,"-w","%{http_code}",u],capture_output=True,text=True)
    return (u, fn if r.stdout.strip()=='200' else None, r.stdout.strip())
with ThreadPoolExecutor(max_workers=10) as ex:
    res=list(ex.map(fetch,batch))
open('done-%d.txt'%int(time.time()*1000),'w').write("\n".join(u for u,fn,c in res if fn))
print('fetched',sum(1 for _,fn,_ in res if fn),'of',len(batch),'remaining',len(todo)-len(batch),'fails',[(u,c) for u,fn,c in res if not fn][:3])
