#!/usr/bin/env python3
"""FAMÍLIA congestion_revisit — densidade de REVISITA de preço (teoria de leilão).

RANGE = preço aceita/revisita os mesmos níveis; TREND = abandona níveis.
Ortogonal a deslocamento: mede quantas vezes o preço VOLTOU, não quanto andou.

Regra (causal, close-only):
  No instante t, seja i o índice da última barra 4H FECHADA (TS4[i]+14400 <= t).
  densidade = fração das últimas W barras fechadas (i-W+1..i) cujo CLOSE está
  a <= 0.5*ATR14(i) do close C[i].
  densidade >= dens_thr -> RANGE
  senão direção = sinal(C[i] - C[i-W]) -> BULL / BEAR (empate -> RANGE).
  Histórico insuficiente (i-W < 0) -> RANGE.

IN-SAMPLE ONLY: métricas apenas em t < SPLIT (2023-01-01 UTC). Séries de
rótulos cobrem TODOS os TS4 (cego avaliado depois, fora deste âmbito).
"""
import sys, json, bisect
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
import gt_pivot_structural_harness as R1

# ---- GRELHA FECHADA (declarada antes de qualquer resultado) ----
FAMILY = "congestion_revisit"
W_GRID = [40, 80, 120]
THR_GRID = [0.30, 0.45]
ATR_MULT = 0.5
SPLIT = 1672531200  # 2023-01-01 UTC
BAR_S = 14400
OUT_PATH = ("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/"
            "results/feat_congestion_revisit_labels.json")

ENG = R1.ENG
TS4 = ENG.TS4
C4 = ENG.C4
CT = [t + BAR_S for t in TS4]  # tempos de FECHO de cada barra 4H


def label_series(W, thr):
    """Rótulo por índice de TS4 (emitido no instante t=TS4[i]; causal)."""
    labs = []
    for t in TS4:
        last = bisect.bisect_right(CT, t) - 1  # última barra FECHADA em t
        if last - W < 0:
            labs.append("RANGE")
            continue
        ref = C4[last]
        tol = ATR_MULT * R1.atr4(last)
        win = C4[last - W + 1:last + 1]
        dens = sum(1 for c in win if abs(c - ref) <= tol) / W
        if dens >= thr:
            labs.append("RANGE")
        else:
            d = C4[last] - C4[last - W]
            labs.append("BULL" if d > 0 else ("BEAR" if d < 0 else "RANGE"))
    return labs


def main():
    sc_in = [(t, g) for t, g in R1.SCOPE if t < SPLIT]
    configs, report = [], []
    cid = 0
    for W in W_GRID:
        for thr in THR_GRID:
            cid += 1
            labs = label_series(W, thr)
            fn = lambda t, _l=labs: _l[R1.T2I[t]]
            s = R1.score_fn(fn, sc_in)
            params = {"W": W, "dens_thr": thr, "atr_mult": ATR_MULT}
            configs.append({"id": f"c{cid}", "params": params, "labels": labs})
            report.append({"id": f"c{cid}", "params": params, "in": s})
            print(f"c{cid} W={W:<3} thr={thr:.2f} | in n={s['n']} acc={s['acc']:5.1f} "
                  f"bal={s['bal']:5.1f} recall B/Be/R="
                  f"{s['recall']['BULL']}/{s['recall']['BEAR']}/{s['recall']['RANGE']}")
    with open(OUT_PATH, "w") as f:
        json.dump({"family": FAMILY, "configs": configs}, f)
    best = max(report, key=lambda r: r["in"]["bal"])
    print(f"\nBEST in-sample: {best['id']} {best['params']} bal={best['in']['bal']}")
    print(f"labels gravados: {OUT_PATH} ({len(TS4)} barras por config, {len(configs)} configs)")


if __name__ == "__main__":
    main()
