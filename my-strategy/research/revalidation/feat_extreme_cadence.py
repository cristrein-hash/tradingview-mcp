#!/usr/bin/env python3
"""FAMÍLIA extreme_cadence — cadência de renovação de EXTREMOS (RAW 4H only, causal close-only).

Conceito: trend renova extremos de UM lado com regularidade; range envelhece ambos.
Feature no instante t (última barra 4H FECHADA i, TS4[i]+14400 <= t):
  novo HIGH na barra j  <=> H4[j] > max(H4[j-W:j])   (exige j >= W)
  novo LOW  na barra j  <=> L4[j] < min(L4[j-W:j])
  bars_since_new_high = i - último j<=i com novo high (inf se nunca)
Regras (grelha FECHADA declarada abaixo, antes de qualquer resultado):
  high recente (<=K) & low velho (>K)  -> BULL
  low  recente (<=K) & high velho (>K) -> BEAR
  ambos velhos -> RANGE · ambos recentes -> RANGE (whipsaw)
Zero repaint: evento da barra j só é usável após o fecho de j; rótulos nunca revistos.
IN-SAMPLE ONLY: métricas apenas em t < SPLIT (2023-01-01 UTC). Séries cobrem TODOS os TS4.
"""
import sys, json, bisect
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
import gt_pivot_structural_harness as R1

# ---- GRELHA FECHADA (declarada antes de qualquer resultado) ----
# Núcleo da família: W em {60,120} x K em {15,30}; +W=90 interpolado (mesma família) => 6 configs.
GRID = [
    ("c1", 60, 15),
    ("c2", 60, 30),
    ("c3", 90, 15),
    ("c4", 90, 30),
    ("c5", 120, 15),
    ("c6", 120, 30),
]
SPLIT = 1672531200  # 2023-01-01 UTC — PROIBIDO olhar métricas t >= SPLIT
BAR_S = 14400
INF = 10**9

ENG = R1.ENG
TS4, H4, L4 = ENG.TS4, ENG.H4, R1.L4
N = len(TS4)

def event_flags(W):
    """new-high / new-low events por barra j (conhecidos no fecho de j)."""
    nh = [False]*N; nl = [False]*N
    for j in range(W, N):
        if H4[j] > max(H4[j-W:j]): nh[j] = True
        if L4[j] < min(L4[j-W:j]): nl[j] = True
    return nh, nl

def label_series(W, K):
    """Rótulo por índice de TS4, emitido no instante t=TS4[idx] usando só barras fechadas <= t."""
    nh, nl = event_flags(W)
    # prefix: último índice de evento <= i
    last_h = [-1]*N; last_l = [-1]*N
    lh = ll = -1
    for j in range(N):
        if nh[j]: lh = j
        if nl[j]: ll = j
        last_h[j] = lh; last_l[j] = ll
    labs = []
    for idx in range(N):
        t = TS4[idx]
        i = bisect.bisect_right(TS4, t - BAR_S) - 1  # última barra fechada <= t
        if i < 0:
            labs.append("RANGE"); continue
        bsh = (i - last_h[i]) if last_h[i] >= 0 else INF
        bsl = (i - last_l[i]) if last_l[i] >= 0 else INF
        hr, lr = bsh <= K, bsl <= K
        if hr and not lr: labs.append("BULL")
        elif lr and not hr: labs.append("BEAR")
        else: labs.append("RANGE")  # ambos velhos OU ambos recentes (whipsaw)
    return labs

def main():
    sc_in = [(t, g) for t, g in R1.SCOPE if t < SPLIT]
    T2I = R1.T2I
    out = {"family": "extreme_cadence", "configs": []}
    summary = []
    for cid, W, K in GRID:
        labs = label_series(W, K)
        assert len(labs) == N
        res = R1.score_fn(lambda t: labs[T2I[t]], sc_in)
        out["configs"].append({"id": cid, "params": {"W": W, "K": K}, "labels": labs})
        summary.append((cid, W, K, res))
        r = res["recall"]
        print(f"{cid} W={W} K={K} | in n={res['n']} acc={res['acc']} bal={res['bal']} "
              f"recall BULL={r['BULL']} BEAR={r['BEAR']} RANGE={r['RANGE']}")
    path = "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/results/feat_extreme_cadence_labels.json"
    with open(path, "w") as f:
        json.dump(out, f)
    best = max(summary, key=lambda x: x[3]["bal"])
    print(f"BEST in-sample: {best[0]} bal={best[3]['bal']}")
    print(f"labels salvos: {path} ({N} TS4 por config)")

if __name__ == "__main__":
    main()
