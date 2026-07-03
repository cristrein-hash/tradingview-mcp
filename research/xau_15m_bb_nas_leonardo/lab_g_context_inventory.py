#!/usr/bin/env python3
"""LAB G · G1 — Inventário total de lentes contextuais (2026-07-03).
Para cada um dos 4502 candidatos (flush-lows do universo pré-gate): TODAS as features do builder
(ROWS) + INDICADORES NOVOS derivados causalmente das séries RAW (<= cj) + regime v5h como MAPA
+ outcome let-run (entry@cj, sl=flush-0,1ATR) para AVALIAÇÃO posterior (nunca para construir feature).
Saída: results/lab_g_candidates.jsonl (tabela integral, regenerável) + results/lab_g_inventory.json (sumário)."""
import json, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "engine", "exec"), ns)
ROWS, PRIMK = ns["ROWS"], ns["PRIMK"]
letrun, f, regime_h, ema_at = ns["letrun"], ns["f"], ns["f"], ns["ema_at"]
letrun = ns["letrun"]; regime_h = ns["regime_hourcausal"]
knife_v2 = ns["knife_v2"]

OUT = []
base_ts = set()
cand = sorted([c for c in ns["cand"] if c["v5h"] != "BEAR"], key=lambda z: z["cj_t"])
base_ts = {c["cj_t"] for c in cand}

def local_lows(L, upto):
    """índices de fractal-lows k2 (L[q]==min(L[q-2..q+3])) até 'upto' exclusivo."""
    out = []
    for q in range(2, upto - 2):
        if L[q] == min(L[q - 2:q + 3]): out.append(q)
    return out

