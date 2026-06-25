#!/usr/bin/env python3
"""ELIMINATION SWEEP — fio vivo: skip-do-claramente-NAO-convergente melhora streak/winrate SEM cortar runner?
Computa CONVERGENCIA (mesmas 4 vozes do _DA_confluence_corpus_test) p/ TODOS os 276, ordem CRONOLOGICA, e
varre regras de ELIMINACAO. Metrica: trades removidos, RUNNERS removidos (mfe>=10, DEVE ser 0), WINNERS removidos
(capped_realR>0, idealmente ~0), winrate, maior sequencia perdedora (losing streak), sumR. Calibracao DENTRO dos
276 (canon), NAO regra/gate promovido. Read-only. Verified 2026-06-24."""
import gzip, json, datetime as dt, csv, bisect

SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
RR = "repro_recovery"
F = [json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
OUT = {int(r["bar_idx"]): r for r in csv.DictReader(open("results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
DSPA = {int(r["bar_idx"]): r for r in csv.DictReader(open("results/l2_bpt_dspa_path_features_276.csv")) if r.get("bar_idx")}
REG = "../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl"

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

SEL = sorted(OUT)  # TODOS os 276
ENTRY = {b: int(F[b]["ts_epoch"]) for b in SEL}

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
        bub[at] = sum(pv(a.get(f"plot_{i}")) for i in (0, 2, 4))
bt = sorted(bub)
def buy8(b):
    et = ENTRY[b]; w = [t for t in bt if t <= et][-8:]
    return sum(bub[t] for t in w)

rows = []
for b in SEL:
    d = DSPA.get(b, {}); o = OUT[b]
    v3 = v3_asof(ENTRY[b])
    vbub = 1 if buy8(b) >= 8 else 0
    vreg = 1 if (v3 and v3 != "BEAR") else 0
    sst = d.get("f6_svp_state"); dpoc = d.get("f6_dist_poc_atr")
    vsnap = 1 if (sst == "ACCEPTING_ABOVE_VALUE" or (dpoc not in (None, "") and float(dpoc) > 0)) else 0
    vsweep = 1 if str(d.get("f1_swept_low_reclaim")).lower() in ("1", "true", "yes") else 0
    rows.append({"b": b, "dt": o["datetime"], "conv": vbub + vreg + vsnap + vsweep,
                 "is_bear": 1 if v3 == "BEAR" else 0, "mfe": float(o["mfe_R"]),
                 "realR": float(o["capped_realR"]) if o.get("capped_realR") not in (None, "") else 0.0})
rows.sort(key=lambda r: r["dt"])

def stats(rs):
    n = len(rs); w = sum(1 for r in rs if r["realR"] > 0)
    sumR = sum(r["realR"] for r in rs)
    ls = mls = 0
    for r in rs:
        if r["realR"] < 0: ls += 1; mls = max(mls, ls)
        else: ls = 0
    return n, w, (w / n if n else 0), sumR, mls

bn, bw, bwr, bsum, bmls = stats(rows)
nrun = sum(1 for r in rows if r["mfe"] >= 10)
print(f"ELIMINATION SWEEP — 276 cronologico | BASELINE: n={bn} W={bw} WR={bwr:.0%} sumR={bsum:+.1f} maxLosingStreak={bmls} runners(mfe>=10)={nrun}\n")
print(f"{'regra de skip':>34} | {'rem':>4} | {'runRem':>6} | {'winRem':>6} | {'n':>3} | {'WR':>5} | {'sumR':>7} | {'maxLoseStreak':>13}")
RULES = [
    ("conv<=0 (nenhuma voz)", lambda r: r["conv"] <= 0),
    ("conv<=1 (<=1 voz)", lambda r: r["conv"] <= 1),
    ("regime BEAR (v3)", lambda r: r["is_bear"] == 1),
    ("conv<=1 OU BEAR", lambda r: r["conv"] <= 1 or r["is_bear"] == 1),
    ("conv<=1 E nao-aceito (snap off)", lambda r: r["conv"] <= 1),  # placeholder ref
]
for name, rule in RULES[:4]:
    removed = [r for r in rows if rule(r)]; kept = [r for r in rows if not rule(r)]
    runRem = sum(1 for r in removed if r["mfe"] >= 10); winRem = sum(1 for r in removed if r["realR"] > 0)
    n, w, wr, sumR, mls = stats(kept)
    print(f"{name:>34} | {len(removed):>4} | {runRem:>6} | {winRem:>6} | {n:>3} | {wr:>4.0%} | {sumR:>+7.1f} | {mls:>13}")
print(f"\nBASE p/ comparar: WR {bwr:.0%} | sumR {bsum:+.1f} | maxLoseStreak {bmls} | runners {nrun} (NENHUMA regra pode remover runner)")
print("Calibracao dentro dos 276 (nao OOS). NAO vira regra/gate. realR = capped_realR (exit OFICIAL capado).")
json.dump(rows, open("results/l2_bpt_elimination_sweep.json", "w"), indent=1)
