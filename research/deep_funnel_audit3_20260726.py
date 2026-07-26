#!/usr/bin/env python3
"""AUDITORIA v3 — corte final: candidatos EXECUTAVEIS (geometria valida + sl_atr>=0.3, i.e. SL real,
nao degenerado). O TP contrafactual de risk sub-ATR e' brinquedo (alvo 5R fica a 2 passos). Funil honesto
de winners perdidos por camada + simulacao anti-spam por zona SO nos executaveis. Read-only."""
import json, bisect, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
R = "/Users/cristrein/tradingview-mcp/"
HORIZON = 96

def hm(ts): return dt.datetime.fromtimestamp(int(ts), LX).strftime("%d/%m %H:%M")

bars = sorted([json.loads(l) for l in open(R + "my-strategy/core/bar_store/store/bars_15m.jsonl") if l.strip()], key=lambda b: b["t"])
T = [b["t"] for b in bars]; H = [b["h"] for b in bars]; L = [b["l"] for b in bars]

def resolve(d, e, sl, tg, bt):
    i0 = bisect.bisect_right(T, bt); risk = abs(e - sl)
    mfe = 0.0; oc = None
    for i in range(i0, min(i0 + HORIZON, len(T))):
        hi, lo = H[i], L[i]
        if d == "LONG":
            mfe = max(mfe, (hi - e) / risk); hit_sl = lo <= sl; hit_tp = hi >= tg
        else:
            mfe = max(mfe, (e - lo) / risk); hit_sl = hi >= sl; hit_tp = lo <= tg
        if oc is None:
            oc = "AMBIGUOUS" if (hit_sl and hit_tp) else ("SL" if hit_sl else ("TP" if hit_tp else None))
    return oc or ("EXPIRED" if len(T) - i0 >= HORIZON else "OPEN"), round(mfe, 2)

uniq = {}; sup_seen = {}
for l in open(R + "alert-bridge/logs/e1_candidates.jsonl"):
    if not l.strip(): continue
    c = json.loads(l)
    k = (c.get("bar_time"), c.get("rule"), c.get("direction"), c.get("tf"))
    uniq[k] = c
    if c.get("suppressed"): sup_seen.setdefault(k, set()).add(c["suppressed"])
t0 = dt.datetime(2026, 7, 16, tzinfo=LX).timestamp()
cands = sorted([c for k, c in uniq.items() if (k[0] or 0) >= t0], key=lambda c: c["bar_time"])
verd = {}
for l in open(R + "alert-bridge/logs/e2_verdicts.jsonl"):
    if l.strip():
        r = json.loads(l); verd.setdefault(r.get("candidate_id"), r)
verd_bk = {(r.get("bar_time"), r.get("rule"), r.get("direction"), r.get("tf")): r for r in verd.values()}

def stage_of(c):
    k = (c["bar_time"], c["rule"], c["direction"], c["tf"])
    v = verd.get(c.get("id")) or verd_bk.get(k)
    if v:
        if v.get("veto"): return "gate:" + v["veto"]
        rd = v.get("read") or {}
        if rd.get("error"): return "read-falhou"
        return "SURFACED" if v.get("surfaced") else "read-recusou"
    if not (c.get("materiality") or {}).get("pass"): return "materiality_fail"
    if sup_seen.get(k) or c.get("suppressed"): return "antispam"
    return "sem_verdict"

ex = []
for c in cands:
    e, sl, tg = c.get("entry"), c.get("sl"), c.get("target")
    if not (e and sl and tg): continue
    if c["direction"] == "LONG" and not (sl < e < tg): continue
    if c["direction"] == "SHORT" and not (tg < e < sl): continue
    sa = (c.get("materiality") or {}).get("sl_atr")
    if sa is None or sa < 0.3: continue
    oc, mfe = resolve(c["direction"], e, sl, tg, c["bar_time"])
    ex.append({"c": c, "t": c["bar_time"], "dir": c["direction"], "rule": c["rule"], "tf": c["tf"],
               "e": e, "conf": (c.get("materiality") or {}).get("confluence"),
               "oc": oc, "mfe": mfe, "stage": stage_of(c)})

from collections import Counter
dec = [r for r in ex if r["oc"] in ("TP", "SL", "AMBIGUOUS")]
tp = [r for r in ex if r["oc"] == "TP"]
print(f"=== EXECUTAVEIS (geom ok + sl_atr>=0.3): {len(ex)} · decididos {len(dec)} · TP {len(tp)} "
      f"({100*len(tp)/max(1,len(dec)):.0f}%) · SL {sum(1 for r in dec if r['oc']=='SL')} ===")
print("\nFUNIL dos TPs executaveis (os winners REAIS que o funil tratou):")
for r in sorted(tp, key=lambda x: x["t"]):
    print(f"  {hm(r['t'])} {r['dir']} {r['rule']}@{r['tf']} e={r['e']} conf={r['conf']} mfe={r['mfe']}R -> {r['stage']}")
print("\nFUNIL dos SLs executaveis por estadio:")
print(" ", dict(Counter(r["stage"].split(":")[0] for r in dec if r["oc"] == "SL")))

print("\n=== SIMULACAO anti-spam POR ZONA nos executaveis (renova se conf sobe ou 4h) ===")
zone = {}; extra_tp = []; extra_sl = 0
for r in sorted(ex, key=lambda x: x["t"]):
    if r["stage"] == "materiality_fail": continue
    zk = (r["dir"], round(r["e"] / 5) * 5)
    zs = zone.get(zk)
    fresh = zs is None or (r["t"] - zs["t"]) >= 4 * 3600 or (r["conf"] or 0) > zs["maxconf"]
    if fresh:
        zone[zk] = {"t": r["t"], "maxconf": max((r["conf"] or 0), (zs or {}).get("maxconf", 0))}
        if r["stage"] == "antispam":
            if r["oc"] == "TP": extra_tp.append(r)
            elif r["oc"] == "SL": extra_sl += 1
    elif zs:
        zone[zk]["maxconf"] = max(zs["maxconf"], r["conf"] or 0)
print(f"  candidatos que o anti-spam VELHO suprimiu e o NOVO admitiria: TP {len(extra_tp)} · SL {extra_sl}")
for r in extra_tp:
    print(f"    +TP {hm(r['t'])} {r['dir']} {r['rule']}@{r['tf']} e={r['e']} conf={r['conf']} mfe={r['mfe']}R")
