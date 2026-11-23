import json, statistics as st

import os
_B=os.path.dirname(os.path.abspath(__file__))
P=lambda n: os.path.join(_B,n)
D = json.load(open(P('season2026.json')))
B12 = list(D['teams'])
GAMES = json.load(open(P('games_clean.json')))

# ---------- inputs: only games where BOTH teams have a stat line (symmetric)
shots = {t: [] for t in B12}      # per-game shots for
shots_a = {t: [] for t in B12}    # per-game shots against
pairs = {t: [] for t in B12}      # opponents (B12 only)
for g in GAMES:
    st_ = g.get('stats') or {}
    h, a = g['home'], g['away']
    if h in B12 and a in B12 and h in st_ and a in st_ and 'shots' in st_[h] and 'shots' in st_[a]:
        shots[h].append(st_[h]['shots']); shots_a[h].append(st_[a]['shots'])
        shots[a].append(st_[a]['shots']); shots_a[a].append(st_[h]['shots'])
        pairs[h].append(a); pairs[a].append(h)

rows = {}
for t in B12:
    m = D['teams'][t]['metrics']['all']
    mc = D['teams'][t]['metrics']['conf']
    rows[t] = {'sf': st.mean(shots[t]), 'sa': st.mean(shots_a[t]),
               'gf': m['gf'], 'ga': m['ga'],
               'shots_tot': m['shots'], 'shots_against_tot': m['oppshots'],
               'ppg_conf': (mc['w'] * 3 + mc['t']) / max(1, mc['gp']), 'conf_gp': mc['gp'],
               'conf': mc, 'all': m}

# pooled league baselines (shots in == shots out by construction)
n_games = sum(len(shots[t]) for t in B12) / 2
L = sum(sum(shots[t]) for t in B12) / sum(len(shots[t]) for t in B12)
L_CONV = sum(r['gf'] for r in rows.values()) / sum(r['shots_tot'] for r in rows.values())
L_CONV_A = sum(r['ga'] for r in rows.values()) / sum(r['shots_against_tot'] for r in rows.values())

# ---------- additive SRS with damping on the same baseline L
adj_sf = {t: rows[t]['sf'] for t in B12}
adj_sa = {t: rows[t]['sa'] for t in B12}
for _ in range(400):
    new_sf, new_sa = {}, {}
    for t in B12:
        o = pairs[t]
        new_sf[t] = L + (rows[t]['sf'] - st.mean([adj_sa[x] for x in o]))
        new_sa[t] = L + (rows[t]['sa'] - st.mean([adj_sf[x] for x in o]))
    adj_sf = {t: 0.5 * adj_sf[t] + 0.5 * new_sf[t] for t in B12}
    adj_sa = {t: 0.5 * adj_sa[t] + 0.5 * new_sa[t] for t in B12}

# ---------- shrunk conversion, projected goals
K = 140.0
proj = {}
for t in B12:
    r = rows[t]
    c_for = (r['gf'] + K * L_CONV) / (r['shots_tot'] + K)
    c_ag = (r['ga'] + K * L_CONV_A) / (r['shots_against_tot'] + K)
    proj[t] = {'adj_sf': adj_sf[t], 'adj_sa': adj_sa[t], 'c_for': c_for, 'c_ag': c_ag,
               'proj_gf': adj_sf[t] * c_for, 'proj_ga': adj_sa[t] * c_ag,
               'e_gf': adj_sf[t] * L_CONV, 'e_ga': adj_sa[t] * L_CONV_A,
               'shotdiff': adj_sf[t] - adj_sa[t]}

# ---------- points-per-game model fitted on 2026 conference play
xs = [(rows[t]['conf']['gf'] - rows[t]['conf']['ga']) / max(1, rows[t]['conf']['gp']) for t in B12]
ys = [rows[t]['ppg_conf'] for t in B12]
mx, my = st.mean(xs), st.mean(ys)
b1 = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
b0 = my - b1 * mx
res = [y - (b0 + b1 * x) for x, y in zip(xs, ys)]
se = st.pstdev(res)
r2 = 1 - sum(r * r for r in res) / sum((y - my) ** 2 for y in ys)

clip = lambda v: max(0.15, min(2.85, v))
for t in B12:
    p = proj[t]
    p['proj_gd'] = p['proj_gf'] - p['proj_ga']
    p['proj_ppg'] = clip(b0 + b1 * p['proj_gd'])
    p['exp_ppg_2026'] = clip(b0 + b1 * (p['e_gf'] - p['e_ga']))
    p['ppg_2026'] = rows[t]['ppg_conf']
    p['luck'] = p['ppg_2026'] - p['exp_ppg_2026']
    p['proj_pts11'] = p['proj_ppg'] * 11
    p['lo'], p['hi'] = max(0.1, p['proj_ppg'] - se), min(2.9, p['proj_ppg'] + se)
    p['conf_gp'] = rows[t]['conf_gp']

order = sorted(B12, key=lambda t: -proj[t]['proj_ppg'])
rank26 = sorted(B12, key=lambda t: -rows[t]['ppg_conf'])
for i, t in enumerate(order, 1):
    proj[t]['proj_rank'] = i
    proj[t]['rank_2026'] = rank26.index(t) + 1
    proj[t]['delta_rank'] = proj[t]['rank_2026'] - i
    proj[t]['tier'] = 'Contender' if i <= 5 else ('Middle' if i <= 11 else 'Rebuild')

D['projection'] = {'teams': proj, 'order': order,
                   'model': {'L': L, 'L_CONV': L_CONV, 'L_CONV_A': L_CONV_A, 'b0': b0, 'b1': b1,
                             'se': se, 'r2': r2, 'K': K, 'games': int(n_games)}}
json.dump({'teams': D['projection']['teams'], 'order': D['projection']['order'], 'model': D['projection']['model']}, open(P('projection.json'), 'w'), separators=(',', ':'))

print(f"baseline: {L:.1f} shots/g each way · conversion {L_CONV*100:.1f}% · conceded/opp shot {L_CONV_A*100:.1f}% · {int(n_games)} paired games")
print(f"points model: PPG = {b0:.2f} + {b1:.2f} × GD/g · R²={r2:.2f} · residual sd {se:.2f}")
print(f"{'team':16}{'projPPG':>8}{'range':>11}{'26PPG':>7}{'luck':>7}{'adjSF':>7}{'adjSA':>7}{'projGF':>7}{'projGA':>7}{'26#':>4}{'27#':>4}")
for t in order:
    p = proj[t]
    print(f"{t:16}{p['proj_ppg']:8.2f}{('%.1f-%.1f'%(p['lo'],p['hi'])):>11}{p['ppg_2026']:7.2f}{p['luck']:+7.2f}{p['adj_sf']:7.1f}{p['adj_sa']:7.1f}{p['proj_gf']:7.2f}{p['proj_ga']:7.2f}{p['rank_2026']:4}{p['proj_rank']:4}")
