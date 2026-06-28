#!/usr/bin/env python3
"""Runner reprodutível p/ a família volat-fluxo (XAU 15M LONG BOTTOM).
Itera uma lista de combos {label, spec}, chama score_lens.py via subprocess, e imprime
um resumo compacto (after/losers_cut/runners_cut/efic/null_p/verdict) por combo.
Critério de aprovação: null_p<0.05 E runners_cut<=0.15*losers_cut E avgR_after>0.446 E todos yr>=0.
Uso: python3 run_volat_fluxo_lens.py
"""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
SCORER = HERE / "score_lens.py"

# Combos da família volat-fluxo (compressão + fluxo), variando q e empilhando eixos ortogonais.
COMBOS = [
    ("atr_contraction_lo25",        [{"feat":"atr_contraction","dir":"lo","q":0.25}]),
    ("vol_cj_hi25",                 [{"feat":"vol_cj","dir":"hi","q":0.25}]),
    ("in_demand_hi25",              [{"feat":"in_demand","dir":"hi","q":0.25}]),
    ("nas_long_16_hi25",            [{"feat":"nas_long_16","dir":"hi","q":0.25}]),
    ("atrcontr_lo20",               [{"feat":"atr_contraction","dir":"lo","q":0.20}]),
    ("atr_regime_lo25",             [{"feat":"atr_regime","dir":"lo","q":0.25}]),
    ("vol_p_spike_lo25",            [{"feat":"vol_p_spike","dir":"lo","q":0.25}]),
    ("sell_bub_w_hi25",             [{"feat":"sell_bub_w","dir":"hi","q":0.25}]),
    ("pullback_depth_lo25",         [{"feat":"pullback_depth","dir":"lo","q":0.25}]),
    # combos ortogonais: compressão + fluxo + estrutura/candle (eixos distintos de posição)
    ("atrcontr_lo20+rsislope_hi25", [{"feat":"atr_contraction","dir":"lo","q":0.20},{"feat":"rsi_slope3","dir":"hi","q":0.25}]),
    ("atrcontr_lo20+bodycj_hi25",   [{"feat":"atr_contraction","dir":"lo","q":0.20},{"feat":"body_cj","dir":"hi","q":0.25}]),
    ("atrcontr_lo20+microbos_hi25", [{"feat":"atr_contraction","dir":"lo","q":0.20},{"feat":"micro_bos_up","dir":"hi","q":0.25}]),
    ("atrcontr_lo20+reclaimspd_hi25",[{"feat":"atr_contraction","dir":"lo","q":0.20},{"feat":"reclaim_speed","dir":"hi","q":0.25}]),
    ("atrcontr_lo20+closepos_hi25", [{"feat":"atr_contraction","dir":"lo","q":0.20},{"feat":"close_pos_cj","dir":"hi","q":0.25}]),
    ("atrcontr_lo20+upclos5_hi25",  [{"feat":"atr_contraction","dir":"lo","q":0.20},{"feat":"up_closes5","dir":"hi","q":0.25}]),
    ("atrcontr_lo25+rsicj_hi25",    [{"feat":"atr_contraction","dir":"lo","q":0.25},{"feat":"rsi_cj","dir":"hi","q":0.25}]),
    ("atrcontr_lo20+hl8_hi25",      [{"feat":"atr_contraction","dir":"lo","q":0.20},{"feat":"higher_lows8","dir":"hi","q":0.25}]),
    ("atrcontr_lo20+upvel_hi25",    [{"feat":"atr_contraction","dir":"lo","q":0.20},{"feat":"up_velocity","dir":"hi","q":0.25}]),
    # pullback_depth_lo (único single-lens PASS) — variantes q + stack ortogonal (fluxo/compressão)
    ("pullback_depth_lo20",         [{"feat":"pullback_depth","dir":"lo","q":0.20}]),
    ("pullback_depth_lo33",         [{"feat":"pullback_depth","dir":"lo","q":0.33}]),
    ("pbdepth_lo25+vpspike_lo25",   [{"feat":"pullback_depth","dir":"lo","q":0.25},{"feat":"vol_p_spike","dir":"lo","q":0.25}]),
    ("pbdepth_lo25+atrcontr_lo20",  [{"feat":"pullback_depth","dir":"lo","q":0.25},{"feat":"atr_contraction","dir":"lo","q":0.20}]),
    ("pbdepth_lo25+atrregime_lo25", [{"feat":"pullback_depth","dir":"lo","q":0.25},{"feat":"atr_regime","dir":"lo","q":0.25}]),
    ("vpspike_lo20",                [{"feat":"vol_p_spike","dir":"lo","q":0.20}]),
    ("vpspike_lo33",                [{"feat":"vol_p_spike","dir":"lo","q":0.33}]),
]

def run(spec):
    out = subprocess.run([sys.executable, str(SCORER), json.dumps(spec)],
                         capture_output=True, text=True)
    return json.loads(out.stdout)

def passes(d):
    a = d["after"]; lc = d["losers_cut"]; rc = d["runners_cut"]
    return (d["null_p_avgR_random_ge"] < 0.05 and rc <= 0.15*lc and
            a["avgR"] > 0.446 and all(v >= 0 for v in a["yr"].values()))

def main():
    base = run([{"feat":"nas_long_16","dir":"hi","q":0.25}])["h1_base"]
    print("BASE:", json.dumps(base))
    for label, spec in COMBOS:
        d = run(spec)
        a = d["after"]
        rec = {"label": label, "spec": json.dumps(spec), "N": a["N"], "avgR": a["avgR"],
               "DD": a["DD"], "yr": a["yr"], "losers_cut": d["losers_cut"],
               "runners_cut": d["runners_cut"], "efic": d["efic_losL_per_runL"],
               "null_p": d["null_p_avgR_random_ge"], "PASS": passes(d)}
        print(json.dumps(rec, ensure_ascii=False))

if __name__ == "__main__":
    main()
