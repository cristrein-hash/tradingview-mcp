#!/usr/bin/env python3
"""
_engine_liquidity_structure.py

Lente liquidez/estrutura sobre entry_dataset.jsonl (RECLAIM model).
Procura GATILHOS CAUSAIS (features no bar do reclaim) que selecionem subconjuntos
com avgR e WR maiores, estaveis nos 3 anos (2024/2025/2026), n>=30, mais perto do
pivo que a confirmacao 8ATR.

Features-lente: sweep_depth_atr, reclaim_speed, leg_ext, room_atr, low_wick, low_closepos
+ confluencia: macro_bull/bear, nas_*, rsi_low, dist_ema_atr, sell/buy bubbles.

REGRAS DURAS:
- features ja causais. NUNCA usar near_M8/R_reclaim/R_8atr/held8/runner como FEATURE.
- alvo = R_reclaim (let-run, SL estrutural).
- robust = avgR>base nos 3 anos E n>=30 E nao-carregada-por-2-trades (ex-top2 ainda > base).
"""
import json, itertools
from collections import defaultdict

BASE_AVGR = 0.727
ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]
# alvo presente em todos (R_reclaim nunca null aqui)
for r in ROWS:
    assert r['R_reclaim'] is not None

YEARS = (2024, 2025, 2026)

def stats(rows):
    n = len(rows)
    if n == 0:
        return None
    Rs = [r['R_reclaim'] for r in rows]
    avg = sum(Rs)/n
    wr = sum(1 for x in Rs if x > 0)/n*100
    runner = sum(1 for x in Rs if x >= 5)/n*100
    nearm8 = sum(r['near_M8'] for r in rows)/n*100
    by = {}
    for y in YEARS:
        sub = [r['R_reclaim'] for r in rows if r['yr'] == y]
        if sub:
            by[y] = (len(sub), round(sum(sub)/len(sub), 3), round(sum(1 for x in sub if x>0)/len(sub)*100,1))
        else:
            by[y] = (0, None, None)
    return dict(n=n, avgR=round(avg,3), WR=round(wr,1), runner=round(runner,1),
               nearM8=round(nearm8,1), by=by, Rs=Rs)

def ex_top2(rows):
    """avgR removendo as 2 maiores R — testa carregamento."""
    Rs = sorted((r['R_reclaim'] for r in rows), reverse=True)
    if len(Rs) <= 2:
        return None
    rest = Rs[2:]
    return round(sum(rest)/len(rest), 3)

def robust(s):
    if s is None or s['n'] < 30:
        return False
    # mesmo sinal (avgR > base) nos 3 anos, exigindo cada ano ter n>=8 p/ nao ser vazio
    for y in YEARS:
        ny, ay, wy = s['by'][y]
        if ny < 8:
            return False
        if ay is None or ay <= BASE_AVGR:
            return False
    # nao carregada por 2 trades
    et2 = ex_top2_from_stats(s)
    if et2 is None or et2 <= BASE_AVGR:
        return False
    return True

def ex_top2_from_stats(s):
    Rs = sorted(s['Rs'], reverse=True)
    if len(Rs) <= 2:
        return None
    rest = Rs[2:]
    return round(sum(rest)/len(rest), 3)

def fmt(name, s):
    if s is None:
        print(f"{name}: EMPTY")
        return
    et2 = ex_top2_from_stats(s)
    by = s['by']
    rb = robust(s)
    print(f"\n=== {name} ===")
    print(f"  n={s['n']} WR={s['WR']}% avgR={s['avgR']} lift={round(s['avgR']-BASE_AVGR,3)} runner={s['runner']}% nearM8={s['nearM8']}%")
    print(f"  y24={by[2024]}  y25={by[2025]}  y26={by[2026]}")
    print(f"  ex_top2_avgR={et2}  ROBUST={rb}")
    return s, rb

def F(pred):
    return [r for r in ROWS if pred(r)]

print(f"BASE: n={len(ROWS)} avgR={BASE_AVGR} ", stats(ROWS)['WR'], "WR; runner", stats(ROWS)['runner'])

# ---------------------------------------------------------------------------
# PHASE 1: single-feature sweeps (monotonic threshold scan) — lente liquidez
# ---------------------------------------------------------------------------
print("\n########## PHASE 1: single-feature threshold scans ##########")

