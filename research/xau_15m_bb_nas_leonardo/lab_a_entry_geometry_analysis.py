#!/usr/bin/env python3
"""LAB A — ENTRY GEOMETRY v2: avaliação determinística (prereg + 4 propostas A6 dos agentes).
Prereg (autoridade): docs/architecture/XAU_15M_LONG_LAB_A_ENTRY_GEOMETRY_PREREG_20260703.md
EMENDAS pós-perspectivas (declaradas ANTES de rodar v2, exigências do DA-agent pré-execução):
  (a) nível não-aplicável (L ≥ entry0 OU L ≤ sl) → MARKET fallback em entry0 (fração `na` reportada;
      corrige drop silencioso do grid δ=0,8 com 20 trades de risk_atr ≤ 0,8);
  (b) same-bar stop: se low do bar de fill ≤ sl → R = −1 (ordem intrabar desconhecível; conservador);
  (c) gap-open ≤ sl → R = −1 (nunca skip);
  (d) horizonte do letrun ANCORADO em cj (end = cj+HMAX, idêntico à base) — réplica exata do letrun
      do engine com end ancorado;
  (e) dois regimes de fill: TOUCH (low ≤ L) e THROUGH (low ≤ L − $0,40) — ambos computados;
  (f) seleção adversa MEDIDA: base avgR filled vs missed + delta pareado nos fills;
  (g) decomposição de miss: winners/losers/runners perdidos.
Seleção A6 (por DESENHO, pré-resultado): A6_CAP20 (mecânica: cap condicional de risco) ·
A6_RECLAIM (DA: fill condicionado a hold/reclaim, anti-seleção-adversa) · A6_HLDEF (estrutura:
higher-low da confirmação) · A6_CR2 (custo: depth c/ piso de risco). Vizinhança CAP 1,8/2,2
reportada (não best-of). Não-aceitas registradas no relatório (SPLIT/CJLOW/MS1/MS3/CR1).
"""
import csv, json, random
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
SB_USD = 0.80; THROUGH_PAD = 0.40

ns = {"__name__": "engine_exec", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile(open(HERE / "engine_substrate4_v5_hourcausal.py").read(),
             "engine_substrate4_v5_hourcausal.py", "exec"), ns)
cand, ROWS, PRIMK = ns["cand"], ns["ROWS"], ns["PRIMK"]
cf_low, HMAX, RCAP = ns["cf_low"], ns["HMAX"], ns["RCAP"]
sel = sorted([c for c in cand if c["v5h"] != "BEAR"], key=lambda z: z["cj_t"])
rmap = {}
for r in ROWS: rmap.setdefault(r["cj_t"], r)

def letrun_anchored(s, fill_j, entry, sl, atr, cj):
    """Réplica EXATA do letrun do engine, com end ancorado em cj (comparável à base)."""
    risk = entry - sl
    if risk <= 0: return None
    trail = sl; r1 = False; ex = None; end = min(cj + HMAX, len(s) - 1)
    for k in range(fill_j + 1, end + 1):
        if s[k]["l"] <= trail: ex = trail; break
        if (s[k]["h"] - entry) / risk >= 1: r1 = True
        if r1:
            sw = cf_low(s, k)
            if sw: trail = max(trail, sw - 0.1 * atr)
    if ex is None: ex = s[end]["c"]
    return max(-1.0, min(RCAP, (ex - entry) / risk))

SIG = []
for c in sel:
    r = rmap[c["cj_t"]]; s = PRIMK[r["block"]]["series"]
    tm = {b["t"]: i for i, b in enumerate(s)}
    p, cj = tm[r["t"]], tm[r["cj_t"]]
    atr = s[p]["atr"] or s[cj]["atr"]
    entry0 = s[cj]["c"]; sl = min(x["l"] for x in s[p:cj + 1]) - 0.1 * atr
    SIG.append({"t": c["cj_t"], "yr": c["yr"], "R0": c["R"], "s": s, "p": p, "cj": cj, "atr": atr,
                "entry0": entry0, "sl": sl, "risk0": entry0 - sl,
                "hl": max(x["l"] for x in s[p + 1:cj + 1])})
assert len(SIG) == 435

