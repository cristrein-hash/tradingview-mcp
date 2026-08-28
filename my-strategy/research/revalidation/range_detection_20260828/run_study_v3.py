#!/usr/bin/env python3
"""RANGE V3 — execução do MANIFEST_V3_PREREG (selado). Candidata contenção/sweeps vs GT humano;
baselines v5 atual e Layer1 no mesmo árbitro. py3.9 stdlib. SANITY_PROBE n/a: estudo prereg'd."""
import bisect
import json
import random
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parent
SEED = 20260828
W, CROSS_MIN, FSW_MIN, FAIL_D, ACC_ATR = 15, 3, 1, 3, 0.5
ENTER_D, EXIT_CROSS, EXIT_D = 2, 2, 3

# ---- diário causal a partir do RAW 4H ----
rows = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/raw_4h_ohlc.jsonl") if l.strip()]
rows.sort(key=lambda x: x["t"])
days = {}
for b in rows:
    d = b["t"] - (b["t"] % 86400)
    if d not in days:
        days[d] = dict(h=b["h"], l=b["l"], c=b["c"])
    else:
        days[d]["h"] = max(days[d]["h"], b["h"]); days[d]["l"] = min(days[d]["l"], b["l"]); days[d]["c"] = b["c"]
DK = sorted(days)
DH = [days[k]["h"] for k in DK]; DL = [days[k]["l"] for k in DK]; DC = [days[k]["c"] for k in DK]
DTR = [0.0] + [max(DH[i] - DL[i], abs(DH[i] - DC[i - 1]), abs(DL[i] - DC[i - 1])) for i in range(1, len(DK))]


def atrd(i):
    seg = DTR[max(1, i - 14):i]
    return sum(seg) / len(seg) if seg else 1.0


def vote(i):
    """vote_RANGE causal no fecho do dia i (janela [i-W+1, i])."""
    if i < W + W:
        return False
    a = i - W + 1
    hi, lo = max(DH[a:i + 1]), min(DL[a:i + 1])
    mid = (hi + lo) / 2
    cross = sum(1 for j in range(a + 1, i + 1) if (DC[j - 1] - mid) * (DC[j] - mid) < 0)
    at = atrd(i)
    fsw = 0
    for j in range(a, i + 1):                       # sweeps falhados, 2 lados, vs extremos dos 15d ANTERIORES a j
        ph = max(DH[j - W:j]); pl = min(DL[j - W:j])
        if DH[j] > ph:
            back = any(DC[k] < ph for k in range(j, min(i, j + FAIL_D) + 1))
            acc = any(DC[k] >= ph + ACC_ATR * at for k in range(j, i + 1))
            if back and not acc:
                fsw += 1
        if DL[j] < pl:
            back = any(DC[k] > pl for k in range(j, min(i, j + FAIL_D) + 1))
            acc = any(DC[k] <= pl - ACC_ATR * at for k in range(j, i + 1))
            if back and not acc:
                fsw += 1
    return cross >= CROSS_MIN and fsw >= FSW_MIN


def v3_states():
    votes = [vote(i) for i in range(len(DK))]
    st = []; cur = False; vt = 0; low_cross = 0
    for i in range(len(DK)):
        vt = vt + 1 if votes[i] else 0
        if not cur and vt >= ENTER_D:
            cur = True
        if cur:
            a = i - W + 1
            hi, lo = max(DH[a:i + 1]), min(DL[a:i + 1])
            at = atrd(i)
            mid = (hi + lo) / 2
            cross = sum(1 for j in range(a + 1, i + 1) if (DC[j - 1] - mid) * (DC[j] - mid) < 0)
            low_cross = low_cross + 1 if cross < EXIT_CROSS else 0
            if DC[i] > hi + ACC_ATR * at or DC[i] < lo - ACC_ATR * at or low_cross >= EXIT_D:
                cur = False; low_cross = 0
        st.append(cur)
    return st


PERIODS = json.load(open(HERE / "gt_human.json"))["periodos"]


def ep(s):
    return int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp())


def in_gt(t):
    return any(ep(p["ini"]) <= t < ep(p["fim"]) + 86400 for p in PERIODS)


