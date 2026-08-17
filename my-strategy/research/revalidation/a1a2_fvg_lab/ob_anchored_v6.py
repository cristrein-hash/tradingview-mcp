#!/usr/bin/env python3
"""A1A2 OB-ANCHORED v6 — RESOLVE o anchor-lag (Cris 10/08: sem inventar, com recursos já construídos).
Troca o argmax-96b instável (causa do lag) pela ÂNCORA = zona OB DEMAND REAL. Corrige as 2 invenções que o
DA apanhou no v5: (1) SL agora é o do MOTOR APROVADO a1_causal_entry (não o meu max-zona); (2) sem
agregação max-zona — a âncora é a barra cujo low entra numa zona DEMAND.

RECURSOS EXISTENTES consumidos (nada inventado):
  - zonas DEMAND: loader canónico de cp_engine/a2_context_build (text real + born_t causal).
  - entry/SL/alvo/MB3: a1_causal_entry (motor APROVADO, intocado, com o SEU SL low-real−0.1ATR).
  - regime BULL: Layer1 (macro_structural_v3), validado.
  - constantes PB_WIN/SCALE_ATR: do runtime A1/A2 aprovado.
Comparado ao baseline A1/A2 aprovado (detect_at v2) nos 32 GT + 605 all-firings.
Read-only. NÃO toca live. py3.9 stdlib."""
import sys, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from a1_causal_entry import load_series, causal_entry, HORIZON
from fvg_localization_study import panel, r_of, BLK
from fvg_localization_study_v2 import PB_WIN, SCALE_ATR, HH_WIN, detect_at as detect_base
from fvg_localization_study_v3 import build_regime_lookup, regime_at
from ob_anchored_study_v5 import load_ob_zones   # loader canónico (cp_engine) já escrito


def _resolve(S, ei, ent, sl):
    L, H, N = S["L"], S["H"], S["N"]
    tgt = ent + 3 * (ent - sl)
    for m in range(ei + 1, min(N, ei + HORIZON + 1)):
        if L[m] <= sl: return "LOSS"
        if H[m] >= tgt: return "WIN"
    return "OPEN"


def detect_ob6(S, i, zones):
    """Âncora = barra cujo low entra numa zona DEMAND real (born<=t). MB3 + SL do motor aprovado.
    Sinal catalogado se ei==i. Devolve dict ou None."""
    L, ATR, T = S["L"], S["ATR"], S["T"]
    atr = ATR[i] or 5.0
    t = T[i]
    # candidatos = barras recentes cujo low está dentro de uma zona DEMAND real nascida <= t
    cand = []
    for k in range(max(0, i - PB_WIN), i + 1):
        lk = L[k]
        if any("DEMAND" in z["text"] and z["born_t"] and z["born_t"] <= t
               and z["low"] is not None and z["low"] <= lk <= z["high"] for z in zones.values()):
            cand.append(k)
    if not cand:
        return None
    j = min(cand, key=lambda k: L[k])                      # fundo do pullback DENTRO da demanda
    start = max(0, j - 3)
    Sx = {k: (v[start:i + 1] if isinstance(v, list) else v) for k, v in S.items()}
    Sx["N"] = len(Sx["T"])
    r = causal_entry(Sx, j - start, kind="MB3")            # MOTOR APROVADO: entry, SL, alvo, MB3
    if not r:
        return None
    ei = r["ei"] + start
    if ei != i:
        return None
    if r["R"] > SCALE_ATR * atr:
        return None
    o = _resolve(S, ei, r["ent"], r["sl"])                 # SL do motor (não inventado)
    return dict(ei=ei, t=t, ent=r["ent"], sl=r["sl"], R=r["R"], o=o, j=j)


def main():
    S = load_series(BLK); N = S["N"]
    zones = load_ob_zones(BLK)
    known, REG = build_regime_lookup()
    ob = {}
    for i in range(HH_WIN + 4, N):
        r = detect_ob6(S, i, zones)
        if r and r["o"] in ("WIN", "LOSS"):
            r["regime"] = regime_at(known, REG, r["t"]); ob[i] = r
    base = {}
    for i in range(HH_WIN + 4, N):
        rb = detect_base(S, i)
        if rb and rb["o"] in ("WIN", "LOSS"):
            base[i] = rb
    bull = lambda d: [r for k, r in d.items() if r.get("regime") == "BULL"] if any("regime" in v for v in d.values()) else None
    obB = [r for r in ob.values() if r["regime"] == "BULL"]
    # baseline BULL via regime lookup
    for k, rb in base.items():
        rb["regime"] = regime_at(known, REG, rb["t"])
    baseB = [r for r in base.values() if r["regime"] == "BULL"]
    print(f"{'='*74}\nA1A2 OB-ANCHORED v6 (resolve lag) — sem invenção\n{'='*74}")
    print(f"[BASELINE argmax · BULL]  {panel([r_of(r['o']) for r in baseB])['s']}")
    print(f"[OB-ANCHORED v6 · BULL]   {panel([r_of(r['o']) for r in obB])['s']}")
    # LAG: firings OB que o baseline rejeitou por 'fundo velho' (desync do argmax)
    from fvg_localization_study_v2 import PB_WIN as PW, HH_GAP, HH_WIN as HW
    def base_fundo_velho(i):
        H, L = S["H"], S["L"]
        if i - HH_GAP <= 0: return False
        hh_i = max(range(max(0, i - HW), i - HH_GAP), key=lambda z: H[z])
        j = min(range(hh_i + 1, i + 1), key=lambda z: L[z])
        return (i - j) > PW
    recovered = [i for i in ob if i not in base and base_fundo_velho(i)]
    rec_win = sum(1 for i in recovered if ob[i]["o"] == "WIN")
    print(f"\n[LAG RESOLVIDO] firings OB que o baseline perdeu por 'fundo velho' (desync argmax): {len(recovered)} "
          f"(WIN {rec_win})")
    print(f"  overlap: OB {len(ob)} · baseline {len(base)} · comuns {len(set(ob)&set(base))}")


if __name__ == "__main__":
    main()
