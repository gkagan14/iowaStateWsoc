import re, json, subprocess, os, hashlib, glob
from concurrent.futures import ThreadPoolExecutor
schools={"Arizona State":"thesundevils.com","BYU":"byucougars.com","Cincinnati":"gobearcats.com","UCF":"ucfknights.com"}
os.makedirs('/tmp/wmt',exist_ok=True)
pages=[]
for t,dom in schools.items():
    h=subprocess.run(["curl","-sL","-A","Mozilla/5.0","--max-time","40",f"https://{dom}/sports/womens-soccer/schedule"],capture_output=True,text=True).stdout
    ids=sorted(set(re.findall(r'/boxscore/(\d+)',h)))
    for i in ids: pages.append((t,dom,i))
print('pages',len(pages))
def grab(item):
    t,dom,i=item
    ph=f'/tmp/wmt/{dom.replace(".","_")}_{i}.html'
    subprocess.run(["curl","-sL","-A","Mozilla/5.0","--max-time","50","-o",ph,f"https://{dom}/boxscore/{i}"])
    src=None
    try:
        c=open(ph,encoding='utf-8',errors='ignore').read()
        m=re.search(r'src="(https://wmt\.games/[^"]+)"',c)
        if m: src=m.group(1)
        else:
            m=re.search(r'(https://wmt\.games/[^\s"\'<>]+)',c)
            if m: src=m.group(1)
    except Exception: pass
    if not src: return (t,i,None)
    wf=f'/tmp/wmt/w_{dom.replace(".","_")}_{i}.html'
    subprocess.run(["curl","-sL","-A","Mozilla/5.0","-H","Referer: https://"+dom+"/","--max-time","50","-o",wf,src])
    return (t,i,wf if os.path.exists(wf) and os.path.getsize(wf)>5000 else None)
res=[]
with ThreadPoolExecutor(max_workers=8) as ex:
    for k,r in enumerate(ex.map(grab,pages)):
        res.append(r)
print('widgets',sum(1 for r in res if r[2]))
json.dump([r for r in res if r[2]],open('wmt_map.json','w'))
