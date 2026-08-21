#!/usr/bin/env python3
"""A2 V1 RE-RUN — prereg 2295898. Censo com detect REAL (M_FRAC patched por source no módulo-mãe),
interferência A1, E1 entrada-limite no retest_zone, null 300reps c/ guarda 2.5×ATR, custos. py3.9."""
import inspect
import json
import random
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "my-strategy/core"))
sys.path.insert(0, str(REPO / "my-strategy/research/revalidation"))
sys.path.insert(0, str(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2"))
import raw_reader as RR  # noqa: E402
import a1_causal_entry as ACE  # noqa: E402
import a1a2_runtime as RT  # noqa: E402

OUT = Path(__file__).resolve().parent
SEED = 20260821
HORIZON = 480


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


def census(S, m_frac):
    """Censo barra-a-barra com o detect REAL, M_FRAC do módulo-mãe patched (restaurado no fim)."""
    old = ACE.M_FRAC
    ACE.M_FRAC = m_frac
    try:
        sigs = []
        for i in range(200, S["N"]):
            Sw = {k: (v[:i + 1] if isinstance(v, list) else v) for k, v in S.items()}
            Sw["N"] = i + 1
            r, why = RT.detect(Sw)
            if r:
                sigs.append(dict(i=i, layer=r["layer"], depth=r["depth_atr"], ent=r["ent"],
                                 sl=r["sl"], tgt=r["tgt"], rz=r.get("retest_zone"),
                                 bpct=r.get("bounce_pct")))
        return sigs
    finally:
        ACE.M_FRAC = old


def episodes(sigs, gap=8):
    out = []
    for s in sigs:
        if out and s["i"] - out[-1]["i"] <= gap:
            continue
        out.append(s)
    return out


def outcome(S, k, ent, sl, tgt):
    H, L = S["H"], S["L"]
    for m in range(k + 1, min(S["N"], k + HORIZON)):
        if L[m] <= sl: return -1.0
        if H[m] >= tgt: return 3.0
    return 0.0


def panel(rs, cost=0.0):
    n = len(rs); w = sum(1 for r in rs if r > 0)
    s = sum(r - cost for r in rs)
    return dict(N=n, W=w, WR=round(100 * w / n) if n else None, sumR=round(s, 1))


def limit_entry(S, sig):
    """E1: limite no topo do retest_zone; fill = low<=nível em <=16b; outcome mesmo SL, 3R do novo entry."""
    rz = sig.get("rz")
    if not rz:
        return None
    level = max(rz)                                   # topo da zona (primeiro a ser tocado por cima)
    if level >= sig["ent"]:
        return None
    for k in range(sig["i"] + 1, min(S["N"], sig["i"] + 17)):
        if S["L"][k] <= level:
            risk = level - sig["sl"]
            if risk <= 0:
                return None
            tgt = level + 3 * risk
            return dict(k=k, ent=level, R=outcome(S, k, level, sig["sl"], tgt),
                        bpct_new=None)
    return dict(k=None, ent=None, R=None)             # no-fill


def main():
    rnd = random.Random(SEED)
    blocks = RR.resolve_gz("XAUUSD", "15M")
    bars = RR.series_flat(blocks)
    rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(bars.items())]
    S = build_series(rows)
    half = lambda i: dt.datetime.fromtimestamp(S["T"][i], dt.timezone.utc).strftime(
        "%Y-H1" if dt.datetime.fromtimestamp(S["T"][i], dt.timezone.utc).month <= 6 else "%Y-H2")

    # P1: identidade — census(m=3) tem de bater o censo do estudo anterior (A1 816 · A2 73)
    s3 = census(S, 3)
    a1_3 = [x for x in s3 if x["layer"] == "A1"]; a2_3 = [x for x in s3 if x["layer"] == "A2"]
    print(f"P1 censo m=3 (identidade): A1 {len(a1_3)} · A2 {len(a2_3)} (esperado 816/73)")
    assert (len(a1_3), len(a2_3)) == (816, 73), "identidade falhou — HARD_STOP"

    s2 = census(S, 2)
    a1_2 = [x for x in s2 if x["layer"] == "A1"]; a2_2 = [x for x in s2 if x["layer"] == "A2"]
    print(f"censo m=2: A1 {len(a1_2)} · A2 {len(a2_2)}")

    # interferência no A1: episódios A1 (m=3) que desaparecem ou mudam com m=2
    ep1_3 = episodes(a1_3); ep1_2 = episodes(a1_2)
    keys_3 = {x["i"] for x in ep1_3}; keys_2 = {x["i"] for x in ep1_2}
    lost = keys_3 - {i for i in keys_3 if any(abs(i - j) <= 2 for j in keys_2)}
    r_a1_3 = [outcome(S, x["i"], x["ent"], x["sl"], x["tgt"]) for x in ep1_3]
    lost_win = sum(1 for x, r in zip(ep1_3, r_a1_3) if x["i"] in lost and r > 0)
    print(f"interferência A1: episódios m=3 {len(ep1_3)} · m=2 {len(ep1_2)} · perdidos {len(lost)} · WINs perdidos {lost_win}")

    # A2 outcomes por episódio (m=3 e m=2) + custos
    res = {}
    for tag, sigs in [("A2_m3", a2_3), ("A2_m2", a2_2)]:
        eps = episodes(sigs)
        rs = [outcome(S, x["i"], x["ent"], x["sl"], x["tgt"]) for x in eps]
        halves = {}
        for x, r in zip(eps, rs):
            halves[half(x["i"])] = round(halves.get(half(x["i"]), 0) + r, 1)
        res[tag] = dict(panel0=panel(rs), panel02=panel(rs, 0.2), panel035=panel(rs, 0.35),
                        bpct_med=sorted([x["bpct"] for x in eps if x["bpct"] is not None])[len(eps) // 2] if eps else None,
                        halves=halves)
        print(f"{tag}: eps {len(eps)} · 0R {res[tag]['panel0']} · c0.35 {res[tag]['panel035']} · "
              f"bounce% {res[tag]['bpct_med']} · {halves}")

    # NULL corrigido (300 reps/episódio, guarda 2.5×ATR) para A2_m2
    eps2 = episodes(a2_2)
    nw = nn = 0
    for x in eps2:
        j0 = x["i"] - 24 if x["i"] >= 24 else 0       # janela do pullback aproximada pelo PB_WIN
        for _ in range(300):
            ei = rnd.randint(j0 + 1, min(S["N"] - 2, j0 + 48))
            ent = S["C"][ei]; atr = S["ATR"][ei] or 5.0
            anchor = min(S["L"][j0:ei + 1]); sl = anchor - 0.1 * atr
            r = ent - sl
            if r <= 0.05 * atr or r > 2.5 * atr:       # MESMAS guardas do detect (fix DA)
                continue
            nn += 1
            if outcome(S, ei, ent, sl, ent + 3 * r) > 0: nw += 1
    null_wr = round(100 * nw / nn, 1) if nn else None
    print(f"null corrigido (300reps, guarda 2.5×ATR): WR {null_wr}% (n={nn})")

    # E1: entrada-limite no retest_zone (sobre A2 m=3 e m=2)
    for tag, sigs in [("E1_sobre_m3", a2_3), ("E1_sobre_m2", a2_2)]:
        eps = episodes(sigs)
        fills, nofill = [], 0
        for x in eps:
            e = limit_entry(S, x)
            if e is None:
                continue
            if e["k"] is None:
                nofill += 1
            else:
                fills.append(e["R"])
        mk = panel([outcome(S, x["i"], x["ent"], x["sl"], x["tgt"]) for x in eps])
        comb = sum(fills)                              # no-fill = 0
        print(f"{tag}: eps {len(eps)} · fills {len(fills)} · no-fill {nofill} · "
              f"market sumR {mk['sumR']} vs limite-comb sumR {round(comb,1)} · fills {panel(fills)}")

    (OUT / "results_summary.json").write_text(json.dumps(dict(
        censo=dict(m3=dict(a1=len(a1_3), a2=len(a2_3)), m2=dict(a1=len(a1_2), a2=len(a2_2))),
        interferencia=dict(ep_m3=len(ep1_3), ep_m2=len(ep1_2), lost=len(lost), lost_win=lost_win),
        a2=res, null_wr=null_wr), indent=1))
    print("gravado results_summary.json")


if __name__ == "__main__":
    main()
