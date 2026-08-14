#!/usr/bin/env python3
"""DEBUG da linha-mãe: porque context_liquidity está muda nos eventos? Corre CL.compute nos MESMOS bares
que o engine passa e imprime o output REAL (direção/move_class/sequence states/trapped) + distribuição."""
import sys, json, datetime as dt
from pathlib import Path
ROOT = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(ROOT / "alert-bridge"))
import context_liquidity as CL
CAP15 = ROOT / "alert-bridge/logs/backtests/XAUUSD_15m_replay_2026-08-10_to_2026-08-14.jsonl"
READS = ROOT / "alert-bridge/logs/candle_reads.jsonl"
MON = int(dt.datetime(2026, 8, 10, tzinfo=dt.timezone.utc).timestamp())


def utc(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")


longs = {}
for l in open(READS):
    if not l.strip(): continue
    r = json.loads(l); bt = r.get("bar_t")
    if bt is None or int(bt) < MON: continue
    if ((r.get("read") or {}).get("direction") or "") == "LONG": longs[int(bt)] = 1
evt = set(longs)
cap = {}
for l in open(CAP15):
    if not l.strip(): continue
    r = json.loads(l)
    oh = r.get("ohlcv"); bars = oh.get("bars") if isinstance(oh, dict) else oh
    if not bars: continue
    last = bars[-1]; t = int(last.get("t") or last.get("time"))
    if t in evt:
        cap[t] = [{"t": int(b.get("t", b.get("time"))), "o": float(b.get("o", b.get("open"))),
                   "h": float(b.get("h", b.get("high"))), "l": float(b.get("l", b.get("low"))),
                   "c": float(b.get("c", b.get("close")))} for b in bars[-500:]]

from collections import Counter
cd, ch, cl_, ct = Counter(), Counter(), Counter(), Counter()
n_bars = []
first = 0
for t in sorted(cap):
    bars = cap[t]; n_bars.append(len(bars))
    liq = CL.compute(bars) or {}
    seq = liq.get("sequence") or {}; hi = seq.get("high") or {}; lo = seq.get("low") or {}
    cd[liq.get("direction")] += 1; ch[hi.get("state")] += 1; cl_[lo.get("state")] += 1
    ct[hi.get("trapped")] += 1
    if first < 4:
        print("%s | dir=%-4s move=%-22s | HIGH %-12s trap=%-6s | LOW %-12s trap=%-6s | nbars=%d taken=%d"
              % (utc(t), liq.get("direction"), str(liq.get("move_class")), str(hi.get("state")),
                 str(hi.get("trapped")), str(lo.get("state")), str(lo.get("trapped")),
                 len(bars), len(liq.get("taken") or [])))
        first += 1
print("\n=== distribuição em %d eventos ===" % len(cap))
print(" nbars: min %d / mediana %d / max %d" % (min(n_bars), sorted(n_bars)[len(n_bars)//2], max(n_bars)))
print(" direction:", dict(cd))
print(" HIGH.state:", dict(ch))
print(" LOW.state:", dict(cl_))
print(" HIGH.trapped:", dict(ct))
print("\n minha condição de voto breakdown = (dir==down AND HIGH.state==FAILED AND HIGH.trapped==buyers)")
print(" -> quantos eventos a satisfazem?",
      sum(1 for t in cap for liq in [CL.compute(cap[t]) or {}]
          if liq.get("direction") == "down"
          and ((liq.get("sequence") or {}).get("high") or {}).get("state") == "FAILED"
          and ((liq.get("sequence") or {}).get("high") or {}).get("trapped") == "buyers"))
