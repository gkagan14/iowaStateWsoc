import re, json, subprocess, os, hashlib, sys, time
from concurrent.futures import ThreadPoolExecutor

SITES = {"Arizona":"arizonawildcats.com","Arizona State":"thesundevils.com","Baylor":"baylorbears.com",
"Cincinnati":"gobearcats.com","Colorado":"cubuffs.com","Houston":"uhcougars.com","Iowa State":"cyclones.com",
"Kansas":"kuathletics.com","Kansas State":"kstatesports.com","Oklahoma State":"okstate.com","TCU":"gofrogs.com",
"Texas Tech":"texastech.com","Utah":"utahutes.com","West Virginia":"wvusports.com"}
PATHS = ["sports/womens-soccer/schedule/2025","sports/womens-soccer/schedule/2025-26","sports/womens-soccer/schedule"]

def curl(url, out=None, extra=None):
    cmd = ["curl","-sL","-A","Mozilla/5.0","--max-time","50"]
    if out: cmd += ["-o", out, "-w", "%{http_code}"]
    if extra: cmd += extra
    r = subprocess.run(cmd+[url], capture_output=True, text=True)
    return r.stdout

# ---- 1. schedules
plan = []
for team, dom in SITES.items():
    best = (None, [])
    for p in PATHS:
        h = curl(f"https://{dom}/{p}")
        links = re.findall(r'href="(/sports/womens-soccer/stats/\d{4}/[^"/]+/boxscore/\d+)"', h)
        short = re.findall(r'href="(/boxscore/\d+)"', h)
        old = re.findall(r'href="(/boxscore\.aspx\?id=\d+)"', h)
        got = links+short+old
        if len(got) > len(best[1]): best = (p, got)
        if len(got) >= 18: break
    uniq = []
    for l in best[1]:
        if l not in uniq: uniq.append(l)
    plan.append({"team": team, "dom": dom, "path": best[0], "links": uniq})
    print(f"{team:14} {str(best[0]):42} {len(uniq)}")
json.dump(plan, open('y25/plan.json','w'), indent=1)
