#!/usr/bin/env python3
"""DA ADVERSARIAL — Lab A entry geometry. Verificação read-only dos ataques:
A1. Rule (b) same-bar stop: correta para fills LIMIT (preço passa L antes de sl quando open>L),
    mas ERRADA para entradas market-at-CLOSE (delay nulls cj2/cj4 e A6_RECLAIM close-fill):
    o low do bar de entrada precede a entrada. Quantificar conversões indevidas e NET corrigido.
A2. Horizonte ancorado em cj: quanto NET as variantes ganham se ancorado no fill (runway igual)?
A3. Fill-rate null: script original usa custo fixo 0.80/8.2 (subestima custo médio real 0.133/trade)
    -> null inflado. Recalcular com custo por-trade da base (0.80/risk0_i).
A4. RECLAIM same-bar (low<=L E close>L no MESMO bar) é implementação estrita; testar reclaim
    multi-bar (touch em k, primeiro close>L em m<=cj+16) p/ ver se o 'pior de todas' é strawman.
A5. Decomposição do déficit da melhor variante: gross vs custo-SB.
Sem escrita fora deste print. Sem tocar script principal / produção / RAW.
"""
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
SB = 0.80

ns = {"__name__": "engine_exec", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile(open(HERE / "engine_substrate4_v5_hourcausal.py").read(),
             "engine_substrate4_v5_hourcausal.py", "exec"), ns)
cand, ROWS, PRIMK = ns["cand"], ns["ROWS"], ns["PRIMK"]
cf_low, HMAX, RCAP = ns["cf_low"], ns["HMAX"], ns["RCAP"]
sel = sorted([c for c in cand if c["v5h"] != "BEAR"], key=lambda z: z["cj_t"])
rmap = {}
for r in ROWS: rmap.setdefault(r["cj_t"], r)

def letrun_anch(s, fill_j, entry, sl, atr, cj, anchor_fill=False):
    risk = entry - sl
    if risk <= 0: return None, False
    trail = sl; r1 = False; ex = None
    end = min((fill_j if anchor_fill else cj) + HMAX, len(s) - 1)
    for k in range(fill_j + 1, end + 1):
        if s[k]["l"] <= trail: ex = trail; break
        if (s[k]["h"] - entry) / risk >= 1: r1 = True
        if r1:
            sw = cf_low(s, k)
            if sw: trail = max(trail, sw - 0.1 * atr)
    at_horizon = ex is None
    if ex is None: ex = s[end]["c"]
    return max(-1.0, min(RCAP, (ex - entry) / risk)), at_horizon

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
base_net_per = [g["R0"] - SB / g["risk0"] for g in SIG]
print(f"base: gross {sum(g['R0'] for g in SIG):.1f}  net(por-trade risk0) {sum(base_net_per):.1f}  "
      f"custo médio/trade {sum(SB/g['risk0'] for g in SIG)/435:.4f}R  (script null usava 0.80/8.2={SB/8.2:.4f}R)")

def fill_limit(g, L, W):
    if L >= g["entry0"] or L <= g["sl"]:
        return ("market", g["cj"], g["entry0"])
    end = min(g["cj"] + W, len(g["s"]) - 1)
    for j in range(g["cj"] + 1, end + 1):
        b = g["s"][j]
        if b["o"] <= L: return ("fill", j, b["o"])
        if b["l"] <= L: return ("fill", j, L)
    return ("miss", None, None)

