#!/usr/bin/env python3
"""LAG DE CONFIRMAÇÃO — execução do prereg selado. Reusa o harness validado do a2_anchor_lag (mesma base
de fundos rasos GT + try_trigger parametrizado por m_frac), acrescenta o braço REJEIÇÃO-NA-VELA (lag 0).
Mede resultado + lag + preço-de-entrada-vs-fundo por braço. py3.9 stdlib. SANITY_PROBE n/a: prereg'd."""
import json
import random
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "my-strategy/core"))
sys.path.insert(0, str(REPO / "my-strategy/research/revalidation/a2_anchor_lag_20260821"))
sys.path.insert(0, str(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2"))
import raw_reader as RR  # noqa: E402
import run_study as AL   # noqa: E402  (harness a2_anchor_lag: build_series, shallow_bottoms, try_trigger, outcome)

SEED = 20260828


def rej_trigger(S, j):
    """REJEIÇÃO-NA-VELA (método do Cris, lag 0): a partir do fundo j, a 1ª barra k>=j cujo LOW fura o
    low anterior (L[k]<L[k-1]) E fecha acima do open E no terço SUPERIOR do próprio range. Entrada=C[k],
    SL=L[k]-0.1ATR. Causal: só usa a própria barra k (fecho conhecido no fecho de k)."""
    L, O, H, C, ATR, N = S["L"], S["O"], S["H"], S["C"], S["ATR"], S["N"]
    for k in range(j, min(N, j + 48)):
        rng = H[k] - L[k]
        if rng <= 0:
            continue
        pierce = L[k] < L[k - 1] if k > 0 else False
        reject = C[k] > O[k] and (C[k] - L[k]) >= 0.66 * rng      # fecho no terço superior
        if pierce and reject:
            atr = ATR[k] or 5.0
            sl = round(L[k] - 0.1 * atr, 2); ent = C[k]; r = ent - sl
            if r <= 0.05 * atr or r > 2.5 * atr:
                continue
            return dict(k=k, ent=ent, sl=sl, r=r, lag=k - j)
    return None


def main():
    rnd = random.Random(SEED)
    bars = RR.series_flat(RR.resolve_gz("XAUUSD", "15M"))
    rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(bars.items())]
    S = AL.build_series(rows)
    bots = AL.shallow_bottoms(S)
    print(f"RAW 15M {S['N']} barras · fundos rasos GT {len(bots)}")

    def panel(rl, cost=0.2):
        n = len(rl); w = sum(1 for r in rl if r > 0); s = sum(r - cost for r in rl)
        cum = peak = dd = 0.0; stk = mx = 0
        for r in rl:
            cum += r - cost; peak = max(peak, cum); dd = min(dd, cum - peak)
            stk = stk + 1 if r <= 0 else 0; mx = max(mx, stk)
        return dict(N=n, WR=round(100 * w / n) if n else None, sumR=round(s, 1),
                    avgR=round(s / n, 2) if n else None, maxDD=round(dd, 1), streak=mx)

    def half(k):
        d = dt.datetime.fromtimestamp(S["T"][k], dt.timezone.utc)
        return f"{d.year}-H{1 if d.month <= 6 else 2}"

    arms = {"m3": lambda j: AL.try_trigger(S, j, 3, "MB3"),
            "m2": lambda j: AL.try_trigger(S, j, 2, "MB3"),
            "m1": lambda j: AL.try_trigger(S, j, 1, "MB3"),
            "rej": lambda j: rej_trigger(S, j)}
    res = {}
    arm_trades = {}
    for name, fn in arms.items():
        trades = []
        for b in bots:
            t = fn(b["j"])
            if t is None:
                continue
            o, R = AL.outcome(S, t["k"], t["ent"], t["sl"])
            fundo = S["L"][b["j"]]
            trades.append(dict(k=t["k"], R=R, lag=t["lag"], half=half(t["k"]),
                               pior=round(t["ent"] - fundo, 1)))   # quanto acima do fundo entrou
        arm_trades[name] = trades
        rs = [x["R"] for x in trades]
        lags = sorted(x["lag"] for x in trades)
        piors = sorted(x["pior"] for x in trades)
        hv = {}
        for x in trades:
            hv[x["half"]] = round(hv.get(x["half"], 0) + x["R"] - 0.2, 1)
        med = lambda a: a[len(a) // 2] if a else None
        res[name] = dict(panel=panel(rs), lag_med=med(lags),
                         preco_acima_fundo_med=med(piors), halves=hv)
        print(f"\n[{name}] {res[name]['panel']}")
        print(f"     lag mediano {res[name]['lag_med']}b · entra {res[name]['preco_acima_fundo_med']}pt acima do fundo · semestres {hv}")

    # null: melhor braço (por avgR c0.2) vs m3 — block-shuffle pareado nos fundos com AMBOS os gatilhos
    best = max((n for n in arms if n != "m3"), key=lambda n: res[n]["panel"]["avgR"] or -9)
    common = {}
    for name in ("m3", best):
        for x in arm_trades[name]:
            common.setdefault(x["k"], {})[name] = x["R"]
    pares = [(v["m3"], v[best]) for v in common.values() if "m3" in v and best in v]
    if pares:
        gap = sum(b - a for a, b in pares) / len(pares)
        ge = 0
        arr = [b - a for a, b in pares]
        for _ in range(2000):
            s = rnd.choice([-1, 1])
            if sum(x * (1 if rnd.random() < 0.5 else -1) for x in arr) / len(arr) >= abs(gap):
                ge += 1
        print(f"\nnull pareado {best} vs m3 (N={len(pares)}): gap avgR {gap:+.2f}R · p {ge/2000:.3f}")
        res["null"] = dict(best=best, n_par=len(pares), gap=round(gap, 3), p=round(ge / 2000, 3))

    (HERE / "results.json").write_text(json.dumps(res, indent=1))
    print("\ngravado results.json")


if __name__ == "__main__":
    main()
