#!/usr/bin/env python3
"""A1/A2 × POOL-SWEEP (ordem Cris 28/08: estratégias buscarem os pontos de entrada dele).
Teste no censo real: o sinal vale mais quando o pullback VARREU um pool de pavios 15M (cluster causal
de >=2 swing-lows anteriores) e fechou de volta (sweep+reject = compra legítima)? Split + null.
Params selados antes de correr: pool = >=2 swing-lows (k=3) a <=0.5 ATR entre si, janela 400 barras;
sweep = nalguma das últimas 12 barras fura o pool (low < lo_pool) E fecha acima; sem sweeps de knobs.
py3.9 stdlib. SANITY_PROBE n/a: extensão prereg'd do deep audit (multi-fatorial: estrutura+pool+trajetória)."""
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
K_SW, CL_ATR, WIN, SWEEP_LOOK = 3, 0.5, 400, 12


def main():
    rnd = random.Random(SEED)
    bars = RR.series_flat(RR.resolve_gz("XAUUSD", "15M"))
    rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(bars.items())]
    T = [r["t"] for r in rows]; H = [r["h"] for r in rows]; L = [r["l"] for r in rows]; C = [r["c"] for r in rows]
    trs = [0.0] + [max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])) for i in range(1, len(T))]

    def atr(i):
        seg = trs[max(1, i - 14):i]
        return sum(seg) / len(seg) if seg else 5.0

    # swing lows causais (confirmados k barras depois)
    swlow = [False] * len(T)
    for i in range(K_SW, len(T) - K_SW):
        if L[i] == min(L[i - K_SW:i + K_SW + 1]):
            swlow[i] = True

    def pool_sweep_at(i):
        """Nas últimas SWEEP_LOOK barras antes de i: alguma barra b furou um pool (>=2 swing-lows
        anteriores a b, agrupados a <=CL_ATR*ATR) e fechou ACIMA do topo do pool? Causal."""
        a_ = atr(i)
        for b in range(max(0, i - SWEEP_LOOK), i + 1):
            los = [L[p] for p in range(max(0, b - WIN), b - K_SW) if swlow[p]]
            if len(los) < 2:
                continue
            los.sort()
            # clusters de >=2
            cl = []
            for p in los:
                if cl and p - cl[-1][-1] <= CL_ATR * a_:
                    cl[-1].append(p)
                else:
                    cl.append([p])
            for grp in cl:
                if len(grp) < 2:
                    continue
                lo_p, hi_p = grp[0], grp[-1]
                if L[b] < lo_p and C[b] > hi_p:      # furou o pool inteiro e fechou acima = sweep+reject
                    return True
        return False

    eps = [json.loads(l) for l in open(HERE / "episodes.jsonl") if l.strip()]
    ti = {t: i for i, t in enumerate(T)}
    for e in eps:
        i = ti.get(e["t"])
        e["pool"] = pool_sweep_at(i) if i is not None else None

    def panel(rl, cost=0.2):
        n = len(rl); w = sum(1 for r in rl if r > 0); s = sum(r - cost for r in rl)
        cum = peak = dd = 0.0; stk = mx = 0
        for r in rl:
            cum += r - cost; peak = max(peak, cum); dd = min(dd, cum - peak)
            stk = stk + 1 if r <= 0 else 0; mx = max(mx, stk)
        return dict(N=n, WR=round(100 * w / n) if n else None, sumR=round(s, 1),
                    avgR=round(s / n, 2) if n else None, maxDD=round(dd, 1), streak=mx)

    on = [e["R"] for e in eps if e["pool"]]
    off = [e["R"] for e in eps if e["pool"] is False]
    p_on, p_off = panel(on), panel(off)
    print(f"POOL-SWEEP no fundo: SIM {p_on}")
    print(f"                     NÃO {p_off}")
    # por semestre
    hv = {}
    for e in eps:
        if e["pool"] is None: continue
        hv.setdefault(e["half"], [0.0, 0.0])
        hv[e["half"]][0 if e["pool"] else 1] += e["R"] - 0.2
    print("por-semestre c0.2 [SIM, NÃO]:", {k: [round(a, 1), round(b, 1)] for k, (a, b) in sorted(hv.items())})
    # block-null shift circular sobre gap de avgR
    flags = [bool(e["pool"]) for e in eps if e["pool"] is not None]
    rs = [e["R"] for e in eps if e["pool"] is not None]
    gap = (p_on["avgR"] or 0) - (p_off["avgR"] or 0)
    ge = 0
    for _ in range(2000):
        k = rnd.randint(1, len(flags) - 1)
        fl = flags[k:] + flags[:k]
        a = [r for r, f in zip(rs, fl) if f]; b = [r for r, f in zip(rs, fl) if not f]
        if a and b and (sum(a) / len(a) - sum(b) / len(b)) >= gap:
            ge += 1
    print(f"gap avgR {gap:+.2f}R · p_blocknull {ge/2000:.3f} · freq SIM {sum(flags)/len(flags):.0%}")
    json.dump(dict(on=p_on, off=p_off, halves=hv, gap=gap, p=ge / 2000),
              open(HERE / "pool_sweep_results.json", "w"), indent=1)
    print("gravado pool_sweep_results.json")


if __name__ == "__main__":
    main()