# ---------- A1: rule(b) sobre entradas market-at-close (delay nulls + RECLAIM) ----------
print("\n=== A1: same-bar stop aplicado a entradas AT-CLOSE (bug) ===")
for lag in (2, 4):
    n_bug = 0; d_asis = []; d_fix = []
    for g in SIG:
        j = g["cj"] + lag
        if j >= len(g["s"]):  # miss no script
            d_asis.append(0.0); d_fix.append(0.0); continue
        b = g["s"][j]; entry = b["c"]; risk = entry - g["sl"]
        if entry <= g["sl"]:
            R_asis = R_fix = -1.0
        elif b["l"] <= g["sl"]:
            R_asis = -1.0
            R_fix, _ = letrun_anch(g["s"], j, entry, g["sl"], g["atr"], g["cj"])
            R_fix = R_fix if R_fix is not None else -1.0
            n_bug += 1
        else:
            R_asis, _ = letrun_anch(g["s"], j, entry, g["sl"], g["atr"], g["cj"])
            R_asis = R_asis if R_asis is not None else -1.0
            R_fix = R_asis
        c = SB / risk if risk > 0 else 0.0
        d_asis.append(R_asis - c); d_fix.append(R_fix - c)
    print(f"NULL_delay_cj{lag}: trades c/ low(entry-bar)<=sl mas close>sl (viraram -1 indevidamente): {n_bug}"
          f" | NET as-is {sum(d_asis):.1f} -> NET corrigido {sum(d_fix):.1f} (Δ {sum(d_fix)-sum(d_asis):+.1f})")

# RECLAIM as-is vs corrigido (entrada no close do bar de reclaim: low do próprio bar não pode stopar)
def reclaim_run(g, W=16, same_bar=True, fix_same_bar_stop=False):
    L = g["entry0"] - 0.5 * g["risk0"]
    if L >= g["entry0"] or L <= g["sl"]: return ("market", g["cj"], g["entry0"])
    end = min(g["cj"] + W, len(g["s"]) - 1)
    if same_bar:
        for j in range(g["cj"] + 1, end + 1):
            b = g["s"][j]
            if b["l"] <= L and b["c"] > L: return ("fill", j, b["c"])
        return ("miss", None, None)
    touched = False
    for j in range(g["cj"] + 1, end + 1):
        b = g["s"][j]
        if b["l"] <= L: touched = True
        if touched and b["c"] > L: return ("fill", j, b["c"])
    return ("miss", None, None)

def run_variant(plan, close_entry_fix=False, anchor_fill=False, tag=""):
    tot = 0.0; n_bug = 0; fills = 0; miss = 0; miss_base = 0.0; yr = {2024: 0.0, 2025: 0.0, 2026: 0.0}
    n_hor = 0; gross = 0.0
    for g in SIG:
        kind, j, price = plan(g)
        if kind == "miss":
            miss += 1; miss_base += g["R0"]; continue
        fills += 1; risk = price - g["sl"]
        if price <= g["sl"]:
            R = -1.0
        elif g["s"][j]["l"] <= g["sl"] and j != g["cj"]:
            entered_at_close = abs(price - g["s"][j]["c"]) < 1e-9
            if close_entry_fix and entered_at_close:
                n_bug += 1
                R, ah = letrun_anch(g["s"], j, price, g["sl"], g["atr"], g["cj"], anchor_fill)
                R = R if R is not None else -1.0; n_hor += ah
            else:
                R = -1.0
        else:
            R, ah = letrun_anch(g["s"], j, price, g["sl"], g["atr"], g["cj"], anchor_fill)
            R = R if R is not None else -1.0; n_hor += ah
        c = SB / risk if risk > 0 else 0.0
        gross += R; tot += R - c; yr[g["yr"]] += R - c
    return {"tag": tag, "net": round(tot, 1), "gross": round(gross, 1), "fills": fills, "miss": miss,
            "missrate": round(100 * miss / 435, 1), "miss_baseR": round(miss_base, 1),
            "n_closebug_fixed": n_bug, "n_horizon_exits": n_hor,
            "yr": {k: round(v, 1) for k, v in yr.items()}}

r_asis = run_variant(lambda g: reclaim_run(g, same_bar=True), tag="RECLAIM as-is")
r_fix = run_variant(lambda g: reclaim_run(g, same_bar=True), close_entry_fix=True, tag="RECLAIM close-fix")
r_multi = run_variant(lambda g: reclaim_run(g, same_bar=False), close_entry_fix=True, tag="RECLAIM multibar+fix")
for r in (r_asis, r_fix, r_multi):
    print(f"{r['tag']:<22} NET {r['net']:>7} gross {r['gross']:>7} fills {r['fills']} miss {r['missrate']}% "
          f"missBaseR {r['miss_baseR']} closebug-fixados {r['n_closebug_fixed']} | yr {r['yr']}")

