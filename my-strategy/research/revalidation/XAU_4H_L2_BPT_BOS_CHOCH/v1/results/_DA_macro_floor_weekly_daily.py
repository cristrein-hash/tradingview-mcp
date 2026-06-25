#!/usr/bin/env python3
"""RE-TESTE FIEL — macro-floor no GRAU CERTO (diario D1 + semanal) + vozes ortogonais a snap+sweep (clean_sky,
room-above D1 supply, cascade). ALVO UNICO = runner (mfe_R>=10, uncapped, convexidade). Mede: lift por voz no 276,
flag dos casos-chave (#5826/#5627/#5555/#3949), 2x2 com snap+sweep (incremento ortogonal), preserve-override sobre
conv<=1 (runners_cut DEVE=0), split temporal. Transparencia de selection: TODAS as vozes testadas listadas.
Calibracao 276 (canon, nao gate). Read-only. Verified 2026-06-25."""
import csv, json
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
def load(p, key="bar_idx"):
    out = {}
    for r in csv.DictReader(open(V1 / p)):
        k = r.get(key) or list(r.values())[0]
        try: out[int(float(k))] = r
        except Exception: pass
    return out
TAB = {int(r["b"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_conv_bear_overlap_table.csv"))}
QUAL = load("results/l2_bpt_trade_qualification_matrix.csv")
DSPA = load("results/l2_bpt_dspa_path_features_276.csv")
MBEAR = load("results/l2_bpt_full276_macro_bear_v3_decisions.csv")
SOSIA = load("results/l2_bpt_sosia_clusters.csv")
def fnum(x, d=None):
    try: return float(x)
    except Exception: return d
def fbool(x): return str(x).strip().lower() in ("1", "true", "yes", "t")

rows = []
for b, r in TAB.items():
    q = QUAL.get(b, {}); d = DSPA.get(b, {}); mb = MBEAR.get(b, {}); so = SOSIA.get(b, {})
    why = r["why_low"].split("|") if r["why_low"] else []
    dist_d1 = fnum(q.get("dist_d1_demand_atr")); has_d1 = fbool(q.get("has_d1_demand"))
    dist_d1_sup = fnum(q.get("dist_d1_supply_atr")); wk = fnum(mb.get("weekly_slope"))
    rng1d = fnum(d.get("f5_range_pos_1d")); casc = fnum(so.get("cascade"))
    clean = fbool(mb.get("clean_sky_flag")) or fbool(so.get("clean_sky"))
    rows.append({"b": b, "dt": r["dt"], "regime": r["regime"], "conv": int(r["conv"]),
                 "rm_conv": int(r["rm_conv"]), "rm_bear": int(r["rm_bear"]),
                 "mfe": float(r["mfe"]), "realR": float(r["realR"]), "winner": int(r["winner"]), "runner": int(r["runner"]),
                 "snap": int("snap" not in why), "sweep": int("sweep" not in why),
                 "d1_floor15": int(has_d1 and dist_d1 is not None and dist_d1 <= 1.5),
                 "d1_floor25": int(has_d1 and dist_d1 is not None and dist_d1 <= 2.5),
                 "wk_bull": int(wk is not None and wk > 0),
                 "clean_sky": int(clean),
                 "room_above": int(dist_d1_sup is not None and dist_d1_sup >= 3.0),
                 "low_d1rng": int(rng1d is not None and rng1d <= 0.34),
                 "casc_up": int(casc is not None and casc > 0),
                 "dist_d1": dist_d1, "dist_d1_sup": dist_d1_sup, "wk": wk})
for r in rows:
    r["snap_sweep"] = int(r["snap"] and r["sweep"])
    r["d1floor_wkbull"] = int(r["d1_floor25"] and r["wk_bull"])
    r["d1floor_clean"] = int(r["d1_floor25"] and r["clean_sky"])
R = {r["b"]: r for r in rows}

VOICES = ["snap_sweep", "d1_floor15", "d1_floor25", "wk_bull", "d1floor_wkbull", "clean_sky", "room_above", "low_d1rng", "casc_up", "d1floor_clean"]
base = sum(r["runner"] for r in rows) / len(rows)
print(f"ALVO = runner mfe>=10 | base runner-rate {base:.0%} ({sum(r['runner'] for r in rows)}/{len(rows)}) | vozes testadas={len(VOICES)} (Bonferroni-aware)\n")
print(f"{'voz':>16} | {'n_ON':>4} | {'run_ON':>6} | {'rate':>5} | {'lift':>5} | {'winON':>5}")
for v in VOICES:
    on = [r for r in rows if r[v] == 1]
    rr = sum(x["runner"] for x in on) / max(1, len(on))
    print(f"{v:>16} | {len(on):>4} | {sum(x['runner'] for x in on):>6} | {rr:>4.0%} | {rr/max(0.01,base):>4.2f}x | {sum(x['winner'] for x in on):>5}")

print("\n=== casos-chave (queremos voz ON nos winners #5826/#5627/#3949, OFF no loser #5555) ===")
for b in (5826, 5627, 3949, 5555):
    r = R.get(b)
    if not r: continue
    flags = [v for v in ("d1_floor25", "wk_bull", "clean_sky", "room_above", "low_d1rng", "casc_up", "snap_sweep") if r[v]]
    print(f"  #{b} {'WIN' if r['winner'] else 'LOSS'} mfe={r['mfe']:.1f} distD1dem={r['dist_d1']} distD1sup={r['dist_d1_sup']} wk={r['wk']} | ON: {flags}")

# 2x2: incremento ortogonal sobre snap+sweep (melhor voz nova candidata = clean_sky e d1_floor25)
print("\n=== 2x2 incremento ortogonal sobre snap+sweep (runner-rate) ===")
for v in ("clean_sky", "d1_floor25", "room_above", "wk_bull"):
    for ss in (0, 1):
        sub = [r for r in rows if r["snap_sweep"] == ss]
        on = [r for r in sub if r[v] == 1]; off = [r for r in sub if r[v] == 0]
        ron = sum(x["runner"] for x in on) / max(1, len(on)); roff = sum(x["runner"] for x in off) / max(1, len(off))
        print(f"  snap_sweep={ss} & {v:>11}: ON {ron:.0%}(n{len(on)}) vs OFF {roff:.0%}(n{len(off)})")

# preserve-override: conv<=1 skip EXCETO se voz-preserve (testa clean_sky, d1_floor25, d1floor_clean)
def streak(rs):
    ls = mls = 0
    for r in sorted(rs, key=lambda x: x["dt"]):
        if r["realR"] < 0: ls += 1; mls = max(mls, ls)
        else: ls = 0
    return mls
def rep(name, keepf):
    kept = [r for r in rows if keepf(r)]; removed = [r for r in rows if not keepf(r)]
    n = len(kept)
    print(f"  {name:>32}: n={n} WR={sum(r['winner'] for r in kept)/n:.0%} capR={sum(r['realR'] for r in kept):+.1f} "
          f"sumMFE={sum(r['mfe'] for r in kept):+.0f} streak={streak(kept)} | rm={len(removed)} RUN_cut={sum(r['runner'] for r in removed)} win_cut={sum(r['winner'] for r in removed)}")
print("\n=== preserve-override sobre conv<=1 (ALVO: RUN_cut=0, resgatar winners nao losers) ===")
rep("BASELINE", lambda r: True)
rep("conv<=1 puro", lambda r: r["rm_conv"] == 0)
for pv in ("clean_sky", "d1_floor25", "d1floor_clean", "room_above"):
    rep(f"conv<=1 EXC {pv}", lambda r, pv=pv: not (r["rm_conv"] == 1 and r[pv] == 0))

# split temporal p/ a melhor preserve (definida por lift+ortogonalidade observada)
print("\n=== split temporal (build<2023 / holdout>=2023) p/ conv<=1 EXC clean_sky ===")
for lab, c in (("BUILD", lambda d: d < "2023"), ("HOLDOUT", lambda d: d >= "2023")):
    sub = [r for r in rows if c(r["dt"])]
    kept = [r for r in sub if not (r["rm_conv"] == 1 and r["clean_sky"] == 0)]
    rm = [r for r in sub if r["rm_conv"] == 1 and r["clean_sky"] == 0]
    print(f"  {lab}: base n={len(sub)} capR={sum(r['realR'] for r in sub):+.1f} streak={streak(sub)} -> "
          f"refinada n={len(kept)} WR={sum(r['winner'] for r in kept)/len(kept):.0%} capR={sum(r['realR'] for r in kept):+.1f} "
          f"streak={streak(kept)} RUN_cut={sum(r['runner'] for r in rm)} win_cut={sum(r['winner'] for r in rm)}")
print("\nCalibracao 276 (canon). Vozes search-selected -> Bonferroni; arbitro=runner mfe>=10; capR so contexto.")
