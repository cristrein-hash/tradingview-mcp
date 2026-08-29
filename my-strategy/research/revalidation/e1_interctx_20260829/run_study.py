#!/usr/bin/env python3
"""E1 INTER-CTX vs ENTREGUE — execução do prereg selado. Reusa o harness e1_edge_2y (dossiê reconstruído
do RAW barra a barra) e corre o detect() REAL duas vezes por barra: braço A tal-qual; braço B com as 4
mudanças aplicadas POR CIMA dos candidatos crus de A (B1 veto-choch/lado, B3 pré-condições cruzadas,
B4 exclusão mútua, B2 fusão) — sem tocar no módulo (o detect é o mesmo; a inter-ctx é pós-processo
determinístico dos candidatos da MESMA barra, fiel às 4 mudanças seladas). py3.9. SANITY_PROBE n/a:
estudo prereg'd."""
import json
import sys
import datetime as dt
from collections import defaultdict
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "my-strategy/core"))
sys.path.insert(0, str(REPO / "alert-bridge"))
sys.path.insert(0, str(REPO / "my-strategy/research/revalidation/e1_edge_2y_20260828"))
import raw_reader as RR  # noqa: E402
import context_structure as CS  # noqa: E402
import e1_detector as E1  # noqa: E402
import run_replay as H  # noqa: E402   (harness validado: resample, resolve_from)

TFS = {"15": 1, "60": 4, "240": 16, "1D": 96}
CONT_RULES = {"bos_continuation", "ema_reclaim"}
DIST_ATR = 0.5


def interctx(cands, d, atr15):
    """As 4 mudanças seladas, aplicadas aos candidatos crus da barra (determinístico, sem estado extra)."""
    mtf = d["axes"]["mtf"]
    out = []
    for c in cands:
        tf = c.get("tf") if c.get("tf") in mtf else "15"
        m = mtf.get(tf) or {}
        ch = m.get("choch") or {}
        dirn = (c.get("direction") or "").upper()
        # B1: veto de lado por choch do TF
        if dirn == "LONG" and ch.get("dn"):
            continue
        if dirn == "SHORT" and ch.get("up"):
            continue
        # B3a: sweep_reclaim precisa de zona conhecida perto do nível varrido (usa o SL como proxy do low varrido)
        if c.get("rule") == "sweep_reclaim":
            zz = (m.get("zones") or {})
            z = zz.get("below") if dirn == "LONG" else zz.get("above")
            lvl = c.get("sl")
            ok = z and lvl is not None and (z.get("low") is not None) and \
                (z["low"] - DIST_ATR * atr15 <= lvl <= (z.get("high") or z["low"]) + DIST_ATR * atr15)
            if not ok:
                continue
        # B3b: ema_reclaim exige trend 60 na direção
        if c.get("rule") == "ema_reclaim":
            t60 = (mtf.get("60") or {}).get("trend")
            if (dirn == "LONG" and t60 != "UP") or (dirn == "SHORT" and t60 != "DOWN"):
                continue
        # B3c: continuação suspensa com choch contrário no TF (já coberto por B1 p/ o mesmo TF; aqui o 60)
        if c.get("rule") in CONT_RULES:
            ch60 = (mtf.get("60") or {}).get("choch") or {}
            if (dirn == "LONG" and ch60.get("dn")) or (dirn == "SHORT" and ch60.get("up")):
                continue
        out.append(c)
    # B4: exclusão mútua LONG×SHORT no mesmo TF
    by_tf = defaultdict(set)
    for c in out:
        by_tf[c.get("tf")].add((c.get("direction") or "").upper())
    out = [c for c in out if len(by_tf[c.get("tf")]) == 1]
    # B2: fusão por direção com entries <=0.5 ATR — fica o SL mais largo; regista n_regras
    merged = []
    for c in sorted(out, key=lambda x: (str(x.get("direction")), x.get("entry") or 0)):
        hit = None
        for mgd in merged:
            if mgd["direction"] == c.get("direction") and abs((mgd["entry"] or 0) - (c.get("entry") or 0)) <= DIST_ATR * atr15:
                hit = mgd
                break
        if hit:
            hit["n_rules"] += 1
            dirn = (c.get("direction") or "").upper()
            if c.get("sl") is not None and hit.get("sl") is not None:
                if (dirn == "LONG" and c["sl"] < hit["sl"]) or (dirn == "SHORT" and c["sl"] > hit["sl"]):
                    hit["sl"] = c["sl"]; hit["rule"] = hit["rule"] + "+" + c.get("rule", "?")
        else:
            merged.append(dict(c, n_rules=1))
    return merged


