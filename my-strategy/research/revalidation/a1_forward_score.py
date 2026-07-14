#!/usr/bin/env python3
"""COLETOR FORWARD A1 (prereg A1_MB3_ENTRY_PREREG_FORWARD_20260714) — pontua cada fundo A1 novo
MB3 vs RECLAIM pelas regras SELADAS e regista num log organizado. Estado PENDING até o outcome
resolver (dados chegarem). RAW 15M direto do HD. NÃO altera as regras do prereg.

USO:
  python3 a1_forward_score.py "2026-07-15 09:00"   # pontua+regista um fundo (dt do candle de fundo)
  python3 a1_forward_score.py --status             # log + progresso (N/20) + painel interino
  python3 a1_forward_score.py --resolve            # re-pontua PENDENTES (dados novos podem ter chegado)
"""
import gzip, json, bisect, random, sys, datetime as dt, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
LOG = HERE / "a1_forward" / "forward_log.jsonl"; LOG.parent.mkdir(exist_ok=True)
LOWBACK, LOWFWD, TRIG_WIN, HORIZON = 16, 8, 48, 480
random.seed(20260714)
sys.path.insert(0, str(HERE)); import macro_structural_v3 as M
ep = lambda s: int(dt.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).timestamp())
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
grp = lambda rec, k, s: next((x for x in (rec.get(k) or []) if s.lower() in str(x.get("name", "")).lower()), None)

def blocks_covering(t0):
    """blocos cujo range cobre [t0-30d, t0+6d]."""
    out = []
    for p in sorted(RAW.glob("XAUUSD_15m_replay_*.jsonl.gz")):
        try:
            a, b = p.name.replace("XAUUSD_15m_replay_", "").split(".jsonl")[0].split("_to_")
            b = b.split("_")[0]
            ta = ep(a + " 00:00"); tb = ep(b + " 00:00") + 86400*95
        except Exception: continue
        if tb >= t0 - 30*86400 and ta <= t0 + 6*86400: out.append(p)
    return out

def load(t0):
    """série 15M (barras completas, merge) + zonas OB SUPPLY causais dos blocos que cobrem o fundo."""
    bars = {}; zones = {}
    for p in blocks_covering(t0):
        with gzip.open(p, "rt") as fh:
            for line in fh:
                i = line.find('"ohlcv":')
                if i >= 0:
                    s = line.find('[', i); e = line.find(']', s)
                    if s >= 0 and e >= 0:
                        try: arr = json.loads(line[s:e+1])
                        except Exception: arr = []
                        for b in arr:
                            t = b.get("time")
                            if t is None: continue
                            if t not in bars: bars[t] = [b["open"], b["high"], b["low"], b["close"]]
                            else: bars[t][1] = max(bars[t][1], b["high"]); bars[t][2] = min(bars[t][2], b["low"]); bars[t][3] = b["close"]
                if '"pine_boxes"' in line and '"Custom OB"' in line:
                    try: r = json.loads(line)
                    except Exception: continue
                    cur = (r.get("ohlcv") or [{}])[-1].get("time")
                    ob = grp(r, "pine_boxes", "Custom OB")
                    for bx in (ob.get("all_boxes") if ob else []) or []:
                        zid = (p.name, bx.get("id"))
                        if bx.get("id") is None: continue
                        if zid not in zones and "SUPPLY" in str(bx.get("text", "")).upper():
                            zones[zid] = {"low": bx.get("low"), "high": bx.get("high"), "born_t": cur}
    T = sorted(bars); O=[bars[t][0] for t in T]; H=[bars[t][1] for t in T]; L=[bars[t][2] for t in T]; C=[bars[t][3] for t in T]
    ema=None; kE=2/22; trs=[]; EMA=[None]*len(T); ATR=[None]*len(T)
    for i, t in enumerate(T):
        ema = C[i] if ema is None else C[i]*kE+ema*(1-kE); EMA[i]=ema
        if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
        ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
    return T, O, H, L, C, EMA, ATR, list(zones.values())

