#!/usr/bin/env python3
"""DSPA MACRO-CONVERGENCE PROBE — testa a TESE VISUAL do Cris (convergencia macro-estrutural na TRAJETORIA da
perna, NAO snapshot na entrada) que separaria runner de stopper. Multi-fatorial + trajetoria (declarado:
anti-miopia/DSPA, NAO eixo-unico). Mede 7 fatores em RAW por barra ao longo de ~30 barras pre-entry, para os
2 RUNNERS (4918, 4926) e os 2 STOPPERS (3825, 3929). SANITY_PROBE: calibracao em 4 episodios contrastivos, NAO
validacao; NAO vira regra/gate. Read-only RAW. Verified at: 2026-06-24."""
import gzip, json, datetime as dt, os

SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
RR = "repro_recovery"; BAR = 14400; LB = 30
F = [json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
BACK = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open("results/l2_bpt_raw_backbone_episodes.jsonl")}
EPS = {4918: "RUNNER", 4926: "RUNNER", 3825: "STOPPER", 3929: "STOPPER"}
ENTRY = {b: int(F[b]["ts_epoch"]) for b in EPS}


def to_ep(t):
    if t is None: return None
    t = float(t); return int(t / 1000) if t > 1e11 else int(t)


def pv(s):
    if s is None: return None
    s = str(s).replace(" ", "").replace(" ", "").replace(",", "").replace(" ", "").replace("−", "-").strip()
    m = 1.0
    if s[-1:] in ("K", "M", "B"): m = {"K": 1e3, "M": 1e6, "B": 1e9}[s[-1]]; s = s[:-1]
    try: return float(s) * m
    except Exception: return None


def studies(rec):
    return {str(s.get("name")): (s.get("values") or {}) for s in (rec.get("study_values") or [])}


def grp(rec, cont, key):
    return next((g for g in (rec.get(cont) or []) if key in str(g.get("name", ""))), {})


# coleta per-bar para janelas dos 4 episodios
dates = set()
for b in EPS:
    for k in range(0, LB + 3):
        dates.add(dt.datetime.utcfromtimestamp(ENTRY[b] - k * BAR).strftime("%Y-%m-%d"))
bars = {}  # asof_t -> per-bar dict
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if not any(d in line for d in dates): continue
        rec = json.loads(line); oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
        if not isinstance(last, dict): continue
        at = to_ep(last.get("time"))
        if at is None or at in bars: continue
        sv = studies(rec); svp = sv.get("Session Volume Profile", {})
        nas = grp(rec, "pine_labels", "NAS"); bub = grp(rec, "pine_shapes_bubbles", "Bubble")
        act = (bub.get("activations_per_plot") or {})
        nas_tail = [l.get("text") for l in (nas.get("labels") or [])[-4:]]
        bars[at] = {"c": last.get("close"), "h": last.get("high"), "l": last.get("low"),
                    "up": pv(svp.get("Up")), "dn": pv(svp.get("Down")), "tot": pv(svp.get("Total")),
                    "rsi": pv((sv.get("Relative Strength Index") or {}).get("RSI")),
                    "nas_tail": nas_tail,
                    "buy_b": sum(pv(act.get(f"plot_{i}")) or 0 for i in (0, 2, 4)),
                    "buy_L": pv(act.get("plot_4")) or 0,
                    "sell_b": sum(pv(act.get(f"plot_{i}")) or 0 for i in (6, 8, 10)),
                    "sell_L": pv(act.get("plot_10")) or 0}
btimes = sorted(bars)


def window(b):
    et = ENTRY[b]
    w = [bars[t] for t in btimes if t <= et][-LB:]
    return w


def slope(ys):
    ys = [y for y in ys if y is not None]
    n = len(ys)
    if n < 4: return None
    xs = list(range(n)); mx = sum(xs) / n; my = sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    return round(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den, 1) if den else None


