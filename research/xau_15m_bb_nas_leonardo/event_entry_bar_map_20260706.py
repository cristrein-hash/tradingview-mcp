#!/usr/bin/env python3
"""MAPA DA CONSTRUÇÃO DO FUNDO — qual barra do evento é a de entrada? (2026-07-06, direção Cris).
A FASE B falhou por entrar no 1º candidato; o fundo REAL se constrói ao longo de barras e a entrada
certa vem APÓS a virada confirmada. Aprender CAUSALMENTE, dentro dos eventos, o que caracteriza a
entry-bar correta. Duas perguntas:
  Q1 hit3R por POSIÇÃO no evento (1º,2º,...,10º cronológico) — entrar mais tarde é melhor?
  Q2 hit3R por ESTADO DE CONSTRUÇÃO causal do candidato (não posição):
     - pos_low: é o candidato do LOW mínimo do evento-até-agora
     - post_low: vem DEPOIS do low-até-agora (o preço já não faz novo mínimo)
     - higher_low: flush deste > menor flush dos anteriores no evento
     - reclaimed: close > high da barra anterior (reversão micro)
     - rebound_atr: (close − low_min_ate_agora)/atr por faixa
     - since_low_bars: barras desde o low-até-agora
     - up_seq: closes subindo consecutivos
+ MICRO-FORMA da barra de entrada (features novas causais):
     lower_wick, close_in_range (fechou no topo), body_up, vol_vs_med
Tudo causal (só barras/candidatos <= o candidato avaliado). Mapa hit3R + recall-círculo por estado.
SANITY_PROBE: sha GT · matcher v2 · low-até-agora causal (min dos candidatos anteriores no evento) ·
micro-forma da barra do cj · recall por círculo distinto."""
import json, bisect, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S); ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]; OP = [b.get("o", b["c"]) for b in S]; VOL = [float(b.get("v") or 0) for b in S]
UNIV = sorted([u for u in U if u["cj_t"] in R3], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0
    u["_circ"] = set()
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]; d = u["_flo"] - g["flush_low"]
        if -3 * u["_a"] <= d <= 1 * u["_a"]: u["_circ"].add(gi)
        j += 1
EV = []; cur = []
for u in UNIV:
    if cur and u["cj_t"] - cur[-1]["cj_t"] <= 48 * 3600 and abs(u["_flo"] - cur[-1]["_flo"]) <= 3 * u["_a"]:
        cur.append(u)
    else:
        if cur: EV.append(cur)
        cur = [u]
if cur: EV.append(cur)

# estado de construção causal por candidato dentro do evento
for ev in EV:
    min_flo = 1e18
    up = 0; prev_close = None
    for pos, u in enumerate(ev, 1):
        ci = bisect.bisect_right(TS, u["cj_t"]) - 1
        a = u["_a"]
        u["_pos"] = pos
        u["_higher_low"] = int(u["_flo"] > min_flo + 0.05 * a) if pos > 1 else 0
        u["_pos_low"] = int(u["_flo"] <= min_flo + 1e-9)
        prevmin = min_flo
        min_flo = min(min_flo, u["_flo"])
        u["_post_low"] = int(pos > 1 and u["_flo"] > prevmin + 0.05 * a)
        u["_rebound"] = (CL[ci] - min_flo) / a
        u["_since_low"] = 0  # aprox: barras desde a barra do min flo — usar índice
        u["_reclaimed"] = int(ci >= 1 and CL[ci] > HI[ci - 1])
        if prev_close is not None:
            up = up + 1 if CL[ci] > prev_close else 0
        prev_close = CL[ci]
        u["_up_seq"] = up
        # micro-forma da barra
        rng = max(1e-9, HI[ci] - LO[ci])
        u["_low_wick"] = (min(OP[ci], CL[ci]) - LO[ci]) / a
        u["_close_in_range"] = (CL[ci] - LO[ci]) / rng
        u["_body_up"] = int(CL[ci] > OP[ci])
        v20 = VOL[max(0, ci - 20):ci]
        u["_vol_vs"] = VOL[ci] / (sum(v20) / len(v20)) if v20 and VOL[ci] else 1.0

