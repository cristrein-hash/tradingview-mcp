#!/usr/bin/env python3
"""RAW BACKBONE BUILDER — reconstroi a Camada-1 do Reader Vivo a partir do RAW ORIGINAL (elimina debito derivado).
FONTE = /Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_240m_replay_*.jsonl.gz (as-of-bar, causal).
  supply/demand (sup_cat/clean_sky/dist_supply/dist_demand) <- pine_boxes['Custom OB Detector v11 - Alert'] (SUPPLY/DEMAND boxes)
  ohlcv window  <- ohlcv do RAW
  weekly/cascade/leg <- regime_classifier_v3 (PRICE-only: ma/breaks/cascade) => DERIVED_FROM_RAW_WITH_MAPPING; fidelity close==RAW
  SVP/POC/VAL/VAH/acceptance <- session_vp guarda itens brutos do VP, VA nao computada => UNKNOWN_BLOCKED (nao inventar)
Cada campo carrega source_mapping_status. SEM outcome/R/MFE/runner/trap. Saida: results/l2_bpt_raw_backbone_episodes.jsonl
Alinhamento: entry_epoch+close do frozen SO p/ localizar a barra e verificar (close=OHLC, nao indicador). RAW e autoridade."""
import gzip, json, datetime as dt, os, bisect

RAWDIR = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H"
BLOCK_2020 = f"{RAWDIR}/XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz"
BLOCK_2023 = f"{RAWDIR}/XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz"
RR = "repro_recovery"; D = "results"; BAR = 14400; W = 14
REG = "../../../../strategies/candidates/regime_classifier_v3"
CL1 = [4918, 4926, 1661, 5701, 6887, 7426, 8878, 8923, 8940]
CL2 = [5826, 1623, 4401, 3825, 1522, 1873, 5627, 1775, 3949, 3929]
EPS = CL1 + CL2
def bar_open(ep): return ep - ((ep - 7200) % BAR)
def to_ep(t):
    if t is None: return None
    t = float(t); return int(t / 1000) if t > 1e11 else int(t)

