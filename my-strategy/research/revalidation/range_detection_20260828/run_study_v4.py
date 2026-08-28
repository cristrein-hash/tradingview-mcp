#!/usr/bin/env python3
"""RANGE V4 — execução do MANIFEST_V4_PREREG (banda ancorada). py3.9 stdlib.
SANITY_PROBE n/a: estudo prereg'd."""
import bisect
import json
import random
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parent
SEED = 20260828
W, WMIN, CROSS_MIN, FSW_MIN, FAIL_D, ACC_ATR = 15, 5, 3, 1, 3, 0.5
ENTER_D, EXIT_CROSS, EXIT_D = 2, 2, 3

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
N = len(DK)


def atrd(i):
    seg = DTR[max(1, i - 14):i]
    return sum(seg) / len(seg) if seg else 1.0


def build_states():
    """Passo único causal: level-shifts, voto ancorado, FSM com banda fixa na entrada."""
    anchor = 2 * W                                # início da janela ancorada (último level-shift)
    st = [False] * N
    cur = False; vt = 0; low_cross = 0; hi0 = lo0 = None
    votes_dbg = []
    for i in range(2 * W, N):
        at = atrd(i)
        # LEVEL-SHIFT: fecho além dos extremos da janela W ANTERIOR ao dia i, com margem 0.5 ATRd
        ph = max(DH[i - W:i]); pl = min(DL[i - W:i])
        if DC[i] > ph + ACC_ATR * at or DC[i] < pl - ACC_ATR * at:
            anchor = i
        a = max(anchor, i - W + 1)
        nwin = i - a + 1
        vote = False
        if nwin >= WMIN:
            hi, lo = max(DH[a:i + 1]), min(DL[a:i + 1])
            mid = (hi + lo) / 2
            cross = sum(1 for j in range(a + 1, i + 1) if (DC[j - 1] - mid) * (DC[j] - mid) < 0)
            fsw = 0
            for j in range(a, i + 1):
                jh = max(DH[j - W:j]); jl = min(DL[j - W:j])
                if DH[j] > jh:
                    back = any(DC[k] < jh for k in range(j, min(i, j + FAIL_D) + 1))
                    acc = any(DC[k] >= jh + ACC_ATR * at for k in range(j, i + 1))
                    if back and not acc: fsw += 1
                if DL[j] < jl:
                    back = any(DC[k] > jl for k in range(j, min(i, j + FAIL_D) + 1))
                    acc = any(DC[k] <= jl - ACC_ATR * at for k in range(j, i + 1))
                    if back and not acc: fsw += 1
            vote = cross >= CROSS_MIN and fsw >= FSW_MIN
        votes_dbg.append(vote)
        vt = vt + 1 if vote else 0
        if not cur and vt >= ENTER_D:
            cur = True
            hi0, lo0 = max(DH[a:i + 1]), min(DL[a:i + 1])   # banda ANCORADA na entrada
            low_cross = 0
        if cur:
            if DC[i] > hi0 + ACC_ATR * at or DC[i] < lo0 - ACC_ATR * at:
                cur = False                                  # aceitação REAL contra banda fixa
            else:
                mid0 = (hi0 + lo0) / 2
                a2 = max(0, i - W + 1)
                cross0 = sum(1 for j in range(a2 + 1, i + 1) if (DC[j - 1] - mid0) * (DC[j] - mid0) < 0)
                low_cross = low_cross + 1 if cross0 < EXIT_CROSS else 0
                if low_cross >= EXIT_D:
                    cur = False
        st[i] = cur
    return st


PERIODS = json.load(open(HERE / "gt_human.json"))["periodos"]


def ep(s):
    return int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp())


def in_gt(t):
    return any(ep(p["ini"]) <= t < ep(p["fim"]) + 86400 for p in PERIODS)


