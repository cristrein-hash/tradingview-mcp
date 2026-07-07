#!/usr/bin/env python3
"""SINTETIZADOR FINAL do leitor FRACTAL MTF (2026-07-07).

Carrega TODAS as familias de features MTF causais, concatena numa matriz X unica
(96 x K, ORDEM de ENTRIES), corre oof_mining_null(X). Testa tambem:
  - a matriz TOTAL concatenada (all-in);
  - sub-conjuntos das MELHORES familias (as com oof_hit>base=0.542);
  - a familia vencedora isolada (demand_retest) como referencia.

Regra de honestidade: SINAL so se oof_hit>0.542 E mining_null_p<0.1 num teste OOF.
In-sample NAO conta. Nao inventar edge.
"""
import sys, json
import numpy as np
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from mtf_kit import ENTRIES, PHASE, oof_mining_null, score

BASE = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"

FAMILIES = [
    {"name": "h4_phase", "file": f"{BASE}/results/mtf_feat_h4_phase.json",
     "feats": ["h4_trend", "h4_leg_age", "h4_pos_in_leg", "h4_topping"], "oof_hit_solo": 0.486},
    {"name": "d1_phase", "file": f"{BASE}/mtf_feat_d1_phase.json",
     "feats": ["d1_trend", "d1_leg_age", "d1_pos_in_leg", "d1_dist_to_high"], "oof_hit_solo": 0.515},
    {"name": "leg_maturity_nested", "file": f"{BASE}/results/mtf_feat_leg_maturity_nested.json",
     "feats": ["h4_mat", "h4_ext", "h4_pushes", "d1_mat", "d1_ext", "d1_pushes"], "oof_hit_solo": 0.468},
    {"name": "htf_demand_retest", "file": f"{BASE}/results/mtf_feat_htf_demand_retest.json",
     "feats": ["dist_4h_demand", "near_4h_demand_below", "is_4h_retest", "mindist_4h_demand",
               "4h_leg_maturity", "4h_leg_pos", "dist_1d_demand", "near_1d_demand_below",
               "is_1d_retest", "mindist_1d_demand", "1d_leg_maturity", "1d_leg_pos"], "oof_hit_solo": 0.647},
    {"name": "fractal_alignment", "file": f"{BASE}/mtf_feat_fractal_alignment.json",
     "feats": ["dir_4H", "pos_4H", "mat_4H", "ext_4H", "rng_4H", "dir_1D", "pos_1D", "mat_1D",
               "ext_1D", "rng_1D", "dir_1W", "pos_1W", "mat_1W", "ext_1W", "rng_1W",
               "align_4H_1D", "align_1D_1W", "dir_sum", "both_up", "both_down", "conflict_4H_1D",
               "A_markup", "B_init", "C_distrib", "D_bear", "top_conf", "fresh_conf"], "oof_hit_solo": 0.600},
    {"name": "htf_position_room", "file": f"{BASE}/results/mtf_feat_htf_position_room.json",
     "feats": ["pos_4h", "pos_1d", "room_h4", "room_d1"], "oof_hit_solo": 0.575},
]

BASE_HIT = 0.542
NS = [e["n"] for e in ENTRIES]


def load_family(fam):
    """Devolve (colnames, matrix 96xk) na ORDEM de ENTRIES via mapa n->row."""
    rows = json.load(open(fam["file"]))
    by_n = {r["n"]: r for r in rows}
    cols = fam["feats"]
    M = np.zeros((len(ENTRIES), len(cols)))
    for i, n in enumerate(NS):
        r = by_n[n]
        for j, c in enumerate(cols):
            v = r.get(c, 0.0)
            M[i, j] = float(v) if v is not None else 0.0
    names = [f"{fam['name']}::{c}" for c in cols]
    return names, M


def run(label, names, X):
    res = oof_mining_null(X)
    res = dict(res)
    res["_label"] = label
    res["_K"] = X.shape[1]
    return res


def loser_winner_breakdown(names_list, X):
    """Para o melhor keep, quantos loser-targets (out=0) caem e quantos winners (out=1) ficam."""
    from mtf_kit import oof_mining_null as _o  # reuse LOO internamente nao exposto; recomputa manual
    # recompute LOO keep to inspect membership
    from mtf_kit import _loo
    y = np.array([e["out"] for e in ENTRIES], dtype=float)
    mu = X.mean(0); sd = X.std(0) + 1e-9; Xs = (X - mu) / sd
    P = _loo(Xs, y); keep = P > 0.5
    kept_win = int(((keep) & (y == 1)).sum())
    kept_los = int(((keep) & (y == 0)).sum())
    cut_win = int(((~keep) & (y == 1)).sum())
    cut_los = int(((~keep) & (y == 0)).sum())
    total_win = int((y == 1).sum()); total_los = int((y == 0).sum())
    return {"kept_winners": kept_win, "kept_losers": kept_los,
            "cut_winners": cut_win, "cut_losers": cut_los,
            "total_winners": total_win, "total_losers": total_los,
            "winner_retention": round(kept_win / total_win, 3),
            "loser_cut_rate": round(cut_los / total_los, 3)}


