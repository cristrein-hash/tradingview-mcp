#!/usr/bin/env python3
"""MOTOR DE AVALIAÇÃO causal (Anel 1) — outcome por candidato sob SL ESTRUTURAL + LET-RUN trailing estrutural, agregado
por fase/bloco/sub-janela. Régua (honest_note R1): runner-capture + DD/streak ANTES de winrate. Fonte: candidates_annotated.csv
+ primitives/*.json (RAW-derivado). Causal nas FEATURES (entrada=entry_t do CSV, já SHIFT1); o OUTCOME usa barras futuras
(é a variável dependente, correto). Filtros via args p/ medir lift INCREMENTAL. Verified 2026-06-26.
Uso: python3 eval_engine.py [with_macro|all|with_macro+is_pullback|...] """
import csv, json, sys, bisect, statistics as st, datetime as dt
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
SER = {b: pr["series"] for b, pr in PRIM.items()}
TID = {b: {x["t"]: i for i, x in enumerate(s)} for b, s in SER.items()}
K, HMAX, RUNNER_R = 2, 480, 3.0   # fractal k, horizonte máx (~5 dias), limiar runner
MIN_RISK_ATR, R_CAP = 0.5, 15.0   # piso de risco (DA 2026-06-26: SL flush=risco~0=R astronômico) + R-cap p/ avaliação

def conf_swed_low(s, i):  # último swing low confirmado até i (fractal k), causal
    L = [b["l"] for b in s]; lo = max(K, i - 120); best = None
    for p in range(lo, i - K + 1):
        if L[p] == min(L[p - K:p + K + 1]): best = L[p]
    return best
def conf_swed_high(s, i):
    H = [b["h"] for b in s]; lo = max(K, i - 120); best = None
    for p in range(lo, i - K + 1):
        if H[p] == max(H[p - K:p + K + 1]): best = H[p]
    return best

def outcome(r):
    b = r["block"]; s = SER.get(b); tid = TID.get(b)
    if s is None: return None
    ei = tid.get(int(r["entry_t"]))
    if ei is None or ei + 2 >= len(s): return None
    entry = float(r["entry_close"]); zlo = float(r["zone_low"]); zhi = float(r["zone_high"]); zwa = float(r["zone_width_atr"])
    atr = (zhi - zlo) / zwa if zwa > 0 else None
    if not atr or atr <= 0: return None
    long = r["dir"] == "LONG"
    sl0 = (zlo - 0.1 * atr) if long else (zhi + 0.1 * atr)
    struct_risk = (entry - sl0) if long else (sl0 - entry)
    if struct_risk <= 0: return None
    risk = max(struct_risk, MIN_RISK_ATR * atr)            # PISO de risco (anti-denominador-zero)
    sl0 = (entry - risk) if long else (entry + risk)        # alarga o stop até o piso se estrutural for fino demais
    trail = sl0; reached_1R = False; mfe = mae = 0.0; exit_px = None; bars = 0
    end = min(ei + HMAX, len(s) - 1)
    for i in range(ei + 1, end + 1):
        bar = s[i]; bars = i - ei
        if long:
            mfe = max(mfe, (bar["h"] - entry) / risk); mae = min(mae, (bar["l"] - entry) / risk)
            if bar["l"] <= trail: exit_px = trail; break
            if (bar["h"] - entry) / risk >= 1.0: reached_1R = True
            if reached_1R:
                sw = conf_swed_low(s, i)
                if sw is not None: trail = max(trail, sw - 0.1 * atr)
        else:
            mfe = max(mfe, (entry - bar["l"]) / risk); mae = min(mae, (entry - bar["h"]) / risk)
            if bar["h"] >= trail: exit_px = trail; break
            if (entry - bar["l"]) / risk >= 1.0: reached_1R = True
            if reached_1R:
                sw = conf_swed_high(s, i)
                if sw is not None: trail = min(trail, sw + 0.1 * atr)
    if exit_px is None: exit_px = s[end]["c"]   # horizonte
    R = ((exit_px - entry) if long else (entry - exit_px)) / risk
    return {"R": R, "mfe_R": mfe, "mae_R": mae, "bars": bars, "runner": mfe >= RUNNER_R, "win": R > 0,
            "entry_t": int(r["entry_t"]), "macro": r["macro"], "dir": r["dir"], "block": b}

