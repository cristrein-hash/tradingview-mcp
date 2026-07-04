#!/usr/bin/env python3
"""
LAB B r2 - DA-PRE adversarial cross-check (2026-07-04).
Cruza as lentes propostas pelas 4 perspectivas sobre os MESMOS 435 trades:
  - overlap real (Jaccard / membros compartilhados) da familia "fundo"
  - runner-kill cruzado com o mapa do runnerpres
  - painel da UNIAO das SKIPs propostas (o que o orquestrador veria se aceitasse tudo)
  - per-year dos flagged de cada lente (assimetria honesta)
  - null episode-aware (semana) para a uniao e para cada lente
Multi-fatorial (lentes de 4 perspectivas), trajetoria (features causais do builder),
dois objetivos (dano dos flagged E runners preservados), validacao por null episode-aware.
NUNCA commita. Leitura-apenas do jsonl canonico + feats do regimebox.
"""
import json, random
from collections import defaultdict

RES = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results"
rows = [json.loads(l) for l in open(f"{RES}/lab_g_candidates.jsonl")]
base = [r for r in rows if r.get("g_in_base435") == 1 and r.get("g_v5h") != "BEAR"]
assert len(base) == 435

def net(r): return r["g_R"] - 0.80 / r["g_risk"]
def is_run(r): return r["g_R"] >= 3

# join regimebox feats by cj_t
feats = json.load(open(f"{RES}/_labB_r2_regime_box_feats.json"))
if isinstance(feats, dict):
    feats = feats.get("feats", feats.get("rows", list(feats.values())[0] if len(feats)==1 else feats))
fmap = {f["cj_t"]: f for f in feats}
joined = sum(1 for r in base if r["cj_t"] in fmap)
print(f"regimebox feats join: {joined}/435")

# ---- streakdd conv lenses (replicated exactly from spec) ----
def conv_count(r):
    c = 0
    if r["n_supply_overhead"] >= 41: c += 1                                  # A_SUPPLY
    if r["clean_sky_atr"] <= 0.08: c += 1                                    # B_SKY
    if r["legpos60"] >= 0.653 and r["legpos90"] >= 0.721: c += 1             # C_LEGTOP
    if r["g_box96"] >= 0.907 and r["g_box480"] >= 0.945: c += 1              # D_BOXTOP
    if (r["h1n_clean_sky_atr"] <= 0.39 and r["h4n_clean_sky_atr"] <= 0.17): c += 1  # E_HTFCEIL
    if r["g_ema21_dist"] >= 1.4 and r["g_ema50_dist"] >= 2.42: c += 1        # F_EXT
    return c

LENSES = {
    "E2_struct":  lambda r: r["legpos60"] <= 0.25 and r["h1_pos"] <= 0.61,
    "CAL8_runp":  lambda r: r["legpos60"] < 0.249 and r["g_ema21_dist"] < 0.16,
    "CONV1_runp": lambda r: r["clean_sky_atr"] <= 0.05 and r["n_supply_overhead"] >= 48,
    "CAL5_runp":  lambda r: r["legpos60"] < 0.249,
    "DEADMID_stk":lambda r: conv_count(r) == 0 and r["g_ema50_dist"] <= 0.94 and r["h1_pos"] <= 0.82,
    "RBSKIP1_rb": lambda r: (lambda f: f is not None and f["v5h"] == "BULL"
                    and f.get("prev_hi_dist_atr") is not None
                    and -10 < f["prev_hi_dist_atr"] <= -2
                    and (r["n_supply_overhead"] >= 16 or (f.get("rbox_age_h") is not None and 178 < f["rbox_age_h"] <= 415))
                   )(fmap.get(r["cj_t"])),
}

flag = {k: [bool(fn(r)) for r in base] for k, fn in LENSES.items()}
nets = [net(r) for r in base]
runs = [is_run(r) for r in base]
yrs  = [str(r.get("g_week"))[:4] for r in base]
wks  = [r.get("g_week") for r in base]

print("\n== PER-LENS (flagged stats + per-year) ==")
for k, fl in flag.items():
    idx = [i for i, f in enumerate(fl) if f]
    n = len(idx); s = sum(nets[i] for i in idx); rk = sum(1 for i in idx if runs[i])
    py = defaultdict(float)
    for i in idx: py[yrs[i]] += nets[i]
    print(f"{k:12s} cov={n:3d} flagSum={s:+7.1f} runKill={rk} perYear={{" +
          ", ".join(f"{y}:{v:+.1f}" for y, v in sorted(py.items())) + "}")

print("\n== PAIRWISE OVERLAP (shared / jaccard) ==")
ks = list(LENSES)
for i in range(len(ks)):
    for j in range(i + 1, len(ks)):
        a = {x for x, f in enumerate(flag[ks[i]]) if f}
        b = {x for x, f in enumerate(flag[ks[j]]) if f}
        inter = len(a & b); uni = len(a | b)
        print(f"{ks[i]:12s} x {ks[j]:12s} shared={inter:3d} jacc={inter/uni if uni else 0:.2f}")

