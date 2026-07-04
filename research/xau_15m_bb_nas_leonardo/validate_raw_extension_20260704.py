#!/usr/bin/env python3
"""R4 v2 — Validação do trecho RAW coletado (2026-05-25 → 2026-07-04), CONVENÇÃO DO BUILDER.
v1 errou a identidade de barra (ohlcv[-1] às vezes é a barra seguinte recém-aberta, flat na abertura —
corrida de captura; o builder oficial une as janelas com last-write-wins e a corrida se auto-cura).
v2: normalização = APENAS aparar cauda pós-replay (replay_current_dt=None); ZERO dedupe (todo snapshot
alimenta first-appearance de eventos). Série validada via simulação da extração do builder (bars dict).
Checks: monotonia/buracos/flats meio-de-sessão/junção com 8º bloco/OHLC sane/contagem/sha256 +
cross-check run-1 (série curada das duas runs deve coincidir). Saídas: validation json + gap csv."""
import json, csv, hashlib, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
BT = Path("/Users/cristrein/tradingview-mcp/alert-bridge/logs/backtests")
STAGE = BT / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl"
RUN1 = BT / "forensics_20260704_run1" / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl"
PREV_END = 1779667200  # última barra do 8º bloco (2026-05-25 00:00 UTC)
REQ = {"_feature_availability", "bar_index", "ohlcv", "study_values", "pine_boxes",
       "pine_labels", "pine_lines", "pine_shapes_bubbles", "replay_current_dt", "symbol", "timeframe"}
fails, warns = [], []

# ---- normalização: aparar cauda pós-replay APENAS ----
NORM = STAGE.with_name(STAGE.stem + ".normalized.jsonl")
kept = 0; junk = 0; schema_bad = 0
sha = hashlib.sha256()
with open(STAGE, "rb") as fi, open(NORM, "wb") as fo:
    for raw in fi:
        r = json.loads(raw)
        if not r.get("replay_current_dt"): junk += 1; continue
        if not REQ.issubset(r.keys()): schema_bad += 1
        if r["symbol"] != "PEPPERSTONE:XAUUSD" or str(r["timeframe"]) != "15":
            fails.append(f"symbol/tf errado em bar_index {r.get('bar_index')}")
        fo.write(raw); sha.update(raw); kept += 1
if schema_bad: fails.append(f"{schema_bad} registros sem schema completo")
print(f"normalização v2: {kept} snapshots reais · {junk} cauda pós-replay descartada · dedupe NENHUM (builder usa todos)")

# ---- extração à moda do builder: união das janelas, last-write-wins ----
def builder_bars(path):
    bars = {}
    for raw in open(path, "rb"):
        r = json.loads(raw)
        if not r.get("replay_current_dt"): continue
        for b in (r.get("ohlcv") or []):
            if isinstance(b, dict) and b.get("time") is not None:
                bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"], "v": b.get("volume")}
    return bars
B2 = builder_bars(NORM)
ts = sorted(B2)
n = len(ts)

# sanidade OHLC + flats meio-de-sessão
flats = []
for t in ts:
    b = B2[t]
    if not (b["h"] >= max(b["o"], b["c"]) >= min(b["o"], b["c"]) >= b["l"]):
        fails.append(f"OHLC insano t={t}")
    if b["o"] == b["h"] == b["l"] == b["c"]:
        a = dt.datetime.utcfromtimestamp(t)
        if a.weekday() < 5 and a.hour not in (20, 21, 22): flats.append(a.isoformat())
# a última barra flat = convenção dos blocos históricos (fim-de-replay; o 8º também termina flat)
if flats and flats[-1] == dt.datetime.utcfromtimestamp(ts[-1]).isoformat():
    warns.append(f"última barra flat (convenção fim-de-replay, igual aos blocos históricos): {flats.pop()}")
if flats: fails.append(f"{len(flats)} barras flat meio-de-sessão NÃO-finais: {flats[:5]}")