def passes(r, flt):
    if flt == "all": return True
    if flt == "with_macro": return r["setup_vs_macro"] == "with_macro"
    if flt == "with_macro+is_pullback": return r["setup_vs_macro"] == "with_macro" and r["is_pullback"] in ("True", True)
    if flt == "with_macro+virgin": return r["setup_vs_macro"] == "with_macro" and r["zone_virgin"] in ("True", True)
    return r["setup_vs_macro"] == "with_macro"

def agg(trs, label):
    if not trs: print(f"  [{label}] vazio"); return
    n = len(trs); w = sum(1 for t in trs if t["win"])
    sumR = sum(t["R"] for t in trs); sumRc = sum(max(-1.0, min(R_CAP, t["R"])) for t in trs)
    runners = sum(1 for t in trs if t["runner"]); avgRc = sumRc / n; medR = st.median([t["R"] for t in trs])
    trs_s = sorted(trs, key=lambda t: t["entry_t"]); eq = 0; peak = 0; maxdd = 0; streak = 0; maxstreak = 0
    for t in trs_s:
        eq += max(-1.0, min(R_CAP, t["R"])); peak = max(peak, eq); maxdd = min(maxdd, eq - peak)
        if t["R"] <= 0: streak += 1; maxstreak = max(maxstreak, streak)
        else: streak = 0
    span = (trs_s[-1]["entry_t"] - trs_s[0]["entry_t"]) / (7 * 86400) or 1
    print(f"  [{label}] n={n} WR={100*w/n:.0f}% medR={medR:+.2f} avgRc={avgRc:+.2f} sumRc={sumRc:+.1f} (raw{sumR:+.0f}) "
          f"run={runners}({100*runners/n:.0f}%) DDc={maxdd:.1f}R streakL={maxstreak} freq={n/span:.2f}/sem")

def leave_out(trs):
    """robustez: remove top-2 blocos (por sumRc) e top-5 trades (por R-capped); restate."""
    cap = lambda t: max(-1.0, min(R_CAP, t["R"]))
    by_blk = {}
    for t in trs: by_blk.setdefault(t["block"], []).append(t)
    blk_sum = sorted(by_blk, key=lambda b: sum(cap(t) for t in by_blk[b]), reverse=True)
    drop_blk = set(blk_sum[:2]); rem = [t for t in trs if t["block"] not in drop_blk]
    rem2 = sorted(rem, key=lambda t: cap(t), reverse=True)[5:]  # tira top-5 trades do restante
    s_all = sum(cap(t) for t in trs); s_b = sum(cap(t) for t in rem); s_b5 = sum(cap(t) for t in rem2)
    print(f"  leave-one-out (capped): full {s_all:+.0f}R (n{len(trs)}) | −top2blocos {s_b:+.0f}R (n{len(rem)}) | "
          f"−top2blocos−top5trades {s_b5:+.0f}R (n{len(rem2)}, avg{s_b5/max(1,len(rem2)):+.2f})")

def main():
    flt = sys.argv[1] if len(sys.argv) > 1 else "with_macro"
    rows = list(csv.DictReader(open(HERE / "candidates_annotated.csv")))
    trs = [outcome(r) for r in rows if passes(r, flt)]
    trs = [t for t in trs if t]
    print(f"=== EVAL ENGINE | filtro='{flt}' | SL estrutural + let-run trailing (HMAX={HMAX}, runner≥{RUNNER_R}R) ===")
    print(f"régua: runner-capture + DD/streak ANTES de WR (honest_note R1). Meta: 1-3/sem, WR50%, streak≤3, DD-funded.\n")
    print(f"(piso risco={MIN_RISK_ATR}xATR, R-cap={R_CAP}; medR=mediana, avgRc/sumRc/DDc=capped)\n")
    agg(trs, "GERAL"); leave_out(trs)
    print("\n BULL-long vs BEAR-short (estratégias DISTINTAS, não agregar — DA):")
    agg([t for t in trs if t["dir"] == "LONG"], "BULL-long")
    agg([t for t in trs if t["dir"] == "SHORT"], "BEAR-short")
    print("\n por BLOCO (estacionariedade / anti-beta):")
    for b in sorted(set(t["block"] for t in trs)):
        agg([t for t in trs if t["block"] == b], b[:21])

if __name__ == "__main__":
    main()
