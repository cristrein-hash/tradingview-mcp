#!/usr/bin/env python3
"""A1/A2 DEEP AUDIT — manifest selado. Censo real + features causais (estruturais + indicadores LIDOS
do RAW as-of) + variante buy-limit. EXPLORATÓRIO. py3.9 stdlib. SANITY_PROBE n/a (é o estudo prereg'd;
leitura multi-fatorial: estrutura+regime+indicador+trajetória-bounce, dois objetivos: reter winners e
cortar losers)."""
import bisect
import json
import random
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "my-strategy/core"))
sys.path.insert(0, str(REPO / "my-strategy/core/layer1_service"))
sys.path.insert(0, str(REPO / "my-strategy/research/revalidation"))
sys.path.insert(0, str(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2"))
import raw_reader as RR  # noqa: E402
sys.path.insert(0, str(REPO / "my-strategy/research/revalidation/distrib_signature_20260828"))
from run_study import build, distrib_flag, K1H  # noqa: E402
from run_study_v2 import atr14  # noqa: E402

OUT = Path(__file__).resolve().parent
SEED = 20260828
EP_GAP, HORIZON, FILL_WIN = 8, 480, 16
LX = dt.timezone(dt.timedelta(hours=1))


def outcome(S, k, ent, sl, fillbar_counts=False):
    tgt = ent + 3 * (ent - sl)
    if fillbar_counts and S["L"][k] <= sl:
        return -1.0
    for m in range(k + 1, min(S["N"], k + HORIZON)):
        if S["L"][m] <= sl: return -1.0
        if S["H"][m] >= tgt: return 3.0
    return 0.0


def panel(rl, cost=0.2):
    n = len(rl); w = sum(1 for r in rl if r > 0)
    s = sum(r - cost for r in rl)
    cum = peak = dd = 0.0; stk = mx = 0
    for r in rl:
        cum += r - cost; peak = max(peak, cum); dd = min(dd, cum - peak)
        stk = stk + 1 if r <= 0 else 0; mx = max(mx, stk)
    return dict(N=n, WR=round(100 * w / n) if n else None, sumR=round(s, 1),
                avgR=round(s / n, 2) if n else None, maxDD=round(dd, 1), streak=mx)


def raw_asof_index(gzs):
    """Uma passagem pelos RAW recs: t → features LIDAS (RSI, zonas OB v11, volume). Nunca re-derivadas."""
    idx = {}
    for g in gzs:
        for rec in RR.iter_records(g):
            b = RR.bar(rec)
            if not b:
                continue
            t = b["t"]; f = {}
            for s in rec.get("study_values") or []:
                if s.get("name") == "Relative Strength Index":
                    v = s.get("values") or {}
                    try: f["rsi"] = float(v.get("RSI"))
                    except Exception: pass
            zones = []
            for bx in rec.get("pine_boxes") or []:
                if "OB Detector" in (bx.get("name") or ""):
                    zones = bx.get("zones") or []
            f["ob_zones"] = [(z["low"], z["high"]) for z in zones if z.get("low") is not None]
            ohl = rec.get("ohlcv") or []
            if ohl and ohl[-1].get("volume") is not None:
                f["vol"] = ohl[-1]["volume"]
            idx[t] = f
    return idx


def regime_labels():
    import layer1_cycle as LC
    import macro_structural_v3 as M
    xau = LC._merge_xau_1d()
    M.T = [b["t"] for b in xau]; M.O = [b["o"] for b in xau]; M.H = [b["h"] for b in xau]
    M.L = [b["l"] for b in xau]; M.C = [b["c"] for b in xau]; M.N = len(xau)
    dxy = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/raw_dxy_1d.jsonl") if l.strip()]
    M.DXY_K = [b["t"] + 86400 for b in dxy]; M.DXY_C = [b["c"] for b in dxy]
    return M.T, M.build_layer1()


def main():
    gzs = RR.resolve_gz("XAUUSD", "15M")
    bars = RR.series_flat(gzs)
    rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(bars.items())]
    S = build(rows)
    T, H, L, C, EMA, ATR = S["T"], S["H"], S["L"], S["C"], S["EMA"], S["ATR"]
    print("a construir índice as-of dos indicadores RAW (1 passagem)...")
    AS = raw_asof_index(gzs)
    print(f"as-of index: {len(AS)} barras com features · cobertura {len(AS)/S['N']:.0%}")
    h1 = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/raw_1h_ohlc.jsonl") if l.strip()]
    h1.sort(key=lambda x: x["t"])
    T1, H1c, C1 = [b["t"] for b in h1], [b["h"] for b in h1], [b["c"] for b in h1]
    ATR1 = atr14(H1c, [b["l"] for b in h1], C1)
    T1d, lab1d = regime_labels()

    # DA-fix: label da última sessão 1D já FECHADA antes de t (fecho = stamp+23h; sessão XAU 22:00→21:00 UTC).
    # A versão anterior usava a sessão que CONTÉM t = fecho do próprio dia = leak (15/863 episódios afetados).
    T1d_close = [tt + 82800 for tt in T1d]

    def reg_at(t):
        i = bisect.bisect_right(T1d_close, t) - 1
        return lab1d[i] if 0 <= i < len(lab1d) else None

    import a1a2_runtime as RT
    eps = []; last_i = -10**9
    for i in range(200, S["N"]):
        Sw = {k: (v[:i + 1] if isinstance(v, list) else v) for k, v in S.items()}
        Sw["N"] = i + 1
        r, why = RT.detect(Sw)
        if not r or i - last_i < EP_GAP:
            continue
        last_i = i
        atr = ATR[i] or 5.0
        ent, sl = r["ent"], r["sl"]
        rz = r.get("retest_zone") or (ent, ent)
        R_mkt = outcome(S, i, ent, sl)
        # buy-limit: topo do retest_zone; fill em <=16b; fill-bar SL conta; 3R do limite
        lim = max(rz)
        fk = next((k for k in range(i + 1, min(S["N"], i + FILL_WIN + 1)) if L[k] <= lim), None)
        R_lim = outcome(S, fk, lim, sl, fillbar_counts=True) if fk is not None else None
        # features
        j = bisect.bisect_right(T1, T[i]) - 1
        while j >= 0 and T1[j] + 3600 > T[i]:
            j -= 1
        v1h = distrib_flag(H1c, C1, ATR1[j], j, K1H) if j > 0 and ATR1[j] else False
        f = AS.get(T[i], {})
        obz = f.get("ob_zones") or []
        inside = any(lo <= C[i] <= hi for lo, hi in obz)
        below = any(hi < C[i] and (C[i] - hi) <= 1.0 * atr for lo, hi in obz)
        lx = dt.datetime.fromtimestamp(T[i], LX)
        eps.append(dict(
            t=T[i], layer=r["layer"], R=R_mkt, R_lim=R_lim, lim_fill=fk is not None,
            depth=r.get("depth_atr"), risk_atr=round((ent - sl) / atr, 2),
            ema_d=round((C[i] - EMA[i]) / atr, 2) if EMA[i] else None,
            hour=lx.hour, wd=lx.weekday(), reg=reg_at(T[i]), v1h=v1h,
            rsi=f.get("rsi"), ob_in=inside, ob_below=below, has_asof=T[i] in AS,
            half=f"{lx.year}-H{1 if lx.month <= 6 else 2}"))
    print(f"censo: {len(eps)} episódios · com as-of {sum(1 for e in eps if e['has_asof'])}")

    res = {"n": len(eps)}
    def show(tag, sub):
        p = panel([e["R"] for e in sub])
        print(f"  {tag:<34} {p}")
        return p

    print("\n=== BASELINE (custo 0.2) ===")
    res["base"] = show("todos", eps)
    res["A1"] = show("A1", [e for e in eps if e["layer"] == "A1"])
    res["A2"] = show("A2", [e for e in eps if e["layer"] == "A2"])

    print("\n=== BUY-LIMIT vs MARKET (mesmos episódios, custo 0.2) ===")
    fills = [e for e in eps if e["lim_fill"]]
    res["mkt_all"] = show("market (todos)", eps)
    res["lim_fills"] = panel([e["R_lim"] for e in fills])
    print(f"  {'limit (fills)':<34} {res['lim_fills']}")
    nofill = [e for e in eps if not e["lim_fill"]]
    res["nofill"] = dict(n=len(nofill), winners_perdidos=sum(1 for e in nofill if e["R"] > 0),
                         losers_evitados=sum(1 for e in nofill if e["R"] < 0),
                         sumR_perdido=round(sum(e["R"] for e in nofill), 1))
    print(f"  no-fill {res['nofill']}")
    res["mkt_dos_fills"] = panel([e["R"] for e in fills])
    print(f"  {'market (só episódios que fillam)':<34} {res['mkt_dos_fills']}")

    print("\n=== SPLITS EXPLORATÓRIOS (custo 0.2; hipóteses, NÃO regras) ===")
    splits = {
        "reg BULL": lambda e: e["reg"] == "BULL",
        "reg TRANSITION": lambda e: e["reg"] == "TRANSITION",
        "reg BEAR": lambda e: e["reg"] == "BEAR",
        "distrib v1h ON": lambda e: e["v1h"],
        "OB: dentro de zona": lambda e: e["ob_in"],
        "OB: zona <=1ATR abaixo": lambda e: e["ob_below"] and not e["ob_in"],
        "OB: sem zona perto": lambda e: not (e["ob_in"] or e["ob_below"]),
        "RSI<40 no gatilho": lambda e: (e["rsi"] or 99) < 40,
        "RSI 40-60": lambda e: e["rsi"] is not None and 40 <= e["rsi"] <= 60,
        "RSI>60": lambda e: (e["rsi"] or 0) > 60,
        "risk<=1.0 ATR": lambda e: e["risk_atr"] <= 1.0,
        "risk >1.5 ATR": lambda e: e["risk_atr"] > 1.5,
        "sessão LDN+NY (08-17 Lx)": lambda e: 8 <= e["hour"] <= 17,
        "madrugada (00-07 Lx)": lambda e: e["hour"] <= 7,
        "fim de tarde/noite (18-23)": lambda e: e["hour"] >= 18,
        "segunda-feira": lambda e: e["wd"] == 0,
        "depth<=1.5 (raso)": lambda e: (e["depth"] or 9) <= 1.5,
        "ema_d<0 (sob EMA21)": lambda e: (e["ema_d"] or 0) < 0,
    }
    res["splits"] = {}
    for tag, fn in splits.items():
        dom = eps if not tag.startswith(("RSI", "OB")) else [e for e in eps if e["has_asof"]]
        res["splits"][tag] = show(tag, [e for e in dom if fn(e)])

    # composto localização (multi-fator: estrutura+regime+zona lida): BULL/TRANSITION + OB in/below + risk<=1.5
    print("\n=== COMPOSTO (multi-fatorial) ===")
    dom = [e for e in eps if e["has_asof"]]
    comp = [e for e in dom if e["reg"] in ("BULL", "TRANSITION") and (e["ob_in"] or e["ob_below"]) and e["risk_atr"] <= 1.5]
    res["comp_loc"] = show("localizado (reg+OB+escala)", comp)
    res["comp_resto"] = show("resto (com as-of)", [e for e in dom if e not in comp])

    # null nos 2 melhores candidatos (block-shuffle avgR) — feito no relatório se algum separar
    (OUT / "episodes.jsonl").write_text("\n".join(json.dumps(e) for e in eps) + "\n")
    (OUT / "results.json").write_text(json.dumps(res, indent=1))
    print("\ngravado episodes.jsonl + results.json")


if __name__ == "__main__":
    main()