def score(flag_at, name):
    """flag_at(k)->bool RANGE no dia DK[k]. Mede por período (deteção+lag) e por dia (recall/FP)."""
    span0, span1 = ep("2024-08-01"), ep("2026-08-28")
    ks = [k for k in range(len(DK)) if span0 <= DK[k] <= span1]
    tp = fn = fp = tn = 0
    for k in ks:
        f = flag_at(k)
        if in_gt(DK[k]):
            tp, fn = tp + (1 if f else 0), fn + (0 if f else 1)
        else:
            fp, tn = fp + (1 if f else 0), tn + (0 if f else 1)
    per = []
    for p in PERIODS:
        kk = [k for k in range(len(DK)) if ep(p["ini"]) <= DK[k] < ep(p["fim"]) + 86400]
        hit = next((k for k in kk if flag_at(k)), None)
        per.append(dict(p=p["name"], det=hit is not None,
                        lag_d=None if hit is None else round((DK[hit] - ep(p["ini"])) / 86400),
                        cob=round(sum(1 for k in kk if flag_at(k)) / len(kk), 2) if kk else None))
    rec = tp / (tp + fn) if tp + fn else None
    fpr = fp / (fp + tn) if fp + tn else None
    r = dict(recall=round(rec, 2), fp_fora=round(fpr, 2),
             bacc=round(((rec or 0) + (1 - (fpr or 0))) / 2, 2), periodos=per)
    print(f"  {name:<10} recall {r['recall']} · FP-fora {r['fp_fora']} · bacc {r['bacc']}")
    for q in per:
        print(f"     {q['p']:<18} det={q['det']} lag={q['lag_d']}d cobertura={q['cob']}")
    return r


def main():
    rnd = random.Random(SEED)
    res = {}
    print("=== V3 candidata (contenção/sweeps) vs GT humano ===")
    st = v3_states()
    res["v3"] = score(lambda k: st[k], "V3")

    # baselines no MESMO árbitro
    import runpy, io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ns = runpy.run_path(str(REPO / "my-strategy/research/revalidation/engine_4h_regime_gate_RAW.py"))
    reg = ns["regime_at"]
    print("=== baselines ===")
    res["v5"] = score(lambda k: reg(DK[k] + 14 * 3600) == "RANGE", "v5 atual")
    import sys
    sys.path.insert(0, str(REPO / "my-strategy/core/layer1_service"))
    sys.path.insert(0, str(REPO / "my-strategy/research/revalidation"))
    import layer1_cycle as LC
    import macro_structural_v3 as M
    xau = LC._merge_xau_1d()
    M.T = [b["t"] for b in xau]; M.O = [b["o"] for b in xau]; M.H = [b["h"] for b in xau]
    M.L = [b["l"] for b in xau]; M.C = [b["c"] for b in xau]; M.N = len(xau)
    dxy = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/raw_dxy_1d.jsonl") if l.strip()]
    M.DXY_K = [b["t"] + 86400 for b in dxy]; M.DXY_C = [b["c"] for b in dxy]
    T1d = M.T; lab = M.build_layer1()
    T1c = [t + 82800 for t in T1d]
    res["layer1"] = score(lambda k: lab[bisect.bisect_right(T1c, DK[k] + 86399) - 1] == "RANGE"
                          if bisect.bisect_right(T1c, DK[k] + 86399) >= 1 else False, "Layer1")

    # null persistente com fração ON da V3 no span
    span0, span1 = ep("2024-08-01"), ep("2026-08-28")
    ks = [k for k in range(len(DK)) if span0 <= DK[k] <= span1]
    frac = sum(1 for k in ks if st[k]) / len(ks)
    baccs = []
    for _ in range(300):
        state = rnd.random() < frac; tp = fn = fp = tn = 0
        for k in ks:
            if rnd.random() < 1 / 20:
                state = rnd.random() < frac
            if in_gt(DK[k]):
                tp, fn = tp + state, fn + (not state)
            else:
                fp, tn = fp + state, tn + (not state)
        baccs.append(((tp / (tp + fn) if tp + fn else 0) + (tn / (tn + fp) if tn + fp else 0)) / 2)
    baccs.sort()
    res["null"] = dict(med=round(baccs[150], 3), p95=round(baccs[285], 3),
                       p_ge=round(sum(1 for b in baccs if b >= res["v3"]["bacc"]) / 300, 3))
    print(f"null: med {res['null']['med']} · p95 {res['null']['p95']} · p(null>=V3) {res['null']['p_ge']}")

    # jackknife leave-one-period-out (recall médio dos restantes; FP-fora inalterado por construção)
    jk = {}
    for skip in [p["name"] for p in PERIODS]:
        tp = fn = 0
        for p in PERIODS:
            if p["name"] == skip:
                continue
            for k in range(len(DK)):
                if ep(p["ini"]) <= DK[k] < ep(p["fim"]) + 86400:
                    tp, fn = tp + st[k], fn + (not st[k])
        jk[skip] = round(tp / (tp + fn), 2) if tp + fn else None
    res["jackknife_recall_sem"] = jk
    print(f"jackknife (recall sem o período): {jk}")

    (HERE / "results_v3.json").write_text(json.dumps(res, indent=1, default=str))
    print("gravado results_v3.json")


if __name__ == "__main__":
    main()
