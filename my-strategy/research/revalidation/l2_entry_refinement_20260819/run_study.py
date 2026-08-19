#!/usr/bin/env python3
"""L2 ENTRY REFINEMENT — execução do prereg selado (MANIFEST_PREREG.md, commit edeca39).
P1 paridade fail-loud → H1 entrada-adiada FVG-1H (pareado, pontos+R, null, sub-janelas, jackknife)
→ H2 flip-2-barras. Reusa l2_engine (motor vivo) e a lógica FVG do AMD. py3.9 stdlib. Read-only."""
import csv
import json
import random
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
L2DIR = REPO / "my-strategy/strategies/xau_4h_long/reversal/L2_BPT_ZONE_TREND_EXIT"
sys.path.insert(0, str(L2DIR))
import l2_engine as E  # noqa: E402

RAW4 = REPO / "my-strategy/research/revalidation/raw_4h_ohlc.jsonl"
RAW1 = REPO / "my-strategy/research/revalidation/raw_1h_ohlc.jsonl"
REGUA = REPO / "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv"
OUT = Path(__file__).resolve().parent
COST = E.COST
MAX_DISC_RISK = 1.0          # prereg: desconto máximo 1×risk
NULL_REPS = 500
SEED = 20260819              # determinístico (sem Date.now)


def jl(p):
    return sorted((json.loads(l) for l in p.read_text().splitlines() if l.strip()), key=lambda x: x["t"])


def panel(rows, key):
    """Painel completo sobre lista de dicts com campo `key` (R ou pontos) ordenável por bi."""
    if not rows:
        return dict(N=0)
    n = len(rows)
    s = sum(x[key] for x in rows)
    w = sum(1 for x in rows if x[key] > 0)
    cum = peak = dd = 0.0
    stk = mx = 0
    for x in sorted(rows, key=lambda z: z["bi"]):
        cum += x[key]; peak = max(peak, cum); dd = min(dd, cum - peak)
        stk = stk + 1 if x[key] <= 0 else 0; mx = max(mx, stk)
    return dict(N=n, soma=round(s, 1), avg=round(s / n, 3), WR=round(100 * w / n),
                maxDD=round(dd, 1), retDD=(round(s / abs(dd), 1) if dd < 0 else None), streak=mx)


def year_of(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).year


def first_fvg_entry(h1, t0, t1, entry, risk):
    """Primeiro FVG-1H (lógica AMD long: gap_top=win[k].l > gap_bot=win[k-2].h) formado em [t0,t1]
    com gap_top<entry e desconto<=MAX_DISC_RISK*risk. Devolve (gap_top, k_index_global) ou None."""
    idx = [i for i, b in enumerate(h1) if t0 <= b["t"] <= t1]
    if len(idx) < 3:
        return None
    for k in range(2, len(idx)):
        a, c = h1[idx[k - 2]], h1[idx[k]]
        gap_bot, gap_top = a["h"], c["l"]
        if gap_top <= gap_bot:
            continue
        if gap_top < entry and (entry - gap_top) <= MAX_DISC_RISK * risk:
            return gap_top, idx[k]
    return None


def delayed_outcome(h1, level, k_form, t_exit, sl, exit_px):
    """Fill = 1ª barra 1H após formação com low<=level; depois SL-first no 1H até t_exit; senão sai exit_px.
    Devolve dict(filled, entry2, exit2, pts, R) — R do PRÓPRIO trade (risk2=entry2-sl)."""
    fill_i = None
    for i in range(k_form + 1, len(h1)):
        if h1[i]["t"] > t_exit:
            break
        if h1[i]["l"] <= level:
            fill_i = i
            break
    if fill_i is None:
        return dict(filled=False)
    entry2 = level
    risk2 = entry2 - sl
    if risk2 <= 0:
        return dict(filled=False)
    for i in range(fill_i, len(h1)):
        if h1[i]["t"] > t_exit:
            break
        if h1[i]["l"] <= sl:
            return dict(filled=True, entry2=entry2, exit2=sl, pts=sl - entry2, R=-1.0 - COST, stopped=True)
    return dict(filled=True, entry2=entry2, exit2=exit_px, pts=exit_px - entry2,
                R=(exit_px - entry2) / risk2 - COST, stopped=False)