def main():
    bars = RR.series_flat(RR.resolve_gz("XAUUSD", "15M"))
    rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(bars.items())]
    N = len(rows)
    T15 = [r["t"] for r in rows]; H15 = [r["h"] for r in rows]; L15 = [r["l"] for r in rows]; C15 = [r["c"] for r in rows]
    print(f"RAW {N} barras", flush=True)

    tfdata = {}
    for tf, mult in TFS.items():
        if tf == "15":
            Hh, Ll, Cc, Tt = H15, L15, C15, T15
        else:
            Hh, Ll, Cc, Tt = H.resample(rows, mult)
        piv = CS.fractal_pivots(Hh, Ll, m=3)
        tfdata[tf] = dict(H=Hh, L=Ll, C=Cc, T=Tt, piv=sorted(piv, key=lambda e: e[0]))
    print("pivôs ok", flush=True)

    import bisect

    def struct_at(tf, t):
        d = tfdata[tf]; Tt = d["T"]
        i = bisect.bisect_right(Tt, t) - 1
        if i < 4:
            return None
        piv = [e for e in d["piv"] if e[0] <= i]
        highs = [e for e in piv if e[1] == "H"]; lows = [e for e in piv if e[1] == "L"]
        lh = highs[-1] if highs else None; ll = lows[-1] if lows else None
        ph = highs[-2] if len(highs) >= 2 else None; pl = lows[-2] if len(lows) >= 2 else None
        a = CS.atr(d["H"], d["L"], d["C"], i, 14)
        C = d["C"]
        trend = "RANGE"
        if lh and ph and ll and pl:
            if lh[3] > ph[3] and ll[3] > pl[3]: trend = "UP"
            elif lh[3] < ph[3] and ll[3] < pl[3]: trend = "DOWN"
        leg = None
        if lh and ll and a and lh[3] > ll[3]:
            lo, hi = ll[3], lh[3]
            leg = {"low": round(lo, 3), "high": round(hi, 3), "mag_atr": round((hi - lo) / a, 2),
                   "pos_in_leg": round(max(0.0, min(1.0, (C[i] - lo) / (hi - lo))), 2),
                   "dir": "up" if ll[0] < lh[0] else "down"}
        pv = lambda e: {"bar": e[2], "price": e[3], "confirm_bar": e[0]} if e else None
        return dict(trend=trend, leg=leg,
                    choch={"up": bool(lh and C[i] > lh[3]), "dn": bool(ll and C[i] < ll[3])},
                    swings={"last_high": pv(lh), "last_low": pv(ll), "prev_high": pv(ph), "prev_low": pv(pl)},
                    atr14=round(a, 4) if a else None)

    gz = RR.resolve_gz("XAUUSD", "15M")
    boxes_by_t = {}
    for g in gz:
        for rec in RR.iter_records(g):
            b = RR.bar(rec)
            if not b:
                continue
            zs = []
            for bx in rec.get("pine_boxes") or []:
                nm = bx.get("name") or ""
                if "OB Detector" in nm or "Smart Money" in nm:
                    for z in (bx.get("zones") or []):
                        if z.get("low") is not None:
                            zs.append((z["low"], z["high"]))
            boxes_by_t[b["t"]] = zs
    print(f"zonas as-of {len(boxes_by_t)}", flush=True)

    def zones_at(t, close):
        zs = boxes_by_t.get(t) or []
        above = sorted([z for z in zs if z[1] > close], key=lambda z: z[1])
        below = sorted([z for z in zs if z[0] < close], key=lambda z: -z[0])
        mk = lambda z: {"high": z[1], "low": z[0], "src": "ob"}
        return {"n": len(zs), "above": mk(above[0]) if above else None,
                "below": mk(below[0]) if below else None,
                "stack": {"above": [mk(z) for z in above[:6]], "below": [mk(z) for z in below[:6]]}}

    aggA = defaultdict(list); aggB = defaultdict(list)
    aggB_conv = []
    seenA = set(); seenB = set()
    prev = None
    step = max(1, N // 40)
    for i in range(200, N):
        t = T15[i]; close = C15[i]
        mtf = {}
        bad = False
        for tf in TFS:
            st = struct_at(tf, t)
            if st is None:
                bad = True
                break
            st = dict(st); st["zones"] = zones_at(t, close)
            mtf[tf] = st
        if bad:
            continue
        d = {"axes": {"mtf": mtf, "micro_15m": {"close": close, "bar_time": t, "rsi": None, "rsi_ma": None}}}
        try:
            cands = E1.detect(d, prev)
        except Exception:
            cands = []
        prev = d
        atr15 = mtf["15"].get("atr14") or 5.0
        for arm, cl in (("A", cands), ("B", interctx(cands, d, atr15))):
            agg = aggA if arm == "A" else aggB
            seen = seenA if arm == "A" else seenB
            for c in cl:
                key = (c.get("rule"), (c.get("direction") or "").upper(), c.get("tf"), t)
                if key in seen:
                    continue
                seen.add(key)
                R = H.resolve_from(i, c.get("entry"), c.get("sl"), c.get("target"),
                                   (c.get("direction") or "").upper() == "LONG", H15, L15, N)
                if R is None:
                    continue
                agg[((c.get("direction") or "").upper(), c.get("tf"))].append(R)
                if arm == "B" and c.get("n_rules", 1) >= 2:
                    aggB_conv.append(R)
        if i % step == 0:
            print(f"  {i}/{N}", flush=True)

    def panel(rs, cost=0.2):
        n = len(rs); w = sum(1 for r in rs if r > 0); s = sum(r - cost for r in rs)
        cum = peak = dd = 0.0; stk = mx = 0
        for r in rs:
            cum += r - cost; peak = max(peak, cum); dd = min(dd, cum - peak)
            stk = stk + 1 if r <= 0 else 0; mx = max(mx, stk)
        return dict(N=n, WR=round(100 * w / n) if n else None, sumR=round(s, 1),
                    avgR=round(s / n, 2) if n else None, maxDD=round(dd, 1), streak=mx)

    res = {}
    for name, agg in (("A_entregue", aggA), ("B_interctx", aggB)):
        allr = [r for lst in agg.values() for r in lst]
        lng = [r for (d_, tf), lst in agg.items() if d_ == "LONG" for r in lst]
        res[name] = dict(total=panel(allr), long_only=panel(lng),
                         por_tf={f"{d_}/{tf}": panel(lst) for (d_, tf), lst in sorted(agg.items())})
        print(f"\n[{name}] TOTAL {res[name]['total']}")
        print(f"[{name}] LONG  {res[name]['long_only']}")
    res["B_convergentes>=2"] = panel(aggB_conv)
    print(f"\n[B convergentes >=2 regras] {res['B_convergentes>=2']}")
    (HERE / "results.json").write_text(json.dumps(res, indent=1))
    print("gravado results.json", flush=True)


if __name__ == "__main__":
    main()
