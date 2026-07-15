#!/usr/bin/env python3
"""Cp MULTIVARIADO + TRAJETÓRIA em RAW-ONLY (Cris 2026-07-15, espírito RWS-15M) — agrega TODOS os
indicadores do RAW e lê a CONVERGÊNCIA dinâmica na janela flush→reclaim, para testar se separa a
capitulação-que-segura (GT 80%) do null (22% = faca). NÃO snapshot de eixo único. Extração causal
(known_at bubbles / born_t zonas / id-seed labels / RSI closed-bars), SEM cache primitives (regra Cris).
Componentes (todos <= barra de entrada = causais):
 ① BUY-ABSORÇÃO: soma de bubbles BUY (S1/M2/L3) na janela [low-16, entry] (compradores a absorver o flush)
 ② NAS LONG perto do low   ③ RSI oversold (<=35) + DIVERGÊNCIA (price lower-low, RSI higher-low)
 ④ zona OB DEMAND contém o low (born<=low)   ⑤ atividade SMC (CHoCH/BOS) na janela [low, entry]
Score = nº de componentes. Testa hit-3R por score + onde caem os 5 GT + null base 22%. RAW 15M do HD."""
import gzip, json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from a1_causal_entry import causal_entry, _is_swinglow, M_FRAC, LOWBACK
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
BLOCKS = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
          "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
          "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
ds = lambda t: dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")
grp = lambda rec, k, s: next((x for x in (rec.get(k) or []) if s.lower() in str(x.get("name", "")).lower()), None)
def fnum(x):
    try: return float(str(x).replace("−", "-"))
    except Exception: return None
def iso2ep(x):
    try: return int(dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp())
    except Exception: return None

bars = {}; rsi_t = {}; nas_ev = []; smc_ev = []; zones = {}; bub = {}
for blk_i, blk in enumerate(BLOCKS):
    mnas = msmc = -1; nasi = smci = False; snaps = []
    with gzip.open(RAW/blk, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try: r = json.loads(line)
            except Exception: continue
            if isinstance(r, dict) and r.get("ohlcv"): snaps.append(r)
    snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
    for r in snaps:
        oh = r.get("ohlcv") or []; cur = oh[-1]["time"] if oh and isinstance(oh[-1], dict) else None
        for b in oh:
            if isinstance(b, dict) and b.get("time") is not None:
                bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}
        rv = grp(r, "study_values", "Relative Strength")
        if rv and cur is not None: rsi_t[cur] = fnum((rv.get("values") or {}).get("RSI"))
        ng = grp(r, "pine_labels", "NAS"); ngi = [l.get("id") for l in (ng.get("labels") or []) if l.get("id") is not None] if ng else []
        if not nasi:
            if ngi: mnas = max(ngi); nasi = True
        else:
            for l in (ng.get("labels") or []) if ng else []:
                lid = l.get("id");
                if lid is None or lid <= mnas: continue
                txt = str(l.get("text", "")).upper()
                if "LONG" in txt: nas_ev.append({"t": cur, "dir": "LONG"})
            if ngi: mnas = max(mnas, max(ngi))
        sg = grp(r, "pine_labels", "Smart Money"); sgi = [l.get("id") for l in (sg.get("labels") or []) if l.get("id") is not None] if sg else []
        if not smci:
            if sgi: msmc = max(sgi); smci = True
        else:
            for l in (sg.get("labels") or []) if sg else []:
                lid = l.get("id")
                if lid is None or lid <= msmc: continue
                smc_ev.append({"t": cur, "text": str(l.get("text", "")).upper()})
            if sgi: msmc = max(msmc, max(sgi))
        ob = grp(r, "pine_boxes", "Custom OB")
        for bx in (ob.get("all_boxes") if ob else []) or []:
            zid = bx.get("id")
            if zid is None: continue
            zk = (blk_i, zid)
            if zk not in zones: zones[zk] = {"text": str(bx.get("text", "")).upper(), "high": bx.get("high"), "low": bx.get("low"), "born_t": cur}
            else: zones[zk]["high"] = bx.get("high"); zones[zk]["low"] = bx.get("low")
        pb = r.get("pine_shapes_bubbles")
        if pb:
            ka = iso2ep(r.get("replay_current_dt") or "")
            BUY = {"plot_0": 1, "plot_2": 2, "plot_4": 3}
            for act in (pb[0].get("activations") or []):
                tt = act.get("time")
                for plot in (act.get("shapes") or {}):
                    if plot not in BUY: continue
                    k = (tt, plot)
                    if k in bub: continue
                    bub[k] = {"t": tt, "size": BUY[plot], "known_at": ka}
ts = sorted(bars); T = ts; O = [bars[t]["o"] for t in ts]; H = [bars[t]["h"] for t in ts]; L = [bars[t]["l"] for t in ts]; C = [bars[t]["c"] for t in ts]
N = len(ts); ATR = [None]*N; EMA = [None]*N; ema = None; kE = 2/22; trs = []
for i in range(N):
    ema = C[i] if ema is None else C[i]*kE+ema*(1-kE); EMA[i] = ema
    if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