def scan(feat, thresholds, direction):
    """direction '>=' or '<=' """
    print(f"\n--- {feat} {direction} ---")
    best = None
    for t in thresholds:
        if direction == '>=':
            rows = [r for r in ROWS if r.get(feat) is not None and r[feat] >= t]
        else:
            rows = [r for r in ROWS if r.get(feat) is not None and r[feat] <= t]
        s = stats(rows)
        if s is None or s['n'] < 30:
            continue
        rb = robust(s)
        tag = " *ROBUST*" if rb else ""
        print(f"  {feat}{direction}{t}: n={s['n']} WR={s['WR']} avgR={s['avgR']} (lift {round(s['avgR']-BASE_AVGR,3)}) y={[s['by'][y][1] for y in YEARS]}{tag}")
        if rb and (best is None or s['avgR'] > best['avgR']):
            best = s
    return best

scan('sweep_depth_atr', [0.5,0.75,1.0,1.25,1.5,2.0], '>=')
scan('reclaim_speed', [1,2,3], '<=')
scan('leg_ext', [0.3,0.4,0.5,0.6,0.75], '<=')
scan('leg_ext', [0.3,0.4,0.5], '>=')
scan('room_atr', [1.5,2.0,2.5,3.0,4.0], '>=')
scan('low_wick', [0.2,0.3,0.4,0.5], '>=')
scan('low_closepos', [0.5,0.6,0.65,0.7], '>=')
scan('rsi_low', [25,30,35,40], '<=')
scan('dist_ema_atr', [-1.0,-0.5,0.0,0.5,1.0], '<=')
scan('macro_drop_atr', [3,4,5,6], '>=')
scan('disp4_atr', [0.5,1.0,1.5], '>=')

# ---------------------------------------------------------------------------
# PHASE 2: confluence (lente liquidez/estrutura) — combinacoes pequenas
# ---------------------------------------------------------------------------
print("\n########## PHASE 2: confluence combos ##########")

combos = {
 # sweep + reclaim rapido + rejeicao na vela + espaco
 "sweep>=0.75 & speed<=2 & lowwick>=0.3":
    lambda r: r['sweep_depth_atr']>=0.75 and r['reclaim_speed']<=2 and r['low_wick']>=0.3,
 "sweep>=1.0 & speed<=2":
    lambda r: r['sweep_depth_atr']>=1.0 and r['reclaim_speed']<=2,
 "sweep>=0.75 & room>=2.5":
    lambda r: r['sweep_depth_atr']>=0.75 and r['room_atr']>=2.5,
 "sweep>=0.75 & lowclosepos>=0.6":
    lambda r: r['sweep_depth_atr']>=0.75 and r['low_closepos']>=0.6,
 "sweep>=1.0 & lowwick>=0.3 & room>=2.0":
    lambda r: r['sweep_depth_atr']>=1.0 and r['low_wick']>=0.3 and r['room_atr']>=2.0,
 "sweep>=0.75 & macro_bull":
    lambda r: r['sweep_depth_atr']>=0.75 and r['macro_bull']==1,
 "sweep>=0.75 & nas_long_48>=1":
    lambda r: r['sweep_depth_atr']>=0.75 and r['nas_long_48']>=1,
 "sweep>=0.75 & rsi_low<=35":
    lambda r: r['sweep_depth_atr']>=0.75 and r['rsi_low']<=35,
 "sweep>=0.75 & speed<=2 & room>=2.0":
    lambda r: r['sweep_depth_atr']>=0.75 and r['reclaim_speed']<=2 and r['room_atr']>=2.0,
 "deep sweep>=1.25 & lowclosepos>=0.55":
    lambda r: r['sweep_depth_atr']>=1.25 and r['low_closepos']>=0.55,
 "sweep>=0.75 & lowwick>=0.3 & lowclosepos>=0.55 & room>=2.0 (full lens)":
    lambda r: r['sweep_depth_atr']>=0.75 and r['low_wick']>=0.3 and r['low_closepos']>=0.55 and r['room_atr']>=2.0,
 "buy_bubble & sweep>=0.5":
    lambda r: (r['buy_S']+r['buy_M']+r['buy_L'])>=1 and r['sweep_depth_atr']>=0.5,
 "smc_choch>=1 & sweep>=0.75":
    lambda r: r['smc_choch']>=1 and r['sweep_depth_atr']>=0.75,
}

results = {}
for name, pred in combos.items():
    s = stats(F(pred))
    out = fmt(name, s)
    if out:
        results[name] = out

# ---------------------------------------------------------------------------
# PHASE 3: auto-grid search over lens features (2-feature) keep robust
# ---------------------------------------------------------------------------
print("\n########## PHASE 3: auto 2-feature grid (lens) ##########")
grid = {
 'sweep_depth_atr': ('>=', [0.5,0.75,1.0,1.25]),
 'room_atr': ('>=', [1.5,2.0,2.5,3.0]),
 'low_wick': ('>=', [0.2,0.3,0.4]),
 'low_closepos': ('>=', [0.5,0.55,0.6]),
 'reclaim_speed': ('<=', [1,2]),
 'leg_ext': ('<=', [0.4,0.5,0.6]),
}
def mk(feat, d, t):
    if d=='>=':
        return lambda r,f=feat,tt=t: r.get(f) is not None and r[f]>=tt
    return lambda r,f=feat,tt=t: r.get(f) is not None and r[f]<=tt

