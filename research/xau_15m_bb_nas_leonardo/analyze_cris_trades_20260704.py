#!/usr/bin/env python3
"""ANÁLISE PROFUNDA das 35 operações manuais do Cris (chart 15M, extraídas 2026-07-04).
Objetivo: engenharia reversa CAUSAL — o que uma estratégia deveria ler, sem lookahead, para
sinalizar estes trades. STATUS: EXPLORATORY_CALIBRATION (leitura, não validação).
Por trade: geometria (entry/SL/target do desenho) · matching com universo de flush-candidates ·
pertenças (base435 / Sistema A / FB2 fundo / FB1 teto / classes) · contexto causal na barra de
entrada (regime v5h, features do candidato casado OU recomputadas da série) · outcome sob NOSSO
exit (let-run com o SL DELE) e sob o PLANO DELE (target/SL primeiro-toque).
Fontes: results/cris_manual_trades_20260704.json + universo SELADO + engine real."""
import json, hashlib
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
TICK = 0.01

# ---- universo selado + engine ----
CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
Ubyt = sorted(U, key=lambda r: r["cj_t"])
ns = {"__name__": "e", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "e", "exec"), ns)
regime_h, PRIMK, cf_low, HMAX, RCAP = ns["regime_hourcausal"], ns["PRIMK"], ns["cf_low"], ns["HMAX"], ns["RCAP"]
ema_at = ns["ema_at"]

def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def sysA(r):
    return (r["g_v5h"] == "BULL" and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0) and r["g_knife"] == 0)
def fb2(r): return fv(r, "legpos60", 1) <= 0.25 and fv(r, "h1_pos", 1) <= 0.61

# séries globais (para features na barra de entrada e letrun)
def find_block(t):
    for k, pr in PRIMK.items():
        s = pr["series"]
        if s[0]["t"] <= t <= s[-1]["t"]: return k, s
    return None, None

def letrun_from(s, j0, entry, sl, atr):
    risk = entry - sl
    if risk <= 0: return None, None
    trail = sl; r1 = False; end = min(j0 + HMAX, len(s) - 1)
    for k in range(j0 + 1, end + 1):
        if s[k]["l"] <= trail: return max(-1.0, min(RCAP, (trail - entry) / risk)), k
        if (s[k]["h"] - entry) / risk >= 1: r1 = True
        if r1:
            sw = cf_low(s, k)
            if sw: trail = max(trail, sw - 0.1 * atr)
    return max(-1.0, min(RCAP, (s[end]["c"] - entry) / risk)), end

def plan_outcome(s, j0, entry, sl, tgt):
    """primeiro-toque target vs SL a partir de j0+1 (plano do Cris)."""
    for k in range(j0 + 1, len(s)):
        hit_sl = s[k]["l"] <= sl; hit_tp = s[k]["h"] >= tgt
        if hit_sl and hit_tp: return "AMBIGUO_same_bar", k
        if hit_sl: return "SL", k
        if hit_tp: return "TARGET", k
    return "OPEN", len(s) - 1