for r in ROWS:
    pr = PRIMK.get(r["block"])
    if not pr: continue
    s = pr["series"]; tmap = {b["t"]: i for i, b in enumerate(s)}
    p, cj = tmap.get(r["t"]), tmap.get(r["cj_t"])
    if p is None or cj is None or cj + 2 >= len(s): continue
    atr = s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    L = [b["l"] for b in s]; H = [b["h"] for b in s]; C = [b["c"] for b in s]
    entry = s[cj]["c"]; sl = min(L[p:cj + 1]) - 0.1 * atr
    R = letrun(s, cj, entry, sl, atr)
    if R is None: continue
    o = dict(r)  # todas as ~60 features do builder
    o.pop("label", None)
    # ---- indicadores NOVOS (todos <= cj, causais) ----
    # divergência RSI bullish no flush: low[p] < low do fractal anterior, rsi[p] > rsi de lá
    lows_prev = [q for q in local_lows(L, p) if p - 96 <= q <= p - 3]
    rsi_p = s[p].get("rsi") or 50
    o["g_rsi_div"] = 0
    if lows_prev:
        q = max(lows_prev, key=lambda q: -q)  # mais recente
        q = lows_prev[-1]
        rq = s[q].get("rsi") or 50
        if L[p] < L[q] and rsi_p > rq + 2: o["g_rsi_div"] = 1
    # spike de ATR (capitulação = expansão violenta)
    win = [x["atr"] for x in s[max(0, p - 96):p] if x.get("atr")]
    med = sorted(win)[len(win) // 2] if win else atr
    o["g_atr_spike"] = round(atr / med, 2) if med else 1.0
    # profundidade do sweep em ATR (abaixo do fractal-low anterior)
    o["g_sweep_depth"] = round((L[lows_prev[-1]] - L[p]) / atr, 2) if lows_prev else 0.0
    # box-position multi-janela no close de cj
    for W in (96, 480):
        lo = min(L[max(0, cj - W):cj + 1]); hi = max(H[max(0, cj - W):cj + 1])
        o[f"g_box{W}"] = round((entry - lo) / ((hi - lo) or atr), 3)
    # velocidade de recuperação (bounce por barra, em ATR)
    o["g_rec_speed"] = round((entry - L[p]) / atr / max(1, cj - p), 2)
    # run de closes vermelhos entrando em p
    run = 0
    for k in range(p, max(0, p - 20), -1):
        if C[k] < C[k - 1]: run += 1
        else: break
    o["g_downrun"] = run
    # distância da EMA21/EMA50 em ATR (esticamento)
    e21 = ema_at(C, cj, 21); e50 = ema_at(C, cj, 50)
    o["g_ema21_dist"] = round((entry - e21) / atr, 2)
    o["g_ema50_dist"] = round((entry - e50) / atr, 2)
    # wick inferior da barra de flush relativo ao range dela
    rng = H[p] - L[p]
    o["g_flush_wick"] = round((min(s[p]["o"], C[p]) - L[p]) / rng, 2) if rng > 0 else 0
    # corpo da barra de confirmação em ATR
    o["g_cj_body"] = round((C[cj] - s[cj]["o"]) / atr, 2)
    # regime como MAPA (não gate)
    o["g_v5h"] = regime_h(r["cj_t"])
    o["g_v5h_5dago"] = regime_h(r["cj_t"] - 5 * 86400)
    o["g_regime_flip5d"] = int(o["g_v5h"] != o["g_v5h_5dago"])
    # pullback-bull-em-BEAR (mandato Cris): CHoCH 1H recente + 1H trend up + reclaim
    o["g_bear_pullback_ok"] = int(o["g_v5h"] == "BEAR" and f(r, "h1n_choch_up_rec", 0) == 1
                                  and f(r, "h1n_trend", 0) == 1 and f(r, "reclaim_atr", 0) >= 0.5)
    # knife + base membership (referência, não gate)
    o["g_knife"] = int(knife_v2(r))
    o["g_in_base435"] = int(r["cj_t"] in base_ts)
    # calendário
    d = dt.datetime.utcfromtimestamp(r["cj_t"])
    o["g_week"] = d.strftime("%G-%V"); o["g_dow"] = d.weekday(); o["g_hour"] = d.hour
    # avaliação (NUNCA feature): outcome let-run + geometria
    o["g_R"] = round(R, 3); o["g_risk"] = round(entry - sl, 2); o["g_atr"] = round(atr, 2)
    o["g_entry"] = entry; o["g_sl"] = sl
    OUT.append(o)

(HERE / "results").mkdir(exist_ok=True)
with open(HERE / "results" / "lab_g_candidates.jsonl", "w") as fh:
    for o in OUT: fh.write(json.dumps(o) + "\n")

# sumário
import collections
weeks = collections.Counter(o["g_week"] for o in OUT)
reg = collections.Counter(o["g_v5h"] for o in OUT)
newf = ["g_rsi_div", "g_atr_spike", "g_sweep_depth", "g_box96", "g_box480", "g_rec_speed",
        "g_downrun", "g_ema21_dist", "g_ema50_dist", "g_flush_wick", "g_cj_body",
        "g_regime_flip5d", "g_bear_pullback_ok"]
summ = {"n_candidates": len(OUT), "weeks": len(weeks), "per_week_avg": round(len(OUT) / len(weeks), 1),
        "regime_dist": dict(reg), "bear_pullback_candidates": sum(o["g_bear_pullback_ok"] for o in OUT),
        "rsi_div_rate": round(sum(o["g_rsi_div"] for o in OUT) / len(OUT), 3),
        "builder_fields": sorted(k for k in OUT[0] if not k.startswith("g_")),
        "new_fields": newf,
        "R_pos_rate_all": round(sum(1 for o in OUT if o["g_R"] > 0) / len(OUT), 3)}
json.dump(summ, open(HERE / "results" / "lab_g_inventory.json", "w"), indent=1)
print(f"OK: {len(OUT)} candidatos · {len(weeks)} semanas ({summ['per_week_avg']}/sem) · regimes {dict(reg)}")
print(f"bear-pullback OK: {summ['bear_pullback_candidates']} · rsi_div {summ['rsi_div_rate']} · winrate bruto geral {summ['R_pos_rate_all']}")
print("campos:", len(summ["builder_fields"]), "builder +", len(newf), "novos")