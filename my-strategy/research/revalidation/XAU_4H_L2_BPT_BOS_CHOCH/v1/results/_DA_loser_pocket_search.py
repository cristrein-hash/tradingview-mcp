#!/usr/bin/env python3
"""LINHA A — busca de bolsões de PURO LOSER nos 214 da base aprovada (régua oficial let-run), p/ WR 50%.
Bateria de condições CAUSAIS estruturalmente motivadas, ortogonais a conv≤1/bear_leg (já aplicados). Restrição DURA:
condição usável = flaga 0 winners E 0 runners. Reporta purity por condição + Bonferroni-aware (N testadas). Empilha
as usáveis. Calibracao 276 — 0-winner em calibração NÃO é prova; precisa validar. Verified 2026-06-25."""
import csv, json
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
COST = 0.35
REG = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_regua_structural.csv"))}
TAB = {int(r["b"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_conv_bear_overlap_table.csv"))}
def load(p):
    out = {}
    for r in csv.DictReader(open(V1 / p)):
        k = r.get("bar_idx") or list(r.values())[0]
        try: out[int(float(k))] = r
        except Exception: pass
    return out
QUAL = load("results/l2_bpt_trade_qualification_matrix.csv")
DSPA = load("results/l2_bpt_dspa_path_features_276.csv")
MB = load("results/l2_bpt_full276_macro_bear_v3_decisions.csv")
SOSIA = load("results/l2_bpt_sosia_clusters.csv")
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
def fn(x, d=None):
    try: return float(x)
    except Exception: return d
def fb(x): return str(x).strip().lower() in ("1", "true", "yes", "t")

# BASE = 214 (não cortados pela camada) e traded
base = []
for b in REG:
    t = TAB.get(b, {})
    if t.get("rm_conv") == "1" or t.get("rm_blr") == "1": continue   # já cortado
    lr = fn(REG[b]["letrun_struct"], 0.0); q = QUAL.get(b, {}); d = DSPA.get(b, {}); mb = MB.get(b, {}); so = SOSIA.get(b, {})
    base.append({"b": b, "net": lr - COST, "letrun": lr, "winner": lr - COST > 0, "runner": lr >= 5,
        "dist_d1_sup": fn(q.get("dist_d1_supply_atr")), "dist_4h_sup": fn(q.get("dist_4h_supply_low_atr")),
        "has_4h_sup": fb(q.get("has_4h_supply_overhead")), "dist_d1_dem": fn(q.get("dist_d1_demand_atr")),
        "clean_sky": fb(mb.get("clean_sky_flag")) or fb(so.get("clean_sky")), "wk": fn(mb.get("weekly_slope")),
        "casc": fn(so.get("cascade")), "rng1d": fn(d.get("f5_range_pos_1d")), "f6_below": fb(d.get("f6_below_value")),
        "f3_break": fb(d.get("f3_breaks_support")), "f3_state": d.get("f3_acceptance_state"),
        "f2_consec": fn(d.get("f2_consec_down")), "rsi": fn(F[b].get("rsi")), "sup_rej": fb(q.get("supply_rejected_before"))})
nB = len(base); nW = sum(1 for r in base if r["winner"]); nL = nB - nW; nRun = sum(1 for r in base if r["runner"])
print(f"BASE 214: trades={nB} winners={nW} losers={nL} runners={nRun} WR={100*nW/nB:.1f}%")
print(f"alvo: cortar losers p/ WR 50% (losers<= {nW}) → precisa cortar {nL-nW} losers com 0 winner/runner\n")

CONDS = {
    "capped_under_4Hsupply(<1.5)": lambda r: r["has_4h_sup"] and r["dist_4h_sup"] is not None and r["dist_4h_sup"] < 1.5,
    "under_D1supply(<1.5)": lambda r: r["dist_d1_sup"] is not None and r["dist_d1_sup"] < 1.5,
    "NOT_clean_sky": lambda r: not r["clean_sky"],
    "far_from_D1demand(>5)": lambda r: r["dist_d1_dem"] is not None and r["dist_d1_dem"] > 5,
    "below_value(f6)": lambda r: r["f6_below"],
    "breaks_support(f3)": lambda r: r["f3_break"],
    "still_flushing(consec>=3)": lambda r: r["f2_consec"] is not None and r["f2_consec"] >= 3,
    "deep_cascade(<=-3)": lambda r: r["casc"] is not None and r["casc"] <= -3,
    "mid_range(0.4-0.6)": lambda r: r["rng1d"] is not None and 0.4 <= r["rng1d"] <= 0.6,
    "high_in_range(>=0.7)": lambda r: r["rng1d"] is not None and r["rng1d"] >= 0.7,
    "supply_rejected_before": lambda r: r["sup_rej"],
    "rsi_no_oversold(>45)": lambda r: r["rsi"] is not None and r["rsi"] > 45,
}
print(f"=== bateria de {len(CONDS)} condições (Bonferroni-aware) — usável SE win=0 E run=0 ===")
print(f"{'condição':>30} | {'n':>3} | {'win':>3} | {'run':>3} | {'loser':>5} | usável?")
usable = []
for name, f in CONDS.items():
    g = [r for r in base if f(r)]
    w = sum(1 for r in g if r["winner"]); ru = sum(1 for r in g if r["runner"]); lo = len(g) - w
    ok = (w == 0 and ru == 0 and lo > 0)
    if ok: usable.append((name, f))
    print(f"{name:>30} | {len(g):>3} | {w:>3} | {ru:>3} | {lo:>5} | {'✅' if ok else ''}")

# empilhar usáveis (union) com restrição dura
print(f"\n=== empilhar usáveis (0-winner/0-runner) ===")
cut = set()
for name, f in usable:
    for r in base:
        if f(r) and not r["winner"] and not r["runner"]: cut.add(r["b"])
kept = [r for r in base if r["b"] not in cut]
kw = sum(1 for r in kept if r["winner"]); kn = len(kept)
print(f"usáveis: {[n for n,_ in usable]}")
print(f"losers extra cortados (puros): {len(cut)} | base após: trades={kn} winners={kw} losers={kn-kw} WR={100*kw/kn:.1f}%")
print(f"\n⚠️ Calibração 276: 0-winner em calibração NÃO prova — {len(CONDS)} condições testadas (selection); cada usável precisa validar (sub-janela/jackknife) + rationale estrutural antes de aprovar. Restrição dura 0-winner/0-runner é a bússola, não garantia.")
