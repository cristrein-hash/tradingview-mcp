#!/usr/bin/env python3
"""DA — probe da convenção do builder vs validação v2:
(a) campo de ordenação do builder ('replay_current_date') existe nos registros? (se não, sort é no-op estável
    e a ordem do arquivo é a temporal — checar monotonia da ordem do arquivo);
(b) registros da cauda pós-replay (replay_current_dt=None) têm ohlcv? (builder NÃO filtra por replay_current_dt —
    só o trim da normalização protege o gz arquivado de contaminação realtime);
(c) verdict/gaps da validação v2."""
import json
from pathlib import Path
BT = Path("/Users/cristrein/tradingview-mcp/alert-bridge/logs/backtests")
NORM = BT / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.normalized.jsonl"
STAGE = BT / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl"

with open(NORM) as f: r0 = json.loads(f.readline())
print("(a) keys:", sorted(r0.keys()))
print("    'replay_current_date' presente?", "replay_current_date" in r0, "· 'replay_current_dt':", r0.get("replay_current_dt"))
# monotonia da ordem do arquivo por replay_current_dt
prev = None; ooo = 0; n = 0
for l in open(NORM):
    r = json.loads(l); n += 1
    d = r.get("replay_current_dt")
    if prev is not None and d is not None and d < prev: ooo += 1
    if d is not None: prev = d
print(f"    ordem do arquivo: {n} registros, fora-de-ordem por replay_current_dt: {ooo}")

# (b) cauda: registros com replay_current_dt=None têm ohlcv?
tail_with_ohlcv = tail_total = 0
for l in open(STAGE):
    r = json.loads(l)
    if not r.get("replay_current_dt"):
        tail_total += 1
        if r.get("ohlcv"): tail_with_ohlcv += 1
print(f"(b) cauda pós-replay: {tail_total} registros · com ohlcv (builder ingeriria!): {tail_with_ohlcv}")

# (b2) a cauda contém barras ALÉM do fim do replay? (risco só se alguém rebuildar do stage não-trimado)
END_T = 1783096200  # 2026-07-03 16:30 UTC
max_tail_t = 0; tail_bars_beyond = 0
for l in open(STAGE):
    r = json.loads(l)
    if not r.get("replay_current_dt"):
        for b in (r.get("ohlcv") or []):
            t = b.get("time") if isinstance(b, dict) else None
            if t: max_tail_t = max(max_tail_t, t); tail_bars_beyond += (t > END_T)
import datetime as dt
print(f"(b2) cauda: max bar time = {dt.datetime.utcfromtimestamp(max_tail_t)} · bars > fim-replay: {tail_bars_beyond}")
p9 = json.load(open(Path(__file__).parent / "primitives" / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.primitives.json"))
print(f"(b3) primitives 9º: n_bars={p9['n_bars']} t_end={dt.datetime.utcfromtimestamp(p9['t_end'])} (sem contaminação se == 16:30)")

# (c) verdict da validação
HERE = Path(__file__).parent
v = json.load(open(HERE / "results" / "raw_15m_extension_validation_20260704.json"))
print("(c) verdict:", v["verdict"], "· fails:", v["fails"], "· warns:", len(v["warns"]),
      "· holes:", v["holes_1bar"], "· inspect:", v["gaps_inspect"], "· xr:", v["cross_check_run1"])
