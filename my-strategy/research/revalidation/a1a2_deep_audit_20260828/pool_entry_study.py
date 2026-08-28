#!/usr/bin/env python3
"""A1/A2 ENTRADA-NO-POOL (fiel ao método do Cris; ordem 28/08 + DA a54031e). LONG-only.
Episódio = 1º TOQUE de um pool de pavios 15M (cluster causal >=2 swing-lows, span<=0.5ATR) DENTRO do
contexto A1/A2 (uptrend: HH na janela 96, pullback raso <=2 ATR) com REJEIÇÃO IMPRESSA na vela do toque
(pavio fura o pool, corpo fecha DE VOLTA acima do topo do pool). Entrada = fecho da vela do toque;
SL = low do pavio −0.1 ATR; alvo 3R fixo (comparável ao censo MB3). Dedup por pool (1 trade por pool).
Params selados ANTES de correr, zero sweeps. Painel + semestres + null block-shuffle + comparação com
o censo MB3 (mesma base RAW). py3.9 stdlib. SANITY_PROBE n/a: estudo prereg'd (este cabeçalho = prereg;
multi-fatorial: contexto uptrend + pool + rejeição na vela + trajetória)."""
import json
import random
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "my-strategy/core"))
import raw_reader as RR  # noqa: E402

SEED = 20260828
K_SW, CL_ATR, WIN = 3, 0.5, 400
HH_WIN, HH_GAP, PB_MAX = 96, 8, 2.0
HORIZON = 480


def main():
    rnd = random.Random(SEED)
    bars = RR.series_flat(RR.resolve_gz("XAUUSD", "15M"))
    rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(bars.items())]
    T = [r["t"] for r in rows]; O = [r["o"] for r in rows]; H = [r["h"] for r in rows]
    L = [r["l"] for r in rows]; C = [r["c"] for r in rows]
    N = len(T)
    trs = [0.0] + [max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])) for i in range(1, N)]

    def atr(i):
        seg = trs[max(1, i - 14):i]
        return sum(seg) / len(seg) if seg else 5.0

    swlow = [False] * N
    for i in range(K_SW, N - K_SW):
        if L[i] == min(L[i - K_SW:i + K_SW + 1]):
            swlow[i] = True

    def pools_at(i):
        """Clusters causais de >=2 swing-lows confirmados antes de i, span<=CL_ATR*ATR. [(lo,hi)]"""
        a_ = atr(i)
        los = sorted(L[p] for p in range(max(0, i - WIN), i - K_SW) if swlow[p])
        out = []; grp = []
        for p in los:
            if grp and p - grp[0] <= CL_ATR * a_:
                grp.append(p)
            else:
                if len(grp) >= 2:
                    out.append((grp[0], grp[-1]))
                grp = [p]
        if len(grp) >= 2:
            out.append((grp[0], grp[-1]))
        return out

    def uptrend_ctx(i):
        """Mesma geometria do censo MB3: pullback = mínimo APÓS o HH (não o range da perna inteira —
        bug N=0 da 1ª execução: usava min da janela toda = 4-12 ATR sempre)."""
        atr_ = atr(i)
        hw = range(max(0, i - HH_WIN), i - HH_GAP)
        hh_i = max(hw, key=lambda z: H[z]); hh = H[hh_i]
        low_pb = min(L[hh_i + 1:i + 1]) if hh_i + 1 <= i else L[i]
        return hh > C[i] and (hh - low_pb) / atr_ <= PB_MAX

    def outcome(k, e, sl):
        tgt = e + 3 * (e - sl)
        for m in range(k + 1, min(N, k + HORIZON)):
            if L[m] <= sl: return -1.0
            if H[m] >= tgt: return 3.0
        return 0.0

    trades = []
    used = set()               # dedup: pool (lo arredondado) já operado
    for i in range(500, N):
        if not uptrend_ctx(i):
            continue
        a_ = atr(i)
        for lo_p, hi_p in pools_at(i):
            key = round(lo_p, 1)
            if key in used:
                continue
            # 1º toque com rejeição impressa NA vela: pavio fura, corpo fecha de volta acima do topo
            if L[i] < lo_p and C[i] > hi_p:
                # 1º toque RECENTE: nenhuma barra das últimas 96 furou antes (a versão 400-barras
                # exigia que o mínimo absoluto da janela fosse swing confirmado = conjunto vazio)
                first = not any(L[b] < lo_p for b in range(max(0, i - HH_WIN), i))
                if not first:
                    continue
                e = C[i]; sl = L[i] - 0.1 * a_
                risk = e - sl
                if risk <= 0.05 * a_ or risk > 2.5 * a_:      # guarda de escala aprovada
                    continue
                used.add(key)
                R = outcome(i, e, sl)
                h = dt.datetime.fromtimestamp(T[i], dt.timezone.utc)
                trades.append(dict(i=i, R=R, half=f"{h.year}-H{1 if h.month <= 6 else 2}"))
                break

    def panel(rl, cost=0.2):
        n = len(rl); w = sum(1 for r in rl if r > 0); s = sum(r - cost for r in rl)
        cum = peak = dd = 0.0; stk = mx = 0
        for r in rl:
            cum += r - cost; peak = max(peak, cum); dd = min(dd, cum - peak)
            stk = stk + 1 if r <= 0 else 0; mx = max(mx, stk)
        return dict(N=n, WR=round(100 * w / n) if n else None, sumR=round(s, 1),
                    avgR=round(s / n, 2) if n else None, maxDD=round(dd, 1), streak=mx)

    rs = [t["R"] for t in trades]
    res = {}
    print("=== ENTRADA-NO-POOL (1º toque + rejeição na vela, contexto uptrend) ===")
    for c in (0.0, 0.2, 0.35):
        res[str(c)] = panel(rs, c)
        print(f"  custo {c}: {res[str(c)]}")
    hv = {}
    for t in trades:
        hv[t["half"]] = round(hv.get(t["half"], 0) + t["R"] - 0.2, 1)
    print("  por-semestre c0.2:", dict(sorted(hv.items())))
    # null: mesma barra de contexto, entrada aleatória nas 12 barras seguintes com mesma regra de SL
    nw = nn = 0
    for t in trades:
        for _ in range(50):
            ei = rnd.randint(t["i"] + 1, min(N - 2, t["i"] + 12))
            e = C[ei]; a_ = atr(ei)
            sl = min(L[t["i"]:ei + 1]) - 0.1 * a_
            if e - sl <= 0.05 * a_ or e - sl > 2.5 * a_:
                continue
            nn += 1
            if outcome(ei, e, sl) > 0:
                nw += 1
    wr = res["0.0"]["WR"]
    print(f"  null WR {100*nw/nn:.0f}% vs estratégia {wr}%" if nn else "  null: n/a")
    # comparação direta: censo MB3 (mesma base) = baseline conhecido
    print("  baseline censo MB3 (deep audit): N863 WR30 avgR c0.2 -0.00")
    json.dump(dict(panels=res, halves=hv, null_wr=round(100 * nw / nn, 1) if nn else None,
                   n_trades=len(trades)), open(HERE / "pool_entry_results.json", "w"), indent=1)
    print("gravado pool_entry_results.json")


if __name__ == "__main__":
    main()
