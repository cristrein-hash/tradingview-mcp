#!/usr/bin/env python3
"""DENSIDADE POR GRANULARIDADE — a unidade 'candidato' infla? (2026-07-06).
Cris: 37:1 indistinguível é impossível no gráfico. Hipótese: o gerador emite vários fractais k=3
no MESMO movimento de reversão que o olho vê como 1 ponto. Medir densidade sósia:fundo colapsando
o pool em unidades cada vez mais grossas (o que o olho realmente conta):
  L0 candidato cru · L1 episódio (±8h & ±1ATR) · L2 evento visual (±24h & ±2ATR) ·
  L3 evento largo (±48h & ±3ATR) · L4 dia-calendário
Um evento CONTA como fundo se contém >=1 candidato-círculo. Densidade = (eventos-sem-fundo)/
(eventos-com-fundo). Se cai de 37:1 p/ ~single-digit, a parede era de contagem, não de gráfico.
SANITY_PROBE: sha GT · matcher v2 · colapso guloso cronológico · círculos por evento distinto."""
import json, bisect, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
UNIV = sorted([u for u in U if u["cj_t"] in R3], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]
for u in UNIV:
    u["_circ"] = set()
    u["_flo"] = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0)
    u["_a"] = u.get("g_atr") or 5.0
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]
        d = u["_flo"] - g["flush_low"]
        if -3 * u["_a"] <= d <= 1 * u["_a"]: u["_circ"].add(gi)
        j += 1

def collapse(dt_h, atr_mult):
    """agrupa candidatos consecutivos dentro de dt_h horas E atr_mult·ATR de preço."""
    events = []; cur = []
    for u in UNIV:
        if cur and (u["cj_t"] - cur[-1]["cj_t"] <= dt_h * 3600
                    and abs(u["_flo"] - cur[-1]["_flo"]) <= atr_mult * u["_a"]):
            cur.append(u)
        else:
            if cur: events.append(cur)
            cur = [u]
    if cur: events.append(cur)
    return events

def day_collapse():
    ev = {}
    for u in UNIV:
        ev.setdefault(u["cj_t"] // 86400, []).append(u)
    return list(ev.values())

def report(events, tag):
    circ_events = [e for e in events if any(u["_circ"] for u in e)]
    circ_covered = len(set().union(*[set().union(*(u["_circ"] for u in e)) for e in circ_events]) if circ_events else set())
    ne = len(events); nf = len(circ_events)
    dens = (ne - nf) / max(1, nf)
    avg_sz = sum(len(e) for e in events) / ne
    print(f"  {tag:<28} eventos {ne:>4} · com-fundo {nf:>3} · densidade {dens:>5.1f}:1 "
          f"· círc {circ_covered}/60 · tam.médio {avg_sz:.1f}")
    return {"events": ne, "with_bottom": nf, "density": round(dens, 1), "circ": circ_covered}

print(f"POOL: N{len(UNIV)} · candidatos-círculo {sum(1 for u in UNIV if u['_circ'])}")
out = {}
out["L0"] = report([[u] for u in UNIV], "L0 candidato cru")
out["L1"] = report(collapse(8, 1), "L1 episódio ±8h ±1ATR")
out["L2"] = report(collapse(24, 2), "L2 evento visual ±24h ±2ATR")
out["L3"] = report(collapse(48, 3), "L3 evento largo ±48h ±3ATR")
out["L4"] = report(day_collapse(), "L4 dia-calendário")
json.dump(out, open(HERE / "results" / "density_granularity_20260706.json", "w"), indent=1)
print("OK → results/density_granularity_20260706.json")
