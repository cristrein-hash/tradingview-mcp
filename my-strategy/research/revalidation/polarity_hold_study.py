#!/usr/bin/env python3
"""VALIDAÇÃO DA LEI DE POLARIDADE (Cris 2026-08-10: "supply furada com força vira demanda obrigatória, alta
prob de segurar — validar a sério"). NÃO assume a lei — TESTA-a nos dados RAW.

Evento: zona SUPPLY (OB Detector, tipo real) que o preço ROMPE (fecho acima do topo = reconquista).
Depois: 1º PULLBACK que volta ao nível (low toca [zl, zh]). SEGUROU (bounce +K·ATR antes de perder o fundo)
ou FALHOU (fecho abaixo de zl−buffer)? Mede a prob de segurar. Espelho para DEMAND furada (vira supply).

RECURSOS EXISTENTES (nada inventado): loader OB canónico (cp_engine, tipo real + born_t) via ob_anchored_study_v5;
load_series aprovado. Só factos: fecho real vs fronteira real da zona OB. py3.9 stdlib."""
import sys, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "a1a2_fvg_lab"))
from a1_causal_entry import load_series
from fvg_localization_study import BLK
from ob_anchored_study_v5 import load_ob_zones
from fvg_localization_study_v3 import build_regime_lookup, regime_at

HOLD_ATR = 1.0     # "segurou" = bounce >= HOLD_ATR·ATR a partir do toque, antes de perder o fundo
FWD = 96           # janela de resolução do pullback (barras)


def atr_at(S, i):
    return S["ATR"][i] or 5.0


def study(S, zones, side):
    """side='SUPPLY'→testa polaridade ex-supply=suporte (LONG hold). 'DEMAND'→ex-demand=resistência (SHORT)."""
    T, H, L, C, N = S["T"], S["H"], S["L"], S["C"], S["N"]
    Tarr = T
    import bisect
    events = []
    for z in zones.values():
        if side not in z["text"] or not z["born_t"] or z["low"] is None:
            continue
        zl, zh = float(z["low"]), float(z["high"])
        b0 = bisect.bisect_left(Tarr, z["born_t"])
        # rompimento: 1ª barra pós-born com fecho além do nível (supply→acima; demand→abaixo)
        brk = None
        for b in range(b0, min(N, b0 + FWD * 3)):
            if side == "SUPPLY" and C[b] > zh:
                brk = b; break
            if side == "DEMAND" and C[b] < zl:
                brk = b; break
        if brk is None:
            continue
        # 1º pullback de volta ao nível
        pb = None
        for p in range(brk + 1, min(N, brk + FWD)):
            if side == "SUPPLY" and L[p] <= zh:
                pb = p; break
            if side == "DEMAND" and H[p] >= zl:
                pb = p; break
        if pb is None:
            continue
        atr = atr_at(S, pb)
        held = None
        for m in range(pb, min(N, pb + FWD)):
            if side == "SUPPLY":
                if C[m] < zl - 0.1 * atr: held = False; break          # perdeu o fundo = falhou
                if H[m] >= zh + HOLD_ATR * atr: held = True; break      # bounce = segurou
            else:
                if C[m] > zh + 0.1 * atr: held = False; break
                if L[m] <= zl - HOLD_ATR * atr: held = True; break
        if held is None:
            continue
        events.append({"t": T[pb], "zl": zl, "zh": zh, "held": held})
    return events


def panel(events, known, REG, label):
    if not events:
        print(f"[{label}] n=0"); return
    n = len(events); held = sum(1 for e in events if e["held"])
    print(f"[{label}] n={n} · SEGUROU {held} ({100*held/n:.0f}%) · FALHOU {n-held} ({100*(n-held)/n:.0f}%)")
    # por regime
    for R in ("BULL", "RANGE", "BEAR"):
        sub = [e for e in events if regime_at(known, REG, e["t"]) == R]
        if sub:
            h = sum(1 for e in sub if e["held"])
            print(f"    {R:5}: n={len(sub):3d} · segurou {100*h/len(sub):.0f}%")


def main():
    S = load_series(BLK)
    zones = load_ob_zones(BLK)
    known, REG = build_regime_lookup()
    from collections import Counter
    print(f"série {S['N']} barras · zonas OB {len(zones)} ({dict(Counter(z['text'] for z in zones.values()))})")
    print(f"HOLD_ATR={HOLD_ATR} · FWD={FWD} barras\n{'='*70}")
    ev_sup = study(S, zones, "SUPPLY")
    panel(ev_sup, known, REG, "LEI: ex-SUPPLY furada = SUPORTE (segura no pullback?)")
    print()
    ev_dem = study(S, zones, "DEMAND")
    panel(ev_dem, known, REG, "espelho: ex-DEMAND furada = RESISTÊNCIA")
    # baseline honesto: numa perna de alta, QUALQUER suporte segura com que prob? (null grosseiro)
    print(f"\n(nota: comparar com base — em BULL o preço tende a segurar suportes; ver split por regime.)")


if __name__ == "__main__":
    main()