# gaps (900s; fds/feriado/sessão)
gaps = []
for i in range(1, n):
    d = ts[i] - ts[i - 1]
    if d > 900:
        a = dt.datetime.utcfromtimestamp(ts[i - 1]); z = dt.datetime.utcfromtimestamp(ts[i])
        weekend = a.weekday() == 4 and z.weekday() == 6 and d <= 60 * 3600
        holiday = a.hour in (17, 18, 19) and z.hour in (22, 23) and d <= 8 * 3600
        typ = "weekend" if weekend else ("holiday_early_close" if holiday else
                                         ("session" if d <= 3 * 3600 and a.hour in (20, 21, 22) else
                                          ("HOLE_1BAR" if d == 1800 else "INSPECT")))
        gaps.append({"from": a.isoformat(), "to": z.isoformat(), "gap_min": d // 60, "type": typ})
holes = [g for g in gaps if g["type"] == "HOLE_1BAR"]; insp = [g for g in gaps if g["type"] == "INSPECT"]
if holes: fails.append(f"{len(holes)} buracos de 1 barra na série curada")
if insp: warns.append(f"{len(insp)} gaps INSPECT")

# junção + equality com 8º bloco nas barras de overlap
prim8 = json.load(open(HERE / "primitives" / "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.primitives.json"))["series"]
p8 = {b["t"]: b for b in prim8}
overlap = [t for t in ts if t <= PREV_END]
ov_mism = 0
for t in overlap:
    if t in p8:
        e = p8[t]; b = B2[t]
        if any(abs(b[k] - e[k]) > 1e-9 for k in ("o", "h", "l", "c")):
            # convenção conhecida: a ÚLTIMA barra de cada bloco histórico é flat (fim-de-replay).
            # Se a divergência é exatamente essa (8º flat, extensão formada), é documentada, não FAIL.
            if e["o"] == e["h"] == e["l"] == e["c"] and t == PREV_END:
                warns.append(f"overlap t={t}: 8º bloco tem barra final FLAT (artefato fim-de-replay do bloco antigo); extensão tem formada — 8º permanece autoritativo via setdefault")
            else:
                ov_mism += 1
if ov_mism: fails.append(f"{ov_mism} barras de overlap divergem do 8º bloco")
new_ts = [t for t in ts if t > PREV_END]
first_new = new_ts[0] if new_ts else None
if first_new is None: fails.append("nenhuma barra nova")
elif first_new - PREV_END > 900: fails.append(f"buraco na junção: {(first_new-PREV_END)//60} min")

# cross-check run-1 (série curada das duas runs)
xr = {"available": RUN1.exists()}
if RUN1.exists():
    B1 = builder_bars(RUN1)
    com = sorted(set(B2) & set(B1))
    mism = sum(1 for t in com if any(abs(B2[t][k] - B1[t][k]) > 1e-9 for k in ("o", "h", "l", "c")))
    xr.update(common=len(com), ohlc_mismatches=mism, only_run2=len(set(B2) - set(B1)), only_run1=len(set(B1) - set(B2)))
    if mism > 0: warns.append(f"cross-check run-1: {mism} barras divergem na série curada (investigar)")

res = {"file": str(NORM), "snapshots": kept, "junk_tail_dropped": junk, "sha256_normalized": sha.hexdigest(),
       "bars_cured": n,
       "first_bar": dt.datetime.utcfromtimestamp(ts[0]).isoformat() if ts else None,
       "last_bar": dt.datetime.utcfromtimestamp(ts[-1]).isoformat() if ts else None,
       "overlap_bars_with_block8": len(overlap), "overlap_ohlc_mismatch_vs_block8": ov_mism,
       "first_new_bar": dt.datetime.utcfromtimestamp(first_new).isoformat() if first_new else None,
       "new_bars_after_block8": len(new_ts), "flats_mid_session": len(flats),
       "gaps_total": len(gaps), "holes_1bar": len(holes), "gaps_inspect": len(insp),
       "cross_check_run1": xr, "fails": fails, "warns": warns,
       "verdict": "PASS" if not fails else "FAIL"}
json.dump(res, open(HERE / "results" / "raw_15m_extension_validation_20260704.json", "w"), indent=1)
with open(HERE / "results" / "raw_15m_extension_gap_report_20260704.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["from", "to", "gap_min", "type"]); w.writeheader()
    for g in gaps: w.writerow(g)
print(json.dumps(res, indent=1))
