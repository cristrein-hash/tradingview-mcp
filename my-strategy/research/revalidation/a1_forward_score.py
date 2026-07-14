#!/usr/bin/env python3
"""COLETOR FORWARD A1/A2 (prereg A1_MB3_ENTRY, âncora CAUSAL pós-fix-lookahead 2026-07-15) — pontua
cada fundo novo MB3 vs RECLAIM pelo ENTRY CAUSAL canónico (a1_causal_entry: âncora = swing-low fractal
confirmado, ZERO lookahead) + supply-overhead + null. Log organizado, estado PENDING até resolver.

USO:
  python3 a1_forward_score.py "2026-07-15 09:00" [A1|A2]   # pontua+regista um fundo (default A1)
  python3 a1_forward_score.py --status
  python3 a1_forward_score.py --resolve
"""
import gzip, json, bisect, random, sys, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import macro_structural_v3 as M
from a1_causal_entry import load_series, causal_entry, HORIZON, LOWBACK, M_FRAC, TRIG_WIN
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
LOG = HERE/"a1_forward"/"forward_log.jsonl"; LOG.parent.mkdir(exist_ok=True)
random.seed(20260714)
ep = lambda s: int(dt.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).timestamp())
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
grp = lambda rec, k, s: next((x for x in (rec.get(k) or []) if s.lower() in str(x.get("name", "")).lower()), None)

def blocks_covering(t0):
    out = []
    for p in sorted(RAW.glob("XAUUSD_15m_replay_*.jsonl.gz")):
        try:
            a, b = p.name.replace("XAUUSD_15m_replay_", "").split(".jsonl")[0].split("_to_")
            b = b.split("_")[0]
            ta = ep(a+" 00:00"); tb = ep(b+" 00:00")+86400*95
        except Exception: continue
        if tb >= t0-30*86400 and ta <= t0+6*86400: out.append(str(p))
    return out

def supply_zones(blocks, t0):
    zones = {}
    for pth in blocks:
        with gzip.open(pth, "rt") as fh:
            for line in fh:
                if '"pine_boxes"' not in line or '"Custom OB"' not in line: continue
                try: r = json.loads(line)
                except Exception: continue
                cur = (r.get("ohlcv") or [{}])[-1].get("time")
                ob = grp(r, "pine_boxes", "Custom OB")
                for bx in (ob.get("all_boxes") if ob else []) or []:
                    zid = (pth, bx.get("id"))
                    if bx.get("id") is None or zid in zones: continue
                    if "SUPPLY" in str(bx.get("text", "")).upper():
                        zones[zid] = {"low": bx.get("low"), "born_t": cur}
    return list(zones.values())

def score(fundo_dt, layer="A1"):
    t0 = ep(fundo_dt); blks = blocks_covering(t0)
    S = load_series(blks); T = S["T"]
    if not T or T[-1] < t0: return {"fundo_dt": fundo_dt, "layer": layer, "status": "SEM-DADOS-RAW (recolher 15M até à data)"}
    j = bisect.bisect_right(T, t0)-1
    gate = M.build_layer1(); KN1 = [x+86400 for x in M.T]
    macro = gate[bisect.bisect_right(KN1, t0)-1] if bisect.bisect_right(KN1, t0)-1 >= 0 else None
    mb, rc = causal_entry(S, j, "MB3"), causal_entry(S, j, "RCL")
    data_end = T[-1]
    def fix_pending(e):
        if e and e["o"] == "OPEN" and T[min(len(T)-1, e["ei"]+HORIZON)] >= data_end: e["o"] = "PENDING"
        return e
    mb, rc = fix_pending(mb), fix_pending(rc)
    low = S["L"][mb["anchor_bar"]] if mb else None; atr = S["ATR"][mb["anchor_bar"]] if mb else None
    sup = supply_zones(blks, t0); supa = None
    if mb and low is not None:
        cs = [z for z in sup if z["born_t"] and z["born_t"] <= t0 and z["low"] and z["low"] >= low]
        if cs: supa = round((min(z["low"] for z in cs)-low)/(atr or 5.0), 2)
    # null: entrada aleatória na reação, mesma âncora/SL do MB3
    nullw = None
    if mb:
        sl = mb["sl"]; ab = mb["anchor_bar"]; wins = 0; nn = 0; L, H, C = S["L"], S["H"], S["C"]; N = S["N"]
        for _ in range(500):
            ei = random.randint(ab+1, min(N-2, ab+TRIG_WIN)); ent = C[ei]; r = ent-sl
            if r <= 0.05*(atr or 5.0): continue
            nn += 1; tgt = ent+3*r
            for m in range(ei+1, min(N, ei+HORIZON+1)):
                if L[m] <= sl: break
                if H[m] >= tgt: wins += 1; break
        nullw = round(100*wins/max(1, nn))
    st = "RESOLVED" if (mb and mb["o"] in ("WIN", "LOSS")) and (rc and rc["o"] in ("WIN", "LOSS", "OPEN")) else "PENDING"
    if macro != "BULL": st = f"NOT-A1A2 (macro={macro})"
    def slim(e): return {k: e[k] for k in ("ent", "sl", "R", "RATR", "lag", "o", "bars")} if e else None
    return {"fundo_dt": fundo_dt, "layer": layer, "macro_1d": macro, "MB3": slim(mb), "RECLAIM": slim(rc),
            "supply_overhead_atr": supa, "null_win_pct": nullw, "data_end": ds(data_end), "status": st}

def load_log(): return [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()] if LOG.exists() else []
def save_log(rows): LOG.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows))
def upsert(rec):
    rows = [r for r in load_log() if r.get("fundo_dt") != rec["fundo_dt"]]; rows.append(rec)
    rows.sort(key=lambda r: r["fundo_dt"]); save_log(rows); return rows

def show_status():
    rows = load_log(); res = [r for r in rows if r.get("status") == "RESOLVED"]
    print(f"FORWARD A1/A2 LOG (entry CAUSAL) — {len(rows)} fundos · {len(res)} RESOLVED · progresso {len(res)}/20")
    for r in rows:
        m, c = r.get("MB3") or {}, r.get("RECLAIM") or {}
        print(f"  {r['fundo_dt']:16} {r.get('layer','?'):3} macro {str(r.get('macro_1d')):5} | MB3 {m.get('o','?')}({m.get('RATR','-')}A) "
              f"RCL {c.get('o','?')} | sup {r.get('supply_overhead_atr')}A null {r.get('null_win_pct')}% [{r.get('status')}]")
    if len(res) >= 20:
        for tag in ("MB3", "RECLAIM"):
            v = [r[tag] for r in res if (r.get(tag) or {}).get("o") in ("WIN", "LOSS")]
            w = sum(1 for x in v if x["o"] == "WIN")
            print(f"  {tag}: hit-3R {100*w/max(1,len(v)):.0f}% ({w}/{len(v)}) → aplicar CRITÉRIO §6 do prereg.")
    else:
        print(f"  INCONCLUSIVO — precisa ≥20 RESOLVED (prereg §6). Continuar a coletar.")

if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "--status"
    if a == "--status": show_status()
    elif a == "--resolve":
        for r in [x for x in load_log() if x.get("status") == "PENDING"]: upsert(score(r["fundo_dt"], r.get("layer", "A1")))
        show_status()
    else:
        lay = sys.argv[2] if len(sys.argv) > 2 else "A1"
        rec = score(a, lay); upsert(rec); print(json.dumps(rec, ensure_ascii=False, indent=1))
