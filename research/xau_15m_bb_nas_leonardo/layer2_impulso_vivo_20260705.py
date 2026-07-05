#!/usr/bin/env python3
"""LAYER 2 — IMPULSO-VIVO: leitura ESTRUTURAL-SEQUENCIAL dos dips (2026-07-05).
Método resgatado dos vencedores (CASCEX/RWS): 1º narrativa estrutural como SEQUÊNCIA de eventos
SMC (known_at provado), 2º indicadores em contexto. Zero geometria de profundidade.

NARRATIVA (dos prints, codificada como ORDEM de eventos):
  CONTEXTO BULL-VIVO: dos últimos 8 tokens direcionais (BOS±/CHoCH±, janela 96h) >=5 bull E
    cascade_down <=1 (estrutura de alta intacta — o ESPELHO da CASCEX).
  GATILHO SWEEP&RECLAIM DE NÍVEL: o flush FURA o preço do nível estrutural mais recente
    (EQL ou o low do último BOS+ rompido... usamos EQL/eq-low tokens e swing-low labels: preço
    do token EQL mais recente em 48h) E o close do cj está DE VOLTA ACIMA desse nível — a ordem
    fura→recupera é o sinal, não a profundidade.
  CONFLUÊNCIA: demanda (<=0,5 ATR) E reclaim_atr >= 1,0.
  CONTEXTO RANGE (2ª classe, +367R): sem cascata dominante (down<=2 E up<=2), fundo da caixa
    (g_box480 <= 0,35), mesmo gatilho sweep&reclaim + demanda + reclaim.
LENTES declaradas (FDR): rsi1h<=55 · swept_prior_low · bolha buy (buy_bub_w>=1) · casc_up>=2.
MÉTRICAS: recall ESTRITO (|flush − flo_GT| <= 1 ATR E ±8h) por classe · painel completo · null
bootstrap vs universo dos candidatos elegíveis · por-ano. Ex-CASCEX."""
import json, bisect, random, hashlib, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])   # U, R3, S, TS, cascade, fv, macro_leg, events(ET tokens dir), close_at
GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GT.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gt = json.load(open(GT))
gap = json.load(open(HERE / "results" / "layer2_gap_map_20260705.json"))
MISSED = gap["missed_rows"]
MISS_BULL = [(r["ft"], r["flo"]) for r in MISSED if r["reg"] == "BULL"]
MISS_RANGE = [(r["ft"], r["flo"]) for r in MISSED if r["reg"] not in ("BULL", "BEAR")]
MISS_BEAR = [(r["ft"], r["flo"]) for r in MISSED if r["reg"] == "BEAR"]

# eventos SMC completos (com EQL/EQH e preços) — o exec acima só carregou BOS/CHoCH; recarrega tudo
EV2 = []
seen2 = set()
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for e in json.load(open(p))["smc_events"]:
        key = (e["t"], e["text"], round(e["price"], 2))
        if key in seen2:
            continue
        seen2.add(key)
        c = close_at(e["t"])
        if c is None:
            continue
        tok = e["text"] + (("+" if c > e["price"] else "-") if e["text"] in ("BOS", "CHoCH") else "")
        EV2.append({"t": e["t"], "tok": tok, "price": e["price"]})
EV2.sort(key=lambda x: x["t"]); ET2 = [e["t"] for e in EV2]

def struct_ctx(cj):
    t0 = cj - 384 * 900  # 96h
    hi = bisect.bisect_right(ET2, cj)
    win = [EV2[i] for i in range(hi) if EV2[i]["t"] >= t0]
    dirs = [e for e in win if e["tok"][-1] in "+-"]
    last8 = dirs[-8:]
    n_bull = sum(1 for e in last8 if e["tok"].endswith("+"))
    cd = 0
    for e in reversed(dirs):
        if e["tok"] in ("BOS-", "CHoCH-"):
            cd += 1
        else:
            break
    cu = 0
    for e in reversed(dirs):
        if e["tok"] in ("BOS+", "CHoCH+"):
            cu += 1
        else:
            break
    # nível estrutural mais recente ABAIXO do preço para sweep: último EQL em 48h
    t48 = cj - 192 * 900
    eqls = [e for e in win if e["tok"] == "EQL" and e["t"] >= t48]
    lvl = eqls[-1]["price"] if eqls else None
    return {"n_bull": n_bull, "n8": len(last8), "cd": cd, "cu": cu, "eql": lvl}

def sweep_reclaim(u, lvl):
    if lvl is None:
        return 0
    flo = u["g_sl"] + 0.1 * u["g_atr"]
    return int(flo < lvl and u["g_entry"] > lvl)

CANDS = []
for u in U:
    if u["cj_t"] not in R3:
        continue
    sc = struct_ctx(u["cj_t"])
    u["_sc"] = sc
    CANDS.append(u)
