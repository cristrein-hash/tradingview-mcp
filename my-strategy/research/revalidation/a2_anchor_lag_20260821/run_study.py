#!/usr/bin/env python3
"""A2 ANCHOR-LAG — execução do prereg selado (5a829c3). RAW canónico via raw_reader.series_flat;
detetor REAL a1a2_runtime.detect replayed barra-a-barra (gate OFF declarado). py3.9 stdlib."""
import json
import random
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "my-strategy/core"))
sys.path.insert(0, str(REPO / "my-strategy/research/revalidation"))
sys.path.insert(0, str(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2"))
import raw_reader as RR  # noqa: E402  (leitor canónico — hook raw_read_guard satisfeito)
import a1_causal_entry as ACE  # noqa: E402

OUT = Path(__file__).resolve().parent
SEED = 20260821
HH_WIN, HH_GAP, PB_WIN = 96, 8, 24
PB_MIN, A2_MAX = 1.0, 2.0
M_FRAC_BASE = ACE.M_FRAC


def build_series(rows):
    T = [r["t"] for r in rows]; O = [r["o"] for r in rows]; H = [r["h"] for r in rows]
    L = [r["l"] for r in rows]; C = [r["c"] for r in rows]
    N = len(rows); EMA = [None] * N; ATR = [None] * N
    ema = None; kE = 2 / 22; trs = []
    for i in range(N):
        ema = C[i] if ema is None else C[i] * kE + ema * (1 - kE); EMA[i] = ema
        if i > 0: trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
        ATR[i] = sum(trs[-14:]) / 14 if len(trs) >= 14 else None
    return dict(T=T, O=O, H=H, L=L, C=C, EMA=EMA, ATR=ATR, N=N)


def shallow_bottoms(S):
    """GT mecânico Q2: barras j que são fundo de pullback raso (mesmas janelas do detect), avaliado
    no PRIMEIRO i em que o fundo é visível (i=j+1..) — deduplicado por j."""
    T, H, L, ATR = S["T"], S["H"], S["L"], S["ATR"]
    N = S["N"]; seen = set(); out = []
    for i in range(HH_WIN + HH_GAP, N):
        atr = ATR[i] or 5.0
        hw = range(max(0, i - HH_WIN), i - HH_GAP)
        hh_i = max(hw, key=lambda z: H[z]); hh = H[hh_i]
        j = min(range(hh_i + 1, i + 1), key=lambda z: L[z])
        if j in seen or i - j > PB_WIN:
            continue
        depth = (hh - L[j]) / atr
        if PB_MIN <= depth <= A2_MAX and j < i:      # fundo raso candidato
            seen.add(j); out.append(dict(j=j, i_seen=i, hh=hh, hh_i=hh_i, depth=round(depth, 2)))
    return out


def try_trigger(S, j, m_frac, kind):
    """A partir do fundo j: 1º gatilho válido (fractal m_frac confirmado + trigger kind) e diagnóstico."""
    L, O, H, C, EMA, ATR, N = S["L"], S["O"], S["H"], S["C"], S["EMA"], S["ATR"], S["N"]
    def swinglow(p, m):
        return (p - m >= 0 and p + m < N and L[p] == min(L[p - m:p + m + 1]))
    for k in range(j + 1, min(N, j + 48)):
        p = k - m_frac
        confirmed = p >= j and swinglow(p, m_frac)   # fractal do próprio fundo (>=j) confirmado em k
        if not confirmed:
            continue
        if kind == "MB3":
            trig = C[k] > O[k] and C[k] > H[k - 1]
        else:  # RCL
            trig = EMA[k] is not None and C[k] > EMA[k] and C[k] > C[k - 1]
        if not trig:
            continue
        anchor_low = min(L[j:k + 1]); atr = ATR[k] or 5.0
        sl = round(anchor_low - 0.1 * atr, 2); ent = C[k]; r = ent - sl
        if r <= 0.05 * atr or r > 2.5 * atr:          # guarda de escala aprovada
            continue
        return dict(k=k, ent=ent, sl=sl, r=r, lag=k - j)
    return None


def outcome(S, k, ent, sl):
    H, L = S["H"], S["L"]; tgt = ent + 3 * (ent - sl)
    for m in range(k + 1, min(S["N"], k + 480)):
        if L[m] <= sl: return "LOSS", -1.0
        if H[m] >= tgt: return "WIN", 3.0
    return "OPEN", 0.0


def main():
    blocks = RR.resolve_gz("XAUUSD", "15M")
    bars = RR.series_flat(blocks)                 # {t:[o,h,l,c]} (padrão a1_causal_entry, merge)
    rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(bars.items())]
    S = build_series(rows)
    print(f"RAW 15M: {S['N']} barras {dt.datetime.fromtimestamp(S['T'][0], dt.timezone.utc):%Y-%m}→"
          f"{dt.datetime.fromtimestamp(S['T'][-1], dt.timezone.utc):%Y-%m}")

    # ===== Q1: censo A2 do detetor REAL barra-a-barra =====
    import a1a2_runtime as RT
    n_a2 = n_a1 = 0
    sigs = []
    for i in range(200, S["N"]):
        Sw = {k: (v[:i + 1] if isinstance(v, list) else v) for k, v in S.items()}
        Sw["N"] = i + 1
        r, why = RT.detect(Sw)
        if r:
            sigs.append(dict(i=i, layer=r["layer"], depth=r["depth_atr"]))
            if r["layer"] == "A2": n_a2 += 1
            else: n_a1 += 1
    print(f"Q1: detetor real em 2 anos — A1 {n_a1} · A2 {n_a2}")

    # ===== Q2: fundos rasos + onde morre =====
    bots = shallow_bottoms(S)
    diag = {"sem_fractal_ou_trigger": 0, "capturado_base": 0}
    lags, bpcts = [], []
    for b in bots:
        t = try_trigger(S, b["j"], M_FRAC_BASE, "MB3")
        if t is None:
            diag["sem_fractal_ou_trigger"] += 1
        else:
            diag["capturado_base"] += 1
            lags.append(t["lag"])
            bounce = t["ent"] - S["L"][b["j"]]
            full = b["hh"] - S["L"][b["j"]]
            bpcts.append(round(100 * bounce / full) if full > 0 else None)
    med = lambda a: sorted(a)[len(a) // 2] if a else None
    print(f"Q2: fundos rasos GT {len(bots)} · capturáveis pela mecânica-base {diag['capturado_base']} · "
          f"perdidos {diag['sem_fractal_ou_trigger']} · lag mediano {med(lags)}b · bounce% mediano no gatilho {med([b for b in bpcts if b is not None])}")

    # ===== Q3: variantes V1/V2 nos fundos rasos =====
    rnd = random.Random(SEED)
    res = {}
    for vname, m_frac, kind in [("base", M_FRAC_BASE, "MB3"), ("V1_mfrac2", 2, "MB3"), ("V2_rcl", M_FRAC_BASE, "RCL")]:
        trades = []
        for b in bots:
            t = try_trigger(S, b["j"], m_frac, kind)
            if t is None:
                continue
            o, R = outcome(S, t["k"], t["ent"], t["sl"])
            bounce = t["ent"] - S["L"][b["j"]]; full = b["hh"] - S["L"][b["j"]]
            trades.append(dict(j=b["j"], k=t["k"], o=o, R=R, lag=t["lag"],
                               bpct=round(100 * bounce / full) if full > 0 else None,
                               half=dt.datetime.fromtimestamp(S["T"][t["k"]], dt.timezone.utc).strftime("%Y-H1" if dt.datetime.fromtimestamp(S["T"][t["k"]], dt.timezone.utc).month <= 6 else "%Y-H2")))
        n = len(trades); w = sum(1 for x in trades if x["o"] == "WIN")
        l = sum(1 for x in trades if x["o"] == "LOSS")
        sumr = sum(x["R"] for x in trades)
        halves = {}
        for x in trades:
            halves[x["half"]] = halves.get(x["half"], 0) + x["R"]
        # null: por trade real, 20 entradas aleatórias na mesma janela com a MESMA regra de SL
        nw = nn = 0
        for x in trades:
            for _ in range(20):
                ei = rnd.randint(x["j"] + 1, min(S["N"] - 2, x["j"] + 48))
                ent = S["C"][ei]
                anchor_low = min(S["L"][x["j"]:ei + 1]); atr = S["ATR"][ei] or 5.0
                slr = anchor_low - 0.1 * atr
                if ent - slr <= 0.05 * atr:
                    continue
                nn += 1
                o, _ = outcome(S, ei, ent, slr)
                if o == "WIN": nw += 1
        wrn = round(100 * nw / nn) if nn else None
        res[vname] = dict(n=n, w=w, l=l, sumR=round(sumr, 1), wr=round(100 * w / n) if n else None,
                          lag_med=med([x["lag"] for x in trades]), bpct_med=med([x["bpct"] for x in trades if x["bpct"] is not None]),
                          null_wr=wrn, halves={k: round(v, 1) for k, v in sorted(halves.items())})
        print(f"Q3 [{vname}] n={n} {w}W-{l}L sumR {sumr:+.1f} WR {res[vname]['wr']}% "
              f"(null {wrn}%) · lag {res[vname]['lag_med']}b · bounce {res[vname]['bpct_med']}% · {res[vname]['halves']}")

    (OUT / "results_summary.json").write_text(json.dumps(dict(
        bars=S["N"], q1=dict(a1=n_a1, a2=n_a2), q2=dict(bots=len(bots), **diag,
        lag_med=med(lags)), q3=res), indent=1))
    print("gravado results_summary.json")


if __name__ == "__main__":
    main()
