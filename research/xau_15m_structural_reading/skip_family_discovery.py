#!/usr/bin/env python3
"""FASE 2 — SKIP FAMILY DISCOVERY LEDGER (prereg XAU_15M_SKIP_FAMILY_DISCOVERY_PREREG.md, GO Cris).
Leitura DINÂMICA multi-fatorial: 5 famílias de SKIP medidas ISOLADAS (contexto+trajetória+estrutura
acima+autoridade de região+posição no range) sobre a base causal live-fireable n=166 (outcomes 3R
reais) — nunca eixo único, nunca snapshot, dois objetivos (cortar losers SEM matar winners), null
episódico estratificado, calibração declarada (base estudada; janela virgem 2024-25 reservada).
MEDIDOR: valores contínuos + marcações DESCRITIVAS declaradas (cláusulas pré-registadas/validadas
onde existem: S1 pos384>0,70 [prereg D1-D3]; S2a BEAR & px1d>=0 [filtro capitulation VALIDADO];
S5 fora do terço inferior [régua 4H do Cris]; S2b/S3 quartil/contagem DECLARADOS como descrição) —
NUNCA regra. Sem entry, sem backtest novo (outcomes já existem na base), sem composto."""
import json, csv, sys, bisect, random, hashlib, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0]/"xau_15m_structural_leg_engine"))
from f1_structural_leg_machine import Data
BASE_CSV = HERE.parents[0]/"xau_15m_bb_nas_leonardo/reports/xau_15m_live_fireable_candidates.csv"
REG4 = HERE.parents[0]/"xau_15m_structural_leg_engine/results/a2_regions_r4.jsonl"
EVT4 = HERE.parents[0]/"xau_15m_structural_leg_engine/results/a2_events_r4.jsonl"
random.seed(20260709)
K_BOUNCE = 1.5   # herdado do D3 (congelado)

def sha16(p):
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    return h

def build_episodes(D):
    """episódios macro (runs de macro_at) com extremos RUNNING por barra (causal)."""
    n = len(D.TS)
    epis = []; cur = None
    for i in range(n):
        m = D.macro_at(D.TS[i])
        if cur is None or m != cur["regime"]:
            if cur is not None:
                cur["t_end"] = D.TS[i]; epis.append(cur)
            cur = {"regime": m, "t_start": D.TS[i], "bot": D.L[i], "top": D.H[i],
                   "run": [(D.TS[i], D.L[i], D.H[i])]}
        else:
            cur["bot"] = min(cur["bot"], D.L[i]); cur["top"] = max(cur["top"], D.H[i])
            cur["run"].append((D.TS[i], cur["bot"], cur["top"]))
        # compactar run: só precisamos de lookup por t -> (bot_sofar, top_sofar); manter lista
    if cur is not None:
        cur["t_end"] = None; epis.append(cur)
    return epis

def episode_at(epis, t):
    for e in epis:
        if e["t_start"] <= t and (e["t_end"] is None or t < e["t_end"]):
            return e
    return None

def running_bounds(e, t):
    lo = None; hi = None
    for (tt, b, tp) in e["run"]:
        if tt > t: break
        lo, hi = b, tp
    return lo, hi

def bounce_peaks(D, j_hi, i):
    """picos dos bounces (K=1,5 ATR) em [j_hi, i]: lista de (peak_px). Causal."""
    run_lo = D.L[j_hi]; armed = False; peak = None; peaks = []
    for k in range(j_hi, i+1):
        a = D.ATR[k] or 5.0
        if D.L[k] < run_lo:
            if armed and peak is not None:
                peaks.append(peak)
            armed = False; peak = None; run_lo = D.L[k]
        elif (D.C[k]-run_lo)/a >= K_BOUNCE:
            armed = True
            peak = max(peak or 0.0, D.H[k])
        elif armed:
            peak = max(peak or 0.0, D.H[k])
    return peaks