# ---- carrega os 35 ----
raw = json.load(open(HERE / "results" / "cris_manual_trades_20260704.json"))
trades = []
for sh in raw["shapes"]:
    if sh.get("name") != "long_position": continue
    p = sh["props"]; pts = p["points"]; props = p["properties"]
    entry = pts[0]["price"]; t0 = pts[0]["time"]
    sl = round(entry - props["stopLevel"] * TICK, 2)
    tgt = round(entry + props["profitLevel"] * TICK, 2)
    trades.append({"id": sh["id"], "t": t0, "entry": entry, "sl": sl, "tgt": tgt,
                   "risk": round(entry - sl, 2), "rr": round((tgt - entry) / (entry - sl), 2),
                   "dur_bars": (pts[1]["time"] - t0) // 900})
trades.sort(key=lambda x: x["t"])
print(f"CRIS TRADES: {len(trades)} LONGs · {dt.datetime.utcfromtimestamp(trades[0]['t']).date()} → "
      f"{dt.datetime.utcfromtimestamp(trades[-1]['t']).date()}")

# ---- análise por trade ----
NEAR_BARS = 12  # candidato flush com cj em até 3h antes do entry
rows_out = []
for i, tr in enumerate(trades, 1):
    bk, s = find_block(tr["t"])
    rec = dict(tr); rec["n"] = i
    rec["utc"] = dt.datetime.utcfromtimestamp(tr["t"]).strftime("%Y-%m-%d %H:%M")
    rec["regime"] = regime_h(tr["t"])
    if s is None:
        rec["note"] = "FORA da cobertura RAW"; rows_out.append(rec); continue
    tmap = {b["t"]: j for j, b in enumerate(s)}
    # barra de entrada = última barra com t <= t0
    ts = [b["t"] for b in s]
    import bisect
    j0 = bisect.bisect_right(ts, tr["t"]) - 1
    bar = s[j0]
    atr = bar.get("atr") or 1.0
    # matching com candidato do universo (cj_t em [t0 - NEAR*900, t0])
    cands = [r for r in Ubyt if tr["t"] - NEAR_BARS * 900 <= r["cj_t"] <= tr["t"]]
    m = min(cands, key=lambda r: tr["t"] - r["cj_t"]) if cands else None
    rec["cand_match"] = bool(m)
    if m:
        rec["cand_dt_bars"] = (tr["t"] - m["cj_t"]) // 900
        rec["in_base435"] = bool(m["g_in_base435"]) and m["g_v5h"] != "BEAR"
        rec["sysA"] = sysA(m); rec["fb2_fundo"] = fb2(m)
        rec["feat"] = {k: m.get(k) for k in ("legpos60", "legpos90", "h1_pos", "g_box96", "g_box480",
                       "n_supply_overhead", "in_demand", "htf_demand_any", "g_ema21_dist", "g_atr_spike",
                       "g_rec_speed", "reclaim_atr", "swept_prior_low", "g_rsi_div", "g_knife", "sell_bub_w", "buy_bub_w")}
    else:
        rec["in_base435"] = rec["sysA"] = rec["fb2_fundo"] = False
        C = [b["c"] for b in s]; L = [b["l"] for b in s]; H = [b["h"] for b in s]
        lo96 = min(L[max(0, j0 - 96):j0 + 1]); hi96 = max(H[max(0, j0 - 96):j0 + 1])
        lo480 = min(L[max(0, j0 - 480):j0 + 1]); hi480 = max(H[max(0, j0 - 480):j0 + 1])
        rec["feat_series"] = {
            "rsi": bar.get("rsi"), "ema21_dist_atr": round((bar["c"] - ema_at(C, j0, 21)) / atr, 2),
            "box96": round((bar["c"] - lo96) / ((hi96 - lo96) or atr), 3),
            "box480": round((bar["c"] - lo480) / ((hi480 - lo480) or atr), 3),
            "dist_last_flush_bars": None}
        flushes = [r["cj_t"] for r in Ubyt if r["block"] == bk and r["cj_t"] <= tr["t"]]
        if flushes: rec["feat_series"]["dist_last_flush_bars"] = (tr["t"] - flushes[-1]) // 900
    # outcomes
    Rlr, ek = letrun_from(s, j0, tr["entry"], tr["sl"], atr)
    rec["R_letrun_ourexit"] = round(Rlr, 2) if Rlr is not None else None
    oc, k2 = plan_outcome(s, j0, tr["entry"], tr["sl"], tr["tgt"])
    rec["plan_outcome"] = oc
    rec["plan_R"] = {"TARGET": tr["rr"], "SL": -1.0}.get(oc)
    rows_out.append(rec)

# ---- agregados ----
matched = [r for r in rows_out if r.get("cand_match")]
print(f"\nMATCHING: {len(matched)}/{len(rows_out)} têm candidato flush-low do universo em ≤{NEAR_BARS} barras antes")
print(f"  em base435: {sum(1 for r in rows_out if r.get('in_base435'))} · Sistema A: {sum(1 for r in rows_out if r.get('sysA'))} · "
      f"região FB2-fundo: {sum(1 for r in rows_out if r.get('fb2_fundo'))}")
from collections import Counter
print(f"  regimes v5h nas entradas: {dict(Counter(r['regime'] for r in rows_out))}")
pr = [r["plan_outcome"] for r in rows_out]
planR = [r["plan_R"] for r in rows_out if r.get("plan_R") is not None]
lrR = [r["R_letrun_ourexit"] for r in rows_out if r.get("R_letrun_ourexit") is not None]
print(f"\nOUTCOMES (plano do Cris, primeiro-toque): {dict(Counter(pr))} · sumR plano {sum(planR):+.1f} "
      f"(WR plano {100*sum(1 for x in planR if x>0)/max(1,len(planR)):.0f}%)")
print(f"OUTCOMES (nosso let-run com o SL dele): sumR {sum(lrR):+.1f} · WR {100*sum(1 for x in lrR if x>0)/max(1,len(lrR)):.0f}% "
      f"· runners R>=3: {sum(1 for x in lrR if x>=3)}")
print(f"RR médio planejado: {sum(t['rr'] for t in trades)/len(trades):.2f} · risco médio ${sum(t['risk'] for t in trades)/len(trades):.2f} "
      f"· duração desenhada média {sum(t['dur_bars'] for t in trades)/len(trades):.0f} barras")

def med(vals):
    v = sorted(x for x in vals if isinstance(x, (int, float))); return v[len(v) // 2] if v else None
if matched:
    print("\nPERFIL CAUSAL (medianas dos casados vs base435):")
    B = [r for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR"]
    for k in ("legpos60", "h1_pos", "g_box96", "g_box480", "n_supply_overhead", "g_ema21_dist",
              "g_atr_spike", "g_rec_speed", "reclaim_atr", "swept_prior_low", "in_demand"):
        mc = med([r["feat"].get(k) for r in matched])
        mb = med([fv(b, k) for b in B])
        print(f"  {k:<18} cris={mc}  base435={mb}")
unm = [r for r in rows_out if not r.get("cand_match")]
if unm:
    print(f"\nSEM CANDIDATO ({len(unm)}) — contexto por série:")
    for r in unm:
        print(f"  #{r['n']} {r['utc']} {r['regime']}: {json.dumps(r.get('feat_series'), ensure_ascii=False)}")

print("\nDETALHE POR TRADE:")
for r in rows_out:
    tags = []
    if r.get("in_base435"): tags.append("BASE")
    if r.get("sysA"): tags.append("SYSA")
    if r.get("fb2_fundo"): tags.append("FB2fundo")
    if not r.get("cand_match"): tags.append("SEM-FLUSH")
    print(f"  #{r['n']:>2} {r['utc']} {r['regime']:<5} entry {r['entry']:>8} risk ${r['risk']:>5} RR {r['rr']:>4} "
          f"| plano {r['plan_outcome']:<7} | letrun {r.get('R_letrun_ourexit')} | {'/'.join(tags) or '—'}")

json.dump(rows_out, open(HERE / "results" / "cris_trades_analysis_20260704.json", "w"), indent=1, ensure_ascii=False)
print("\nOK → results/cris_trades_analysis_20260704.json")
