#!/usr/bin/env python3
"""SUBSTRATO RAW A2 — dossiê de CONTEXTO CAUSAL por fundo A2 (18) para leitura de CONTINUAÇÃO.
Moldura INVERTIDA vs A1 (aprovada Cris 2026-07-14): A2 = pullback RASO num IMPULSO de alta em curso;
o edge (se existir) é EVITAR impulsos EXAUSTOS, não cronometrar o dip (null alto). Por isso o dossiê
ENRIQUECE com CONTEXTO DE EXAUSTÃO: highs recentes + RSI (divergência), extensão/idade do impulso,
profundidade do dip, supply overhead. RAW 15M direto do HD (sem cache primitives). Causal."""
import gzip, json, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
import sys; sys.path.insert(0, str(HERE)); sys.path.insert(0, "/Users/cristrein/tradingview-mcp/my-strategy/core"); import raw_reader as RR
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
OUT = HERE / "a2_context"; OUT.mkdir(exist_ok=True)
BLOCKS = ["XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz", "XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
          "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz", "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
LOOKBACK, FORWARD = 120, 288
import macro_structural_v3 as M, leg_v3 as LV
ds = lambda t: dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")
grp = RR.study
def fnum(x):
    try: return float(str(x).replace("−", "-"))
    except Exception: return None
def iso2ep(x):
    try: return int(dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp())
    except Exception: return None

bars = {}; rsi_t = {}; nasd_t = {}; nas_ev = []; smc_ev = []; zones = {}; bub = {}
for blk_i, blk in enumerate(BLOCKS):
    mnas = msmc = -1; nasi = smci = False
    snaps = RR.records(RAW/blk)
    for r in snaps:
        oh = r.get("ohlcv") or []
        cur = oh[-1]["time"] if oh and isinstance(oh[-1], dict) else None
        for b in oh:
            if isinstance(b, dict) and b.get("time") is not None:
                bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}  # overwrite=barra completa
        rv = grp(r, "study_values", "Relative Strength")
        if rv and cur is not None: rsi_t[cur] = fnum((rv.get("values") or {}).get("RSI"))
        nv = grp(r, "study_values", "NAS")
        if nv and cur is not None: nasd_t[cur] = fnum((nv.get("values") or {}).get("NAS_DISTANCE_FROM_EMA_ATR"))
        ng = grp(r, "pine_labels", "NAS"); ngi = [l.get("id") for l in (ng.get("labels") or []) if l.get("id") is not None] if ng else []
        if not nasi:
            if ngi: mnas = max(ngi); nasi = True
        else:
            for l in (ng.get("labels") or []) if ng else []:
                lid = l.get("id")
                if lid is None or lid <= mnas: continue
                txt = str(l.get("text", "")).upper()
                if "LONG" in txt or "SHORT" in txt: nas_ev.append({"t": cur, "dir": "LONG" if "LONG" in txt else "SHORT"})
            if ngi: mnas = max(mnas, max(ngi))
        sg = grp(r, "pine_labels", "Smart Money"); sgi = [l.get("id") for l in (sg.get("labels") or []) if l.get("id") is not None] if sg else []
        if not smci:
            if sgi: msmc = max(sgi); smci = True
        else:
            for l in (sg.get("labels") or []) if sg else []:
                lid = l.get("id")
                if lid is None or lid <= msmc: continue
                smc_ev.append({"t": cur, "text": l.get("text")})
            if sgi: msmc = max(msmc, max(sgi))
        ob = grp(r, "pine_boxes", "Custom OB")
        for bx in (ob.get("all_boxes") if ob else []) or []:
            zid = (blk_i, bx.get("id"))
            if bx.get("id") is None: continue
            if zid not in zones: zones[zid] = {"text": str(bx.get("text","")).upper(), "high": bx.get("high"), "low": bx.get("low"), "born_t": cur}
            else: zones[zid]["high"] = bx.get("high"); zones[zid]["low"] = bx.get("low")
        pb = r.get("pine_shapes_bubbles")
        if pb:
            ka = iso2ep(r.get("replay_current_dt") or "")
            BUY = {"plot_0": "S", "plot_2": "M", "plot_4": "L"}; SELL = {"plot_6": "S", "plot_8": "M", "plot_10": "L"}
            for act in (pb[0].get("activations") or []):
                tt = act.get("time")
                for plot in (act.get("shapes") or {}):
                    if plot not in BUY and plot not in SELL: continue
                    if (tt, plot) in bub: continue
                    bub[(tt, plot)] = {"t": tt, "side": "BUY" if plot in BUY else "SELL", "size": (BUY if plot in BUY else SELL)[plot], "known_at": ka}