def main():
    B4 = jl(RAW4)
    H1 = jl(RAW1)
    h1_min_t = H1[0]["t"]
    fsm = E.make_regime_fsm(B4)
    reg = fsm["run"](0.03, 1.15, 0.88)
    segs = E.prepare_segments(fsm["build_segments"](reg))
    sel_obj = E.make_selector(segs, fsm["T"], fsm["H"], fsm["L"])
    ex = E.make_trend_exit(B4, segs)
    T4, C4, L4 = ex["T"], ex["C"], ex["L"]

    RG = list(csv.DictReader(open(REGUA)))
    # ===== P1: PARIDADE FAIL-LOUD (gates do parity_trend_exit) =====
    rows_full = []
    for r in RG:
        bi, entry, sl = int(r["bar_idx"]), float(r["entry"]), float(r["sl"])
        d = ex["regime_flip_detail"](bi, entry, sl)
        d.update(entry=entry, sl=sl, risk=entry - sl, year=year_of(T4[bi]))
        d["exit_px"] = sl if d["mot"] == "STOP" else C4[d["exit_bar"]]
        d["pts"] = d["exit_px"] - entry
        rows_full.append(d)
    SEL17 = {int(r["bar_idx"]) for r in RG if sel_obj["keep_signal"](int(r["bar_idx"]), float(r["entry"]))[0]}
    rows_17 = [x for x in rows_full if x["bi"] in SEL17]
    s17 = round(sum(x["R"] for x in rows_17), 1)
    sF = round(sum(x["R"] for x in rows_full), 1)
    assert abs(s17 - 105.3) < 0.6, f"PARIDADE SELECT-17 FAIL {s17}"
    assert abs(sF - 399.2) < 0.6, f"PARIDADE FULL FAIL {sF}"
    print(f"P1 PARIDADE PASS · SELECT-17 sumR {s17} · FULL {sF}")

    # ===== H1: entrada adiada FVG-1H (só cobertura 1H) =====
    covered = [x for x in rows_full if T4[x["bi"]] >= h1_min_t]
    out_cov = len(rows_full) - len(covered)
    print(f"cobertura 1H: {len(covered)}/{len(rows_full)} trades (OUT_OF_1H_COVERAGE={out_cov})")

    paired, nofill, no_fvg, discounts = [], [], [], []
    for x in covered:
        t0, t1 = T4[x["bi"]], T4[x["exit_bar"]]
        fv = first_fvg_entry(H1, t0, t1, x["entry"], x["risk"])
        if fv is None:
            no_fvg.append(x)
            continue
        level, kf = fv
        o = delayed_outcome(H1, level, kf, t1, x["sl"], x["exit_px"])
        if not o.get("filled"):
            nofill.append(x)
            continue
        discounts.append(x["entry"] - level)
        paired.append(dict(bi=x["bi"], year=x["year"], mech_pts=x["pts"], mech_R=x["R"],
                           fvg_pts=o["pts"], fvg_R=o["R"], disc=x["entry"] - level,
                           sel17=x["bi"] in SEL17))
    print(f"H1: FVG elegível {len(paired) + len(nofill)}/{len(covered)} · fill {len(paired)} · "
          f"NO-FILL {len(nofill)} ({round(100 * len(nofill) / max(1, len(paired) + len(nofill)))}%) · sem-FVG {len(no_fvg)}")

    def h1_report(scope_name, rows):
        if not rows:
            print(f"  [{scope_name}] N=0")
            return None
        d_pts = sum(r["fvg_pts"] - r["mech_pts"] for r in rows)
        mech = panel([dict(bi=r["bi"], v=r["mech_pts"]) for r in rows], "v")
        fvg = panel([dict(bi=r["bi"], v=r["fvg_pts"]) for r in rows], "v")
        mR = panel([dict(bi=r["bi"], v=r["mech_R"]) for r in rows], "v")
        fR = panel([dict(bi=r["bi"], v=r["fvg_R"]) for r in rows], "v")
        wins = sum(1 for r in rows if r["fvg_pts"] > r["mech_pts"])
        print(f"  [{scope_name}] N={len(rows)} pareado: FVG melhor em {wins}/{len(rows)} · Δpts total {d_pts:+.1f}")
        print(f"    pontos  mech {mech} ")
        print(f"    pontos  fvg  {fvg}")
        print(f"    R-próprio mech {mR}")
        print(f"    R-próprio fvg  {fR}")
        return d_pts

    print("H1 PAINÉIS (pareado, só fills):")
    d_full = h1_report("FULL∩1H", paired)
    d_17 = h1_report("SELECT17∩1H", [r for r in paired if r["sel17"]])

    # combinado com NO-FILL=0 (o trade não aconteceu) vs mecânico dos MESMOS episódios
    all_h1 = paired + [dict(bi=x["bi"], year=x["year"], mech_pts=x["pts"], mech_R=x["R"],
                            fvg_pts=0.0, fvg_R=0.0, disc=None, sel17=x["bi"] in SEL17) for x in nofill]
    comb_mech = sum(r["mech_pts"] for r in all_h1)
    comb_fvg = sum(r["fvg_pts"] for r in all_h1)
    print(f"H1 COMBINADO (fills + no-fill=0): mech {comb_mech:+.1f}pts vs fvg {comb_fvg:+.1f}pts")

    # NULL desconto-igual
    rnd = random.Random(SEED)
    null_deltas = []
    base_rows = [x for x in covered if any(p["bi"] == x["bi"] for p in paired + nofill)]
    for _ in range(NULL_REPS):
        tot = 0.0
        for x in base_rows:
            d = rnd.choice(discounts)
            level = x["entry"] - d
            t0, t1 = T4[x["bi"]], T4[x["exit_bar"]]
            idx0 = next((i for i, b in enumerate(H1) if b["t"] >= t0), None)
            if idx0 is None:
                continue
            o = delayed_outcome(H1, level, idx0, t1, x["sl"], x["exit_px"])
            tot += (o["pts"] if o.get("filled") else 0.0) - x["pts"]
        null_deltas.append(tot)
    obs = comb_fvg - comb_mech
    rank = sum(1 for v in null_deltas if v < obs) / len(null_deltas)
    print(f"H1 NULL: Δ observado {obs:+.1f}pts · rank vs {NULL_REPS} nulls = {rank:.3f} "
          f"(null mediana {sorted(null_deltas)[len(null_deltas)//2]:+.1f})")

    # sub-janelas por ano + jackknife
    years = sorted({r["year"] for r in paired})
    print("H1 por-ano (Δpts pareado):", {y: round(sum(r['fvg_pts'] - r['mech_pts'] for r in paired if r['year'] == y), 1) for y in years})
    jk = {y: round(sum(r["fvg_pts"] - r["mech_pts"] for r in paired if r["year"] != y), 1) for y in years}
    print("H1 jackknife (Δpts sem o ano):", jk)

    # ===== H2: flip confirmado 2 barras (base completa) =====
    def flip2(bi, entry, sl):
        risk = entry - sl
        consec = 0
        N4 = ex["N"]
        for j in range(bi + 1, min(bi + E.CAP, N4 - 1) + 1):
            if L4[j] <= sl:
                return dict(bi=bi, R=-1.0 - COST, pts=sl - entry, mot="STOP")
            consec = consec + 1 if ex["regime_at"](j) == "BEAR" else 0
            if consec >= 2:
                return dict(bi=bi, R=(C4[j] - entry) / risk - COST, pts=C4[j] - entry, mot="BEAR2")
        ej = min(bi + E.CAP, N4 - 1)
        return dict(bi=bi, R=(C4[ej] - entry) / risk - COST, pts=C4[ej] - entry, mot="CAP")

    h2_full = [flip2(x["bi"], x["entry"], x["sl"]) for x in rows_full]
    h2_17 = [x for x in h2_full if x["bi"] in SEL17]
    print("H2 flip-2-barras vs baseline (R):")
    print(f"  FULL     base {panel(rows_full, 'R')}")
    print(f"  FULL     flip2 {panel(h2_full, 'R')}")
    print(f"  SELECT17 base {panel(rows_17, 'R')}")
    print(f"  SELECT17 flip2 {panel(h2_17, 'R')}")
    per_year_h2 = {}
    for x, b in zip(h2_full, rows_full):
        per_year_h2.setdefault(b["year"], [0.0, 0.0])
        per_year_h2[b["year"]][0] += b["R"]; per_year_h2[b["year"]][1] += x["R"]
    print("H2 por-ano (base→flip2 R):", {y: (round(a, 1), round(c, 1)) for y, (a, c) in sorted(per_year_h2.items())})

    # persist resultados brutos
    (OUT / "results_h1_paired.jsonl").write_text("\n".join(json.dumps(r) for r in paired) + "\n")
    (OUT / "results_summary.json").write_text(json.dumps(dict(
        paridade=dict(sel17=s17, full=sF), cobertura=dict(covered=len(covered), out=out_cov),
        h1=dict(fills=len(paired), nofill=len(nofill), sem_fvg=len(no_fvg),
                delta_pts_paired_full=d_full, delta_pts_paired_sel17=d_17,
                comb_mech_pts=round(comb_mech, 1), comb_fvg_pts=round(comb_fvg, 1),
                null_rank=rank, jackknife=jk),
        h2=dict(full_base=panel(rows_full, "R"), full_flip2=panel(h2_full, "R"),
                sel17_base=panel(rows_17, "R"), sel17_flip2=panel(h2_17, "R"))), indent=1))
    print("resultados gravados em", OUT)


if __name__ == "__main__":
    main()