def exec_trade(g, j, price, limit_style):
    """Fill em (j, price) → R bruto. Regra (b) same-bar stop SÓ para fills LIMIT (touch/open):
    entrada at-close (market/delay/reclaim) não pode ser stopada pelo low que a PRECEDE no
    próprio bar (correção DA Lab A 2026-07-03 — antes corrompia delay-nulls e RECLAIM)."""
    if price <= g["sl"]:
        return -1.0, None                                   # (c) fill já abaixo/no SL
    if limit_style and g["s"][j]["l"] <= g["sl"] and j != g["cj"]:
        return -1.0, price - g["sl"]                        # (b) intrabar order desconhecível → conservador
    R = letrun_anchored(g["s"], j, price, g["sl"], g["atr"], g["cj"])
    return (R if R is not None else -1.0), price - g["sl"]

def fill_limit(g, L, W, through):
    """(a) na→market; touch/through; gap→open; retorna ('market'|'fill'|'miss', j, price)."""
    if L >= g["entry0"] or L <= g["sl"]:
        return ("market", g["cj"], g["entry0"])
    trigger = L - THROUGH_PAD if through else L
    end = min(g["cj"] + W, len(g["s"]) - 1)
    for j in range(g["cj"] + 1, end + 1):
        b = g["s"][j]
        if b["o"] <= L:
            return ("fill", j, b["o"])
        if b["l"] <= trigger:
            return ("fill", j, L)
    return ("miss", None, None)

def fill_reclaim(g, L, W):
    """A6_RECLAIM: primeira barra k>cj com low ≤ L E close > L → market no CLOSE de k."""
    if L >= g["entry0"] or L <= g["sl"]:
        return ("market", g["cj"], g["entry0"])
    end = min(g["cj"] + W, len(g["s"]) - 1)
    for j in range(g["cj"] + 1, end + 1):
        b = g["s"][j]
        if b["l"] <= L and b["c"] > L:
            return ("fill", j, b["c"])
    return ("miss", None, None)

