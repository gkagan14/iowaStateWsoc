import json, re, os, subprocess, hashlib, sys
from concurrent.futures import ThreadPoolExecutor

plan = json.load(open('y25/plan.json'))
os.makedirs('/tmp/b25/pages', exist_ok=True)
os.makedirs('/tmp/b25/widgets', exist_ok=True)

jobs = []          # (url, kind)
seen = set()
for p in plan:
    for l in p['links']:
        url = f"https://{p['dom']}{l}"
        if url in seen: continue
        seen.add(url)
        kind = 'widget' if re.match(r'^https://[^/]+/boxscore/\d+$', url) else 'page'
        jobs.append((url, kind))
print('jobs', len(jobs), 'widgets', sum(1 for _,k in jobs if k=='widget'))

def fetch(job):
    url, kind = job
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    if kind == 'page':
        fp = f'/tmp/b25/pages/{h}.html'
        curl_code = subprocess.run(["curl","-sL","-A","Mozilla/5.0","--max-time","60","-o",fp,"-w","%{http_code}",url],
                                   capture_output=True, text=True).stdout.strip()
        if curl_code != '200' or not os.path.exists(fp) or os.path.getsize(fp) < 20000:
            return None
        try:
            html = open(fp, encoding='utf-8', errors='ignore').read()
        except Exception:
            return None
        m = re.search(r'src="(https://wmt\.games/[^"]+)"', html)
        if m:
            wfp = f'/tmp/b25/widgets/{h}.html'
            subprocess.run(["curl","-sL","-A","Mozilla/5.0","-H",f"Referer: {url}","--max-time","60","-o",wfp,m.group(1)])
            if os.path.exists(wfp) and os.path.getsize(wfp) > 5000:
                return wfp
        return fp
    else:
        # NUXT page -> find widget
        tmp = f'/tmp/b25/pages/{h}_w.html'
        subprocess.run(["curl","-sL","-A","Mozilla/5.0","--max-time","60","-o",tmp,url])
        try:
            html = open(tmp, encoding='utf-8', errors='ignore').read()
        except Exception:
            return None
        m = re.search(r'src="(https://wmt\.games/[^"]+)"', html)
        if not m:
            m = re.search(r'(https://wmt\.games/[^\s"\'<>]+)', html)
        if not m: return None
        wfp = f'/tmp/b25/widgets/{h}.html'
        subprocess.run(["curl","-sL","-A","Mozilla/5.0","--max-time","60","-o",wfp,m.group(1)])
        if os.path.exists(wfp) and os.path.getsize(wfp) > 5000:
            return wfp
        return None

with ThreadPoolExecutor(max_workers=10) as ex:
    out = list(ex.map(fetch, jobs))
print('fetched', sum(1 for o in out if o), 'of', len(jobs))
json.dump([o for o in out if o], open('y25/files.json','w'))
smap = {u: (t, k) for u, k in jobs}
rep = []
for (url, kind), res in zip(jobs, out):
    t, _ = smap.get(url, ('?', kind))
    rep.append({'school': t, 'url': url, 'kind': kind, 'ok': bool(res)})
json.dump(rep, open('y25/fetch_report.json', 'w'))