# ---- panel helper ----
def panel(keep_idx, label):
    ns = [nets[i] for i in keep_idx]
    eq = 0.0; peak = 0.0; dd = 0.0
    stk = 0; worst_stk = 0
    for v in ns:
        eq += v; peak = max(peak, eq); dd = min(dd, eq - peak)
        stk = stk + 1 if v < 0 else 0
        worst_stk = max(worst_stk, stk)
    rk = sum(1 for i in keep_idx if runs[i])
    py = defaultdict(float)
    for i in keep_idx: py[yrs[i]] += nets[i]
    wr = 100 * sum(1 for v in ns if v > 0) / len(ns)
    print(f"{label:28s} N={len(ns)} WR={wr:.1f} sum={eq:+.1f} avg={eq/len(ns):+.3f} "
          f"DD={dd:+.1f} r/DD={eq/abs(dd) if dd else 0:.1f} stk=-{worst_stk} run={rk} "
          f"perYear={{" + ", ".join(f"{y}:{v:+.1f}" for y, v in sorted(py.items())) + "}")
    return dict(sum=eq, dd=dd, stk=worst_stk, run=rk)

print("\n== PANELS ==")
allidx = list(range(435))
panel(allidx, "BASELINE")
union_skip = {i for k in ("E2_struct", "CAL8_runp", "CONV1_runp", "RBSKIP1_rb") for i, f in enumerate(flag[k]) if f}
print(f"\nUNION of proposed SKIPs (E2|CAL8|CONV1|RBSKIP1): {len(union_skip)} trades")
p_union = panel([i for i in allidx if i not in union_skip], "SKIP UNION(4 lenses)")
for k in ("E2_struct", "CAL8_runp", "CONV1_runp", "RBSKIP1_rb", "DEADMID_stk"):
    rm = {i for i, f in enumerate(flag[k]) if f}
    panel([i for i in allidx if i not in rm], f"SKIP {k} only")

# fundo-family core overlap: E2 vs CAL8 vs DEADMID
a = {i for i, f in enumerate(flag["E2_struct"]) if f}
b = {i for i, f in enumerate(flag["CAL8_runp"]) if f}
c = {i for i, f in enumerate(flag["DEADMID_stk"]) if f}
print(f"\nFUNDO family: |E2|={len(a)} |CAL8|={len(b)} |DEADMID|={len(c)} "
      f"E2&CAL8={len(a&b)} E2&DEAD={len(a&c)} CAL8&DEAD={len(b&c)} triple={len(a&b&c)} union={len(a|b|c)}")
tf = a | b | c
s = sum(nets[i] for i in tf); rk = sum(1 for i in tf if runs[i])
py = defaultdict(float)
for i in tf: py[yrs[i]] += nets[i]
print(f"FUNDO union flagged: n={len(tf)} sum={s:+.1f} runKill={rk} perYear=" +
      str({y: round(v, 1) for y, v in sorted(py.items())}))

# ---- episode(week)-aware null: random skip of same #weeks-worth of trades ----
def week_null(target_idx, label, iters=2000):
    tgt = set(target_idx)
    n_t = len(tgt)
    base_p = panel_quiet(allidx)
    real = panel_quiet([i for i in allidx if i not in tgt])
    wk_groups = defaultdict(list)
    for i, w in enumerate(wks): wk_groups[w].append(i)
    weeks = list(wk_groups)
    rng = random.Random(42)
    beat = 0; valid = 0
    for _ in range(iters):
        # sample whole weeks until >= n_t trades, then trim randomly to n_t
        rng.shuffle(weeks)
        pick = []
        for w in weeks:
            pick += wk_groups[w]
            if len(pick) >= n_t: break
        pick = set(rng.sample(pick, n_t))
        pn = panel_quiet([i for i in allidx if i not in pick])
        valid += 1
        if pn["sum"] >= real["sum"] and pn["dd"] >= real["dd"] and pn["stk"] <= real["stk"] and pn["run"] >= real["run"]:
            beat += 1
    print(f"NULL(week-aware,{iters}) {label}: P(random >= real on sum&DD&stk&run) = {beat/valid:.4f}")

def panel_quiet(keep_idx):
    eq = 0.0; peak = 0.0; dd = 0.0; stk = 0; ws = 0
    for i in keep_idx:
        v = nets[i]; eq += v; peak = max(peak, eq); dd = min(dd, eq - peak)
        stk = stk + 1 if v < 0 else 0; ws = max(ws, stk)
    return dict(sum=eq, dd=dd, stk=ws, run=sum(1 for i in keep_idx if runs[i]))

print("\n== EPISODE-AWARE NULLS ==")
week_null(sorted({i for i, f in enumerate(flag["E2_struct"]) if f}), "E2_struct")
week_null(sorted({i for i, f in enumerate(flag["CAL8_runp"]) if f}), "CAL8_runp")
week_null(sorted({i for i, f in enumerate(flag["RBSKIP1_rb"]) if f}), "RBSKIP1_rb")
week_null(sorted(union_skip), "UNION4")
