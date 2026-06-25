#!/usr/bin/env python3
"""TESTE DECISIVO — voz MACRO-FLOOR (piso de demanda macro / origem da pernada bull, tese do Cris print 03.14.23)
vs snap+sweep, como separador de winner-vs-loser. (1) grupo F dump; (2) separacao de vozes no grupo F; (3) lift no
corpus 276 (runner mfe>=10 vs resto); (4) PRESERVE-override: conv<=1 skip EXCETO se macro_floor — runners/winners
cortados, WR, sumR, streak vs baseline e vs conv<=1 puro; (5) split temporal build(2020-22)/holdout(2023-26).
Causal as-of-entry (features ja causais). Calibracao 276 (canon, nao gate). Read-only. Verified 2026-06-25."""
import csv, json
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
TAB = {int(r["b"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_conv_bear_overlap_table.csv"))}
QUAL = {int(float(r["bar_idx"])): r for r in csv.DictReader(open(V1 / "results/l2_bpt_trade_qualification_matrix.csv")) if r.get("bar_idx")}
DSPA = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_dspa_path_features_276.csv")) if r.get("bar_idx")}

def fnum(x, d=None):
    try: return float(x)
    except Exception: return d
def fbool(x):
    return str(x).strip().lower() in ("1", "true", "yes", "t")

# enrich spine com features de piso macro
rows = []
for b, r in TAB.items():
    q = QUAL.get(b, {}); d = DSPA.get(b, {})
    dist_dem = fnum(q.get("dist_4h_demand_low_atr"))
    dem_origin = fbool(q.get("demand_origin_of_leg"))
    rng1d = fnum(d.get("f5_range_pos_1d"))
    sweep = "sweep" not in (r["why_low"].split("|") if r["why_low"] else [])
    snap = "snap" not in (r["why_low"].split("|") if r["why_low"] else [])
    near_dem = (dist_dem is not None and dist_dem <= 1.0)
    low_rng = (rng1d is not None and rng1d <= 0.34)
    macro_floor = bool(dem_origin or near_dem)            # "nasceu no piso de demanda / origem da perna"
    rows.append({"b": int(r["b"]), "dt": r["dt"], "conv": int(r["conv"]), "regime": r["regime"],
                 "rm_conv": int(r["rm_conv"]), "rm_bear": int(r["rm_bear"]), "rm_blr": int(r["rm_blr"]),
                 "mfe": float(r["mfe"]), "realR": float(r["realR"]), "winner": int(r["winner"]), "runner": int(r["runner"]),
                 "snap": int(snap), "sweep": int(sweep), "snap_sweep": int(snap and sweep),
                 "dist_dem": dist_dem, "dem_origin": int(dem_origin), "near_dem": int(near_dem),
                 "low_rng": int(low_rng), "macro_floor": int(macro_floor), "floor_sweep": int(macro_floor and sweep)})
R = {r["b"]: r for r in rows}

print(f"cobertura: qual={sum(1 for r in rows if R[r['b']]['dist_dem'] is not None)}/{len(rows)}\n")
# (1)(2) GRUPO F dump + separacao
F = [r for r in rows if r["rm_bear"] == 1 and r["rm_conv"] == 0]
print(f"=== GRUPO F (BEAR\\conv, n={len(F)}) — winner vs loser por feature ===")
print(f"{'#':>5} {'res':>4} {'realR':>6} {'mfe':>6} {'snap':>4} {'swp':>3} {'distDem':>7} {'demOrig':>7} {'lowRng':>6} {'MFLOOR':>6}")
for r in sorted(F, key=lambda x: -x["realR"]):
    print(f"{r['b']:>5} {'WIN' if r['winner'] else 'LOSS':>4} {r['realR']:>+6.1f} {r['mfe']:>6.1f} {r['snap']:>4} {r['sweep']:>3} "
          f"{(r['dist_dem'] if r['dist_dem'] is not None else -1):>7.2f} {r['dem_origin']:>7} {r['low_rng']:>6} {r['macro_floor']:>6}")
# #5627 (∩BEAR winner que Cris quer resgatar) + #5555 (contra-exemplo)
print("\nreferencias-chave:")
for b in (5627, 5555, 5826):
    r = R.get(b)
    if r: print(f"  #{b} {'WIN' if r['winner'] else 'LOSS'} realR={r['realR']:+.1f} mfe={r['mfe']:.1f} snap={r['snap']} sweep={r['sweep']} distDem={r['dist_dem']} demOrigin={r['dem_origin']} MACRO_FLOOR={r['macro_floor']}")

def sep_on(group, voice, name):
    on = [r for r in group if r[voice] == 1]; off = [r for r in group if r[voice] == 0]
    won = sum(x["winner"] for x in on); woff = sum(x["winner"] for x in off)
    print(f"  {name:>12}: ON {won}/{len(on)} win  | OFF {woff}/{len(off)} win")

print("\n=== separacao no GRUPO F (queremos ON pega winners, OFF pega losers) ===")
for v, n in (("snap_sweep", "snap+sweep"), ("macro_floor", "macro_floor"), ("floor_sweep", "floor+sweep"), ("near_dem", "near_dem"), ("dem_origin", "dem_origin"), ("low_rng", "low_rng")):
    sep_on(F, v, n)

# (3) lift no corpus 276: runner-rate por voz
print("\n=== LIFT no corpus 276 (runner mfe>=10) ===")
base = sum(r["runner"] for r in rows) / len(rows)
print(f"base runner-rate = {base:.0%} ({sum(r['runner'] for r in rows)}/{len(rows)})")
for v, n in (("snap_sweep", "snap+sweep"), ("macro_floor", "macro_floor"), ("floor_sweep", "floor+sweep"), ("near_dem", "near_dem"), ("dem_origin", "dem_origin")):
    on = [r for r in rows if r[v] == 1]
    rr = sum(x["runner"] for x in on) / max(1, len(on))
    print(f"  {n:>12}: ON runner-rate {rr:.0%} (n={len(on)}) lift {rr/max(0.01,base):.2f}x | winners ON {sum(x['winner'] for x in on)}")

# (4) regra refinada: conv<=1 skip EXCETO se macro_floor (preserve override)
def streak(rs):
    ls = mls = 0
    for r in sorted(rs, key=lambda x: x["dt"]):
        if r["realR"] < 0: ls += 1; mls = max(mls, ls)
        else: ls = 0
    return mls
def report(kept, removed, name):
    n = len(kept)
    if n == 0: print(f"  {name:>34}: (vazio)"); return
    w = sum(r["winner"] for r in kept); sr = sum(r["realR"] for r in kept); smfe = sum(r["mfe"] for r in kept)
    rc = sum(r["runner"] for r in removed); wc = sum(r["winner"] for r in removed)
    # ARBITRO = runners preservados (mfe>=10 uncapped); capR so contexto (hit-rate)
    print(f"  {name:>34}: n={n} WR={w/n:.0%} capR={sr:+.1f} sumMFE(uncap)={smfe:+.0f} streak={streak(kept)} | rm={len(removed)} RUNNERS_cut={rc} winners_cut={wc}")

print("\n=== IMPACTO NOS 276 (exit OFICIAL capado) ===")
report(rows, [], "BASELINE (sem skip)")
rm_conv = [r for r in rows if r["rm_conv"] == 1]
report([r for r in rows if r["rm_conv"] == 0], rm_conv, "conv<=1 (puro)")
rm_ref = [r for r in rows if r["rm_conv"] == 1 and r["macro_floor"] == 0]   # skip conv MAS preserva piso macro
report([r for r in rows if not (r["rm_conv"] == 1 and r["macro_floor"] == 0)], rm_ref, "conv<=1 EXCETO macro_floor")
resgatados = [r for r in rows if r["rm_conv"] == 1 and r["macro_floor"] == 1]
print(f"  -> resgatados pelo macro_floor (conv cortava, agora preserva): {[(r['b'], 'W' if r['winner'] else 'L', round(r['realR'],1)) for r in sorted(resgatados, key=lambda x: x['dt'])]}")

# (5) split temporal build/holdout p/ a regra refinada
print("\n=== SPLIT TEMPORAL (build 2020-22 / holdout 2023-26) — regra conv<=1 EXCETO macro_floor ===")
for lab, cond in (("BUILD 2020-22", lambda d: d < "2023"), ("HOLDOUT 2023-26", lambda d: d >= "2023")):
    sub = [r for r in rows if cond(r["dt"])]
    rm = [r for r in sub if r["rm_conv"] == 1 and r["macro_floor"] == 0]
    kept = [r for r in sub if not (r["rm_conv"] == 1 and r["macro_floor"] == 0)]
    base_sr = sum(r["realR"] for r in sub); base_w = sum(r["winner"] for r in sub)
    print(f"  {lab}: base n={len(sub)} WR={base_w/len(sub):.0%} sumR={base_sr:+.1f} streak={streak(sub)} "
          f"-> refinada n={len(kept)} WR={sum(r['winner'] for r in kept)/len(kept):.0%} sumR={sum(r['realR'] for r in kept):+.1f} "
          f"streak={streak(kept)} | runners_cut={sum(r['runner'] for r in rm)} winners_cut={sum(r['winner'] for r in rm)}")

# salva tabela enriquecida (base candidata mais limpa)
with open(V1 / "results/l2_bpt_macro_floor_table.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("\ntabela enriquecida -> results/l2_bpt_macro_floor_table.csv. Calibracao 276, nao gate.")