# ---------- A2: horizonte ancorado em cj vs no fill ----------
print("\n=== A2: horizonte cj-anchored vs fill-anchored (runway) ===")
variants = {
    "LIM_0.3ATR_W16": lambda g: fill_limit(g, g["entry0"] - 0.3 * g["atr"], 16),
    "A6_CR2": (lambda g: (lambda d: ("market", g["cj"], g["entry0"]) if g["risk0"] - d < 0.9 * g["atr"]
               else fill_limit(g, g["entry0"] - d, 16))(min(0.5 * g["atr"], 0.35 * g["risk0"]))),
}
for name, plan in variants.items():
    a = run_variant(plan, tag=name + " cj-anch")
    b2 = run_variant(plan, anchor_fill=True, tag=name + " fill-anch")
    print(f"{name:<16} NET cj-anch {a['net']:>7} (exits@horizonte {a['n_horizon_exits']}) | "
          f"NET fill-anch {b2['net']:>7} (Δ {b2['net']-a['net']:+.1f})")

# ---------- A1b: quantos fills LIMIT a rule(b) converteu em -1 (fisicamente corretos?) ----------
print("\n=== A1b: rule(b) em fills LIMIT (fisicamente correta: open>L => L antes de sl) ===")
for name, plan in variants.items():
    n_sb = 0; n_gapopen = 0
    for g in SIG:
        kind, j, price = plan(g)
        if kind != "fill": continue
        if price > g["sl"] and g["s"][j]["l"] <= g["sl"]:
            n_sb += 1
            if abs(price - g["s"][j]["o"]) < 1e-9: n_gapopen += 1
    print(f"{name:<16} fills convertidos p/ -1 pela rule(b): {n_sb} (dos quais gap-open-fill {n_gapopen})")

# ---------- A3: fill-rate null CORRIGIDO (custo por-trade da base) ----------
print("\n=== A3: fill-rate null corrigido ===")
cr2 = run_variant(variants["A6_CR2"], tag="A6_CR2")
mrate = cr2["miss"] / 435
random.seed(20260703)
sims = 2000; wins_fix = 0; wins_old = 0
for _ in range(sims):
    s_fix = sum(0.0 if random.random() < mrate else v for v in base_net_per)
    if s_fix >= cr2["net"]: wins_fix += 1
random.seed(20260703)
for _ in range(sims):
    s_old = sum(0.0 if random.random() < mrate else g["R0"] - SB / 8.2 for g in SIG)
    if s_old >= cr2["net"]: wins_old += 1
exp_fix = (1 - mrate) * sum(base_net_per)
print(f"A6_CR2 NET {cr2['net']} | miss-rate {mrate:.3f} | E[null corrigido] {exp_fix:.1f} | "
      f"p_corrigido(null>=var) {wins_fix/sims:.3f} vs p_original-style {wins_old/sims:.3f}")

# ---------- A5: decomposição do déficit ----------
print("\n=== A5: decomposição déficit A6_CR2 vs base ===")
base_gross = sum(g["R0"] for g in SIG); base_net = sum(base_net_per)
print(f"base gross {base_gross:.1f} net {base_net:.1f} custo {base_gross-base_net:.1f}")
print(f"CR2  gross {cr2['gross']} net {cr2['net']} custo {cr2['gross']-cr2['net']:.1f} | "
      f"déficit NET {base_net-cr2['net']:.1f} = gross {base_gross-cr2['gross']:.1f} + custo-extra "
      f"{(cr2['gross']-cr2['net'])-(base_gross-base_net):.1f}")
print(f"CR2 por ano {cr2['yr']} vs base "
      f"{ {y: round(sum(v for g, v in zip(SIG, base_net_per) if g['yr']==y),1) for y in (2024,2025,2026)} }")
print("\nDONE")
