#!/usr/bin/env python3
"""A1A2 OB-ANCHORED v7 — v6 + GATE DE IMPULSO (Cris 10/08: "pullback curto só funciona em leg de impulsão,
nas outras dá SL"). Adiciona o gate leg_v3==IMPULSO_UP (motor de legs VALIDADO, já usado por a2_context_build)
para filtrar os toques de demanda que NÃO estão num impulso de alta (range/não-impulso = SL).

RECURSOS EXISTENTES (nada inventado):
  - âncora = zona OB DEMAND real (loader cp_engine/a2_context_build).
  - GATE = leg_v3.build_leg_v3() IMPULSO_UP (a2_context_build linha 95-97: leg_at).
  - entry/SL/alvo/MB3 = a1_causal_entry aprovado (SL próprio).
  - regime BULL = Layer1.
Read-only. NÃO toca live. py3.9 stdlib."""
import sys, bisect
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from a1_causal_entry import load_series, causal_entry, HORIZON
from fvg_localization_study import panel, r_of, BLK
from fvg_localization_study_v2 import PB_WIN, SCALE_ATR, HH_WIN, HH_GAP, detect_at as detect_base
from fvg_localization_study_v3 import build_regime_lookup, regime_at
from ob_anchored_study_v5 import load_ob_zones
import leg_v3 as LV   # motor de legs VALIDADO (a2_context_build)

_v3 = LV.build_leg_v3()
_LC = [r["t"] + 14400 for r in _v3]          # known-at = fecho da barra 4H (idêntico a a2_context_build)


def leg_at(t):
    i = bisect.bisect_right(_LC, t) - 1
    return _v3[i].get("leg") if i >= 0 else None


def _resolve(S, ei, ent, sl):
    L, H, N = S["L"], S["H"], S["N"]
    tgt = ent + 3 * (ent - sl)
    for m in range(ei + 1, min(N, ei + HORIZON + 1)):
        if L[m] <= sl: return "LOSS"
        if H[m] >= tgt: return "WIN"
    return "OPEN"


def detect_ob7(S, i, zones):
    L, ATR, T = S["L"], S["ATR"], S["T"]
    atr = ATR[i] or 5.0
    t = T[i]
    if leg_at(t) != "IMPULSO_UP":                         # GATE: só pullback em leg de IMPULSO de alta
        return None
    cand = [k for k in range(max(0, i - PB_WIN), i + 1)
            if any("DEMAND" in z["text"] and z["born_t"] and z["born_t"] <= t
                   and z["low"] is not None and z["low"] <= L[k] <= z["high"] for z in zones.values())]
    if not cand:
        return None
    j = min(cand, key=lambda k: L[k])
    start = max(0, j - 3)
    Sx = {k: (v[start:i + 1] if isinstance(v, list) else v) for k, v in S.items()}
    Sx["N"] = len(Sx["T"])
    r = causal_entry(Sx, j - start, kind="MB3")
    if not r:
        return None
    ei = r["ei"] + start
    if ei != i or r["R"] > SCALE_ATR * atr:
        return None
    o = _resolve(S, ei, r["ent"], r["sl"])
    return dict(ei=ei, t=t, ent=r["ent"], sl=r["sl"], R=r["R"], o=o, j=j)


def main():
    S = load_series(BLK); N = S["N"]
    zones = load_ob_zones(BLK)
    known, REG = build_regime_lookup()
    ob = {}
    for i in range(HH_WIN + 4, N):
        r = detect_ob7(S, i, zones)
        if r and r["o"] in ("WIN", "LOSS"):
            r["regime"] = regime_at(known, REG, r["t"]); ob[i] = r
    base = {}
    for i in range(HH_WIN + 4, N):
        rb = detect_base(S, i)
        if rb and rb["o"] in ("WIN", "LOSS"):
            rb["regime"] = regime_at(known, REG, rb["t"]); base[i] = rb
    obB = [r for r in ob.values() if r["regime"] == "BULL"]
    baseB = [r for r in base.values() if r["regime"] == "BULL"]
    print(f"{'='*74}\nA1A2 OB-ANCHORED v7 = v6 + GATE IMPULSO_UP (leg_v3) — sem invenção\n{'='*74}")
    print(f"[BASELINE argmax · BULL]     {panel([r_of(r['o']) for r in baseB])['s']}")
    print(f"[OB-ANCHORED v7 · BULL]      {panel([r_of(r['o']) for r in obB])['s']}")

    def base_fundo_velho(i):
        H, L = S["H"], S["L"]
        if i - HH_GAP <= 0: return False
        hh_i = max(range(max(0, i - HH_WIN), i - HH_GAP), key=lambda z: H[z])
        j = min(range(hh_i + 1, i + 1), key=lambda z: L[z])
        return (i - j) > PB_WIN
    recovered = [i for i in ob if i not in base and base_fundo_velho(i)]
    rec_win = sum(1 for i in recovered if ob[i]["o"] == "WIN")
    print(f"\n[LAG] bounces frescos recuperados (baseline perdia por fundo-velho): {len(recovered)} (WIN {rec_win})")
    print(f"  overlap: v7 {len(ob)} · baseline {len(base)} · comuns {len(set(ob)&set(base))} · só-v7 {len(set(ob)-set(base))}")


if __name__ == "__main__":
    main()