S = dict(T=T, O=O, H=H, L=L, C=C, EMA=EMA, ATR=ATR, N=N)
RSI = [rsi_t.get(t) for t in ts]
print(f"RAW: {N} barras {ds(T[0])}→{ds(T[-1])} · NAS-long {len(nas_ev)} · SMC {len(smc_ev)} · zonas {len(zones)} · buy-bubbles {len(bub)}")
buys = sorted(bub.values(), key=lambda x: x["t"])

# GT panic lows
def panic_low(a_t, b_t, buf=12*3600):
    a = bisect.bisect_left(T, min(a_t, b_t)-buf); b = bisect.bisect_right(T, max(a_t, b_t)+buf)
    return T[min(range(a, b), key=lambda k: L[k])] if a < b else None
GT_LOWS = [panic_low(a, b) for a, b in [(1770015600, 1770210000), (1770339600, 1771448400),
           (1774242000, 1774270800), (1781128800, 1781128800), (1782781200, 1782907200)]]

def converge(e):
    ei = e["ei"]; ab = e["anchor_bar"]; kt = T[ei]
    # ① buy-absorção (known_at <= entry, bubble bar em [anchor-16, entry])
    lo_t = T[max(0, ab-16)]
    buy = sum(x["size"] for x in buys if x["known_at"] and x["known_at"] <= kt and lo_t <= x["t"] <= kt)
    # ② NAS long perto do low (t <= entry, dentro de [anchor-8, entry])
    nas = any(ev["t"] and T[max(0, ab-8)] <= ev["t"] <= kt for ev in nas_ev)
    # ③ RSI oversold + divergência
    r_now = RSI[ab]; rsi_os = (r_now is not None and r_now <= 35)
    lows = [(p, L[p]) for p in range(max(M_FRAC, ab-LOWBACK), ab) if _is_swinglow(L, p, M_FRAC)]
    div = False
    if lows and r_now is not None:
        pp, pl = lows[-1]; rp = RSI[pp]
        if rp is not None and L[ab] < pl and r_now > rp: div = True
    # ④ zona demand contém o low (born <= T[anchor])
    dem = any("DEMAND" in z["text"] and z["born_t"] and z["born_t"] <= T[ab] and z["low"] is not None
              and z["low"] <= L[ab] <= z["high"] for z in zones.values())
    # ⑤ atividade SMC na janela [anchor, entry]
    smc = any(ev["t"] and T[ab] <= ev["t"] <= kt for ev in smc_ev)
    comps = {"buy": buy >= 3, "nas": nas, "rsi": rsi_os or div, "demand": dem, "smc": smc}
    return comps, buy

# enumera flushes + convergência + desfecho
t_lo = int(dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc).timestamp()); t_hi = int(dt.datetime(2026, 7, 4, tzinfo=dt.timezone.utc).timestamp())
seen = set(); rows = []
for k in range(120, N):
    if not (t_lo <= T[k] <= t_hi): continue
    atr = ATR[k] or 5.0
    if (H[k]-L[k]) < 1.8*atr or C[k] >= O[k]: continue
    e = causal_entry(S, k, "MB3")
    if not e or e["ei"] in seen or e["o"] == "OPEN": continue
    seen.add(e["ei"])
    comps, buy = converge(e); score = sum(comps.values())
    is_gt = any(abs(T[e["anchor_bar"]]-g) < 6*3600 for g in GT_LOWS if g)
    rows.append({"o": e["o"], "score": score, "comps": comps, "buy": buy, "is_gt": is_gt})

def hit(sub):
    w = sum(1 for r in sub if r["o"] == "WIN"); return w, len(sub), (100*w/len(sub) if sub else 0)
print(f"\nFlushes resolvidos: {len(rows)} · base hit-3R {hit(rows)[2]:.0f}%")
print("hit-3R por SCORE de convergência (multivariado):")
for sc in range(0, 6):
    sub = [r for r in rows if r["score"] == sc]; w, n, h = hit(sub)
    print(f"  score={sc}: N={n:3d}  hit-3R {h:4.0f}%  ({w}/{n})")
for thr in (2, 3, 4):
    sub = [r for r in rows if r["score"] >= thr]; w, n, h = hit(sub)
    print(f"  score>={thr}: N={n:3d}  hit-3R {h:4.0f}%  [null base {hit(rows)[2]:.0f}%]")
print("\ncomponente isolado (hit-3R quando fire):")
for key in ("buy", "nas", "rsi", "demand", "smc"):
    sub = [r for r in rows if r["comps"][key]]; w, n, h = hit(sub)
    print(f"  {key:7}: N={n:3d} hit {h:4.0f}%")
gtr = [r for r in rows if r["is_gt"]]
print(f"\n5 GT: {len(gtr)} no conjunto · scores {[r['score'] for r in gtr]} · outcomes {[r['o'] for r in gtr]} · comps {[ {k for k,v in r['comps'].items() if v} for r in gtr]}")