WEEKS = len({u["g_week"] for u in U})

def strict_recall(rows, gtlist):
    got = 0
    ts = sorted((u["cj_t"], u["g_sl"] + 0.1 * u["g_atr"], u.get("g_atr") or 5.0) for u in rows)
    T = [x[0] for x in ts]
    for ft, flo in gtlist:
        j = bisect.bisect_left(T, ft - 8 * 3600); ok = False
        while j < len(T) and T[j] <= ft + 8 * 3600:
            if abs(ts[j][1] - flo) <= ts[j][2]:
                ok = True; break
            j += 1
        got += ok
    return got

def full_panel(rows, tag, gtlist):
    if not rows:
        print(f"  {tag:<34} vazio"); return None
    rows = sorted(rows, key=lambda u: u["cj_t"])
    nets = [R3[u["cj_t"]]["net3"] for u in rows]
    n = len(rows); h = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3)
    s = sum(nets); eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {y: round(sum(nets[i] for i, u in enumerate(rows) if u["yr"] == y), 1) for y in (2024, 2025, 2026)}
    sr = strict_recall(rows, gtlist)
    print(f"  {tag:<34} N{n:>4} hit3R {100*h/n:>5.1f}% sumR {s:>+7.1f} avgR {s/n:>+.3f} DD {dd:>6.1f} "
          f"stk-{mL} | {n/WEEKS:.2f}/sem | recallESTRITO {sr}/{len(gtlist)} | {yr}")
    return {"n": n, "hit": h / n, "sum": round(s, 1), "stk": mL, "recall": sr}

def is_cascex_member(u):
    if cascade(u["cj_t"]) < 4:
        return False
    if not (fv(u, "reclaim_atr", 0) >= 1.5 and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)
            and fv(u, "h1_rsi", 99) <= 42):
        return False
    ml = macro_leg(u["cj_t"])
    return ml["vel"] < 0.10 and ml["recent_frac"] < 0.5

ELIG = [u for u in CANDS if not is_cascex_member(u)]
uni_hit = sum(1 for u in ELIG if R3[u["cj_t"]]["R3"] >= 3) / len(ELIG)
print(f"elegíveis (ex-CASCEX): N{len(ELIG)} · hit universo {100*uni_hit:.1f}%")

def dem_ok(u):
    return fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5

BULLV = [u for u in ELIG if u["_sc"]["n8"] >= 6 and u["_sc"]["n_bull"] >= 5 and u["_sc"]["cd"] <= 1
         and sweep_reclaim(u, u["_sc"]["eql"]) and dem_ok(u) and fv(u, "reclaim_atr", 0) >= 1.0]
RANGEV = [u for u in ELIG if u["_sc"]["cd"] <= 2 and u["_sc"]["cu"] <= 2
          and fv(u, "g_box480", 9) <= 0.35
          and sweep_reclaim(u, u["_sc"]["eql"]) and dem_ok(u) and fv(u, "reclaim_atr", 0) >= 1.0]
print("\nBASES estruturais-sequenciais:")
pb = full_panel(BULLV, "BULL-VIVO (sweep&reclaim EQL)", MISS_BULL)
pr = full_panel(RANGEV, "RANGE-FUNDO (sweep&reclaim)", MISS_RANGE)

# lentes sobre a base BULL (se N>=60)
LENS = {
    "rsi1h<=55": lambda u: fv(u, "h1_rsi", 99) <= 55,
    "swept_prior": lambda u: fv(u, "swept_prior_low", 0) == 1,
    "bolha_buy": lambda u: fv(u, "buy_bub_w", 0) >= 1,
    "casc_up>=2": lambda u: u["_sc"]["cu"] >= 2,
}
for basename, BASEX, gl in (("BULL-VIVO", BULLV, MISS_BULL), ("RANGE-FUNDO", RANGEV, MISS_RANGE)):
    if len(BASEX) < 60:
        continue
    H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in BASEX]
    random.seed(31)
    print(f"\n  lentes sobre {basename}:")
    for nm, fn in LENS.items():
        g = [u for u in BASEX if fn(u)]
        if len(g) < 25:
            continue
        hs = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in g]
        obs = sum(hs) / len(hs)
        ge = sum(1 for _ in range(2000) if sum(random.sample(H0, len(g))) / len(g) >= obs)
        print(f"    {nm:<16} N{len(g):>4} hit {100*obs:>5.1f}% NET {sum(R3[u['cj_t']]['net3'] for u in g):>+7.1f} "
              f"recall {strict_recall(g, gl)}/{len(gl)} P {ge/2000:.4f}")
json.dump({"bull": pb, "range": pr},
          open(HERE / "results" / "layer2_impulso_vivo_20260705.json", "w"), indent=1, default=str)
print("OK → results/layer2_impulso_vivo_20260705.json")
