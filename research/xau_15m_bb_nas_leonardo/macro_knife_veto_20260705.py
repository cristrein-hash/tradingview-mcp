#!/usr/bin/env python3
"""VETO MACRO/CONTEXTUAL DE FACAS — sobre o pocket trio (2026-07-05, ordem Cris pós-visual).
Diagnóstico visual do Cris nos 20 plotados: losers em pontos de FACA CAINDO clara. Teste: leitura
contextual macro (features que JÁ temos: regime detector v5h, macro, HTF 4H/1H, perna, estrutura)
consegue vetar losers sem matar winners?

LEDGER DE VETOS (15, DECLARADO ANTES DE CORRER — cada um = "não entrar se ..."):
  V01 knife flag        g_knife==1
  V02 regime BEAR       g_v5h=='BEAR'
  V03 macro bear        macro_bear==1
  V04 4H em queda       h4_trend==-1
  V05 1H em queda       h1_trend==-1
  V06 4H sem virada     h4n_choch_up_rec==0
  V07 perna sem decel   downleg_decel==0
  V08 perna eficiente   downleg_eff>=0.6 (cachoeira)
  V09 downrun longo     g_downrun>=6
  V10 confirmação fraca confirm_body_atr<0.3
  V11 4H esticado       h4_dist<=-2
  V12 4H RSI freefall   h4n_rsi<=25
  V13 flip de regime 5d g_regime_flip5d==1
  V14 vol expandindo    atr_regime>=1.3
  V15 1H esticado       h1_dist<=-2.5
AVALIAÇÃO: no POCKET (N56, cascata>=4 & reclaim>=1,5 & demanda & rsi1h<=42) e replicação no
CONTEXTO (N228, cascata>=4): kept-N/hit/NET, losers vs winners removidos, ΔNET.
NULL por veto (2000×): remoção aleatória do mesmo k → P(NET_kept >= obs).
UNIÃO (regra fixa, 1 look): vetos com ΔNET>0 em AMBOS os conjuntos E razão losers:winners
removidos >=2:1 no pocket → painel completo do pocket vetado."""
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

CTX = [u for u in U if u["cj_t"] in R3 and cascade(u["cj_t"]) >= 4]
POCKET = [u for u in CTX if fv(u, "reclaim_atr", 0) >= 1.5
          and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)
          and fv(u, "h1_rsi", 99) <= 42]
assert len(POCKET) == 56 and len(CTX) == 228

VETOS = {
    "V01_knife": lambda u: fv(u, "g_knife", 0) == 1,
    "V02_bear": lambda u: u.get("g_v5h") == "BEAR",
    "V03_macro_bear": lambda u: fv(u, "macro_bear", 0) == 1,
    "V04_4h_queda": lambda u: fv(u, "h4_trend", 0) == -1,
    "V05_1h_queda": lambda u: fv(u, "h1_trend", 0) == -1,
    "V06_4h_sem_virada": lambda u: fv(u, "h4n_choch_up_rec", 0) == 0,
    "V07_sem_decel": lambda u: fv(u, "downleg_decel", 1) == 0,
    "V08_cachoeira": lambda u: fv(u, "downleg_eff", 0) >= 0.6,
    "V09_downrun6": lambda u: fv(u, "g_downrun", 0) >= 6,
    "V10_confirm_fraca": lambda u: fv(u, "confirm_body_atr", 9) < 0.3,
    "V11_4h_esticado": lambda u: fv(u, "h4_dist", 0) <= -2,
    "V12_4h_rsi_freefall": lambda u: fv(u, "h4n_rsi", 99) <= 25,
    "V13_flip5d": lambda u: fv(u, "g_regime_flip5d", 0) == 1,
    "V14_vol_expand": lambda u: fv(u, "atr_regime", 0) >= 1.3,
    "V15_1h_esticado": lambda u: fv(u, "h1_dist", 0) <= -2.5,
}

def panel(rows):
    nets = [R3[u["cj_t"]]["net3"] for u in rows]
    h = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3)
    return len(rows), h, sum(nets)