F = [json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
ENTRY = {b: int(F[b]["ts_epoch"]) for b in EPS}; FCLOSE = {b: float(F[b]["close"]) for b in EPS}
# ATR14 do RAW frozen (price-faithful) so p/ normalizar distancias (escala); valor = preco RAW depois
H = [r['high'] for r in F]; L = [r['low'] for r in F]; C = [r['close'] for r in F]
ATR = [None] * len(F); trs = []
for i in range(1, len(F)):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14: ATR[i] = sum(trs[i - 14:i]) / 14

# regime price-derived (DERIVED_FROM_RAW): por ts mais recente <= entry
def _toep(s):
    try: return int(dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
    except Exception:
        try: return int(dt.datetime.strptime(str(s)[:10], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
        except Exception: return None
def load_reg(path, keys):
    rows = [json.loads(l) for l in open(path) if json.loads(l).get('ts')]
    for r in rows: r["_ep"] = _toep(r["ts"])
    rows = [r for r in rows if r["_ep"] is not None]
    rows.sort(key=lambda r: r["_ep"]); ts = [r["_ep"] for r in rows]
    return rows, ts
RB, RBts = load_reg(f"{REG}/regime_B_v3_classifications.jsonl", None)
WK, WKts = load_reg(f"{REG}/xau_weekly_with_features.jsonl", None)
def asof(rows, ts, edate):
    k = bisect.bisect_right(ts, edate) - 1
    return rows[k] if k >= 0 else {}

def block_of(b): return BLOCK_2020 if ENTRY[b] < int(dt.datetime(2023, 1, 1, tzinfo=dt.timezone.utc).timestamp()) else BLOCK_2023

# coleta RAW: OHLC + Custom OB boxes p/ janelas-alvo (prefiltro por data)
target_dates = set()
for b in EPS:
    eo = bar_open(ENTRY[b])
    for k in range(0, W + 1):
        target_dates.add(dt.datetime.utcfromtimestamp(eo - k * BAR).strftime("%Y-%m-%d"))
        target_dates.add(dt.datetime.utcfromtimestamp(eo - k * BAR + BAR - 1).strftime("%Y-%m-%d"))
def ob_boxes(rec):
    for bx in (rec.get("pine_boxes") or []):
        if "Custom OB" in str(bx.get("name", "")):
            return bx.get("boxes") or bx.get("all_boxes") or []
    return []
def rec_close(rec):
    oh = rec.get("ohlcv")
    if isinstance(oh, list) and oh: return (oh[-1].get("close") if isinstance(oh[-1], dict) else None)
    if isinstance(oh, dict): return oh.get("close")
    return None
snap = {}
for blk in (BLOCK_2020, BLOCK_2023):
    if not os.path.exists(blk): continue
    with gzip.open(blk, "rt") as fh:
        for line in fh:
            if not any(d8 in line for d8 in target_dates): continue
            rec = json.loads(line)
            oh = rec.get("ohlcv")
            win = [{"o": x.get("open"), "h": x.get("high"), "l": x.get("low"), "c": x.get("close"), "t": x.get("time")}
                   for x in (oh if isinstance(oh, list) else [])][-W:]
            if not win or win[-1].get("t") is None: continue
            # CHAVE = timestamp REAL da ultima barra fechada (as-of bar), NAO bar_open(grade fixa).
            # A grade 4H do feed desloca com DST de NY (achado 2026-06-23); usar o tempo real elimina a suposicao.
            asof_t = to_ep(win[-1]["t"])
            snap.setdefault(asof_t, {"close": rec_close(rec), "boxes": ob_boxes(rec),
                                     "ohlc_window": win, "dt": rec.get("replay_current_dt")})

snaps_sorted = sorted(snap.items())              # por asof_t (tempo real da barra)
asof_keys = [t for t, _ in snaps_sorted]
def anchor(b):
    """CAUSAL as-of join por TIMESTAMP real (sem grade): snapshot cuja ultima barra fechada == entry (ENTRY[b]).
    Fallback = maior asof_t <= entry dentro de 1 barra. NUNCA escolhe barra futura. Substitui o close-match
    (look-ahead, +1/+2 barras futuras, DA 2026-06-23) e o bar_open de grade fixa (errado no DST)."""
    et = ENTRY[b]
    if et in snap:                               # match exato da barra de entry
        return asof_keys.index(et)
    k = bisect.bisect_right(asof_keys, et) - 1   # as-of: ultima barra fechada <= entry
    if k >= 0 and et - asof_keys[k] <= BAR:
        return k
    return None

def supply_demand(idx, b):
    s = snaps_sorted[idx][1]; close = s["close"]; atr = ATR[b] or 1.0
    sup = [bx for bx in s["boxes"] if str(bx.get("text", "")).upper() == "SUPPLY"]
    dem = [bx for bx in s["boxes"] if str(bx.get("text", "")).upper() == "DEMAND"]
    # supply overhead = box com low >= close (acima); demand = box com high <= close (abaixo)
    over = [bx for bx in sup if bx.get("low") is not None and bx["low"] >= close]
    under = [bx for bx in dem if bx.get("high") is not None and bx["high"] <= close]
    dist_sup = round((min(bx["low"] for bx in over) - close) / atr, 2) if over else None
    dist_dem = round((close - max(bx["high"] for bx in under)) / atr, 2) if under else None
    has_overhead = bool(over)
    clean_sky = (not over) or (dist_sup is not None and dist_sup > 3.0)
    sup_cat = ("CLEAN_SKY" if not over else
               ("SUPPLY_NEAR" if dist_sup is not None and dist_sup <= 1.0 else
                ("SUPPLY_BLOCKS" if dist_sup is not None and dist_sup <= 2.0 else "SUPPLY_FAR")))
    return {"sup_cat": sup_cat, "clean_sky": clean_sky, "has_overhead": has_overhead,
            "dist_supply_atr": dist_sup, "dist_demand_atr": dist_dem,
            "n_supply_boxes": len(sup), "n_demand_boxes": len(dem),
            "_status": "RAW_ORIGINAL_OK", "_raw_field": "pine_boxes[Custom OB Detector v11]"}

out = []
for b in EPS:
    idx = anchor(b); s = snaps_sorted[idx][1] if idx is not None else {}
    raw_close = s.get("close"); edate = ENTRY[b]
    rb = asof(RB, RBts, edate); wk = asof(WK, WKts, edate)
    # fidelity do regime: close do regime ~ close RAW (price-faithful)
    reg_close = rb.get("close")
    reg_fid = (reg_close is not None and raw_close is not None and abs(float(reg_close) - raw_close) / raw_close < 0.01)
    sd = supply_demand(idx, b) if idx is not None else {"_status": "UNKNOWN_BLOCKED"}
    # GUARD CAUSAL (as-of por tempo real): ultima barra da janela NUNCA pode ser futura (t > entry); ideal == entry.
    win = s.get("ohlc_window") or []
    win_last_t = to_ep(win[-1].get("t")) if win and win[-1].get("t") is not None else None
    causal_ok = (win_last_t is not None and win_last_t <= ENTRY[b])      # sem barra futura
    exact_anchor = (win_last_t == ENTRY[b])                             # barra de entry exata
    anchor_close_fid = (raw_close is not None and abs(float(raw_close) - FCLOSE[b]) / FCLOSE[b] < 0.005)
    out.append({
        "bar_idx": b, "timestamp": dt.datetime.utcfromtimestamp(ENTRY[b]).strftime("%Y-%m-%d %H:%M"),
        "source_raw_file": os.path.basename(block_of(b)),
        "ohlcv_window": s.get("ohlc_window"), "ohlcv_status": "RAW_ORIGINAL_OK",
        "raw_close": raw_close, "frozen_close": FCLOSE[b],
        "causal_window_ends_at_entry": causal_ok, "anchor_exact": exact_anchor, "anchor_close_fidelity": anchor_close_fid,
        "supply_demand_raw_mapped": sd,
        "regime_raw_mapped": {"weekly_slope": wk.get("slope_20_pct"), "cascade_score": rb.get("cascade_score"),
                              "combined_score": rb.get("combined_score"), "macro_broken": (rb.get("combined_score") is not None and rb.get("combined_score") < 0),
                              "ma200_bull": rb.get("ma200_bull"), "ma200_bear": rb.get("ma200_bear"),
                              "v3_state": rb.get("raw_state"), "_status": "DERIVED_FROM_RAW_WITH_MAPPING",
                              "_transform": "regime_classifier_v3 price-only (ma/breaks/cascade)", "_fidelity_close_vs_raw": reg_fid},
        "svp_status": "UNKNOWN_BLOCKED", "svp_note": "session_vp guarda itens VP brutos; POC/VAL/VAH exigem agregacao VA (bloco futuro); NAO inventado",
        "acceptance_status": "UNKNOWN_BLOCKED", "acceptance_note": "depende de SVP value-area (blocked)",
        "blocked_fields": ["svp_poc_val_vah", "above_value", "below_value", "acceptance"],
        "source_mapping_status_by_field": {
            "ohlcv": "RAW_ORIGINAL_OK", "supply_demand": sd.get("_status"),
            "weekly_cascade_leg": "DERIVED_FROM_RAW_WITH_MAPPING", "svp": "UNKNOWN_BLOCKED", "acceptance": "UNKNOWN_BLOCKED"},
        "warnings": ([] if reg_fid else ["regime close fidelity vs RAW > 1pct"])
                    + ([] if idx is not None else ["sem snapshot RAW (anchor falhou)"])
                    + ([] if causal_ok else ["janela contem barra FUTURA (look-ahead)"])
                    + ([] if exact_anchor else ["anchor as-of barra anterior (sem futuro; entry exata ausente)"])
                    + ([] if anchor_close_fid else ["anchor close fidelity vs frozen > 0.5pct (feed RAW != frozen)"]),
    })

with open(f"{D}/l2_bpt_raw_backbone_episodes.jsonl", "w") as f:
    for o in out: f.write(json.dumps(o, ensure_ascii=False) + "\n")
nfid = [o["bar_idx"] for o in out if not o["regime_raw_mapped"]["_fidelity_close_vs_raw"]]
nanch = [o["bar_idx"] for o in out if o["supply_demand_raw_mapped"].get("_status") != "RAW_ORIGINAL_OK"]
print(f"RAW BACKBONE: {len(out)} episodios -> {D}/l2_bpt_raw_backbone_episodes.jsonl")
print(f"  supply/demand RAW (Custom OB boxes): {len(out)-len(nanch)}/{len(out)} OK | regime fidelity-fail: {nfid or 'nenhum'}")
print("  SVP/acceptance = UNKNOWN_BLOCKED (nao inventado). OHLC=RAW, supply/demand=RAW, regime=DERIVED_FROM_RAW(price).")
for b in (5826, 5627, 4918, 3949):
    o = [x for x in out if x["bar_idx"] == b][0]; sd = o["supply_demand_raw_mapped"]
    print(f"    #{b} close{o['raw_close']} sup_cat={sd.get('sup_cat')} clean_sky={sd.get('clean_sky')} distSup={sd.get('dist_supply_atr')} distDem={sd.get('dist_demand_atr')} | weekly={o['regime_raw_mapped']['weekly_slope']} casc={o['regime_raw_mapped']['cascade_score']}")
