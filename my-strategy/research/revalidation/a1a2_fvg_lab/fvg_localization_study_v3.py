#!/usr/bin/env python3
"""A1A2_FVG_LAB v3 — REFINAMENTO DECISIVO (recomendação do Devil's Advocate): re-correr o teste v2 mas com
GATE BULL causal (structural_1d via Layer1 macro detector aprovado, build_layer1), porque o live só dispara
A1/A2 em regime BULL. v2 misturava longs contra-tendência de BEAR (=WR 30% e A/B FAIL descrevem uma
população que o live NÃO negoceia). Aqui isolamos os disparos BULL e vemos se FVG-fill discrimina DENTRO
do BULL. Regime = último 1D FECHADO <= t (known-at = T_1d+86400). Motor read-only. NÃO toca nada live."""
import sys, bisect, datetime as dt, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from a1_causal_entry import load_series, HORIZON
from fvg_localization_study import resolve_limit, panel, r_of, BLK
from fvg_localization_study_v2 import detect_at, HH_WIN
import macro_structural_v3 as M3

ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")


def build_regime_lookup():
    """Série de regime 1D causal (Layer1 aprovado). Devolve (known_at[], REG[]) para lookup por bisect:
    regime conhecido no instante t = REG[bisect_right(known_at, t)-1]."""
    REG = M3.build_layer1()                       # regime por barra 1D, alinhado a M3.T
    known = [M3.T[i] + 86400 for i in range(len(REG))]   # fecho da barra 1D = known-at
    return known, REG


def regime_at(known, REG, t):
    k = bisect.bisect_right(known, t) - 1
    return REG[k] if k >= 0 else "RANGE"


def main():
    S = load_series(BLK); N = S["N"]
    known, REG = build_regime_lookup()
    print(f"série RAW 15M: {N} barras · Layer1 1D: {len(REG)} barras {ds(M3.T[0])}→{ds(M3.T[-1])}")

    fires = []
    for i in range(HH_WIN + 4, N):
        r = detect_at(S, i)
        if r and r["o"] in ("WIN", "LOSS"):
            r["regime"] = regime_at(known, REG, r["t"])
            fires.append(r)

    from collections import Counter
    print(f"\ndisparos resolvidos: {len(fires)} · por regime: {dict(Counter(r['regime'] for r in fires))}")

    for REGIME in ("BULL", "RANGE", "BEAR"):
        sub = [r for r in fires if r["regime"] == REGIME]
        if len(sub) < 8:
            print(f"\n[{REGIME}] n={len(sub)} — amostra pequena, salto análise fina.")
            continue
        bs = sorted(r["bounce"] for r in sub)
        base = [r_of(r["o"]) for r in sub]; bp = panel(base)
        fs = [r for r in sub if r["fvg"]]; nf = [r for r in sub if not r["fvg"]]
        print(f"\n{'='*80}\n[{REGIME}]  {len(sub)} disparos — a população-{'LIVE' if REGIME=='BULL' else 'x'}\n{'='*80}")
        print(f"  bounce% mediana {st.median(bs):.0f} (min {bs[0]:.0f} max {bs[-1]:.0f}) · bounce>60 = "
              f"{sum(1 for r in sub if r['bounce']>60)}")
        print(f"  BASELINE: {bp['s']}")
        print(f"  FVG=SIM ({len(fs)}): {panel([r_of(r['o']) for r in fs])['s']}")
        print(f"  FVG=NÃO ({len(nf)}): {panel([r_of(r['o']) for r in nf])['s']}")
        # avgR lado-a-lado (a chave: FVG discrimina outcome ALÉM da profundidade?)
        if fs and nf:
            avg_f = sum(r_of(r['o']) for r in fs)/len(fs); avg_n = sum(r_of(r['o']) for r in nf)/len(nf)
            print(f"  → avgR FVG=SIM {avg_f:+.2f} vs FVG=NÃO {avg_n:+.2f}  (Δ {avg_f-avg_n:+.2f})")
        # bandas de localização
        for lab, cond in [("early≤40", lambda b: b <= 40), ("mid40-60", lambda b: 40 < b <= 60),
                          ("late>60", lambda b: b > 60)]:
            ss = [r for r in sub if cond(r["bounce"])]
            if ss:
                w = sum(1 for r in ss if r["o"] == "WIN")
                print(f"    {lab:9}: n={len(ss):3d} WR {100*w/len(ss):.0f}%")
        if REGIME != "BULL":
            continue
        # --- variantes A/B só no BULL (a decisão relevante ao live) ---
        passA = [r for r in sub if r["bounce"] <= 50 or r["fvg"]]
        killedA = [r for r in sub if r["o"] == "WIN" and not (r["bounce"] <= 50 or r["fvg"])]
        ap = panel([r_of(r["o"]) for r in passA])
        print(f"\n  [A gate] passa {len(passA)}/{len(sub)} · {ap['s']} · mata {len(killedA)} winners · "
              f"mediana bounce {st.median([r['bounce'] for r in passA]):.0f}")
        b_res = []; fills = expires = killedB = 0
        for r in sub:
            if r["fvg"]:
                o, rr = resolve_limit(S, r["ei"], r["gap"][1], r["sl"])
                if o in ("WIN", "LOSS"): fills += 1; b_res.append(rr)
                else:
                    expires += 1
                    if r["o"] == "WIN": killedB += 1
            else:
                b_res.append(r_of(r["o"]))
        bpB = panel(b_res)
        print(f"  [B limite] {bpB['s']} · fills {fills} · expires {expires} · winners perdidos {killedB}")
        # VEREDITO §4 no BULL
        c1A = len(killedA) <= 1
        c2A = (st.median(bs) - st.median([r["bounce"] for r in passA])) >= 15 and sum(1 for r in passA if r["bounce"]>60) <= 1
        c3A = ap["sumR"] >= bp["sumR"] - 1e-9 and (ap["rdd"] >= bp["rdd"] - 1e-9 or ap["rdd"] == float("inf"))
        c1B = killedB <= 1
        c3B = bpB["sumR"] >= bp["sumR"] - 1e-9 and (bpB["rdd"] >= bp["rdd"] - 1e-9 or bpB["rdd"] == float("inf"))
        print(f"\n  VEREDITO §4 (BULL):")
        print(f"    A: {'PASS' if (c1A and c2A and c3A) else 'FAIL'} (mata≤1={c1A}/{len(killedA)} · loc={c2A} · agr={c3A} sumR {ap['sumR']:+.0f}v{bp['sumR']:+.0f})")
        print(f"    B: {'PASS' if (c1B and c3B) else 'FAIL'} (mata≤1={c1B}/{killedB} · agr={c3B} sumR {bpB['sumR']:+.0f}v{bp['sumR']:+.0f})")


if __name__ == "__main__":
    main()
