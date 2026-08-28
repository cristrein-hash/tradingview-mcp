#!/usr/bin/env python3
"""RANGE V2 — execução do prereg MANIFEST_V2_PREREG (unlock de BEAR). Source-patch do FSM do motor
real; GT-v2 com ATR-d real + duração mínima 2d. py3.9 stdlib. SANITY_PROBE n/a: estudo prereg'd."""
import json
import random
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parent
ENG = REPO / "my-strategy/research/revalidation/engine_4h_regime_gate_RAW.py"
SEED = 20260828
KGT, W_ATR, NET_FRAC, MIN_SEG = 30, 4.0, 0.40, 12
N_UNLOCK = 10

FSM_ORIG = """stable=[]; cur="RANGE"; pend=None; pn=0
for v in rawS:
    if v==cur: pend=None; pn=0
    elif v==pend: pn+=1
    else: pend=v; pn=1
    need=Kbear if pend=="BEAR" else K
    if pn>=need: cur=pend; pend=None; pn=0
    stable.append(cur)"""

FSM_V2 = """stable=[]; cur="RANGE"; pend=None; pn=0
def _bl(j): return j>=17 and DC[j]<min(DL[j-15:j-2])
for _iv,v in enumerate(rawS):
    if v==cur: pend=None; pn=0
    elif v==pend: pn+=1
    else: pend=v; pn=1
    need=Kbear if pend=="BEAR" else K
    if pn>=need: cur=pend; pend=None; pn=0
    if cur=="BEAR" and _iv>=41 and DC[_iv]>=E50[_iv] and not any(_bl(j) for j in range(_iv-9,_iv+1)):
        cur="RANGE"; pend=None; pn=0   # V2 UNLOCK: 10d sem novo-low estrutural + fecho>=E50
    stable.append(cur)"""


def load_engine(patched):
    import runpy, tempfile, io, contextlib
    src = ENG.read_text()
    assert FSM_ORIG in src, "âncora FSM não encontrada — motor mudou"
    if patched:
        src = src.replace(FSM_ORIG, FSM_V2, 1)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir=str(HERE)) as f:
        f.write(src); tmp = f.name
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ns = runpy.run_path(tmp)
    Path(tmp).unlink()
    return ns


