#!/usr/bin/env python3
"""SUBSTRATO RAW — dossiê de CONTEXTO CAUSAL por fundo A1 (14) para leitura contextual ampla.
Lê DIRETO do RAW 15M no HD (raw_replay/XAUUSD/15M), replica o parse causal (first-appearance:
NAS/SMC por id, zonas OB por born_t, bubbles por known_at) — NÃO usa o cache primitives (regra Cris).
Junta o stack novo (macro 1D Layer1 + leg 4H v3) + HTF 4H/1D. SL=fundo−0,1ATR. Escreve
a1_context/fundo_NN.json (o que os agentes leem). SVP não está no RAW 15M = GAP declarado."""
import gzip, json, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
OUT = HERE / "a1_context"; OUT.mkdir(exist_ok=True)
BLOCKS = ["XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz",
          "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
LOOKBACK, FORWARD = 96, 288          # 24h antes, 72h depois (15M)
import macro_structural_v3 as M, leg_v3 as LV
ds = lambda t: dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")
grp = lambda rec, k, s: next((x for x in (rec.get(k) or []) if s.lower() in str(x.get("name","")).lower()), None)
def fnum(x):
    try: return float(str(x).replace("−", "-"))
    except Exception: return None
def iso2ep(x):
    try: return int(dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp())
    except Exception: return None

# ---- walk RAW causal (série + NAS + SMC + zonas + bubbles) ----
bars = {}; rsi_t = {}; nasd_t = {}; nas_ev = []; smc_ev = []; zones = {}; bub = {}
for blk_i, blk in enumerate(BLOCKS):
    mnas = msmc = -1; nasi = smci = False        # SEED POR-BLOCO (ids de label reiniciam por bloco de replay)
    snaps = []
    with gzip.open(RAW / blk, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try: r = json.loads(line)
            except Exception: continue
            if isinstance(r, dict) and r.get("ohlcv"): snaps.append(r)
    snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
    for r in snaps:
        oh = r.get("ohlcv") or []
        cur = oh[-1]["time"] if oh and isinstance(oh[-1], dict) else None
        for b in oh:
            if isinstance(b, dict) and b.get("time") is not None:
                bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"], "v": b.get("volume")}
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
                if "LONG" in txt or "SHORT" in txt:
                    nas_ev.append({"t": cur, "dir": "LONG" if "LONG" in txt else "SHORT", "price": l.get("price")})
            if ngi: mnas = max(mnas, max(ngi))
        sg = grp(r, "pine_labels", "Smart Money"); sgi = [l.get("id") for l in (sg.get("labels") or []) if l.get("id") is not None] if sg else []
        if not smci:
            if sgi: msmc = max(sgi); smci = True
        else:
            for l in (sg.get("labels") or []) if sg else []:
                lid = l.get("id")
                if lid is None or lid <= msmc: continue
                smc_ev.append({"t": cur, "text": l.get("text"), "price": l.get("price")})
            if sgi: msmc = max(msmc, max(sgi))
        ob = grp(r, "pine_boxes", "Custom OB")
        for bx in (ob.get("all_boxes") if ob else []) or []:
            zid = bx.get("id")
            if zid is None: continue
            zk = (blk_i, zid)                    # chave por-bloco (ids de box reiniciam por bloco)
            if zk not in zones:
                zones[zk] = {"text": str(bx.get("text", "")).upper(), "high": bx.get("high"), "low": bx.get("low"), "born_t": cur, "last_t": cur}
            else:
                zones[zk]["last_t"] = cur; zones[zk]["high"] = bx.get("high"); zones[zk]["low"] = bx.get("low")
        pb = r.get("pine_shapes_bubbles")
        if pb:
            ka = iso2ep(r.get("replay_current_dt") or "")
            BUY = {"plot_0": "S", "plot_2": "M", "plot_4": "L"}; SELL = {"plot_6": "S", "plot_8": "M", "plot_10": "L"}
            for act in (pb[0].get("activations") or []):
                tt = act.get("time")
                for plot in (act.get("shapes") or {}):
                    if plot not in BUY and plot not in SELL: continue
                    k = (tt, plot)
                    if k in bub: continue
                    bub[k] = {"t": tt, "side": "BUY" if plot in BUY else "SELL",
                              "size": (BUY if plot in BUY else SELL)[plot], "known_at": ka}
# série ordenada + ATR14 + EMA21
ts = sorted(bars); series = []; ema = None; kE = 2/22; trs = []
for i, t in enumerate(ts):
    b = bars[t]; ema = b["c"] if ema is None else b["c"]*kE + ema*(1-kE)
    if i > 0:
        pc = bars[ts[i-1]]["c"]; trs.append(max(b["h"]-b["l"], abs(b["h"]-pc), abs(b["l"]-pc)))
    atr = sum(trs[-14:])/14 if len(trs) >= 14 else None
    series.append({"t": t, "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"],
                   "rsi": rsi_t.get(t), "nas_dist": nasd_t.get(t), "atr": atr, "ema21": round(ema, 2)})
sidx = {s["t"]: i for i, s in enumerate(series)}
STS = [s["t"] for s in series]
print(f"RAW 15M: {len(series)} barras {ds(STS[0])}→{ds(STS[-1])} · NAS {len(nas_ev)} · SMC {len(smc_ev)} · zonas {len(zones)} · bubbles {len(bub)}")

# ---- stack novo (macro 1D + leg 4H v3) causal + HTF RAW ----
lab1d = M.build_layer1(); T1 = M.T; KN1 = [t+86400 for t in T1]
def macro_at(t):
    j = bisect.bisect_right(KN1, t)-1; return lab1d[j] if j >= 0 else None
v3 = LV.build_leg_v3(); LC = [r["t"]+14400 for r in v3]
def leg_at(t):
    i = bisect.bisect_right(LC, t)-1; return (v3[i].get("leg"), v3[i].get("leg_dir")) if i >= 0 else (None, None)
H4 = [json.loads(l) for l in open(HERE/"raw_4h_ohlc.jsonl")] if (HERE/"raw_4h_ohlc.jsonl").exists() else []
T4 = [b["t"] for b in H4]
D1 = [json.loads(l) for l in open(HERE/"raw_1d_ohlc.jsonl")]; TD = [b["t"] for b in D1]

# ---- dossiê por fundo A1 ----
GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
A1 = sorted([f for f in GT["fundos"] if f.get("subclasse") == "A1_pullback_fundo"], key=lambda x: x["t"])
idx_summary = []
for n, f in enumerate(A1, 1):
    t0 = int(f["t"]); price = float(f["price"])
    # bar 15M mais próximo (âncora) — usa último bar <= t0
    j = bisect.bisect_right(STS, t0)-1
    if j < 0: continue
    a_at = series[j]["atr"] or 5.0
    sl = round(price - 0.1*a_at, 2)
    lo, hi = max(0, j-LOOKBACK), min(len(series), j+FORWARD)
    win = [{"t": s["t"], "dt": ds(s["t"]), "o": s["o"], "h": s["h"], "l": s["l"], "c": s["c"],
            "rsi": round(s["rsi"], 1) if s["rsi"] else None, "ema21": s["ema21"],
            "atr": round(s["atr"], 1) if s["atr"] else None, "nas_dist": round(s["nas_dist"], 2) if s["nas_dist"] else None}
           for s in series[lo:hi]]
    wt0, wt1 = series[lo]["t"], series[hi-1]["t"]
    # zonas OB RELEVANTES (causal born<=wt1): dedup + nearest demand abaixo / supply acima / que contêm o preço
    cand = {}
    for z in zones.values():
        if not (z["born_t"] and z["born_t"] <= wt1 and z["low"] and z["high"]): continue
        key = (round(z["high"], 1), round(z["low"], 1), "DEMAND" if "DEMAND" in z["text"] else "SUPPLY" if "SUPPLY" in z["text"] else z["text"])
        if key not in cand or z["born_t"] < cand[key]["born_t"]: cand[key] = z
    dem = sorted([z for z in cand.values() if "DEMAND" in z["text"] and z["low"] <= price], key=lambda z: price - z["high"])[:3]
    sup = sorted([z for z in cand.values() if "SUPPLY" in z["text"] and z["high"] >= price], key=lambda z: z["low"] - price)[:3]
    inside = [z for z in cand.values() if z["low"] <= price <= z["high"]][:2]
    zsel = list({id(z): z for z in dem + sup + inside}.values())
    zw = [{"type": z["text"], "high": z["high"], "low": z["low"], "born": ds(z["born_t"])} for z in zsel]
    nw = [{"dt": ds(e["t"]), "dir": e["dir"]} for e in nas_ev if e["t"] and wt0 <= e["t"] <= wt1]
    sw = [{"dt": ds(e["t"]), "text": e["text"]} for e in smc_ev if e["t"] and wt0 <= e["t"] <= wt1]
    bw = [{"dt": ds(b["t"]), "side": b["side"], "size": b["size"], "known_at": ds(b["known_at"]) if b["known_at"] else None}
          for b in bub.values() if b["t"] and wt0 <= b["t"] <= wt1]
    # referência forward (contexto, NÃO gatilho): MFE do low nos próximos FORWARD bars
    fseg = series[j:min(len(series), j+FORWARD)]
    mfe = round(max(s["h"] for s in fseg)-price, 1) if fseg else None
    # HTF
    m1d = macro_at(t0); lg, lgd = leg_at(t0)
    i4 = bisect.bisect_right(T4, t0)-1
    htf4 = [{"dt": ds(H4[k]["t"]), "o": H4[k]["o"], "h": H4[k]["h"], "l": H4[k]["l"], "c": H4[k]["c"]} for k in range(max(0, i4-15), i4+1)]
    iD = bisect.bisect_right(TD, t0)-1
    htf1d = [{"dt": ds(D1[k]["t"]), "c": D1[k]["c"], "h": D1[k]["h"], "l": D1[k]["l"]} for k in range(max(0, iD-8), iD+1)]
    doss = {"id": f"A1_{n:02d}", "fundo": {"t": t0, "dt": ds(t0), "low": price, "leg_15m_gt": f["leg"],
             "src": f.get("src"), "atr_15m": round(a_at, 2), "SL": sl, "risk_unit": round(price-sl, 2)},
            "macro_1d": m1d, "leg_4h_v3": lg, "leg_4h_dir": lgd,
            "window_note": f"15M {ds(wt0)}→{ds(wt1)} (−{LOOKBACK}/+{FORWARD} bars em torno do fundo)",
            "forward_mfe_from_low": mfe,
            "htf_4h_recent": htf4, "htf_1d_recent": htf1d,
            "ob_zones": zw, "nas_events": nw, "smc_events": sw, "bubbles": bw,
            "window_15m": win, "SVP_note": "SVP não disponível no RAW 15M (só 4H/1D via chart) = GAP declarado"}
    (OUT / f"fundo_{n:02d}.json").write_text(json.dumps(doss, ensure_ascii=False))
    idx_summary.append({"id": doss["id"], "dt": ds(t0), "low": price, "macro": m1d, "leg4h": lg,
                        "zonas": len(zw), "nas": len(nw), "smc": len(sw), "bub": len(bw), "mfe": mfe})
(OUT / "index.json").write_text(json.dumps({"n": len(idx_summary), "fundos": idx_summary}, ensure_ascii=False, indent=1))
print(f"\nDossiês A1 escritos: {len(idx_summary)} em {OUT.relative_to(HERE)}/")
for s in idx_summary:
    print(f"  {s['id']} {s['dt']} low {s['low']:.0f} · macro {s['macro']} leg4h {s['leg4h']} · OB{s['zonas']} NAS{s['nas']} SMC{s['smc']} BUB{s['bub']} · MFE {s['mfe']}")
