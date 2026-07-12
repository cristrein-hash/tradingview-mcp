#!/usr/bin/env python3
"""CHURN do regime detector (plano Cris/Claude-chat 2026-07-12) — número "antes" da contenção.
churn = flips de rótulo / barras × 100, por janela FIXADA POR CRITÉRIO EXTERNO (datas congeladas
ANTES de rodar; NÃO derivadas dos rótulos do próprio detector — anti-circularidade):
  RANGE_2021_22 : 2021-05-01 → 2022-10-31 (macro-range 1700-2000 no diário)
  TREND_2024_25 : 2024-10-01 → 2025-10-31 (rally)
Séries: (a) detector 4H-nativo RAW pós-fix causal (rótulo por barra 4H, regime_at no open da barra);
(b) macro_at do leg engine 15M (rótulo por barra 15M; dados só ≥2024-05-24 → janela 2021-22
NÃO mensurável no 15M — declarado, não escondido). Sem contenção, sem tuning, medição pura."""
import io, sys, contextlib, datetime as dt
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp")

WINDOWS = {
    "RANGE_2021_22": ("2021-05-01", "2022-10-31"),
    "TREND_2024_25": ("2024-10-01", "2025-10-31"),
}

def ep(s): return int(dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())

def churn(labels):
    n = len(labels)
    if n < 2: return None
    flips = sum(1 for i in range(1, n) if labels[i] != labels[i-1])
    return n, flips, round(100.0*flips/n, 2)

def main():
    # (a) 4H-nativo RAW (pós-fix)
    spec = importlib.util.spec_from_file_location("eng", HERE/"engine_4h_regime_gate_RAW.py")
    eng = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(eng)
    lab4 = [(t, eng.regime_at(t)) for t in eng.TS4]
    # (b) macro_at 15M (leg engine)
    sys.path.insert(0, str(REPO/"research/xau_15m_structural_leg_engine"))
    from f1_structural_leg_machine import Data
    D = Data()
    lab15 = [(t, D.macro_at(t)) for t in D.TS]
    print("janelas congeladas (critério externo):", WINDOWS)
    for name, (a, b) in WINDOWS.items():
        ta, tb = ep(a), ep(b)+86400
        for tag, series in (("4H-nativo", lab4), ("15M-macro_at", lab15)):
            sel = [r for t, r in series if ta <= t < tb]
            c = churn(sel)
            if c is None or len(sel) == 0:
                print(f"{name:<14} {tag:<13} SEM DADOS NA JANELA")
            else:
                n, f, ch = c
                print(f"{name:<14} {tag:<13} barras {n:>6} flips {f:>4} churn/100b {ch:>6}")
    # referência: série completa de cada uma
    for tag, series in (("4H-nativo FULL", lab4), ("15M-macro_at FULL", lab15)):
        n, f, ch = churn([r for _, r in series])
        t0, t1 = series[0][0], series[-1][0]
        print(f"{tag:<18} {dt.datetime.utcfromtimestamp(t0).strftime('%Y-%m-%d')}→"
              f"{dt.datetime.utcfromtimestamp(t1).strftime('%Y-%m-%d')} barras {n} flips {f} churn/100b {ch}")

if __name__ == "__main__":
    main()
