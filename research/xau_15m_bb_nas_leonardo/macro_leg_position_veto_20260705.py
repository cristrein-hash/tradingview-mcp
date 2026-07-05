#!/usr/bin/env python3
"""VETO POSIÇÃO-NA-PERNADA-MACRO — mecanismo nomeado pelo Cris (2026-07-05).
"O que distingue os losers é entrarem no INÍCIO ou no MEIO de uma pernada macro FORTÍSSIMA."
Família NOVA (nunca testada): não é profundidade nem verticalidade local — é ONDE na pernada macro
a entrada cai e quão forte a pernada é.

DEFINIÇÃO DA PERNADA MACRO (congelada, causal, só barras <= cj):
  origem = barra do HIGH máximo das últimas 1920 barras (20 dias) antes de cj
  low_run = low mínimo desde a origem até cj
  age_h        = horas desde a origem (jovem = início)
  travel_atr   = (high_origem − low_run)/ATR@cj (tamanho da pernada)
  vel          = travel_atr / barras desde a origem (fortíssima = veloz)
  recent_frac  = queda das últimas 96 barras / travel total (≈1 = a pernada é toda recente = início)
  n_retraces   = nº de bounces >= 1,5 ATR a partir do low corrente dentro da pernada (fim = vários)

LEDGER DE VETOS (thresholds PRÉ-FIXADOS antes de rodar, 7):
  M1 age_h <= 24        (pernada nasceu ontem)
  M2 age_h <= 48
  M3 recent_frac >= 0.5 (metade+ da pernada nas últimas 24h)
  M4 recent_frac >= 0.7
  M5 n_retraces == 0    (pernada nunca respirou)
  M6 vel >= 0.10 ATR/barra (fortíssima)
  M7 M2 OU M4           (início OU aceleração — a frase do Cris literal)
PROTOCOLO (o mesmo): pocket N56 + réplica ctx N228; kept-panel, ΔNET ambos, razão L:W >= 2:1,
null remoção aleatória 2000×. Tabela dos 20 plotados com os valores (reconciliação visual)."""
import json, glob, bisect, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
series = {}; EV = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]:
        series.setdefault(b["t"], b)
    EV += d["smc_events"]
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]

def close_at(t):
    i = bisect.bisect_right(TS, t) - 1
    return S[i]["c"] if i >= 0 else None

seen = set(); events = []
for e in sorted(EV, key=lambda x: x["t"]):
    key = (e["t"], e["text"], round(e["price"], 2))
    if key in seen or e["text"] not in ("BOS", "CHoCH"):
        continue
    seen.add(key)
    c = close_at(e["t"])
    if c is None:
        continue
    events.append({"t": e["t"], "tok": e["text"] + ("+" if c > e["price"] else "-")})
ET = [e["t"] for e in events]

def cascade(cj):
    hi = bisect.bisect_right(ET, cj)
    dirs = [events[i]["tok"] for i in range(hi) if events[i]["t"] >= cj - 192 * 900]
    n = 0
    for tok in reversed(dirs):
        if tok in ("BOS-", "CHoCH-"):
            n += 1
        else:
            break
    return n

def fv(u, k, d=None):
    v = u.get(k)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d

def macro_leg(cj):
    i = bisect.bisect_right(TS, cj) - 1
    j0 = max(0, i - 1920)
    hi_k = max(range(j0, i + 1), key=lambda k: S[k]["h"])
    H = S[hi_k]["h"]; atr = S[i].get("atr") or 5.0
    lows = [S[k]["l"] for k in range(hi_k, i + 1)]
    low_run = min(lows)
    age_b = i - hi_k; age_h = age_b * 0.25
    travel = (H - low_run) / atr
    vel = travel / max(1, age_b)
    lo96 = min(S[k]["l"] for k in range(max(hi_k, i - 96), i + 1))
    hi96 = max(S[k]["h"] for k in range(max(hi_k, i - 96), i + 1))
    recent_frac = ((hi96 - lo96) / atr) / max(0.001, travel)
    # retraces >=1.5 ATR a partir do low corrente
    nr = 0; run_lo = S[hi_k]["l"]; peak = None
    for k in range(hi_k, i + 1):
        if S[k]["l"] < run_lo:
            run_lo = S[k]["l"]; peak = None
        bounce = (S[k]["h"] - run_lo) / atr
        if bounce >= 1.5 and peak is None:
            nr += 1; peak = k
    return {"age_h": age_h, "travel": travel, "vel": vel,
            "recent_frac": min(recent_frac, 1.5), "n_retraces": nr}

