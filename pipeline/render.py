"""Assemble the single-file dashboard from the view sources + composed data."""
import os, json
base = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(base, 'part_a.html')).read() + open(os.path.join(base, 'part_b.html')).read()
data = open(os.path.join(base, 'dashboard_data.json')).read()
out = src.replace('/*__DATA__*/{}', data)
target_dir = os.path.join(base, '..', 'files')
os.makedirs(target_dir, exist_ok=True)
target = os.path.join(target_dir, 'big12-womens-soccer-2026-dashboard.html')
open(target, 'w').write(out)
print(f'wrote {target} ({len(out)//1024} KB, data {len(data)//1024} KB)')
