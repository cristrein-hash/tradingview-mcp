#!/usr/bin/env python3
"""AUDITORIA PROFUNDA DO FUNIL (pre-implementacao pontos 4+5, ordem Cris 2026-07-26).
Leitura DINAMICA MULTI-FATORIAL (checklist anti-miopia cumprido): trajetoria (MFE/MAE por barra, nao
snapshot), multi-camada (materiality/anti-spam/gate/read × perna × zona × RR), dois objetivos (capturar
winners E nao abrir flood de losers), feature-set = funil inteiro + outcome contrafactual. DIAGNOSTICO
in-sample de 1 semana — informa DESENHO, nao valida edge (arbitro = forward).
Resolve TODOS os candidatos unicos E1 da semana contra bars_15m (SL-first, horizonte 96 barras),
simula o anti-spam novo (renova por zona se confluencia sobe) e o gate novo (so bad_rr), e mapeia
as 5 regioes ideais do Cris. Read-only."""
import json, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
R = "/Users/cristrein/tradingview-mcp/"
HORIZON = 96

def hm(ts): return dt.datetime.fromtimestamp(int(ts), LX).strftime("%d/%m %H:%M")

bars = [json.loads(l) for l in open(R + "my-strategy/core/bar_store/store/bars_15m.jsonl") if l.strip()]
bars.sort(key=lambda b: b["t"])
T = [b["t"] for b in bars]; H = [b["h"] for b in bars]; L = [b["l"] for b in bars]

import bisect
def resolve(d, e, sl, tg, bt):
    """First-touch SL-vs-TP (SL-first na barra ambigua, igual ao backfill) + MFE/MAE em R."""
    i0 = bisect.bisect_right(T, bt)
    risk = abs(e - sl)
    if risk <= 0: return "BAD", None, None, None
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
    if oc is None:
        oc = "EXPIRED" if len(T) - i0 >= HORIZON else "OPEN"
    return oc, nb, round(mfe, 2), round(mae, 2)

# candidatos unicos (ultima gravacao por chave; suppressed = uniao das gravacoes)
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
# verdicts indexados tambem por (bar_time, rule, dir, tf) — id inclui cycle_ts que muda entre gravacoes
verd_bk = {}
for r in verd.values():
    verd_bk[(r.get("bar_time"), r.get("rule"), r.get("direction"), r.get("tf"))] = r

def stage_of(c):
    k = (c.get("bar_time"), c.get("rule"), c.get("direction"), c.get("tf"))
    m = c.get("materiality") or {}
    v = verd.get(c.get("id")) or verd_bk.get(k)
    if v:  # chegou ao E2
        if v.get("veto"): return "gate:" + v["veto"], v
        rd = v.get("read") or {}
        if rd.get("error"): return "read-falhou", v
        if v.get("surfaced"): return "SURFACED", v
        return "read-recusou", v
    if not m.get("pass"): return "materiality_fail", None
    if sup_seen.get(k) or c.get("suppressed"):
        s = sup_seen.get(k) or {c.get("suppressed")}
        return "antispam:" + "/".join(sorted(x for x in s if x)), None
    return "sem_verdict", None

def leg_proxy(c):
    tr = ((c.get("dossier") or {}).get("mtf") or {}).get("60", {}).get("trend")
    if tr not in ("UP", "DOWN"): return "?"
    return "com" if ((tr == "UP") == (c["direction"] == "LONG")) else "contra"

# resolver todos
rows = []
for c in cands:
    e, sl, tg = c.get("entry"), c.get("sl"), c.get("target")
    if not (e and sl and tg): continue
    oc, nb, mfe, mae = resolve(c["direction"], e, sl, tg, c["bar_time"])
    st, v = stage_of(c)
    m = c.get("materiality") or {}
    rows.append({"t": c["bar_time"], "dir": c["direction"], "rule": c["rule"], "tf": c["tf"],
                 "e": e, "sl": sl, "tg": tg, "rr": c.get("rr"), "conf": m.get("confluence"),
                 "oc": oc, "nb": nb, "mfe": mfe, "mae": mae, "stage": st, "leg": leg_proxy(c)})

dec = [r for r in rows if r["oc"] in ("TP", "SL", "AMBIGUOUS")]
tp = [r for r in rows if r["oc"] == "TP"]
hidden = [r for r in rows if r["oc"] in ("SL", "AMBIGUOUS") and (r["mfe"] or 0) >= 2.0]
print(f"=== BASE: {len(rows)} candidatos unicos resolvidos | decididos {len(dec)} · TP {len(tp)} · "
      f"SL {sum(1 for r in dec if r['oc']=='SL')} · AMBIG {sum(1 for r in dec if r['oc']=='AMBIGUOUS')} ===")
print(f"WINNERS ESCONDIDOS (outcome SL/AMBIG mas MFE>=2R — trade certo, SL do E1 curto): {len(hidden)}")