def main():
    rnd = random.Random(SEED)
    ns1 = load_engine(True)      # patched PRIMEIRO (side-effect: original por último restaura artefacto)
    ns0 = load_engine(False)
    T4 = ns0["TS4"]; H4 = ns0["H4"]; C4 = ns0["C4"]
    L4 = [b["l"] for b in ns0["B4"]]
    DK, DH, DL, DC = ns0["DK"], ns0["DH"], ns0["DL"], ns0["DC"]
    atrd = ns0["atrd"]
    import bisect
    print(f"RAW 4H {len(T4)} barras · diário {len(DK)}")

    # GT-v2: ATR-d REAL (atrd do resample do motor, as-of dia anterior ao dia da barra 4H)
    gt = []
    for i in range(len(T4)):
        if i < KGT + 90:
            gt.append(None); continue
        di = bisect.bisect_right(DK, T4[i] - (T4[i] % 86400)) - 1
        a = atrd(max(15, di - 1))
        w = max(H4[i - KGT:i + 1]) - min(L4[i - KGT:i + 1])
        net = abs(C4[i] - C4[i - KGT])
        gt.append("RANGE" if (w / a <= W_ATR and net <= NET_FRAC * w) else "TREND")
    # duração mínima: segmentos RANGE <12 barras viram TREND
    i = 0
    while i < len(gt):
        if gt[i] == "RANGE":
            j = i
            while j < len(gt) and gt[j] == "RANGE":
                j += 1
            if j - i < MIN_SEG:
                for k in range(i, j):
                    gt[k] = "TREND"
            i = j
        else:
            i += 1
    n_r = sum(1 for g in gt if g == "RANGE"); n_t = sum(1 for g in gt if g == "TREND")
    segs = []
    for i, g in enumerate(gt):
        if g == "RANGE" and (i == 0 or gt[i - 1] != "RANGE"):
            segs.append([i, i])
        elif g == "RANGE":
            segs[-1][1] = i
    print(f"GT-v2: RANGE {n_r} ({n_r/(n_r+n_t):.0%}) · segmentos {len(segs)} · dur mediana "
          f"{sorted(b-a+1 for a,b in segs)[len(segs)//2] if segs else None} barras")

    def confusion(det_at, name):
        tp = fp = fn = tn = 0
        for i, g in enumerate(gt):
            if g is None: continue
            isr = det_at(i) == "RANGE"
            if g == "RANGE" and isr: tp += 1
            elif g == "RANGE": fn += 1
            elif isr: fp += 1
            else: tn += 1
        prec = tp / (tp + fp) if tp + fp else None
        rec = tp / (tp + fn) if tp + fn else None
        bacc = ((tp / (tp + fn) if tp + fn else 0) + (tn / (tn + fp) if tn + fp else 0)) / 2
        lags = [next((i - a for i in range(a, b + 1) if det_at(i) == "RANGE"), None) for a, b in segs]
        det = sum(1 for l in lags if l is not None)
        lm = sorted(l for l in lags if l is not None)
        r = dict(prec=round(prec, 2) if prec else None, rec=round(rec, 2) if rec else None,
                 bacc=round(bacc, 3), segs=f"{det}/{len(segs)}",
                 lag_med_4h=lm[len(lm) // 2] if lm else None)
        print(f"  {name:<14} {r}")
        return r

    print("\n=== CONFUSÃO vs GT-v2 ===")
    res = {"gt": dict(n_range=n_r, n_trend=n_t, segs=len(segs))}
    reg0, reg1 = ns0["regime_at"], ns1["regime_at"]
    res["v5_atual"] = confusion(lambda i: reg0(T4[i]), "v5 ATUAL")
    res["v5_V2"] = confusion(lambda i: reg1(T4[i]), "v5 V2-unlock")

    # null persistente com a fração RANGE do V2
    frac = sum(1 for i, g in enumerate(gt) if g and reg1(T4[i]) == "RANGE") / (n_r + n_t)
    baccs = []
    for _ in range(300):
        state = rnd.random() < frac; tp = fp = fn = tn = 0
        for i, g in enumerate(gt):
            if rnd.random() < 1 / 30:
                state = rnd.random() < frac
            if g is None: continue
            if g == "RANGE" and state: tp += 1
            elif g == "RANGE": fn += 1
            elif state: fp += 1
            else: tn += 1
        baccs.append(((tp / (tp + fn) if tp + fn else 0) + (tn / (tn + fp) if tn + fp else 0)) / 2)
    baccs.sort()
    res["null"] = dict(med=round(baccs[150], 3), p95=round(baccs[int(.95 * 300)], 3),
                       p_ge=round(sum(1 for b in baccs if b >= res["v5_V2"]["bacc"]) / 300, 3))
    print(f"null: med {res['null']['med']} · p95 {res['null']['p95']} · p(null>=V2) {res['null']['p_ge']}")

    # jackknife semestral bacc V2
    jk = {}
    for i, g in enumerate(gt):
        if g is None: continue
        d = dt.datetime.utcfromtimestamp(T4[i])
        jk.setdefault(f"{d.year}-H{1 if d.month <= 6 else 2}", []).append(i)
    res["v2_bacc_sem"] = {}
    for hx, idxs in sorted(jk.items()):
        tp = fp = fn = tn = 0
        for i in idxs:
            g = gt[i]; isr = reg1(T4[i]) == "RANGE"
            if g == "RANGE" and isr: tp += 1
            elif g == "RANGE": fn += 1
            elif isr: fp += 1
            else: tn += 1
        res["v2_bacc_sem"][hx] = round(((tp / (tp + fn) if tp + fn else 0) + (tn / (tn + fp) if tn + fp else 0)) / 2, 2)
    print(f"V2 bacc/semestre: {res['v2_bacc_sem']}")

    # DESCRITIVO jul-ago/2026 (não pontua)
    print("\n=== DESCRITIVO jul-ago/2026 (atual → V2) ===")
    tl = []
    for i in range(len(T4)):
        d = dt.datetime.utcfromtimestamp(T4[i])
        if d >= dt.datetime(2026, 7, 1) and d.hour == 14:
            tl.append((d.strftime("%d/%m"), reg0(T4[i]), reg1(T4[i])))
    ch = [(d, a, b) for d, a, b in tl if a != b]
    print(f"  dias diferentes: {len(ch)}/{len(tl)}")
    for d, a, b in ch:
        print(f"    {d}: {a} → {b}")
    res["julago"] = dict(dias=len(tl), mudancas=ch)

    # censo A1/A2 relabel (exploratório)
    eps = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/a1a2_deep_audit_20260828/episodes.jsonl") if l.strip()]

    def panel(rl, cost=0.2):
        n = len(rl); w = sum(1 for r in rl if r > 0); s = sum(r - cost for r in rl)
        return dict(N=n, WR=round(100 * w / n) if n else None, sumR=round(s, 1),
                    avgR=round(s / n, 2) if n else None)
    print("\n=== censo A1/A2 por rótulo V2 (exploratório, custo 0.2) ===")
    res["censo_v2"] = {}
    for lab in ("BULL", "RANGE", "BEAR"):
        p = panel([e["R"] for e in eps if reg1(e["t"]) == lab])
        res["censo_v2"][lab] = p
        print(f"  {lab:<6} {p}")

    (HERE / "results_v2.json").write_text(json.dumps(res, indent=1, default=str))
    print("\ngravado results_v2.json")


if __name__ == "__main__":
    main()