def factors(b):
    w = window(b); bk = BACK.get(b, {}); rg = bk.get("regime_raw_mapped", {}); sd = bk.get("supply_demand_raw_mapped", {})
    lows = [x["l"] for x in w]; closes = [x["c"] for x in w]; rsis = [x["rsi"] for x in w]; tots = [x["tot"] for x in w]
    lo_i = lows.index(min(x for x in lows if x is not None))
    # 1 regime
    regime = f"weekly={rg.get('weekly_slope'):+.2f} casc={rg.get('cascade_score')} macro_broken={rg.get('macro_broken')} v3={rg.get('v3_state')}" if isinstance(rg.get('weekly_slope'), (int, float)) else str(rg)
    # 2 vol decay sobre a DESCIDA (do high da janela ate o low)
    hi_i = closes.index(max(x for x in closes if x is not None))
    decline = tots[hi_i:lo_i + 1] if lo_i > hi_i else tots[:lo_i + 1]
    vol_decay = slope(decline)
    # 3 absorcao: barra de MAIOR volume nas ultimas 12; fez lower-low DEPOIS dela?
    seg = w[-12:]; mv_i = max(range(len(seg)), key=lambda i: (seg[i]["tot"] or 0))
    mv = seg[mv_i]; after = seg[mv_i + 1:]
    lower_low_after = any((x["l"] is not None and mv["l"] is not None and x["l"] < mv["l"]) for x in after)
    absorption = (not lower_low_after) and ((mv["dn"] or 0) > (mv["up"] or 0))  # clinax vendedor absorvido
    # 4 bubble cluster no fundo (ultimas 8): buy total + buy LARGE
    last8 = w[-8:]; buy8 = sum(x["buy_b"] for x in last8); buyL8 = sum(x["buy_L"] for x in last8); sell8 = sum(x["sell_b"] for x in last8)
    # 5 nas bottom nas ultimas 6
    nas_bottom = any("LONG" in (t or "") or "BOTTOM" in (t or "") for x in w[-6:] for t in x["nas_tail"])
    # 6 rsi min + n divergencias bull (preco lower-low x rsi higher-low)
    rsi_min = min(x for x in rsis if x is not None) if any(rsis) else None
    ndiv = 0; pl = None; pr = None
    for i in range(2, len(w) - 1):
        if w[i]["l"] is None or w[i]["rsi"] is None: continue
        if w[i]["l"] <= (w[i - 1]["l"] or 9e9) and w[i]["l"] <= (w[i + 1]["l"] or 9e9):  # low local
            if pl is not None and w[i]["l"] < pl and w[i]["rsi"] > pr:  # preco menor, rsi maior = bull div
                ndiv += 1
            pl, pr = w[i]["l"], w[i]["rsi"]
    # 7 polaridade: swing-high anterior agora ABAIXO do close de entrada?
    entry_c = w[-1]["c"]; highs = [x["h"] for x in w[:-3] if x["h"] is not None]
    prior_high_below = bool(highs) and entry_c is not None and max(highs[:max(1, len(highs)//2)]) < entry_c
    # struct SL = low da perna
    struct_sl = min(x for x in lows if x is not None)
    return {"lbl": EPS[b], "regime": regime, "vol_decay_slope": vol_decay, "absorption_at_climax": absorption,
            "buy_bub_8": round(buy8, 1), "buy_LARGE_8": round(buyL8, 1), "sell_bub_8": round(sell8, 1),
            "nas_bottom_6": nas_bottom, "rsi_min": round(rsi_min, 1) if rsi_min else None, "n_bull_div": ndiv,
            "polarity_top_below": prior_high_below, "struct_sl": round(struct_sl, 2), "entry_close": round(entry_c, 2),
            "sup_cat": sd.get("sup_cat"), "dist_supply": sd.get("dist_supply_atr")}


print(f"DSPA MACRO-CONVERGENCE PROBE — lookback {LB} barras, RAW per-bar. CALIBRACAO em 4 (nao validacao).\n")
hdr = ["ep", "lbl", "regime", "vol_decay", "absorp", "buy_b8", "buy_L8", "sell_b8", "nas_bot", "rsi_min", "n_div", "pol_below", "struct_sl", "sup_cat/dist"]
rows = []
for b in (4918, 4926, 3825, 3929):
    f = factors(b)
    rows.append(f)
    print(f"#{b} [{f['lbl']}]")
    print(f"   regime: {f['regime']}")
    print(f"   2 vol_decay_slope(descida)={f['vol_decay_slope']}  3 absorption_at_climax={f['absorption_at_climax']}")
    print(f"   4 buy_bub_8={f['buy_bub_8']} buy_LARGE_8={f['buy_LARGE_8']} sell_bub_8={f['sell_bub_8']}")
    print(f"   5 nas_bottom_6={f['nas_bottom_6']}  6 rsi_min={f['rsi_min']} n_bull_div={f['n_bull_div']}  7 polarity_top_below={f['polarity_top_below']}")
    print(f"   sup_cat={f['sup_cat']} dist_supply={f['dist_supply']} | struct_SL={f['struct_sl']} (entry {f['entry_close']})\n")
out = "results/l2_bpt_dspa_macro_convergence_probe.json"
json.dump(rows, open(out, "w"), indent=2, ensure_ascii=False)
print(f"-> {out}")