print("\n=== FUNIL: onde morreram os TPs (e onde morrem os SLs, p/ comparar) ===")
from collections import Counter, defaultdict
for label, grp in (("TP", tp), ("SL", [r for r in dec if r["oc"] == "SL"])):
    cnt = Counter(r["stage"].split(":")[0] for r in grp)
    print(f"  {label} (n={len(grp)}): " + " · ".join(f"{k} {v}" for k, v in cnt.most_common()))

print("\n=== PERNA (proxy trend-1H do dossie no momento) × outcome ===")
for lg in ("com", "contra", "?"):
    g = [r for r in dec if r["leg"] == lg]
    ntp = sum(1 for r in g if r["oc"] == "TP")
    print(f"  {lg:6s}: {ntp}/{len(g)} TP ({100*ntp/max(1,len(g)):.0f}%)")

print("\n=== RR do E1 × TP-rate (fator oculto: alvo cap 5R = quase-improvavel) ===")
for lo, hi in ((0, 2.5), (2.5, 4.0), (4.0, 5.1)):
    g = [r for r in dec if lo <= (r["rr"] or 0) < hi]
    ntp = sum(1 for r in g if r["oc"] == "TP")
    print(f"  rr {lo}-{hi}: {ntp}/{len(g)} TP ({100*ntp/max(1,len(g)):.0f}%)")

# SIMULACAO ANTI-SPAM NOVO (ponto 5): por zona (5 pts) × dir; renova se conf > max anterior OU passou 4h
print("\n=== SIMULACAO anti-spam POR ZONA (renova se confluencia sobe ou 4h) ===")
zone_state = {}
adm_old = adm_new = 0; new_tp = []; new_sl = 0
for r in sorted(rows, key=lambda x: x["t"]):
    st = r["stage"]
    admitted_old = not (st.startswith("antispam") or st == "materiality_fail")
    if admitted_old: adm_old += 1
    if st == "materiality_fail":
        continue
    zk = (r["dir"], round(r["e"] / 5) * 5)
    zs = zone_state.get(zk)
    fresh = zs is None or (r["t"] - zs["t"]) >= 4 * 3600 or (r["conf"] or 0) > zs["maxconf"]
    if fresh:
        adm_new += 1
        zone_state[zk] = {"t": r["t"], "maxconf": max((r["conf"] or 0), (zs or {}).get("maxconf", 0))}
        if not admitted_old:                     # candidato que SO o sistema novo admite
            if r["oc"] == "TP": new_tp.append(r)
            elif r["oc"] == "SL": new_sl += 1
    else:
        if zs: zone_state[zk]["maxconf"] = max(zs["maxconf"], r["conf"] or 0)
print(f"  admitidos antes {adm_old} -> novo {adm_new} | ADICIONAIS que o novo admite: TP {len(new_tp)} · SL {new_sl}")
for r in new_tp[:12]:
    print(f"    +TP {hm(r['t'])} {r['dir']} {r['rule']}@{r['tf']} e={r['e']} conf={r['conf']} mfe={r['mfe']}R (era {r['stage']})")

# REGIOES IDEAIS DO CRIS
print("\n=== REGIOES IDEAIS (prints) × cobertura do funil ===")
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
    g = [r for r in rows if r["dir"] == d and tt0 <= r["t"] < tt1 and plo <= r["e"] <= phi]
    ntp = sum(1 for r in g if r["oc"] == "TP"); nh = sum(1 for r in g if r in hidden)
    best = max(g, key=lambda r: (r["oc"] == "TP", r["mfe"] or 0), default=None)
    stg = Counter(r["stage"].split(":")[0] for r in g)
    print(f"  {name}: {len(g)} cand · TP {ntp} · escondidos {nh} · estadios {dict(stg)}")
    if best:
        print(f"     melhor: {hm(best['t'])} {best['rule']}@{best['tf']} e={best['e']} oc={best['oc']} mfe={best['mfe']}R stage={best['stage']}")
    else:
        print(f"     SEM CANDIDATO — gap de gatilho (ponto 4)")

# READ sobre winners que chegaram: como o E2 os julgou
print("\n=== TPs que CHEGARAM ao read — julgamento do E2 (p/ calibrar o frame) ===")
for r in tp:
    if r["stage"] in ("SURFACED", "read-recusou", "read-falhou"):
        k = (r["t"], r["rule"], r["dir"], r["tf"])
        v = verd_bk.get(k) or {}
        rd = v.get("read") or {}
        print(f"  {hm(r['t'])} {r['dir']} {r['rule']}@{r['tf']} e={r['e']} leg={r['leg']} -> {r['stage']} "
          f"(ctx={rd.get('context_direction')} conv={rd.get('convergence')} fit={rd.get('candidate_fit')})")

print("\n=== WINNERS ESCONDIDOS (top 10 por MFE) — o preco deu, o SL do E1 nao ===")
for r in sorted(hidden, key=lambda x: -(x["mfe"] or 0))[:10]:
    print(f"  {hm(r['t'])} {r['dir']} {r['rule']}@{r['tf']} e={r['e']} sl={r['sl']} mfe={r['mfe']}R mae={r['mae']}R "
          f"leg={r['leg']} stage={r['stage']}")