def evaluate(name, plan, through=False):
    """plan(g) → ('market'|'fill'|'miss', j, price)."""
    per = []
    for g in SIG:
        kind, j, price = plan(g) if not through else plan(g)
        # through só afeta fills limit; plan já parametrizado externamente quando through=True
        if kind == "miss":
            per.append({"yr": g["yr"], "filled": False, "kind": kind, "Rg": 0.0, "Rn": 0.0,
                        "base": g["R0"], "risk": None})
            continue
        # limit_style = fill por touch/open de limit; entradas at-close (market/reclaim) não
        limit_style = (kind == "fill") and (name not in ("A6_RECLAIM", "A6_RECLAIM_THR"))
        R, risk = exec_trade(g, j, price, limit_style)
        risk = risk if risk is not None else price - g["sl"]
        cost = SB_USD / risk if risk and risk > 0 else 0.0
        per.append({"yr": g["yr"], "filled": True, "kind": kind, "Rg": R, "Rn": R - cost,
                    "base": g["R0"], "risk": risk})
    def chrono(key):
        rs = [x[key] for x in per]
        sm = sum(rs); eq = pk = dd = 0.0
        for x in rs: eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        mL = cl = 0
        for x in rs:
            cl = 0 if x > 0 else cl + 1; mL = max(mL, cl)
        return round(sm, 1), round(dd, 1), mL
    fills = [x for x in per if x["filled"]]
    limits = [x for x in fills if x["kind"] == "fill"]
    miss = [x for x in per if not x["filled"]]
    gs, gdd, _ = chrono("Rg"); nsm, ndd, nstk = chrono("Rn")
    rk = sorted(x["risk"] for x in fills if x["risk"])
    net_sorted = sorted((x["Rn"] for x in fills), reverse=True)
    return {"variant": name, "regime": "through" if through else "touch",
            "fills": len(fills), "limit_fills": len(limits), "na_market": len(fills) - len(limits),
            "miss_rate": round(100 * len(miss) / 435, 1),
            "WR_fill": round(100 * sum(1 for x in fills if x["Rn"] > 0) / max(1, len(fills)), 1),
            "gross_sumR": gs, "net_sumR": nsm, "net_DD": ndd,
            "net_rDD": round(abs(nsm / ndd), 2) if ndd < 0 else None, "net_streak": nstk,
            "net_yr": {y: round(sum(x["Rn"] for x in per if x["yr"] == y), 1) for y in (2024, 2025, 2026)},
            "risk_usd_med": round(rk[len(rk) // 2], 2) if rk else None,
            "runners_net": sum(1 for x in fills if x["Rn"] >= 3),
            "miss_win_n": sum(1 for x in miss if x["base"] > 0), "miss_loss_n": sum(1 for x in miss if x["base"] <= 0),
            "miss_baseR": round(sum(x["base"] for x in miss), 1),
            "miss_runners": sum(1 for x in miss if x["base"] >= 3),
            "adv_sel_filled_baseAvgR": round(sum(x["base"] for x in fills) / max(1, len(fills)), 3),
            "adv_sel_missed_baseAvgR": round(sum(x["base"] for x in miss) / max(1, len(miss)), 3) if miss else None,
            "paired_delta_on_fills": round(sum(x["Rn"] - x["base"] for x in limits), 1),
            "net_drop_top3": round(nsm - sum(net_sorted[:3]), 1) if len(net_sorted) >= 3 else None,
            "_per": per}

def mk(name, planf):
    return (name, planf)

PLANS = [
    mk("BASE_market_cj", lambda g: ("market", g["cj"], g["entry0"])),
]
for dep in (0.3, 0.5, 0.8):
    for W in (8, 16):
        PLANS.append(mk(f"LIM_{dep}ATR_W{W}",
                        (lambda d, w: lambda g: fill_limit(g, g["entry0"] - d * g["atr"], w, False))(dep, W)))
PLANS += [
    mk("LIM_mid_risk_W16", lambda g: fill_limit(g, g["entry0"] - 0.5 * g["risk0"], 16, False)),
    mk("LIM_pHigh_W16", lambda g: fill_limit(g, g["s"][g["p"]]["h"], 16, False)),
    mk("NULL_delay_cj2", lambda g: ("market", g["cj"] + 2, g["s"][g["cj"] + 2]["c"]) if g["cj"] + 2 < len(g["s"]) else ("miss", None, None)),
    mk("NULL_delay_cj4", lambda g: ("market", g["cj"] + 4, g["s"][g["cj"] + 4]["c"]) if g["cj"] + 4 < len(g["s"]) else ("miss", None, None)),
    # ---- A6 aceitas (definições exatas dos agentes) ----
    mk("A6_CAP20", lambda g: ("market", g["cj"], g["entry0"]) if g["risk0"] <= 2.0 * g["atr"]
       else fill_limit(g, g["sl"] + 2.0 * g["atr"], 16, False)),
    mk("A6_CAP18_nb", lambda g: ("market", g["cj"], g["entry0"]) if g["risk0"] <= 1.8 * g["atr"]
       else fill_limit(g, g["sl"] + 1.8 * g["atr"], 16, False)),
    mk("A6_CAP22_nb", lambda g: ("market", g["cj"], g["entry0"]) if g["risk0"] <= 2.2 * g["atr"]
       else fill_limit(g, g["sl"] + 2.2 * g["atr"], 16, False)),
    mk("A6_RECLAIM", lambda g: fill_reclaim(g, g["entry0"] - 0.5 * g["risk0"], 16)),
    mk("A6_HLDEF", lambda g: fill_limit(g, g["hl"], 16, False)),
    mk("A6_CR2", (lambda g: (lambda depth: ("market", g["cj"], g["entry0"])
        if g["risk0"] - depth < 0.9 * g["atr"]
        else fill_limit(g, g["entry0"] - depth, 16, False))(min(0.5 * g["atr"], 0.35 * g["risk0"])))),
]

results = [evaluate(n, f) for n, f in PLANS]

# regime THROUGH para as variantes-limite principais (e) — não para nulls/base
THROUGH_SET = {"LIM_0.3ATR_W16", "A6_CAP20", "A6_RECLAIM", "A6_HLDEF", "A6_CR2"}
def through_wrap(name, f):
    def plan(g):
        # reusar mesmas regras com trigger deslocado: só fill_limit interno usa through;
        # para simplicidade determinística re-parametrizamos via closure específica abaixo.
        return f(g)
    return plan
TH = []
for n, f in PLANS:
    if n not in THROUGH_SET: continue
    if n == "A6_RECLAIM":
        TH.append((n, lambda g: fill_reclaim(g, g["entry0"] - 0.5 * g["risk0"], 16)))  # reclaim já é close-based (through n/a) — reportado igual
        continue
    if n == "LIM_0.3ATR_W16":
        TH.append((n, lambda g: fill_limit(g, g["entry0"] - 0.3 * g["atr"], 16, True)))
    elif n == "A6_CAP20":
        TH.append((n, lambda g: ("market", g["cj"], g["entry0"]) if g["risk0"] <= 2.0 * g["atr"]
                   else fill_limit(g, g["sl"] + 2.0 * g["atr"], 16, True)))
    elif n == "A6_HLDEF":
        TH.append((n, lambda g: fill_limit(g, g["hl"], 16, True)))
    elif n == "A6_CR2":
        TH.append((n, (lambda g: (lambda depth: ("market", g["cj"], g["entry0"])
            if g["risk0"] - depth < 0.9 * g["atr"]
            else fill_limit(g, g["entry0"] - depth, 16, True))(min(0.5 * g["atr"], 0.35 * g["risk0"])))))
results_th = [evaluate(n + "_THR", f) for n, f in TH]  # through embutido no plano (closures)
for r in results_th: r["regime"] = "through"  # correção de label (DA)

# ---- fail-loud baseline ----
b = results[0]
assert b["fills"] == 435 and abs(b["gross_sumR"] - 291.5) < 0.5 and abs(b["net_sumR"] - 233.6) < 0.5, b
print("BASELINE OK (bruto +291,5 / SB-net +233,6)\n")

def show(rs):
    for r in rs:
        print(f"{r['variant']:<18} fills{r['fills']:>4}(lim{r['limit_fills']:>3}/na{r['na_market']:>3}) "
              f"miss{r['miss_rate']:>5}% WRf{r['WR_fill']:>5}% | bruto{r['gross_sumR']:>7} | NET{r['net_sumR']:>7} "
              f"DD{r['net_DD']:>7} r/DD{r['net_rDD']!s:>6} strk-{r['net_streak']:<3}| risk${r['risk_usd_med']!s:>6} "
              f"run{r['runners_net']:>3} | missW/L {r['miss_win_n']}/{r['miss_loss_n']} missRun{r['miss_runners']:>2} "
              f"| advSel f/m {r['adv_sel_filled_baseAvgR']}/{r['adv_sel_missed_baseAvgR']} pairΔ{r['paired_delta_on_fills']:>7} "
              f"| yr {r['net_yr']}")
show(results); print("\n--- regime THROUGH (fill exige low ≤ L−$0,40; anti-otimismo) ---"); show(results_th)

# ---- nulls da melhor variante NET (excl. base/nulls/vizinhança) ----
cand_best = [r for r in results if r["variant"].startswith(("LIM", "A6")) and not r["variant"].endswith("_nb")]
best = max(cand_best, key=lambda r: r["net_sumR"])
print(f"\nMELHOR variante NET: {best['variant']} ({best['net_sumR']})")
if best["miss_rate"] > 0:
    per = best["_per"]; mrate = sum(1 for x in per if not x["filled"]) / 435
    random.seed(20260703)
    # custo POR-TRADE da base (0,80/risk0_i) — correção DA: custo fixo/mediana subestimava (Jensen)
    base_net_pt = [g["R0"] - SB_USD / g["risk0"] for g in SIG]
    wins = 0; sims = 500
    for _ in range(sims):
        sim = sum(0.0 if random.random() < mrate else x for x in base_net_pt)
        if sim >= best["net_sumR"]: wins += 1
    print(f"FILL-RATE NULL (500 reps, miss aleatório à mesma taxa, custo por-trade): "
          f"p(null ≥ variante) = {wins/sims:.3f}")
# jackknife-episódio (drop-top contribuições por episódio ≤8 barras)
eps = []; curr = [(SIG[0], best["_per"][0])]
for (ga, xa), (gb, xb) in zip(zip(SIG, best["_per"]), list(zip(SIG, best["_per"]))[1:]):
    if gb["t"] - ga["t"] <= 8 * 900: curr.append((gb, xb))
    else: eps.append(curr); curr = [(gb, xb)]
eps.append(curr)
contrib = sorted((sum(x["Rn"] for _, x in e) for e in eps), reverse=True)
print(f"JACKKNIFE-EPISÓDIO ({len(eps)} eps): net drop-top1 {round(best['net_sumR']-contrib[0],1)} "
      f"drop-top3 {round(best['net_sumR']-sum(contrib[:3]),1)}")

hdr = [k for k in results[0].keys() if k != "_per"]
with open(OUT / "lab_a_entry_geometry_results.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=hdr, extrasaction="ignore"); w.writeheader()
    for r in results + results_th: w.writerow({k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in r.items() if k != "_per"})
json.dump({"prereg": "XAU_15M_LONG_LAB_A_ENTRY_GEOMETRY_PREREG_20260703.md",
           "amendments": "na->market, same-bar stop -1, gap<=sl -1, horizon anchored cj, touch/through, adverse-selection metrics",
           "results": [{k: v for k, v in r.items() if k != "_per"} for r in results + results_th]},
          open(OUT / "lab_a_entry_geometry_summary.json", "w"), indent=1)
print("\noutputs OK")
