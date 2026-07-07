#!/usr/bin/env python3
"""CANDIDATO: filtro macro-contextual CAUSAL = REGIME SEQUENCIAL RSI/EMA.

Leitura estrutural (multi-barra, SO barras <= j):
  - RSI sustentado acima da sua propria media movel (regime de momentum-up),
  - EMA21 com slope a subir nas ultimas K barras (trajetoria, nao snapshot).
  MANTEM os entries em regime UP; corta os que decidem sem regime UP (fundo/contra-tendencia).

CAUSALIDADE: para cada entry usamos apenas barras com indice <= j (barra de decisao).
  rsi_ma = SMA(RSI, W) computada em [j-W+1 .. j].
  frac_above = fracao de barras em [j-K+1 .. j] com RSI > rsi_ma_local (ambos <=j).
  ema_up = EMA21[j] > EMA21[j-K] (slope positivo na janela passada).
  Nenhuma janela ultrapassa j; nenhum uso de out/last_t/pivo-futuro.
"""
import sys
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S, TS, HI, LO, CL, ATR, EMA, RSI, N, ENTRIES, score


def rsi_ma_at(idx, W):
    """SMA de RSI sobre [idx-W+1 .. idx], SO barras <=idx. None se dados insuficientes."""
    lo = idx - W + 1
    if lo < 0:
        return None
    vals = [RSI[k] for k in range(lo, idx + 1) if RSI[k] is not None]
    if len(vals) < max(2, W // 2):
        return None
    return sum(vals) / len(vals)


def frac_rsi_above_ma(j, K, W):
    """Fracao das ultimas K barras (<=j) em que RSI[k] > SMA(RSI,W) local em k. Tudo causal."""
    cnt = 0
    tot = 0
    for k in range(j - K + 1, j + 1):
        if k < 0 or RSI[k] is None:
            continue
        m = rsi_ma_at(k, W)
        if m is None:
            continue
        tot += 1
        if RSI[k] > m:
            cnt += 1
    if tot == 0:
        return None
    return cnt / tot


def ema_slope_up(j, K):
    """EMA21 a subir: EMA[j] > EMA[j-K]. Causal (barras <=j)."""
    if j - K < 0 or EMA[j] is None or EMA[j - K] is None:
        return None
    return EMA[j] > EMA[j - K]


def regime_up(e, K, W, frac_thr):
    j = e["j"]
    fa = frac_rsi_above_ma(j, K, W)
    es = ema_slope_up(j, K)
    if fa is None or es is None:
        return None  # sem dados -> tratamos como nao-keep abaixo
    return (fa >= frac_thr) and es


def evaluate(K, W, frac_thr):
    keep = set()
    undef = 0
    for e in ENTRIES:
        r = regime_up(e, K, W, frac_thr)
        if r is None:
            undef += 1
            continue
        if r:
            keep.add(e["n"])
    sc = score(keep)
    return keep, sc, undef


if __name__ == "__main__":
    print("BASE:", score([e["n"] for e in ENTRIES]))
    print()
    grid = []
    for K in (5, 8, 10, 12, 16, 20):
        for W in (10, 14, 20):
            for frac_thr in (0.5, 0.6, 0.7, 0.8, 1.0):
                keep, sc, undef = evaluate(K, W, frac_thr)
                grid.append((K, W, frac_thr, keep, sc, undef))

    # imprime todas as combinacoes que passam gates minimos
    def ok(sc):
        y25w, y25n = map(int, sc["y2025"].split("/"))
        y26w, y26n = map(int, sc["y2026"].split("/"))
        y25_pos = y25n > 0 and (y25w / y25n) > 0.5
        y26_pos = y26n > 0 and (y26w / y26n) > 0.5
        return (sc["N_kept"] >= 20 and sc["poison_ratio"] < 0.9
                and sc["hit3r_kept"] > 0.542 and y25_pos and y26_pos)

    print("=== TODAS as combinacoes (K,W,frac -> score) ===")
    for K, W, frac_thr, keep, sc, undef in grid:
        flag = "  <== PASS" if ok(sc) else ""
        print(f"K={K:2d} W={W:2d} f={frac_thr:.1f} | N={sc['N_kept']:2d} hit3r={sc['hit3r_kept']:.3f} "
              f"poison={sc['poison_ratio']:.2f} y25={sc['y2025']} y26={sc['y2026']} "
              f"wc={sc['winners_cut']} lc={sc['losers_cut']} undef={undef}{flag}")

    print()
    passers = [(K, W, f, keep, sc, undef) for (K, W, f, keep, sc, undef) in grid if ok(sc)]
    if passers:
        # melhor = maior hit3r, depois menor poison, depois maior N
        best = max(passers, key=lambda x: (x[4]["hit3r_kept"], -x[4]["poison_ratio"], x[4]["N_kept"]))
        K, W, f, keep, sc, undef = best
        print(f"=== MELHOR PASSER: K={K} W={W} frac_thr={f} ===")
        print(sc)
        print("keep_ns =", sorted(keep))
    else:
        print("=== NENHUM passa todos os gates. Melhor por hit3r com poison<0.9 & N>=20: ===")
        cand = [g for g in grid if g[4]["poison_ratio"] < 0.9 and g[4]["N_kept"] >= 20]
        if cand:
            best = max(cand, key=lambda x: (x[4]["hit3r_kept"], -x[4]["poison_ratio"]))
            K, W, f, keep, sc, undef = best
            print(f"K={K} W={W} frac_thr={f}")
            print(sc)
            print("keep_ns =", sorted(keep))
        else:
            print("Nem poison<0.9 & N>=20. Mostrando o de menor poison:")
            best = min(grid, key=lambda x: (x[4]["poison_ratio"], -x[4]["hit3r_kept"]))
            K, W, f, keep, sc, undef = best
            print(f"K={K} W={W} frac_thr={f}")
            print(sc)
            print("keep_ns =", sorted(keep))