ts = sorted(bars); series = []; ema = None; kE = 2/22; trs = []
for i, t in enumerate(ts):
    b = bars[t]; ema = b["c"] if ema is None else b["c"]*kE+ema*(1-kE)
    if i > 0:
        pc = bars[ts[i-1]]["c"]; trs.append(max(b["h"]-b["l"], abs(b["h"]-pc), abs(b["l"]-pc)))
    atr = sum(trs[-14:])/14 if len(trs) >= 14 else None
    series.append({"t": t, "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "rsi": rsi_t.get(t),
                   "nas_dist": nasd_t.get(t), "atr": round(ema, 2) if False else (round(atr, 1) if atr else None), "ema21": round(ema, 2)})
STS = [s["t"] for s in series]
print(f"RAW 15M: {len(series)} barras {ds(STS[0])}→{ds(STS[-1])} · NAS {len(nas_ev)} · SMC {len(smc_ev)} · zonas {len(zones)} · bubbles {len(bub)}")

lab1d = M.build_layer1(); T1 = M.T; KN1 = [t+86400 for t in T1]
macro_at = lambda t: lab1d[bisect.bisect_right(KN1, t)-1] if bisect.bisect_right(KN1, t)-1 >= 0 else None
v3 = LV.build_leg_v3(); LC = [r["t"]+14400 for r in v3]
def leg_at(t):
    i = bisect.bisect_right(LC, t)-1; return (v3[i].get("leg"), v3[i].get("leg_dir")) if i >= 0 else (None, None)
H4 = [json.loads(l) for l in open(HERE/"raw_4h_ohlc.jsonl")]; T4 = [b["t"] for b in H4]
D1 = [json.loads(l) for l in open(HERE/"raw_1d_ohlc.jsonl")]; TD = [b["t"] for b in D1]

def swing_highs(a, b):
    """máximos locais (fractal ±3) em series[a:b] → [(dt, price, rsi)] (para divergência)."""
    out = []
    for k in range(a+3, b-3):
        if series[k]["h"] > max(series[k-3:k]["h"] if False else [series[q]["h"] for q in range(k-3, k)]) \
           and series[k]["h"] >= max([series[q]["h"] for q in range(k+1, k+4)]):
            out.append((ds(series[k]["t"]), series[k]["h"], round(series[k]["rsi"], 1) if series[k]["rsi"] else None))
    return out[-3:]

GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
A2 = sorted([f for f in GT["fundos"] if f.get("subclasse") == "A2_pullback_raso"], key=lambda x: x["t"])
idx = []
for n, f in enumerate(A2, 1):
    t0 = int(f["t"]); j = bisect.bisect_right(STS, t0)-1
    if j < 0: continue
    a_at = series[j]["atr"] or 5.0
    lo0r, hi0r = max(0, j-8), min(len(series), j+9); kmin = min(range(lo0r, hi0r), key=lambda k: series[k]["l"]); low_real = series[kmin]["l"]
    sl = round(low_real-0.1*a_at, 2)
    lo, hi = max(0, j-LOOKBACK), min(len(series), j+FORWARD)
    win = [{"t": s["t"], "dt": ds(s["t"]), "o": s["o"], "h": s["h"], "l": s["l"], "c": s["c"],
            "rsi": round(s["rsi"], 1) if s["rsi"] else None, "ema21": s["ema21"], "atr": s["atr"],
            "nas_dist": round(s["nas_dist"], 2) if s["nas_dist"] else None} for s in series[lo:hi]]
    wt0, wt1 = series[lo]["t"], series[hi-1]["t"]
    # --- CONTEXTO DE EXAUSTÃO (o novo, para A2) ---
    lb0 = max(0, j-96)
    rhb = max(range(lb0, j+1), key=lambda k: series[k]["h"]); recent_high = series[rhb]["h"]
    rlow = min(series[k]["l"] for k in range(lb0, j+1))
    imp = {"recent_high": recent_high, "recent_high_dt": ds(series[rhb]["t"]), "rsi_at_high": round(series[rhb]["rsi"], 1) if series[rhb]["rsi"] else None,
           "cur_rsi": round(series[j]["rsi"], 1) if series[j]["rsi"] else None,
           "bars_since_high": j-rhb, "dip_from_high_atr": round((recent_high-low_real)/a_at, 1),
           "runup_atr": round((recent_high-rlow)/a_at, 1), "swing_highs_recent": swing_highs(lb0, j+1)}
    # supply overhead acima do low (causal born<=wt1)
    sup = [z for z in zones.values() if z["born_t"] and z["born_t"] <= wt1 and z["low"] and "SUPPLY" in z["text"] and z["low"] >= low_real]
    sup_atr = round((min(z["low"] for z in sup)-low_real)/a_at, 1) if sup else None
    zw = []
    for z in zones.values():
        if z["born_t"] and z["born_t"] <= wt1 and z["low"] and z["high"] and low_real*0.985 <= z["low"] and z["high"] <= low_real*1.03:
            zw.append({"type": z["text"], "high": z["high"], "low": z["low"], "born": ds(z["born_t"])})
    nw = [{"dt": ds(e["t"]), "dir": e["dir"]} for e in nas_ev if e["t"] and wt0 <= e["t"] <= wt1]
    sw = [{"dt": ds(e["t"]), "text": e["text"]} for e in smc_ev if e["t"] and wt0 <= e["t"] <= wt1]
    bw = [{"dt": ds(b["t"]), "side": b["side"], "size": b["size"], "known_at": ds(b["known_at"]) if b["known_at"] else None} for b in bub.values() if b["t"] and wt0 <= b["t"] <= wt1]
    fseg = series[j:min(len(series), j+FORWARD)]; mfe = round(max(s["h"] for s in fseg)-low_real, 1) if fseg else None
    m1d = macro_at(t0); lg, lgd = leg_at(t0)
    i4 = bisect.bisect_right(T4, t0)-1; htf4 = [{"dt": ds(H4[k]["t"]), "o": H4[k]["o"], "h": H4[k]["h"], "l": H4[k]["l"], "c": H4[k]["c"]} for k in range(max(0, i4-15), i4+1)]
    iD = bisect.bisect_right(TD, t0)-1; htf1d = [{"dt": ds(D1[k]["t"]), "c": D1[k]["c"], "h": D1[k]["h"], "l": D1[k]["l"]} for k in range(max(0, iD-8), iD+1)]
    doss = {"id": f"A2_{n:02d}", "fundo": {"t": t0, "dt": ds(t0), "low": low_real, "gt_price": f["price"], "leg_15m_gt": f["leg"],
             "src": f.get("src"), "atr_15m": round(a_at, 2), "SL_dip": sl,
             "note": "A2=pullback RASO em impulso; SL do dip pode ser apertado — ler se o SL real e o higher-low estrutural anterior"},
            "macro_1d": m1d, "leg_4h_v3": lg, "leg_4h_dir": lgd, "impulse_exhaustion_ctx": imp, "supply_above_atr": sup_atr,
            "forward_mfe_from_low": mfe, "htf_4h_recent": htf4, "htf_1d_recent": htf1d,
            "ob_zones": zw, "nas_events": nw, "smc_events": sw, "bubbles": bw, "window_15m": win}
    (OUT/f"fundo_{n:02d}.json").write_text(json.dumps(doss, ensure_ascii=False))
    idx.append({"id": doss["id"], "dt": ds(t0), "low": low_real, "macro": m1d, "leg4h": lg,
                "runup": imp["runup_atr"], "dip": imp["dip_from_high_atr"], "rsi_hi": imp["rsi_at_high"], "cur_rsi": imp["cur_rsi"],
                "bars_since_hi": imp["bars_since_high"], "sup_atr": sup_atr, "mfe": mfe})
(OUT/"index.json").write_text(json.dumps({"n": len(idx), "fundos": idx}, ensure_ascii=False, indent=1))
print(f"\nDossiês A2 escritos: {len(idx)} em {OUT.relative_to(HERE)}/")
for s in idx:
    print(f"  {s['id']} {s['dt']} low {s['low']:.0f} · runup {s['runup']}ATR dip {s['dip']}ATR · RSI hi {s['rsi_hi']}/cur {s['cur_rsi']} · barras_desde_hi {s['bars_since_hi']} · sup {s['sup_atr']}ATR · MFE {s['mfe']}")