def main():
    D = Data()
    epis = build_episodes(D)
    # regiões A2 r=4 + timeline de invalidação (autoridade S4)
    regions = [json.loads(l) for l in open(REG4)]
    inval_at = {}
    for l in open(EVT4):
        e = json.loads(l)
        if e["event"] == "invalidated": inval_at[e["region_id"]] = e["known_at"]
    bt_regions = [r for r in regions if r["kind"] == "BOTTOM"]
    # EMA21 1D price-agg (S2a, variante RAW-clean do filtro validado)
    ema = []; k21 = 2/22; e = D.DC[0]
    for v in D.DC: e = v*k21+e*(1-k21); ema.append(e)
    def px1d(t, px, a):
        di = bisect.bisect_left(D.DK, t//86400)-1
        return (px-ema[di])/(a or 5) if di >= 0 else None
    rows = []
    cands = list(csv.DictReader(open(BASE_CSV)))
    assert len(cands) == 166, f"base != 166: {len(cands)}"
    for c in cands:
        t = int(c["t"]); px = float(c["ent"]); out = int(c["out"])
        i = bisect.bisect_right(D.TS, t)-1
        a = D.ATR[i] or 5.0
        w0 = max(0, i-384)
        hi384 = max(D.H[w0:i+1]); lo384 = min(D.L[w0:i+1])
        j_hi = w0 + max(range(i+1-w0), key=lambda k: D.H[w0+k])
        lo_since = min(D.L[j_hi:i+1])
        dev = (hi384-lo_since)/a; rng384 = (hi384-lo384)/a
        pos384 = (px-lo384)/(hi384-lo384) if hi384 > lo384 else None
        w96 = max(0, i-96)
        h96 = max(D.H[w96:i]); l96 = min(D.L[w96:i])
        pos96 = (px-l96)/(h96-l96) if h96 > l96 else None
        net384 = (D.C[i]-D.C[w0])/a
        ep = episode_at(epis, t)
        macro = ep["regime"] if ep else None
        closed = [x for x in epis if x["t_end"] is not None and x["t_end"] <= t]
        prev_ep = closed[-1] if closed else None
        prev_rng = next((x for x in reversed(closed) if x["regime"] == "RANGE"), None)
        # S3 — estrutura acima (picos de bounce desde o high-384)
        pks = bounce_peaks(D, j_hi, i)
        ndesc = 0
        for kk in range(len(pks)-1, 0, -1):
            if pks[kk] < pks[kk-1]: ndesc += 1
            else: break
        peak_trend_down = int(len(pks) >= 2 and pks[-1] < pks[-2])
        # S4 — autoridade da região A2 que cobre px em t (ativa)
        cover = None
        for r in bt_regions:
            ia = inval_at.get(r["region_id"])
            if r["known_at"] < t and (ia is None or ia > t) and r["price_low"] <= px <= r["price_high"]:
                if cover is None or r["known_at"] > cover["known_at"]: cover = r
        s4 = {"s4_covered": int(cover is not None), "s4_age_bars": None, "s4_same_episode": None,
              "s4_n_retests": None}
        if cover is not None:
            s4 = {"s4_covered": 1, "s4_age_bars": (t-cover["known_at"])//900,
                  "s4_same_episode": int(ep is not None and cover["known_at"] >= ep["t_start"]),
                  "s4_n_retests": cover["n_retests"]}
        # S5 — posição no episódio RANGE corrente (bounds RUNNING em t, causal)
        s5_pos = None
        if macro == "RANGE" and ep is not None:
            lo_e, hi_e = running_bounds(ep, t)
            if lo_e is not None and hi_e > lo_e:
                s5_pos = (px-lo_e)/(hi_e-lo_e)
        row = {"t": t, "d": c["d"], "out": out, "regime_csv": c["regime"], "macro": macro,
               "S1_pos384": round(pos384, 2), "S1_pos96": round(pos96, 2) if pos96 is not None else None,
               "S1_ratio": round(dev/rng384, 2) if rng384 > 0 else None,
               "S1_net384_atr": round(net384, 1),
               "S2a_px1d_atr": round(px1d(t, px, a), 1),
               "S2b_dist_prev_ep_bot": round((px-prev_ep["bot"])/a, 1) if prev_ep else None,
               "S2b_dist_prev_rng_bot": round((px-prev_rng["bot"])/a, 1) if prev_rng else None,
               "S3_n_bounces": len(pks), "S3_n_desc_peaks": ndesc, "S3_peak_trend_down": peak_trend_down,
               **s4, "S5_pos_in_range": round(s5_pos, 2) if s5_pos is not None else None}
        # ---- marcações DESCRITIVAS (declaradas; nunca regra) ----
        row["F_S1"] = int(pos384 is not None and pos384 > 0.70)
        row["F_S2a"] = int(macro == "BEAR" and row["S2a_px1d_atr"] is not None and row["S2a_px1d_atr"] >= 0)
        row["F_S3"] = int(macro == "BEAR" and ndesc >= 2)
        row["F_S4"] = int(cover is not None and s4["s4_same_episode"] == 0)
        row["F_S5"] = int(macro == "RANGE" and s5_pos is not None and s5_pos > 1/3)
        rows.append(row)
    # F_S2b: quartil descritivo DENTRO dos BEAR (declarado): quarto mais RASO (dist maior)
    bearr = [r for r in rows if r["macro"] == "BEAR" and r["S2b_dist_prev_ep_bot"] is not None]
    if bearr:
        q = sorted(r["S2b_dist_prev_ep_bot"] for r in bearr)[int(len(bearr)*0.75)]
        for r in rows:
            r["F_S2b"] = int(r["macro"] == "BEAR" and r["S2b_dist_prev_ep_bot"] is not None
                             and r["S2b_dist_prev_ep_bot"] >= q)
        s2b_q = q
    else:
        s2b_q = None
    # ---- sumários por família ----
    fams = ["F_S1", "F_S2a", "F_S2b", "F_S3", "F_S4", "F_S5"]
    def summ(f):
        m = [r for r in rows if r.get(f)]
        return {"marked": len(m), "losers_marked": sum(1 for r in m if r["out"] == 0),
                "winners_marked": sum(1 for r in m if r["out"] == 1),
                "by_macro": {g: sum(1 for r in m if r["macro"] == g) for g in ("BULL", "BEAR", "RANGE")}}
    summary = {f: summ(f) for f in fams}
    base = {"n": len(rows), "losers": sum(1 for r in rows if r["out"] == 0),
            "winners": sum(1 for r in rows if r["out"] == 1)}
    # overlap (Jaccard nos conjuntos marcados + interseção de losers)
    overlap = {}
    for x in range(len(fams)):
        for y in range(x+1, len(fams)):
            A = {r["t"] for r in rows if r.get(fams[x])}
            B = {r["t"] for r in rows if r.get(fams[y])}
            if A or B:
                overlap[f"{fams[x]}∩{fams[y]}"] = {
                    "jaccard": round(len(A & B)/len(A | B), 2) if (A | B) else None,
                    "both": len(A & B), "only_x": len(A-B), "only_y": len(B-A)}
    # redundância central S2a vs S2b (losers marcados)
    A = {r["t"] for r in rows if r.get("F_S2a") and r["out"] == 0}
    B = {r["t"] for r in rows if r.get("F_S2b") and r["out"] == 0}
    s2_redund = {"S2a_only_losers": len(A-B), "S2b_only_losers": len(B-A), "both": len(A & B)}
    # ---- null episódico estratificado por macro (permutação de outcomes, 2000x) ----
    nulls = {}
    for f in fams:
        obs = summary[f]["losers_marked"]
        if summary[f]["marked"] == 0: nulls[f] = None; continue
        cnt = 0; TRI = 2000
        strata = {}
        for r in rows: strata.setdefault(r["macro"], []).append(r)
        for _ in range(TRI):
            tot = 0
            for g, rs in strata.items():
                outs = [r["out"] for r in rs]; random.shuffle(outs)
                tot += sum(1 for r, o in zip(rs, outs) if r.get(f) and o == 0)
            if tot >= obs: cnt += 1
        nulls[f] = round(cnt/TRI, 4)
    out = {"prereg": "XAU_15M_SKIP_FAMILY_DISCOVERY_PREREG.md", "base_sha16": sha16(BASE_CSV),
           "base": base, "s2b_quartil_descritivo": s2b_q,
           "familias": summary, "nulls_p_estratificado": nulls,
           "overlap": overlap, "s2a_vs_s2b_losers": s2_redund,
           "note": "MEDIDOR + marcações descritivas — nunca regra; leitura = READER; caminho = CRIS"}
    (HERE/"results/skip_family_discovery_result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    with open(HERE/"results/skip_family_discovery_ledger.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows: w.writerow(r)
    print(json.dumps({k: v for k, v in out.items() if k != "overlap"}, indent=2, ensure_ascii=False))
    print("overlap pares-chave:")
    for k, v in overlap.items():
        if v["both"] > 0: print(" ", k, v)
    print("MEASURED_OK")

if __name__ == "__main__":
    main()