def main():
    rnd = random.Random(SEED)
    st = build_states()
    span0, span1 = ep("2024-08-01"), ep("2026-08-28")
    ks = [k for k in range(N) if span0 <= DK[k] <= span1]

    tp = fn = fp = tn = 0
    for k in ks:
        f = st[k]
        if in_gt(DK[k]):
            tp, fn = tp + f, fn + (not f)
        else:
            fp, tn = fp + f, tn + (not f)
    rec = tp / (tp + fn); fpr = fp / (fp + tn)
    frac_on = sum(1 for k in ks if st[k]) / len(ks)
    res = dict(recall=round(rec, 2), fp_fora=round(fpr, 2), bacc=round((rec + 1 - fpr) / 2, 3),
               frac_on=round(frac_on, 2))
    print(f"V4: recall {res['recall']} · FP-fora {res['fp_fora']} · bacc {res['bacc']} · ON {res['frac_on']:.0%} do tempo")

    per = []
    for p in PERIODS:
        kk = [k for k in range(N) if ep(p["ini"]) <= DK[k] < ep(p["fim"]) + 86400]
        hit = next((k for k in kk if st[k]), None)
        epis = sum(1 for x, k in enumerate(kk) if st[k] and (x == 0 or not st[kk[x - 1]]))
        per.append(dict(p=p["name"], det=hit is not None,
                        lag=None if hit is None else round((DK[hit] - ep(p["ini"])) / 86400),
                        cob=round(sum(1 for k in kk if st[k]) / len(kk), 2), episodios=epis))
        q = per[-1]
        print(f"  {q['p']:<18} det={q['det']} lag={q['lag']}d cob={q['cob']} episodios_ON={q['episodios']}")
    res["periodos"] = per

    # blocos FP >=5d + teste de overcall (limiar 30% dos dias-em-bloco com |net15|>=3 ATRd)
    blocks = []
    run = None
    for k in ks:
        if st[k] and not in_gt(DK[k]):
            if run is None: run = [k, k]
            else: run[1] = k
        else:
            if run and run[1] - run[0] + 1 >= 5: blocks.append(tuple(run))
            run = None
    if run and run[1] - run[0] + 1 >= 5: blocks.append(tuple(run))
    hot = tot = 0
    binfo = []
    for a, b in blocks:
        nd = b - a + 1; tot += nd
        nets = [abs(DC[k] - DC[k - 15]) / atrd(k) for k in range(a, b + 1) if k >= 15]
        h = sum(1 for x in nets if x >= 3.0); hot += h
        binfo.append(dict(ini=dt.datetime.utcfromtimestamp(DK[a]).strftime("%y-%m-%d"),
                          dias=nd, net_ini=round(nets[0], 1) if nets else None, dias_trend=h))
    res["fp_blocos"] = binfo
    res["overcall_pct_dias_trend"] = round(100 * hot / tot) if tot else 0
    print(f"blocos FP>=5d: {len(blocks)} · dias em trend forte {hot}/{tot} ({res['overcall_pct_dias_trend']}%)")
    for x in binfo: print("   ", x)

    # NULL POR PERÍODO: episódios ON reais realocados sem sobreposição, 300 reps
    epis_on = []
    run = None
    for k in ks:
        if st[k]:
            if run is None: run = [k, k]
            else: run[1] = k
        else:
            if run: epis_on.append(run[1] - run[0] + 1); run = None
    if run: epis_on.append(run[1] - run[0] + 1)
    real_det = sum(1 for q in per if q["det"])
    real_lag = sorted(q["lag"] for q in per if q["lag"] is not None)
    real_lag = real_lag[len(real_lag) // 2] if real_lag else None
    ge = 0
    for _ in range(300):
        flags = [False] * len(ks)
        for ln in epis_on:
            for _try in range(50):
                s = rnd.randint(0, len(ks) - ln)
                if not any(flags[s:s + ln]):
                    for x in range(s, s + ln): flags[x] = True
                    break
        det = 0; lags = []
        for p in PERIODS:
            kk = [x for x, k in enumerate(ks) if ep(p["ini"]) <= DK[k] < ep(p["fim"]) + 86400]
            hit = next((x for x in kk if flags[x]), None)
            if hit is not None:
                det += 1; lags.append((DK[ks[hit]] - ep(p["ini"])) / 86400)
        lm = sorted(lags)[len(lags) // 2] if lags else 99
        if det >= real_det and lm <= (real_lag if real_lag is not None else 99):
            ge += 1
    res["null_periodo"] = dict(p=round(ge / 300, 3), det_real=real_det, lag_med_real=real_lag,
                               episodios_on=len(epis_on))
    print(f"null-por-período: p(null>= {real_det}/5 com lag<={real_lag}d) = {res['null_periodo']['p']} · episódios ON {len(epis_on)}")

    # jackknife leave-one-period-out
    jk = {}
    for skip in [p["name"] for p in PERIODS]:
        t2 = f2 = 0
        for p in PERIODS:
            if p["name"] == skip: continue
            for k in range(N):
                if ep(p["ini"]) <= DK[k] < ep(p["fim"]) + 86400:
                    t2, f2 = t2 + st[k], f2 + (not st[k])
        jk[skip] = round(t2 / (t2 + f2), 2) if t2 + f2 else None
    res["jackknife"] = jk
    print(f"jackknife recall sem período: {jk}")

    (HERE / "results_v4.json").write_text(json.dumps(res, indent=1, default=str))
    print("gravado results_v4.json")


if __name__ == "__main__":
    main()