feats=list(grid.keys())
robust_hits=[]
for a,b in itertools.combinations(feats,2):
    da,ta = grid[a]; db,tb = grid[b]
    for va in ta:
        for vb in tb:
            pa=mk(a,da,va); pb=mk(b,db,vb)
            rows=[r for r in ROWS if pa(r) and pb(r)]
            s=stats(rows)
            if s and robust(s):
                desc=f"{a}{da}{va} & {b}{db}{vb}"
                robust_hits.append((s['avgR'], desc, s))

robust_hits.sort(reverse=True, key=lambda x:x[0])
print(f"\n{len(robust_hits)} robust 2-feature combos. Top 12:")
for avg,desc,s in robust_hits[:12]:
    et2=ex_top2_from_stats(s)
    print(f"  avgR={avg} n={s['n']} WR={s['WR']} y={[s['by'][y][1] for y in YEARS]} ex2={et2}  | {desc}")

# ---------------------------------------------------------------------------
# PHASE 4: deep-dive on dist_ema_atr (the discount/position axis) + lens add-ons
# ---------------------------------------------------------------------------
print("\n########## PHASE 4: dist_ema_atr deep dive ##########")
scan('dist_ema_atr', [-2.5,-2.0,-1.75,-1.5,-1.25,-1.0,-0.75], '<=')

print("\n--- lens add-ons ON TOP of dist_ema_atr<=-1.0 ---")
addons = {
 "base dist<=-1.0": lambda r: r['dist_ema_atr']<=-1.0,
 "dist<=-1.0 & sweep>=0.75": lambda r: r['dist_ema_atr']<=-1.0 and r['sweep_depth_atr']>=0.75,
 "dist<=-1.0 & sweep>=1.0": lambda r: r['dist_ema_atr']<=-1.0 and r['sweep_depth_atr']>=1.0,
 "dist<=-1.0 & low_wick>=0.3": lambda r: r['dist_ema_atr']<=-1.0 and r['low_wick']>=0.3,
 "dist<=-1.0 & room>=2.0": lambda r: r['dist_ema_atr']<=-1.0 and r['room_atr']>=2.0,
 "dist<=-1.0 & low_closepos>=0.55": lambda r: r['dist_ema_atr']<=-1.0 and r['low_closepos']>=0.55,
 "dist<=-1.0 & reclaim_speed<=1": lambda r: r['dist_ema_atr']<=-1.0 and r['reclaim_speed']<=1,
 "dist<=-1.0 & leg_ext>=0.3": lambda r: r['dist_ema_atr']<=-1.0 and r['leg_ext']>=0.3,
 "dist<=-1.0 & macro_bull": lambda r: r['dist_ema_atr']<=-1.0 and r['macro_bull']==1,
 "dist<=-1.0 & not macro_bear": lambda r: r['dist_ema_atr']<=-1.0 and r['macro_bear']==0,
 "dist<=-1.0 & ema_slope>=0": lambda r: r['dist_ema_atr']<=-1.0 and r['ema_slope_atr']>=0,
 "dist<=-1.0 & buy_bubble": lambda r: r['dist_ema_atr']<=-1.0 and (r['buy_S']+r['buy_M']+r['buy_L'])>=1,
 "dist<=-1.0 & smc_choch>=1": lambda r: r['dist_ema_atr']<=-1.0 and r['smc_choch']>=1,
 "dist<=-1.0 & rsi_low>30 (not exhausted)": lambda r: r['dist_ema_atr']<=-1.0 and r['rsi_low']>30,
 "dist<=-1.0 & low_wick>=0.3 & room>=2.0": lambda r: r['dist_ema_atr']<=-1.0 and r['low_wick']>=0.3 and r['room_atr']>=2.0,
 "dist<=-1.5 & low_wick>=0.3": lambda r: r['dist_ema_atr']<=-1.5 and r['low_wick']>=0.3,
}
for name,pred in addons.items():
    fmt(name, stats(F(pred)))

# Did dist<=-1.0 just inherit base? check the COMPLEMENT (dist>-1.0)
print("\n--- complement check ---")
fmt("dist_ema_atr > -1.0 (complement)", stats(F(lambda r: r['dist_ema_atr']>-1.0)))
fmt("dist_ema_atr > 1.0 (extended ABOVE ema)", stats(F(lambda r: r['dist_ema_atr']>1.0)))

print("\n########## DONE ##########")
