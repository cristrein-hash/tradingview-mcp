#!/usr/bin/env python3
"""Os 9 candidatos que TERIAM BATIDO TP (winners) mas foram SKIPADOS. Junta outcome(TP) + levels(verdicts) +
motivo do skip (veto do gate OU read nao-surfaced + para onde o contexto pendia). Salva p/ plotar. Read-only."""
import json, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
L = "/Users/cristrein/tradingview-mcp/alert-bridge/logs/"
verd = {}
for l in open(L + "e2_verdicts.jsonl"):
    if l.strip():
        r = json.loads(l); verd[r.get("candidate_id")] = r
def hm(ts):
    try: return dt.datetime.fromisoformat(ts).astimezone(LX).strftime("%d/%m %H:%M")
    except Exception: return (ts or "")[:16]
mw = []
for l in open(L + "e2_outcomes.jsonl"):
    if not l.strip(): continue
    o = json.loads(l)
    if o.get("outcome") != "TP": continue
    cid = o.get("candidate_id") or o.get("id")
    v = verd.get(cid) or {}
    lv = v.get("levels") or {}
    read = v.get("read") or {}
    veto = o.get("veto") or v.get("veto")
    why = f"gate VETOU: {veto}" if veto else f"read: contexto pendia {read.get('context_direction')} / conv {read.get('convergence')} (candidato {read.get('candidate_fit')})"
    mw.append({"ts": v.get("ts") or o.get("ts"), "t": v.get("bar_time"), "dir": o.get("direction"),
               "rule": o.get("rule"), "tf": o.get("tf"), "entry": lv.get("entry"), "sl": lv.get("sl"),
               "tgt": lv.get("target"), "rr": lv.get("rr") or o.get("rr"), "why": why})
mw = [m for m in mw if m["entry"] and m["t"]]
mw.sort(key=lambda z: z["t"])
print(f"=== {len(mw)} WINNERS SKIPADOS (teriam batido TP) ===\n")
for i, m in enumerate(mw):
    print(f"#{i+1} {hm(m['ts'])} {m['dir']} {m['rule']}@{m['tf']} | entry {m['entry']} SL {m['sl']} alvo {m['tgt']} RR {m['rr']}")
    print(f"     porque skipado -> {m['why']}\n")
json.dump(mw, open("/Users/cristrein/tradingview-mcp/research/.e2_missed_winners.json", "w"))
print("(salvo em research/.e2_missed_winners.json p/ plot)")