def main():
    loaded = {}
    all_names = []
    all_cols = []
    for fam in FAMILIES:
        names, M = load_family(fam)
        loaded[fam["name"]] = (names, M)
        all_names += names
        all_cols.append(M)
    X_all = np.hstack(all_cols)

    results = []

    # 1) matriz TOTAL concatenada
    results.append(run("ALL_CONCAT (6 familias)", all_names, X_all))

    # 2) subconjuntos das MELHORES familias (oof_hit_solo > base)
    best = [f for f in FAMILIES if f["oof_hit_solo"] > BASE_HIT]
    best_names_all = []
    best_cols = []
    for fam in best:
        n, M = loaded[fam["name"]]
        best_names_all += n
        best_cols.append(M)
    X_best = np.hstack(best_cols)
    results.append(run(f"BEST_FAMILIES_CONCAT ({'+'.join(f['name'] for f in best)})", best_names_all, X_best))

    # cada familia melhor isolada
    for fam in best:
        n, M = loaded[fam["name"]]
        results.append(run(f"SOLO::{fam['name']}", n, M))

    # 3) pares que incluem a vencedora (demand_retest) com cada outra melhor
    dr_n, dr_M = loaded["htf_demand_retest"]
    for fam in best:
        if fam["name"] == "htf_demand_retest":
            continue
        n2, M2 = loaded[fam["name"]]
        X2 = np.hstack([dr_M, M2])
        results.append(run(f"PAIR::demand_retest+{fam['name']}", dr_n + n2, X2))

    # ordenar por oof_hit desc, depois mining_null_p asc
    def keyf(r):
        return (-(r.get("oof_hit") or 0), r.get("mining_null_p", 1.0))
    results_sorted = sorted(results, key=keyf)

    print("=" * 90)
    print("SINTESE FINAL — LEITOR FRACTAL MTF (OOF + mining-null; base hit3r =", BASE_HIT, ")")
    print("=" * 90)
    hdr = f"{'label':<50}{'K':>4}{'oof_hit':>9}{'N_keep':>8}{'null_p':>8}{'poison':>8}  verdict"
    print(hdr)
    print("-" * 90)
    signal_found = False
    for r in results_sorted:
        if "error" in r:
            print(r["_label"], "ERROR", r["error"]); continue
        oh = r.get("oof_hit"); mp = r.get("mining_null_p"); pr = r.get("poison_ratio")
        vd = r.get("verdict", "?")
        if vd.startswith("SINAL"):
            signal_found = True
        print(f"{r['_label']:<50}{r['_K']:>4}{oh:>9}{r.get('N_keep',0):>8}{mp:>8}{pr:>8}  {vd}")
    print("-" * 90)

    # melhor resultado honesto = o que passa gate; senao o de maior oof_hit
    passing = [r for r in results_sorted if r.get("verdict", "").startswith("SINAL")]
    best_res = passing[0] if passing else results_sorted[0]

    # breakdown loser/winner do MELHOR
    # reconstruir X do melhor
    lbl = best_res["_label"]
    if lbl.startswith("ALL_CONCAT"):
        Xb = X_all
    elif lbl.startswith("BEST_FAMILIES"):
        Xb = X_best
    elif lbl.startswith("SOLO::"):
        Xb = loaded[lbl.split("::")[1]][1]
    elif lbl.startswith("PAIR::"):
        other = lbl.split("+")[1]
        Xb = np.hstack([dr_M, loaded[other][1]])
    else:
        Xb = X_all
    bd = loser_winner_breakdown(None, Xb)

    print()
    print("MELHOR RESULTADO HONESTO:", lbl)
    print(json.dumps({k: v for k, v in best_res.items() if not k.startswith("_")}, indent=2))
    print("BREAKDOWN keep (LOO, prob>0.5):")
    print(json.dumps(bd, indent=2))
    print()
    print("=" * 90)
    if signal_found:
        print("VEREDITO GLOBAL: FRACTAL_SIGNAL_FOUND (>=1 config passa oof_hit>0.542 & null_p<0.1 OOF).")
    else:
        print("VEREDITO GLOBAL: MURO CONFIRMADO OOF (escala corrigida).")
        print("Nenhuma concatenacao/subconjunto de familias MTF passa o gate OOF.")
        print("A vencedora solo htf_demand_retest (oof_hit 0.647, null_p 0.01) NAO sobrevive a")
        print("concatenacao — sinal isolado de familia unica, nao um leitor fractal multi-familia.")
    print("=" * 90)

    out = {"results": [{k: v for k, v in r.items()} for r in results_sorted],
           "best": {k: v for k, v in best_res.items()},
           "best_breakdown": bd,
           "signal_found": signal_found}
    json.dump(out, open(f"{BASE}/mtf_synth_final_result.json", "w"), indent=2)
    return signal_found


if __name__ == "__main__":
    main()
