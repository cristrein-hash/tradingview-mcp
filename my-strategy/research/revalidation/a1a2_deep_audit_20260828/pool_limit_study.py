#!/usr/bin/env python3
"""A1/A2 × BUY-LIMIT NO POOL (gramática REAL do Cris, lida do chart 28/08):
ele coloca a LIMITE NO nível $$$ (topo do pool de pavios) ANTES do toque; o fill é o próprio pavio que
varre; SL curto atrás do pool; a rejeição impressa é confirmação PÓS-fill; alvo = próximo pool.
Teste selado: para cada sinal MB3 do censo real (863), colocar limite no TOPO do pool de pavios 15M
mais próximo <=1.5 ATR abaixo do preço do sinal; fill em <=16 barras; SL = lo_pool − 0.3 ATR; alvo 3R;
fill-bar SL conta. Comparar com o MB3 market dos MESMOS episódios + no-fill accounting (a lição do
estudo buy-limit anterior: o que se perde nos que não recuam). Params selados agora, zero sweeps.
py3.9 stdlib. SANITY_PROBE n/a: estudo prereg'd (este cabeçalho)."""
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
NEAR_ATR, FILL_WIN, SLBUF = 1.5, 16, 0.3
HORIZON = 480


def main():
    rnd = random.Random(SEED)
    bars = RR.series_flat(RR.resolve_gz("XAUUSD", "15M"))
    rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(bars.items())]
    T = [r["t"] for r in rows]; H = [r["h"] for r in rows]; L = [r["l"] for r in rows]; C = [r["c"] for r in rows]
    N = len(T)
    trs = [0.0] + [max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])) for i in range(1, N)]

    def atr(i):
        seg = trs[max(1, i - 14):i]
        return sum(seg) / len(seg) if seg else 5.0

    swlow = [False] * N
    for i in range(K_SW, N - K_SW):
        if L[i] == min(L[i - K_SW:i + K_SW + 1]):
            swlow[i] = True

    def nearest_pool_below(i):
        a_ = atr(i)
        los = sorted(L[p] for p in range(max(0, i - WIN), i - K_SW) if swlow[p])
        pools = []; grp = []
        for p in los:
            if grp and p - grp[0] <= CL_ATR * a_:
                grp.append(p)
            else:
                if len(grp) >= 2:
                    pools.append((grp[0], grp[-1]))
                grp = [p]
        if len(grp) >= 2:
            pools.append((grp[0], grp[-1]))
        cand = [z for z in pools if z[1] < C[i] and (C[i] - z[1]) <= NEAR_ATR * a_]
        return max(cand, key=lambda z: z[1]) if cand else None

    def outcome_from(k, e, sl, fillbar=True):
        tgt = e + 3 * (e - sl)
        if fillbar and L[k] <= sl:
            return -1.0
        for m in range(k + 1, min(N, k + HORIZON)):
            if L[m] <= sl: return -1.0
            if H[m] >= tgt: return 3.0
        return 0.0

    eps = [json.loads(l) for l in open(HERE / "episodes.jsonl") if l.strip()]
    ti = {t: i for i, t in enumerate(T)}
    out = []
    for e in eps:
        i = ti.get(e["t"])
        if i is None:
            continue
        z = nearest_pool_below(i)
        if z is None:
            out.append(dict(e, mode="SEM-POOL")); continue
        lo_p, hi_p = z
        a_ = atr(i)
        lim = hi_p; sl = lo_p - SLBUF * a_
        risk = lim - sl
        if risk <= 0.05 * a_ or risk > 2.5 * a_:
            out.append(dict(e, mode="ESCALA")); continue
        fk = next((k for k in range(i + 1, min(N, i + FILL_WIN + 1)) if L[k] <= lim), None)
        if fk is None:
            out.append(dict(e, mode="NO-FILL")); continue
        R = outcome_from(fk, lim, sl)
        out.append(dict(e, mode="FILL", R_pool=R))

    def panel(rl, cost=0.2):
        n = len(rl); w = sum(1 for r in rl if r > 0); s = sum(r - cost for r in rl)
        cum = peak = dd = 0.0; stk = mx = 0
        for r in rl:
            cum += r - cost; peak = max(peak, cum); dd = min(dd, cum - peak)
            stk = stk + 1 if r <= 0 else 0; mx = max(mx, stk)
        return dict(N=n, WR=round(100 * w / n) if n else None, sumR=round(s, 1),
                    avgR=round(s / n, 2) if n else None, maxDD=round(dd, 1), streak=mx)

    fills = [o for o in out if o["mode"] == "FILL"]
    nofill = [o for o in out if o["mode"] == "NO-FILL"]
    sem = [o for o in out if o["mode"] in ("SEM-POOL", "ESCALA")]
    print(f"episódios {len(out)} · FILL {len(fills)} · NO-FILL {len(nofill)} · sem-pool/escala {len(sem)}")
    print("LIMIT-NO-POOL (fills):", panel([o["R_pool"] for o in fills]))
    print("MB3 market MESMOS episódios:", panel([o["R"] for o in fills]))
    print("no-fill: winners MB3 perdidos", sum(1 for o in nofill if o["R"] > 0),
          "· sumR MB3 perdido", round(sum(o["R"] for o in nofill), 1))
    print("sem-pool: MB3 sumR", round(sum(o["R"] for o in sem), 1))
    # ESTRATÉGIA COMBINADA (a ordem do Cris: A1/A2 BUSCA o ponto — limite quando há pool, market quando não há)
    comb = [o.get("R_pool") if o["mode"] == "FILL" else (o["R"] if o["mode"] in ("SEM-POOL", "ESCALA") else None)
            for o in out]
    comb = [r for r in comb if r is not None]
    print("COMBINADA (limit-se-há-pool, market-se-não; no-fill=sem trade):", panel(comb))
    hv = {}
    for o in out:
        r = o.get("R_pool") if o["mode"] == "FILL" else (o["R"] if o["mode"] in ("SEM-POOL", "ESCALA") else None)
        if r is None: continue
        hv[o["half"]] = round(hv.get(o["half"], 0) + r - 0.2, 1)
    print("combinada por-semestre c0.2:", dict(sorted(hv.items())))
    json.dump(dict(fills=panel([o["R_pool"] for o in fills]), mb3_same=panel([o["R"] for o in fills]),
                   combinada=panel(comb), halves=hv, n_fill=len(fills), n_nofill=len(nofill),
                   nofill_sumR_mb3=round(sum(o["R"] for o in nofill), 1)),
              open(HERE / "pool_limit_results.json", "w"), indent=1)
    print("gravado pool_limit_results.json")


if __name__ == "__main__":
    main()
