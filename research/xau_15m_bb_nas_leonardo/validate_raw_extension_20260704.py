#!/usr/bin/env python3
"""R4 — Validação do trecho RAW coletado (2026-05-25 → 2026-07-04) ANTES de qualquer promoção.
Checks: schema/availability · barras monotônicas sem dup · freq 900s (gaps de sessão listados) ·
junção com fim do 8º bloco (t=1779667200, overlap ~1 dia por design) · OHLC sane · contagem esperada ·
amostras · sha256. Saídas: results/raw_15m_extension_validation_20260704.json + gap_report csv."""
import json, csv, hashlib, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
STAGE = Path("/Users/cristrein/tradingview-mcp/alert-bridge/logs/backtests/XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl")
PREV_END = 1779667200  # última barra do 8º bloco (2026-05-25 00:00 UTC)
REQ = {"_feature_availability", "bar_index", "ohlcv", "study_values", "pine_boxes",
       "pine_labels", "pine_lines", "pine_shapes_bubbles", "replay_current_dt", "symbol", "timeframe"}
fails, warns = [], []

# NORMALIZAÇÃO: o replay terminou no live-edge (2026-07-03 16:44 UTC) e o coletor queimou o resto do
# cap com registros replay_current_dt=None (no-op). Normalized candidate = só registros com replay real.
NORM = STAGE.with_name(STAGE.stem + ".normalized.jsonl")
kept_raw = []; junk = 0; dedup_consec = 0; last_t = None
with open(STAGE, "rb") as fh:
    for raw in fh:
        r = json.loads(raw)
        if not r.get("replay_current_dt"): junk += 1; continue
        t = (r.get("ohlcv") or [{}])[-1].get("time")
        if t is not None and t == last_t:
            dedup_consec += 1; continue   # soluço de replay_step: mesmo bar 2x consecutivo → keep-first (causal)
        last_t = t; kept_raw.append(raw)
with open(NORM, "wb") as fh:
    for raw in kept_raw: fh.write(raw)
print(f"normalização: {len(kept_raw)} registros reais · {junk} cauda pós-replay descartada · {dedup_consec} dup consecutivo removido (keep-first)")

sha = hashlib.sha256()
bars = []; navail = 0; schema_bad = 0
with open(NORM, "rb") as fh:
    for raw in fh:
        sha.update(raw)
        r = json.loads(raw)
        if not REQ.issubset(r.keys()): schema_bad += 1
        if r["symbol"] != "PEPPERSTONE:XAUUSD" or str(r["timeframe"]) != "15":
            fails.append(f"symbol/tf errado em bar_index {r.get('bar_index')}")
        av = r.get("_feature_availability", {})
        if not all(av.get(k) for k in ("ohlcv", "study_values", "pine_boxes", "pine_labels", "pine_shapes_bubbles")):
            navail += 1
        o = r.get("ohlcv") or []
        if not o: fails.append(f"sem ohlcv em bar_index {r.get('bar_index')}"); continue
        b = o[-1]
        if not (b["high"] >= max(b["open"], b["close"]) >= min(b["open"], b["close"]) >= b["low"]):
            fails.append(f"OHLC insano t={b['time']}")
        bars.append((b["time"], r["bar_index"], b["open"], b["high"], b["low"], b["close"], b.get("volume")))
if schema_bad: fails.append(f"{schema_bad} registros sem schema completo")
if navail: warns.append(f"{navail} registros com availability parcial")

n = len(bars)
ts = [b[0] for b in bars]
dups = sum(1 for i in range(1, n) if ts[i] == ts[i - 1])
nonmono = sum(1 for i in range(1, n) if ts[i] < ts[i - 1])
if nonmono: fails.append(f"{nonmono} timestamps não-monotônicos")
if dups: fails.append(f"{dups} timestamps duplicados")

# gaps (freq 900s; fds = sex ~21/22h UTC → dom 22/23h = legítimo)
gaps = []
for i in range(1, n):
    d = ts[i] - ts[i - 1]
    if d > 900:
        a = dt.datetime.utcfromtimestamp(ts[i - 1]); z = dt.datetime.utcfromtimestamp(ts[i])
        weekend = a.weekday() == 4 and z.weekday() == 6 and d <= 60 * 3600
        # feriado/early-close: fecha 17-19h UTC e reabre 22-23h UTC (ex.: Memorial Day 2026-05-25)
        holiday = a.hour in (17, 18, 19) and z.hour in (22, 23) and d <= 8 * 3600
        gaps.append({"from": a.isoformat(), "to": z.isoformat(), "gap_min": d // 60,
                     "type": "weekend" if weekend else ("holiday_early_close" if holiday else
                             ("session" if d <= 3 * 3600 else "INSPECT"))})
bad_gaps = [g for g in gaps if g["type"] == "INSPECT"]
if bad_gaps: warns.append(f"{len(bad_gaps)} gaps INSPECT (ver csv)")

# junção: overlap com fim do 8º (barras <= PREV_END) + primeira barra estritamente nova
overlap = sum(1 for t in ts if t <= PREV_END)
new_ts = [t for t in ts if t > PREV_END]
first_new = new_ts[0] if new_ts else None
join_gap = (first_new - PREV_END) if first_new else None
if first_new is None: fails.append("nenhuma barra nova além do fim do 8º bloco")
elif join_gap > 900 * 4 and not (dt.datetime.utcfromtimestamp(PREV_END).weekday() >= 4):
    fails.append(f"buraco na junção: {join_gap//60} min")
last_bar = ts[-1] if ts else None
if last_bar and (dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(last_bar)).days > 2:
    warns.append(f"última barra {dt.datetime.utcfromtimestamp(last_bar)} — >2 dias atrás (fechamento parcial explicar)")

res = {"file": str(NORM), "original_records": len(kept_raw) + junk, "junk_tail_dropped": junk,
       "sha256": sha.hexdigest(), "records": n,
       "first_bar": dt.datetime.utcfromtimestamp(ts[0]).isoformat() if ts else None,
       "last_bar": dt.datetime.utcfromtimestamp(last_bar).isoformat() if last_bar else None,
       "overlap_bars_with_block8": overlap, "first_new_bar": dt.datetime.utcfromtimestamp(first_new).isoformat() if first_new else None,
       "join_gap_min": (join_gap // 60) if join_gap else None,
       "new_bars_after_block8": len(new_ts), "dup": dups, "nonmono": nonmono,
       "gaps_total": len(gaps), "gaps_inspect": len(bad_gaps),
       "sample_first5": [list(b[:6]) for b in bars[:5]], "sample_last5": [list(b[:6]) for b in bars[-5:]],
       "fails": fails, "warns": warns, "verdict": "PASS" if not fails else "FAIL"}
(HERE / "results").mkdir(exist_ok=True)
json.dump(res, open(HERE / "results" / "raw_15m_extension_validation_20260704.json", "w"), indent=1)
with open(HERE / "results" / "raw_15m_extension_gap_report_20260704.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["from", "to", "gap_min", "type"]); w.writeheader()
    for g in gaps: w.writerow(g)
print(json.dumps({k: v for k, v in res.items() if k not in ("sample_first5", "sample_last5")}, indent=1))
