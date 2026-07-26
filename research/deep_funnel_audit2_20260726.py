#!/usr/bin/env python3
"""AUDITORIA PROFUNDA v2 — refinamento: (1) separa GEOMETRIA INVALIDA (SL do lado errado / risk<1pt =
bug de levels do E1, fator oculto que inflava MFE); (2) refaz paineis so com validos; (3) DECOMPOE o
materiality_fail nos TPs (qual regua mata: rr? sl_atr? confluencia? act?); (4) escondidos validos.
Multi-fatorial/trajetoria; diagnostico in-sample p/ desenho, arbitro=forward. Read-only."""
import json, bisect, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
R = "/Users/cristrein/tradingview-mcp/"
HORIZON = 96

def hm(ts): return dt.datetime.fromtimestamp(int(ts), LX).strftime("%d/%m %H:%M")

bars = sorted([json.loads(l) for l in open(R + "my-strategy/core/bar_store/store/bars_15m.jsonl") if l.strip()], key=lambda b: b["t"])
T = [b["t"] for b in bars]; H = [b["h"] for b in bars]; L = [b["l"] for b in bars]

def resolve(d, e, sl, tg, bt):
    i0 = bisect.bisect_right(T, bt)
    risk = abs(e - sl)
    mfe = mae = 0.0; oc = None; nb = None
    for n, i in enumerate(range(i0, min(i0 + HORIZON, len(T)))):
        hi, lo = H[i], L[i]
        if d == "LONG":
            mfe = max(mfe, (hi - e) / risk); mae = max(mae, (e - lo) / risk)
            hit_sl = lo <= sl; hit_tp = hi >= tg
        else:
            mfe = max(mfe, (e - lo) / risk); mae = max(mae, (hi - e) / risk)
            hit_sl = hi >= sl; hit_tp = lo <= tg
        if oc is None:
            if hit_sl and hit_tp: oc, nb = "AMBIGUOUS", n
            elif hit_sl: oc, nb = "SL", n
            elif hit_tp: oc, nb = "TP", n
    if oc is None: oc = "EXPIRED" if len(T) - i0 >= HORIZON else "OPEN"
    return oc, nb, round(mfe, 2), round(mae, 2)

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
    m = c.get("materiality") or {}
    v = verd.get(c.get("id")) or verd_bk.get(k)
    if v:
        if v.get("veto"): return "gate"
        rd = v.get("read") or {}
        if rd.get("error"): return "read-falhou"
        return "SURFACED" if v.get("surfaced") else "read-recusou"
    if not m.get("pass"): return "materiality_fail"
    if sup_seen.get(k) or c.get("suppressed"): return "antispam"
    return "sem_verdict"

def geom_ok(c):
    e, sl, tg = c.get("entry"), c.get("sl"), c.get("target")
    if not (e and sl and tg): return False
    if abs(e - sl) < 1.0: return False                      # risk sub-ponto = degenerado
    if c["direction"] == "LONG": return sl < e < tg
    return tg < e < sl

rows = []
for c in cands:
    if not (c.get("entry") and c.get("sl") and c.get("target")): continue
    oc, nb, mfe, mae = resolve(c["direction"], c["entry"], c["sl"], c["target"], c["bar_time"])
    tr = ((c.get("dossier") or {}).get("mtf") or {}).get("60", {}).get("trend")
    leg = "?" if tr not in ("UP", "DOWN") else ("com" if (tr == "UP") == (c["direction"] == "LONG") else "contra")
    rows.append({"c": c, "t": c["bar_time"], "dir": c["direction"], "rule": c["rule"], "tf": c["tf"],
                 "e": c["entry"], "sl": c["sl"], "tg": c["target"], "rr": c.get("rr"),
                 "m": c.get("materiality") or {}, "ok": geom_ok(c),
                 "oc": oc, "mfe": mfe, "mae": mae, "stage": stage_of(c), "leg": leg})

bad = [r for r in rows if not r["ok"]]
good = [r for r in rows if r["ok"]]
print(f"=== GEOMETRIA: {len(good)} validos · {len(bad)} INVALIDOS (SL lado errado ou risk<1pt) de {len(rows)} ===")
from collections import Counter
print("  invalidos por estadio:", dict(Counter(r['stage'] for r in bad)))
sl_wrong = sum(1 for r in bad if (r['dir']=='LONG' and r['sl']>=r['e']) or (r['dir']=='SHORT' and r['sl']<=r['e']))
print(f"  dos invalidos, SL do LADO ERRADO da entry: {sl_wrong} (bug levels E1 a investigar)")

dec = [r for r in good if r["oc"] in ("TP", "SL", "AMBIGUOUS")]
tp = [r for r in good if r["oc"] == "TP"]
hidden = [r for r in good if r["oc"] in ("SL", "AMBIGUOUS") and (r["mfe"] or 0) >= 2.0]
print(f"\n=== VALIDOS: decididos {len(dec)} · TP {len(tp)} ({100*len(tp)/max(1,len(dec)):.0f}%) · "
      f"SL {sum(1 for r in dec if r['oc']=='SL')} · AMBIG {sum(1 for r in dec if r['oc']=='AMBIGUOUS')} · escondidos {len(hidden)} ===")