ALL = [u for ev in EV for u in ev]
def rate(rows):
    if not rows: return (0, 0.0, 0.0, 0)
    h = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3)
    net = sum(R3[u["cj_t"]]["net3"] for u in rows)
    circ = len(set().union(*(u["_circ"] for u in rows)) if rows else set())
    return (len(rows), 100 * h / len(rows), net, circ)

print(f"eventos {len(EV)} · candidatos {len(ALL)} · base hit3R {rate(ALL)[1]:.1f}%")
print("\nQ1 — hit3R por POSIÇÃO cronológica no evento:")
for p in range(1, 11):
    r = rate([u for u in ALL if u["_pos"] == p])
    if r[0] >= 10: print(f"  pos {p:>2}: N{r[0]:>4} hit3R {r[1]:>5.1f}% NET {r[2]:>+7.1f} círc {r[3]}")
r = rate([u for u in ALL if u["_pos"] >= 11])
if r[0]: print(f"  pos11+: N{r[0]:>4} hit3R {r[1]:>5.1f}% NET {r[2]:>+7.1f} círc {r[3]}")

print("\nQ2 — hit3R por ESTADO DE CONSTRUÇÃO causal:")
STATES = {
    "pos_low (é o low)": lambda u: u["_pos_low"] == 1,
    "post_low (após low)": lambda u: u["_post_low"] == 1,
    "higher_low": lambda u: u["_higher_low"] == 1,
    "reclaimed(>H-1)": lambda u: u["_reclaimed"] == 1,
    "post_low & reclaimed": lambda u: u["_post_low"] == 1 and u["_reclaimed"] == 1,
    "higher_low & reclaimed": lambda u: u["_higher_low"] == 1 and u["_reclaimed"] == 1,
    "rebound 0.5-2ATR": lambda u: 0.5 <= u["_rebound"] <= 2.0,
    "up_seq>=2": lambda u: u["_up_seq"] >= 2,
}
for nm, fn in STATES.items():
    r = rate([u for u in ALL if fn(u)])
    print(f"  {nm:<24} N{r[0]:>4} hit3R {r[1]:>5.1f}% NET {r[2]:>+7.1f} círc {r[3]}")

print("\nMICRO-FORMA da barra (quartis, hit3R):")
for f in ("_low_wick", "_close_in_range", "_vol_vs"):
    vals = sorted(u[f] for u in ALL)
    q1, q3 = vals[len(vals)//4], vals[3*len(vals)//4]
    lo = rate([u for u in ALL if u[f] <= q1]); hi = rate([u for u in ALL if u[f] >= q3])
    print(f"  {f:<16} baixo(<= {q1:.2f}) hit {lo[1]:.1f}% · alto(>= {q3:.2f}) hit {hi[1]:.1f}%")
r = rate([u for u in ALL if u["_body_up"] == 1])
print(f"  _body_up==1            N{r[0]} hit {r[1]:.1f}%")

# combinação candidata pós-low: entrar no 1º candidato pós-low com reclaim + micro-forma
print("\nCANDIDATA (mapa): post_low & reclaimed & close_in_range>=0.5 & body_up:")
cand = [u for u in ALL if u["_post_low"] == 1 and u["_reclaimed"] == 1 and u["_close_in_range"] >= 0.5 and u["_body_up"] == 1]
r = rate(cand); print(f"  N{r[0]} hit3R {r[1]:.1f}% NET {r[2]:+.1f} círc {r[3]}/60")
json.dump({"by_pos": {p: rate([u for u in ALL if u['_pos']==p])[:3] for p in range(1,11)}},
          open(HERE / "results" / "event_entry_bar_map_20260706.json", "w"), indent=1, default=float)
print("OK → results/event_entry_bar_map_20260706.json")
