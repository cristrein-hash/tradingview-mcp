#!/usr/bin/env python3
"""TESTE B — separacao por CONVERGENCIA (NAO fator isolado) no corpus 276: RUNNERS (mfe>=10, n=30) vs STOPPERS
(stop_before_2R & mfe<1.5, n=168). 4 vozes: (1) buy-bubble cluster no fundo [RAW], (2) regime nao-BEAR [v3 asof],
(3) snapshot VA [f6 svp_state/dist_poc], (4) f1_swept_low_reclaim [DSPA engine, flexivel por-trade]. Mede se a
CONVERGENCIA (nº de vozes alinhadas) separa — e cada voz como contexto secundario. CALIBRACAO dentro dos 276
(canon: validacao mora dentro dos 276), NAO regra/gate/score promovido. Read-only. Verified 2026-06-24."""
import gzip, json, datetime as dt, csv, collections

SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
RR = "repro_recovery"; BAR = 14400
F = [json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
OUT = {int(r["bar_idx"]): r for r in csv.DictReader(open("results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
DSPA = {int(r["bar_idx"]): r for r in csv.DictReader(open("results/l2_bpt_dspa_path_features_276.csv")) if r.get("bar_idx")}
# regime v3 asof
REG = "../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl"
import bisect
def toep(s):
    try: return int(dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
    except Exception:
        return int(dt.datetime.strptime(str(s)[:10], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
rb = [json.loads(l) for l in open(REG) if json.loads(l).get("ts")]
for r in rb: r["_ep"] = toep(r["ts"])
rb.sort(key=lambda r: r["_ep"]); rbt = [r["_ep"] for r in rb]
def v3_asof(et):
    k = bisect.bisect_right(rbt, et) - 1
    return rb[k].get("raw_state") if k >= 0 else None


def pv(s):
    if s is None: return 0
    s = str(s).replace(" ", "").replace(" ", "").replace(",", "").strip()
    m = 1.0
    if s[-1:] in ("K", "M", "B"): m = {"K": 1e3, "M": 1e6, "B": 1e9}[s[-1]]; s = s[:-1]
    try: return float(s) * m
    except Exception: return 0


def to_ep(t):
    t = float(t); return int(t / 1000) if t > 1e11 else int(t)


# label
RUN = [b for b in OUT if float(OUT[b]["mfe_R"]) >= 10]
STO = [b for b in OUT if OUT[b]["stop_before_2R"] == "1" and float(OUT[b]["mfe_R"]) < 1.5]
SEL = sorted(set(RUN + STO))
ENTRY = {b: int(F[b]["ts_epoch"]) for b in SEL}

# bubbles por barra (1 passada no gz; guarda buy/sell por asof_t)
bub = {}
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if '"activations_per_plot"' not in line: continue
        rec = json.loads(line); oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
        if not isinstance(last, dict): continue
        at = to_ep(last.get("time"))
        if at is None or at in bub: continue
        g = next((x for x in (rec.get("pine_shapes_bubbles") or []) if "Bubble" in str(x.get("name", ""))), {})
        a = g.get("activations_per_plot") or {}
        bub[at] = (sum(pv(a.get(f"plot_{i}")) for i in (0, 2, 4)), sum(pv(a.get(f"plot_{i}")) for i in (6, 8, 10)))
bt = sorted(bub)


def buy_bottom(b):
    et = ENTRY[b]; w = [t for t in bt if t <= et][-8:]
    return sum(bub[t][0] for t in w), sum(bub[t][1] for t in w)


rows = []
for b in SEL:
    d = DSPA.get(b, {}); o = OUT.get(b, {})
    buy8, sell8 = buy_bottom(b)
    v3 = v3_asof(ENTRY[b])
    # 4 vozes bullish (1/0)
    voice_bub = 1 if buy8 >= 8 else 0                                   # cluster de buy bubbles no fundo
    voice_reg = 1 if (v3 and v3 != "BEAR") else 0                       # regime nao-BEAR
    sst = d.get("f6_svp_state"); dpoc = d.get("f6_dist_poc_atr")
    voice_snap = 1 if (sst == "ACCEPTING_ABOVE_VALUE" or (dpoc not in (None, "") and float(dpoc) > 0)) else 0  # snapshot acceptance
    voice_sweep = 1 if str(d.get("f1_swept_low_reclaim")).lower() in ("1", "true", "yes") else 0  # liquidity sweep+reclaim
    conv = voice_bub + voice_reg + voice_snap + voice_sweep
    lab = "RUNNER" if b in RUN else "STOPPER"
    rows.append({"b": b, "lab": lab, "mfe": float(o["mfe_R"]), "conv": conv,
                 "vbub": voice_bub, "vreg": voice_reg, "vsnap": voice_snap, "vsweep": voice_sweep, "buy8": buy8})

nR = sum(1 for r in rows if r["lab"] == "RUNNER"); nS = sum(1 for r in rows if r["lab"] == "STOPPER")
print(f"TESTE B (CONVERGENCIA) — corpus 276 | RUNNERS(mfe>=10)={nR} STOPPERS(stop<2R & mfe<1.5)={nS}\n")
print("=== CONVERGENCIA (nº de vozes alinhadas 0-4) x runner-rate ===")
print(f"{'conv':>4} | {'n':>3} | {'RUN':>4} | {'STO':>4} | {'runner-rate':>11} | {'mean mfe':>8}")
base = nR / (nR + nS)
for c in range(4, -1, -1):
    g = [r for r in rows if r["conv"] == c]
    if not g: continue
    r_ = sum(1 for r in g if r["lab"] == "RUNNER")
    print(f"{c:>4} | {len(g):>3} | {r_:>4} | {len(g)-r_:>4} | {r_/len(g):>10.0%} | {sum(r['mfe'] for r in g)/len(g):>8.1f}")
print(f"\nbase runner-rate = {base:.0%}")
# convergencia alta (>=3) vs baixa (<=1)
hi = [r for r in rows if r["conv"] >= 3]; lo = [r for r in rows if r["conv"] <= 1]
rh = sum(1 for r in hi if r["lab"] == "RUNNER") / max(1, len(hi)); rl = sum(1 for r in lo if r["lab"] == "RUNNER") / max(1, len(lo))
print(f"CONVERGENCIA>=3: runner-rate {rh:.0%} ({len(hi)} ep) vs CONVERGENCIA<=1: {rl:.0%} ({len(lo)} ep) | lift={rh/max(0.01,rl):.2f}x")
print("\n=== cada voz isolada (CONTEXTO secundario, NAO o teste principal) ===")
for v, nm in (("vbub", "buy-bubble cluster"), ("vreg", "regime nao-BEAR"), ("vsnap", "snapshot acceptance"), ("vsweep", "f1 sweep+reclaim")):
    on = [r for r in rows if r[v] == 1]; off = [r for r in rows if r[v] == 0]
    ron = sum(1 for r in on if r["lab"] == "RUNNER") / max(1, len(on)); roff = sum(1 for r in off if r["lab"] == "RUNNER") / max(1, len(off))
    print(f"  {nm:>22}: ON runner-rate {ron:.0%} (n={len(on)}) vs OFF {roff:.0%} (n={len(off)}) | lift {ron/max(0.01,roff):.2f}x")
json.dump(rows, open("results/l2_bpt_confluence_corpus_test.json", "w"), indent=1)
print("\nCALIBRACAO dentro dos 276 (nao validacao OOS; canon). NAO vira regra/gate/score.")