print("\n=== FUNIL dos TPs validos vs SLs validos ===")
for label, grp in (("TP", tp), ("SL", [r for r in dec if r["oc"] == "SL"])):
    print(f"  {label} (n={len(grp)}): " + " · ".join(f"{k} {v}" for k, v in Counter(r["stage"] for r in grp).most_common()))

print("\n=== PERNA (proxy trend-60 dossie) × outcome (validos) ===")
for lg in ("com", "contra", "?"):
    g = [r for r in dec if r["leg"] == lg]
    ntp = sum(1 for r in g if r["oc"] == "TP")
    print(f"  {lg:6s}: {ntp}/{len(g)} TP ({100*ntp/max(1,len(g)):.0f}%)")

print("\n=== PORQUE a materialidade mata TPs (decomposicao das reguas nos TPs materiality_fail) ===")
mtp = [r for r in tp if r["stage"] == "materiality_fail"]
reasons = Counter()
for r in mtp:
    m = r["m"]
    if not m.get("min_rr_ok", True): reasons["rr<1.5"] += 1
    sa = m.get("sl_atr")
    if sa is not None and not (0.3 <= sa <= 3.0): reasons[f"sl_atr fora 0.3-3"] += 1
    if (m.get("confluence") or 0) < 2: reasons["confluencia<2"] += 1
    if m.get("act_ok") is False: reasons["act_dens (atividade)"] += 1
print(f"  TPs mortos pela materialidade: {len(mtp)}; motivos (nao-exclusivos): {dict(reasons)}")
# comparacao: os mesmos motivos nos SLs materiality_fail
msl = [r for r in dec if r["oc"] == "SL" and r["stage"] == "materiality_fail"]
rsl = Counter()
for r in msl:
    m = r["m"]
    if not m.get("min_rr_ok", True): rsl["rr<1.5"] += 1
    sa = m.get("sl_atr")
    if sa is not None and not (0.3 <= sa <= 3.0): rsl["sl_atr fora 0.3-3"] += 1
    if (m.get("confluence") or 0) < 2: rsl["confluencia<2"] += 1
    if m.get("act_ok") is False: rsl["act_dens (atividade)"] += 1
print(f"  SLs mortos pela materialidade: {len(msl)}; motivos: {dict(rsl)}")

print("\n=== act_dens: TP-rate com vs sem act_ok (a regua paga-se?) ===")
for flag in (True, False):
    g = [r for r in dec if r["m"].get("act_ok") is flag]
    ntp = sum(1 for r in g if r["oc"] == "TP")
    print(f"  act_ok={flag}: {ntp}/{len(g)} TP ({100*ntp/max(1,len(g)):.0f}%)")

print("\n=== REGIOES IDEAIS (validos) ===")
regs = [
    ("A LONG fundo 16-17/07 3965-3990", "LONG", 3965, 3990, "2026-07-16", "2026-07-17"),
    ("B LONG demanda 20-21/07 4000-4022", "LONG", 4000, 4022, "2026-07-20", "2026-07-21"),
    ("C SHORT topo 22-23/07 >=4090", "SHORT", 4090, 4200, "2026-07-22", "2026-07-23"),
    ("D LONG pullback 24/07 4028-4056", "LONG", 4028, 4056, "2026-07-24", "2026-07-24"),
    ("E SHORT rejeicao 21/07 4055-4080", "SHORT", 4055, 4080, "2026-07-21", "2026-07-21"),
]
for name, d, plo, phi, d0, d1 in regs:
    tt0 = dt.datetime.strptime(d0, "%Y-%m-%d").replace(tzinfo=LX).timestamp()
    tt1 = dt.datetime.strptime(d1, "%Y-%m-%d").replace(tzinfo=LX).timestamp() + 86400
    g = [r for r in good if r["dir"] == d and tt0 <= r["t"] < tt1 and plo <= r["e"] <= phi]
    ntp = sum(1 for r in g if r["oc"] == "TP")
    stg = Counter(r["stage"] for r in g)
    print(f"  {name}: {len(g)} validos · TP {ntp} · {dict(stg)}")
    for r in sorted(g, key=lambda x: (x["oc"] != "TP", -(x["mfe"] or 0)))[:2]:
        print(f"     {hm(r['t'])} {r['rule']}@{r['tf']} e={r['e']} oc={r['oc']} mfe={r['mfe']}R conf={r['m'].get('confluence')} sl_atr={r['m'].get('sl_atr')} stage={r['stage']}")

print("\n=== ESCONDIDOS validos (top 8 MFE) — SL do E1 curto, trade certo ===")
for r in sorted(hidden, key=lambda x: -(x["mfe"] or 0))[:8]:
    print(f"  {hm(r['t'])} {r['dir']} {r['rule']}@{r['tf']} e={r['e']} sl={r['sl']} mfe={r['mfe']}R mae={r['mae']}R leg={r['leg']} stage={r['stage']}")
