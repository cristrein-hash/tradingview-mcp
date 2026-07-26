#!/usr/bin/env python3
"""AUDITORIA DO FUNIL v2 (display read-only): dedup dos candidatos E1 por (bar_time,rule,dir,tf), campos flat.
Para as regioes ideais da semana: o que o E1 gerou, se materiality passou, e o destino no E2. Nada e alterado."""
import json, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
L = "/Users/cristrein/tradingview-mcp/alert-bridge/logs/"

def hm(ts):
    return dt.datetime.fromtimestamp(int(ts), LX).strftime("%d/%m %H:%M")

uniq = {}
for l in open(L + "e1_candidates.jsonl"):
    if not l.strip():
        continue
    c = json.loads(l)
    k = (c.get("bar_time"), c.get("rule"), c.get("direction"), c.get("tf"))
    uniq[k] = c  # ultima gravacao vence
cands = sorted(uniq.values(), key=lambda c: c.get("bar_time") or 0)

verd = {}
for l in open(L + "e2_verdicts.jsonl"):
    if l.strip():
        r = json.loads(l)
        verd[r.get("candidate_id")] = r

t0 = dt.datetime(2026, 7, 16, tzinfo=LX).timestamp()
week = [c for c in cands if (c.get("bar_time") or 0) >= t0]
print(f"=== E1 unicos na semana: {len(week)} ===")
per_day = {}
for c in week:
    d = dt.datetime.fromtimestamp(c["bar_time"], LX).strftime("%d/%m")
    p = per_day.setdefault(d, {"LONG": 0, "SHORT": 0, "pass": 0})
    p[c.get("direction", "?")] += 1
    if (c.get("materiality") or {}).get("pass"):
        p["pass"] += 1
for d in sorted(per_day):
    p = per_day[d]
    print(f"  {d}: LONG {p['LONG']:2d} · SHORT {p['SHORT']:2d} · materiality-PASS {p['pass']}")

print("\n=== TOPO 22-23/07, entry >= 4090 — candidatos unicos e destino ===")
a0 = dt.datetime(2026, 7, 22, 0, 0, tzinfo=LX).timestamp()
a1 = dt.datetime(2026, 7, 23, 23, 59, tzinfo=LX).timestamp()
for c in week:
    bt = c.get("bar_time") or 0
    e = c.get("entry")
    if a0 <= bt <= a1 and e and e >= 4090:
        m = c.get("materiality") or {}
        v = verd.get(c.get("id")) or {}
        rd = v.get("read") or {}
        dest = "nao chegou ao E2" if not v else (
            f"veto={v.get('veto')}" if v.get("veto") else
            f"read ctx={rd.get('context_direction')} conv={rd.get('convergence')} fit={rd.get('candidate_fit')} surf={v.get('surfaced')}")
        print(f"  {hm(bt)} {c['direction']} {c.get('rule')}@{c.get('tf')} e={e} rr={c.get('rr')} "
              f"conf={m.get('confluence')} pass={m.get('pass')} supp={c.get('suppressed')} | {dest}")

print("\n=== DEMANDA 19-21/07, LONG entry 4000-4025 — candidatos unicos e destino ===")
b0 = dt.datetime(2026, 7, 19, 0, 0, tzinfo=LX).timestamp()
b1 = dt.datetime(2026, 7, 21, 23, 59, tzinfo=LX).timestamp()
for c in week:
    bt = c.get("bar_time") or 0
    e = c.get("entry")
    if b0 <= bt <= b1 and c.get("direction") == "LONG" and e and 4000 <= e <= 4025:
        m = c.get("materiality") or {}
        v = verd.get(c.get("id")) or {}
        rd = v.get("read") or {}
        dest = "nao chegou ao E2" if not v else (
            f"veto={v.get('veto')}" if v.get("veto") else
            f"read ctx={rd.get('context_direction')} conv={rd.get('convergence')} fit={rd.get('candidate_fit')} surf={v.get('surfaced')}")
        print(f"  {hm(bt)} {c.get('rule')}@{c.get('tf')} e={e} rr={c.get('rr')} "
              f"conf={m.get('confluence')} pass={m.get('pass')} supp={c.get('suppressed')} | {dest}")

print("\n=== SHORTs unicos da semana inteira (qualquer preco) ===")
for c in week:
    if c.get("direction") == "SHORT":
        m = c.get("materiality") or {}
        if m.get("pass"):
            v = verd.get(c.get("id")) or {}
            rd = v.get("read") or {}
            dest = "nao chegou" if not v else (
                f"veto={v.get('veto')}" if v.get("veto") else
                f"read ctx={rd.get('context_direction')} surf={v.get('surfaced')}")
            print(f"  {hm(c['bar_time'])} {c.get('rule')}@{c.get('tf')} e={c.get('entry')} | {dest}")
