#!/usr/bin/env python3
"""AUDITORIA DO FUNIL (display read-only, nao computa estrategia): para cada regiao IDEAL da semana (prints
do Cris, 1H), diz o que cada camada fez: E1 gerou candidato? gate vetou? read recusou/aprovou? Cobertura por
dia/direcao do E1 incluida. Nada e alterado."""
import json, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
L = "/Users/cristrein/tradingview-mcp/alert-bridge/logs/"

def hm(ts):
    return dt.datetime.fromtimestamp(int(ts), LX).strftime("%d/%m %H:%M")

cands = [json.loads(l) for l in open(L + "e1_candidates.jsonl") if l.strip()]
verd = {}
for l in open(L + "e2_verdicts.jsonl"):
    if l.strip():
        r = json.loads(l)
        verd[r.get("candidate_id")] = r

# perfil geral do E1 na semana (20/07 -> 25/07)
t0 = dt.datetime(2026, 7, 16, tzinfo=LX).timestamp()
week = [c for c in cands if (c.get("bar_time") or 0) >= t0]
print(f"=== E1 na semana 16-25/07: {len(week)} candidatos ===")
per_day = {}
for c in week:
    d = dt.datetime.fromtimestamp(c["bar_time"], LX).strftime("%d/%m")
    per_day.setdefault(d, {"LONG": 0, "SHORT": 0})[c.get("direction", "?")] += 1
for d in sorted(per_day):
    p = per_day[d]
    print(f"  {d}: LONG {p['LONG']:2d} · SHORT {p['SHORT']:2d}")

# REGIAO C — o topo 22-23/07 (4100-4165): houve candidato SHORT?
print("\n=== TOPO 22-23/07 (>=4100) — candidatos E1 (qualquer direcao) ===")
top_t0 = dt.datetime(2026, 7, 22, 0, 0, tzinfo=LX).timestamp()
top_t1 = dt.datetime(2026, 7, 23, 23, 59, tzinfo=LX).timestamp()
n_top = 0
for c in week:
    bt = c.get("bar_time") or 0
    if top_t0 <= bt <= top_t1:
        lv = c.get("levels") or {}
        e = lv.get("entry")
        if e and e >= 4100:
            n_top += 1
            cid = c.get("id") or c.get("candidate_id")
            v = verd.get(cid) or {}
            veto = v.get("veto") or (v.get("vetos_all") if v.get("veto") is None else None)
            rd = v.get("read") or {}
            sf = v.get("surfaced")
            print(f"  {hm(bt)} {c['direction']} {c.get('rule')}@{c.get('tf')} entry {e} "
                  f"| veto={veto} read_ctx={rd.get('context_direction')} conv={rd.get('convergence')} surf={sf}")
if n_top == 0:
    print("  NENHUM candidato E1 com entry >= 4100 nos dias 22-23/07.")
    # mostrar o que o E1 gerou nesses dias (independente do preco)
    print("  -- tudo o que o E1 gerou 22-23/07:")
    for c in week:
        bt = c.get("bar_time") or 0
        if top_t0 <= bt <= top_t1:
            lv = c.get("levels") or {}
            print(f"    {hm(bt)} {c['direction']} {c.get('rule')}@{c.get('tf')} entry {lv.get('entry')}")

# REGIAO B — 19-21/07 demanda 4000-4020 pre-rally: candidatos LONG e o que aconteceu
print("\n=== DEMANDA 19-21/07 (4000-4020) — candidatos LONG e destino ===")
b_t0 = dt.datetime(2026, 7, 19, 0, 0, tzinfo=LX).timestamp()
b_t1 = dt.datetime(2026, 7, 21, 23, 59, tzinfo=LX).timestamp()
for c in week:
    bt = c.get("bar_time") or 0
    if b_t0 <= bt <= b_t1 and c.get("direction") == "LONG":
        lv = c.get("levels") or {}
        e = lv.get("entry")
        if e and 4000 <= e <= 4022:
            cid = c.get("id") or c.get("candidate_id")
            v = verd.get(cid) or {}
            rd = v.get("read") or {}
            print(f"  {hm(bt)} {c.get('rule')}@{c.get('tf')} entry {e} | veto={v.get('veto')} "
                  f"read_ctx={rd.get('context_direction')} conv={rd.get('convergence')} fit={rd.get('candidate_fit')} surf={v.get('surfaced')}")