def score(fundo_dt):
    t0 = ep(fundo_dt); T, O, H, L, C, EMA, ATR, sup = load(t0)
    if not T or T[-1] < t0: return {"fundo_dt": fundo_dt, "status": "SEM-DADOS-RAW (recolher 15M até à data)"}
    j = bisect.bisect_right(T, t0)-1; N = len(T)
    gate = M.build_layer1(); KN1 = [x+86400 for x in M.T]
    macro = gate[bisect.bisect_right(KN1, t0)-1] if bisect.bisect_right(KN1, t0)-1 >= 0 else None
    lo0, hi0 = max(0, j-LOWBACK), min(N, j+LOWFWD+1); al = min(range(lo0, hi0), key=lambda k: L[k])
    low = L[al]; atr = ATR[al] or 5.0; sl = round(low-0.1*atr, 2); data_end = T[-1]
    def outc(ei, tgt):
        for m in range(ei+1, min(N, ei+HORIZON+1)):
            if L[m] <= sl: return "LOSS", m-ei
            if H[m] >= tgt: return "WIN", m-ei
        return ("OPEN" if T[min(N-1, ei+HORIZON)] < data_end else "PENDING", None)
    def mb3():
        for k in range(al+1, min(N, al+TRIG_WIN+1)):
            if C[k] > O[k] and C[k] > H[k-1]: return k
        return None
    def rcl():
        for k in range(al+1, min(N, al+TRIG_WIN+1)):
            if EMA[k] is not None and C[k] > EMA[k] and C[k] > C[k-1]: return k
        return None
    def leg(tag, ei):
        if ei is None: return {"trig": "NO-TRIG"}
        ent = C[ei]; r = ent-sl
        if r <= 0.05*atr: return {"trig": "SKIP-tinyR", "entry": round(ent, 2)}
        o, b = outc(ei, ent+3*r)
        return {"entry": round(ent, 2), "R": round(r, 2), "RATR": round(r/atr, 2), "lag": ei-al,
                "outcome": o, "bars_to_3R": b, "tight_R": r/atr < 1.65}
    # supply overhead imediato (zona SUPPLY causal born<=fundo, acima do low, mais próxima)
    supa = None
    cs = [z for z in sup if z["born_t"] and z["born_t"] <= t0 and z["low"] and z["low"] >= low]
    if cs:
        z = min(cs, key=lambda z: z["low"]-low); supa = round((z["low"]-low)/atr, 2)
    # null
    wins = 0
    for _ in range(500):
        ei = random.randint(al+1, min(N-2, al+TRIG_WIN)); ent = C[ei]; r = ent-sl
        if r > 0.05*atr and outc(ei, ent+3*r)[0] == "WIN": wins += 1
    mb, rc = leg("MB3", mb3()), leg("RCL", rcl())
    st = "RESOLVED" if all(x.get("outcome") in ("WIN", "LOSS", "OPEN") for x in (mb, rc) if "outcome" in x) else "PENDING"
    if macro != "BULL": st = f"NOT-A1 (macro={macro})"
    return {"fundo_dt": fundo_dt, "low": low, "atr": round(atr, 2), "SL": sl, "macro_1d": macro,
            "MB3": mb, "RECLAIM": rc, "supply_overhead_atr": supa, "null_win_pct": round(100*wins/500),
            "data_end": ds(data_end), "status": st, "scored_at": ds(int(M.T[-1]))}

def load_log():
    return [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()] if LOG.exists() else []
def save_log(rows):
    LOG.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows))
def upsert(rec):
    rows = load_log(); rows = [r for r in rows if r.get("fundo_dt") != rec["fundo_dt"]]; rows.append(rec)
    rows.sort(key=lambda r: r["fundo_dt"]); save_log(rows); return rows

def show_status():
    rows = load_log()
    res = [r for r in rows if r.get("status") == "RESOLVED"]
    print(f"FORWARD A1 LOG — {len(rows)} fundos registados · {len(res)} RESOLVED · progresso {len(res)}/20")
    for r in rows:
        m, c = r.get("MB3", {}), r.get("RECLAIM", {})
        print(f"  {r['fundo_dt']:16} macro {str(r.get('macro_1d')):5} | MB3 {m.get('outcome','?')}({m.get('RATR','-')}R/ATR) "
              f"RCL {c.get('outcome','?')} | sup {r.get('supply_overhead_atr')}ATR null {r.get('null_win_pct')}% [{r.get('status')}]")
    if len(res) >= 20:
        for tag in ("MB3", "RECLAIM"):
            v = [r[tag] for r in res if r.get(tag, {}).get("outcome") in ("WIN", "LOSS")]
            w = sum(1 for x in v if x["outcome"] == "WIN")
            print(f"  {tag}: hit-3R {100*w/len(v):.0f}% ({w}/{len(v)})")
        print("  → aplicar CRITÉRIO §6 do prereg (PASS/FAIL).")
    else:
        print(f"  INCONCLUSIVO — precisa ≥20 RESOLVED (prereg §6). Continuar a coletar.")

if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "--status"
    if a == "--status": show_status()
    elif a == "--resolve":
        rows = load_log()
        for r in [x for x in rows if x.get("status") in ("PENDING",)]:
            upsert(score(r["fundo_dt"]))
        show_status()
    else:
        rec = score(a); upsert(rec); print(json.dumps(rec, ensure_ascii=False, indent=1))
