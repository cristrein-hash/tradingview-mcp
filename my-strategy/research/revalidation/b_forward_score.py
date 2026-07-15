#!/usr/bin/env python3
"""COLETOR FORWARD ENGINE DE B v1.1 (prereg B_ENGINE_V1, 2026-07-15) — pontua cada novo fundo B pelo
`b_engine_v1.b_signal` (gate macro ORDERLY + posição≤40% banda causal + MB3 + SPRING + SL low-real + 3R)
+ null (buy-any-dip porção baixa). Regista gate ON/off + entry + outcome + null. PENDING até resolver.

USO:
  python3 b_forward_score.py "YYYY-MM-DD HH:MM"   # pontua+regista um fundo B candidato
  python3 b_forward_score.py --status
  python3 b_forward_score.py --resolve
"""
import json, bisect, sys, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import b_engine_v1 as BE
from a1_causal_entry import load_series, HORIZON
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
LOG = HERE/"b_forward"/"forward_log.jsonl"; LOG.parent.mkdir(exist_ok=True)
ep = lambda s: int(dt.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).timestamp())
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")

def blocks_covering(t0):
    out = []
    for p in sorted(RAW.glob("XAUUSD_15m_replay_*.jsonl.gz")):
        try:
            a, b = p.name.replace("XAUUSD_15m_replay_", "").split(".jsonl")[0].split("_to_")
            b = b.split("_")[0]
            ta = ep(a+" 00:00"); tb = ep(b+" 00:00")+86400*95
        except Exception: continue
        if tb >= t0-200*86400 and ta <= t0+6*86400: out.append(str(p))   # range-so-far precisa histórico longo
    return out

def score(fundo_dt):
    t0 = ep(fundo_dt); blks = blocks_covering(t0)
    S = load_series(blks); T = S["T"]
    if not T or T[-1] < t0: return {"fundo_dt": fundo_dt, "status": "SEM-DADOS-RAW"}
    r = BE.b_signal(t0, S)
    if not r["engine"]:
        return {"fundo_dt": fundo_dt, "engine": False, "reason": r["reason"],
                "pos": r.get("pos"), "band": r.get("band"), "status": f"REJEITADO ({r['reason']})"}
    e = r["entry"]; j = bisect.bisect_right(T, t0)-1
    o = e["o"]; data_end = T[-1]
    if o == "OPEN" and T[min(len(T)-1, e["ei"]+HORIZON)] >= data_end: o = "PENDING"
    nl = BE._null(j, e["sl"], S["ATR"][j] or 5.0, S)
    st = "RESOLVED" if o in ("WIN", "LOSS") else "PENDING"
    return {"fundo_dt": fundo_dt, "engine": True, "pos": r["pos"], "band": r["band"], "spring": True,
            "entry": {k: e[k] for k in ("ent", "sl", "R", "RATR", "lag", "bars")}, "outcome": o,
            "room_to_res_R": r["room_to_res_R"], "null_win_pct": nl, "data_end": ds(data_end), "status": st}

def load_log(): return [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()] if LOG.exists() else []
def save_log(rows): LOG.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows))
def upsert(rec):
    rows = [r for r in load_log() if r.get("fundo_dt") != rec["fundo_dt"]]; rows.append(rec)
    rows.sort(key=lambda r: r["fundo_dt"]); save_log(rows); return rows

def show_status():
    rows = load_log(); onr = [r for r in rows if r.get("engine")]
    res = [r for r in onr if r.get("status") == "RESOLVED"]
    print(f"FORWARD B-ENGINE v1.1 — {len(rows)} candidatos · {len(onr)} ENGINE-ON · {len(res)} RESOLVED · progresso {len(res)}/20")
    for r in rows:
        if r.get("engine"):
            e = r.get("entry", {})
            print(f"  {r['fundo_dt']:16} ON  pos{r.get('pos')}% {r.get('outcome','?'):7} R{e.get('R','-')}({e.get('RATR','-')}A) null{r.get('null_win_pct')}% [{r.get('status')}]")
        else:
            print(f"  {r['fundo_dt']:16} off {r.get('reason','')} [{r.get('status')}]")
    if len(res) >= 20:
        v = [r for r in res if r["outcome"] in ("WIN", "LOSS")]; w = sum(1 for r in v if r["outcome"] == "WIN")
        print(f"  hit-3R {100*w/max(1,len(v)):.0f}% ({w}/{len(v)}) → aplicar CRITÉRIO §6 do prereg.")
    else:
        print(f"  INCONCLUSIVO — precisa ≥20 RESOLVED (prereg §6).")

if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "--status"
    if a == "--status": show_status()
    elif a == "--resolve":
        for r in [x for x in load_log() if x.get("status") == "PENDING"]: upsert(score(r["fundo_dt"]))
        show_status()
    else:
        rec = score(a); upsert(rec); print(json.dumps(rec, ensure_ascii=False, indent=1))