CTX = [u for u in U if u["cj_t"] in R3 and cascade(u["cj_t"]) >= 4]
POCKET = sorted([u for u in CTX if fv(u, "reclaim_atr", 0) >= 1.5
                 and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)
                 and fv(u, "h1_rsi", 99) <= 42], key=lambda u: u["cj_t"])
for u in CTX:
    u["_ml"] = macro_leg(u["cj_t"])

CUT = int(dt.datetime(2025, 8, 1, tzinfo=dt.timezone.utc).timestamp())
print("RECONCILIAÇÃO — os 20 plotados (valores da pernada macro):")
print(f"{'#':>3} {'data':>16} {'res':>4} {'age_h':>6} {'travel':>7} {'vel':>6} {'recFrac':>8} {'retr':>5}")
for gid, u in enumerate(POCKET, 1):
    if u["cj_t"] < CUT:
        continue
    m = u["_ml"]; win = R3[u["cj_t"]]["R3"] >= 3
    print(f"#{gid:>2} {dt.datetime.utcfromtimestamp(u['cj_t']).strftime('%Y-%m-%d %H:%M'):>16} "
          f"{'WIN' if win else 'LOSS':>4} {m['age_h']:>6.0f} {m['travel']:>7.1f} {m['vel']:>6.3f} "
          f"{m['recent_frac']:>8.2f} {m['n_retraces']:>5}")

VETOS = {
    "M1_age<=24h": lambda u: u["_ml"]["age_h"] <= 24,
    "M2_age<=48h": lambda u: u["_ml"]["age_h"] <= 48,
    "M3_recFrac>=0.5": lambda u: u["_ml"]["recent_frac"] >= 0.5,
    "M4_recFrac>=0.7": lambda u: u["_ml"]["recent_frac"] >= 0.7,
    "M5_sem_retrace": lambda u: u["_ml"]["n_retraces"] == 0,
    "M6_vel>=0.10": lambda u: u["_ml"]["vel"] >= 0.10,
    "M7_age48_ou_frac70": lambda u: u["_ml"]["age_h"] <= 48 or u["_ml"]["recent_frac"] >= 0.7,
}

def panel(rows):
    nets = [R3[u["cj_t"]]["net3"] for u in rows]
    h = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3)
    return len(rows), h, sum(nets)

random.seed(41)
def eval_veto(fn, rows):
    kept = [u for u in rows if not fn(u)]; rem = [u for u in rows if fn(u)]
    if not rem or not kept:
        return None
    nk, hk, sk = panel(kept)
    rw = sum(1 for u in rem if R3[u["cj_t"]]["R3"] >= 3); rl = len(rem) - rw
    n0, h0, s0 = panel(rows)
    nets_all = [R3[u["cj_t"]]["net3"] for u in rows]
    ge = 0
    for _ in range(2000):
        drop = set(random.sample(range(len(rows)), len(rem)))
        if sum(x for i, x in enumerate(nets_all) if i not in drop) >= sk:
            ge += 1
    return dict(kept_n=nk, kept_hit=hk / nk, kept_net=sk, d_net=sk - s0, rl=rl, rw=rw, p=ge / 2000)

n0, h0, s0 = panel(POCKET); nc, hc, sc = panel(CTX)
print(f"\nPOCKET N{n0} hit {100*h0/n0:.1f}% NET {s0:+.1f} | CTX N{nc} hit {100*hc/nc:.1f}% NET {sc:+.1f}")
print(f"{'veto':<22} {'kept':>5} {'hit%':>6} {'NET':>7} {'ΔNET':>7} {'remL:W':>7} {'P':>7} | ctx {'ΔNET':>7} {'remL:W':>7}")
out = {}
for nm, fn in VETOS.items():
    rp = eval_veto(fn, POCKET); rc = eval_veto(fn, CTX)
    if rp is None or rc is None:
        print(f"{nm:<22} veto vazio/total"); continue
    ok = rp["d_net"] > 0 and rc["d_net"] > 0 and rp["rl"] >= 2 * max(1, rp["rw"])
    print(f"{nm:<22} {rp['kept_n']:>5} {100*rp['kept_hit']:>5.1f}% {rp['kept_net']:>+7.1f} {rp['d_net']:>+7.1f} "
          f"{rp['rl']:>3}:{rp['rw']:<3} {rp['p']:>7.3f} |     {rc['d_net']:>+7.1f} {rc['rl']:>3}:{rc['rw']:<3}"
          f"{'   <<< PASSA' if ok else ''}")
    out[nm] = {"pocket": rp, "ctx": rc, "passa": ok}
json.dump(out, open(HERE / "results" / "macro_leg_position_veto_20260705.json", "w"), indent=1, default=str)
print("OK → results/macro_leg_position_veto_20260705.json")