random.seed(33)
def eval_veto(name, fn, rows, label):
    kept = [u for u in rows if not fn(u)]
    rem = [u for u in rows if fn(u)]
    if not rem or not kept:
        return None
    n0, h0, s0 = panel(rows); nk, hk, sk = panel(kept)
    rw = sum(1 for u in rem if R3[u["cj_t"]]["R3"] >= 3); rl = len(rem) - rw
    nets_all = [R3[u["cj_t"]]["net3"] for u in rows]
    ge = 0
    for _ in range(2000):
        drop = set(random.sample(range(len(rows)), len(rem)))
        if sum(x for i, x in enumerate(nets_all) if i not in drop) >= sk:
            ge += 1
    return {"label": label, "kept_n": nk, "kept_hit": hk / nk, "kept_net": sk,
            "d_net": sk - s0, "rem_l": rl, "rem_w": rw, "p": ge / 2000}

n0, h0, s0 = panel(POCKET); nc, hc, sc = panel(CTX)
print(f"POCKET N{n0} hit {100*h0/n0:.1f}% NET {s0:+.1f}   |   CTX N{nc} hit {100*hc/nc:.1f}% NET {sc:+.1f}")
print(f"{'veto':<22} {'kept':>5} {'hit%':>6} {'NET':>7} {'ΔNET':>7} {'remL:W':>7} {'P':>6}  | ctx: {'ΔNET':>7} {'remL:W':>7}")
union = []
res = {}
for nm, fn in VETOS.items():
    rp = eval_veto(nm, fn, POCKET, "pocket")
    rc = eval_veto(nm, fn, CTX, "ctx")
    if rp is None or rc is None:
        print(f"{nm:<22} {'—':>5} (veto vazio ou total)")
        continue
    ok = rp["d_net"] > 0 and rc["d_net"] > 0 and rp["rem_l"] >= 2 * max(1, rp["rem_w"])
    if ok:
        union.append(nm)
    print(f"{nm:<22} {rp['kept_n']:>5} {100*rp['kept_hit']:>5.1f}% {rp['kept_net']:>+7.1f} {rp['d_net']:>+7.1f} "
          f"{rp['rem_l']:>3}:{rp['rem_w']:<3} {rp['p']:>6.3f}  |      {rc['d_net']:>+7.1f} {rc['rem_l']:>3}:{rc['rem_w']:<3}"
          f"{'   <<< UNIAO' if ok else ''}")
    res[nm] = {"pocket": rp, "ctx": rc, "union": ok}

print(f"\nUNIÃO (regra fixa): {union if union else 'NENHUM veto qualifica'}")
if union:
    fnu = lambda u: any(VETOS[nm](u) for nm in union)
    kept = [u for u in POCKET if not fnu(u)]
    kept.sort(key=lambda u: u["cj_t"])
    nets = [R3[u["cj_t"]]["net3"] for u in kept]
    n = len(kept); h = sum(1 for u in kept if R3[u["cj_t"]]["R3"] >= 3)
    w = sum(1 for x in nets if x > 0); s = sum(nets)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    WEEKS = len({u["g_week"] for u in U})
    yr = {y: round(sum(nets[i] for i, u in enumerate(kept) if u["yr"] == y), 1) for y in (2024, 2025, 2026)}
    rem = [u for u in POCKET if fnu(u)]
    rw = sum(1 for u in rem if R3[u["cj_t"]]["R3"] >= 3)
    print(f"\nPAINEL POCKET VETADO: N{n} hit3R {100*h/n:.1f}% WR {100*w/n:.1f}% sumR {s:+.1f} avgR {s/n:+.3f} "
          f"DD {dd:.1f} r/DD {s/abs(dd) if dd else 0:.1f} stk-{mL} | {n/WEEKS:.2f}/sem | {yr}")
    print(f"  removidos: {len(rem)} ({len(rem)-rw}L/{rw}W)")
    # null da união (1 look)
    nets_all = [R3[u["cj_t"]]["net3"] for u in POCKET]
    ge = 0
    for _ in range(2000):
        drop = set(random.sample(range(len(POCKET)), len(rem)))
        if sum(x for i, x in enumerate(nets_all) if i not in drop) >= s:
            ge += 1
    print(f"  P(remoção aleatória de {len(rem)} >= NET kept) = {ge/2000:.4f}")
    res["_union_panel"] = {"vetos": union, "n": n, "hit": round(h / n, 3), "sumR": round(s, 1),
                           "dd": round(dd, 1), "stk": mL, "yr": yr, "p_null": ge / 2000}
json.dump(res, open(HERE / "results" / "macro_knife_veto_20260705.json", "w"), indent=1, default=str)
print("OK → results/macro_knife_veto_20260705.json")
