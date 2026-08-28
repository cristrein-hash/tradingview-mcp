#!/usr/bin/env python3
"""RANGE DETECTION — execução do prereg selado (20e3908). SANITY_PROBE n/a: estudo prereg'd.
GT mecânico independente sobre 4H → matriz de confusão v5/Layer1 → candidata ÚNICA principiada
(v5_new: cont⇒RANGE com prioridade absoluta — promove a feature 'sem progresso líquido' que o motor
JÁ calcula, alinhada com VHF/CHOP/Range-Detector da literatura; zero thresholds novos, zero sweeps)
→ validação (null rotulador aleatório, jackknife semestral, impacto no censo A1/A2 exploratório)
→ 2 ranges do Cris = DESCRITIVOS (timeline jul-ago/2026). py3.9 stdlib."""
import json
import random
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "my-strategy/research/revalidation"))
SEED = 20260828
KGT, W_ATR, NET_FRAC = 30, 4.0, 0.40      # GT selado no manifest

ENG = REPO / "my-strategy/research/revalidation/engine_4h_regime_gate_RAW.py"
ORIG = '    if (bl and bef) or (retreat>=R_thr and lh and bef) or td or (se and pos<0.6 and not cont): return "BEAR"'
PATCH = ('    if cont: return "RANGE"   # V_NEW: sem-progresso-liquido AFIRMA range (prioridade absoluta)\n'
         + ORIG)


def load_engine(patched):
    """Corre o motor real (byte-exato ou com a única linha da candidata) e devolve o namespace."""
    import runpy, tempfile, io, contextlib
    src = ENG.read_text()
    assert ORIG in src, "âncora do source-patch não encontrada — motor mudou"
    if patched:
        src = src.replace(ORIG, PATCH, 1)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir=str(HERE)) as f:
        f.write(src); tmp = f.name
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ns = runpy.run_path(tmp)
    Path(tmp).unlink()
    return ns


def main():
    rnd = random.Random(SEED)
    # ORDEM IMPORTA (bug DA 28/08): o motor tem side-effect (json.dump do l1_FINAL_regime_gated.json).
    # Patched PRIMEIRO, original POR ÚLTIMO ⇒ o artefacto partilhado fica com o conteúdo do motor real.
    ns1 = load_engine(True)
    ns0 = load_engine(False)
    T4 = ns0["TS4"]; H4 = ns0["H4"]; C4 = ns0["C4"]
    L4 = [b["l"] for b in ns0["B4"]]
    print(f"RAW 4H: {len(T4)} barras {dt.datetime.utcfromtimestamp(T4[0]):%Y-%m}→{dt.datetime.utcfromtimestamp(T4[-1]):%Y-%m}")

    # GT selado: largura em ATR DIÁRIO como no manifest ((max-min)/ATR14d <= 4)
    trs4 = [0] + [max(H4[i] - L4[i], abs(H4[i] - C4[i - 1]), abs(L4[i] - C4[i - 1])) for i in range(1, len(T4))]
    gt = []
    for i in range(len(T4)):
        if i < KGT + 90:
            gt.append(None); continue
        atr_d = sum(trs4[i - 84:i]) / 84 * 6                       # ATR diário ≈ média TR4h × 6
        w = max(H4[i - KGT:i + 1]) - min(L4[i - KGT:i + 1])
        net = abs(C4[i] - C4[i - KGT])
        gt.append("RANGE" if (w / atr_d <= W_ATR and net <= NET_FRAC * w) else "TREND")
    n_r = sum(1 for g in gt if g == "RANGE"); n_t = sum(1 for g in gt if g == "TREND")
    print(f"GT: RANGE {n_r} ({n_r/(n_r+n_t):.0%}) · TREND {n_t}")

    # segmentos GT de range (para lag)
    segs = []
    for i, g in enumerate(gt):
        if g == "RANGE" and (i == 0 or gt[i - 1] != "RANGE"):
            segs.append([i, i])
        elif g == "RANGE":
            segs[-1][1] = i
    segs = [s for s in segs if s[1] - s[0] >= 6]                   # ranges com >=6 barras 4H (>=1 dia)
    print(f"segmentos GT de range (>=1d): {len(segs)}")

    def confusion(det_at, name):
        tp = fp = fn = tn = 0
        for i, g in enumerate(gt):
            if g is None:
                continue
            d = det_at(i)
            isr = d == "RANGE"
            if g == "RANGE" and isr: tp += 1
            elif g == "RANGE": fn += 1
            elif isr: fp += 1
            else: tn += 1
        prec = tp / (tp + fp) if tp + fp else None
        rec = tp / (tp + fn) if tp + fn else None
        bacc = ((tp / (tp + fn) if tp + fn else 0) + (tn / (tn + fp) if tn + fp else 0)) / 2
        lags = []
        for a, b in segs:
            hit = next((i for i in range(a, b + 1) if det_at(i) == "RANGE"), None)
            lags.append(hit - a if hit is not None else None)
        det_rate = sum(1 for l in lags if l is not None) / len(segs) if segs else None
        lag_med = sorted(l for l in lags if l is not None)
        lag_med = lag_med[len(lag_med) // 2] if lag_med else None
        r = dict(precision=round(prec, 2) if prec is not None else None,
                 recall=round(rec, 2) if rec is not None else None, bacc=round(bacc, 2),
                 seg_detectados=f"{sum(1 for l in lags if l is not None)}/{len(segs)}",
                 lag_mediano_4h=lag_med)
        print(f"  {name:<14} {r}")
        return r

    print("\n=== MATRIZ DE CONFUSÃO vs GT (por barra 4H) ===")
    res = {"gt": dict(n_range=n_r, n_trend=n_t, segs=len(segs))}
    reg0, reg1 = ns0["regime_at"], ns1["regime_at"]
    res["v5_atual"] = confusion(lambda i: reg0(T4[i]), "v5 ATUAL")
    res["v5_new"] = confusion(lambda i: reg1(T4[i]), "v5 NEW (cont)")

    # Layer1 (labels causais D-1, motor real)
    sys.path.insert(0, str(REPO / "my-strategy/core/layer1_service"))
    import layer1_cycle as LC
    import macro_structural_v3 as M
    xau = LC._merge_xau_1d()
    M.T = [b["t"] for b in xau]; M.O = [b["o"] for b in xau]; M.H = [b["h"] for b in xau]
    M.L = [b["l"] for b in xau]; M.C = [b["c"] for b in xau]; M.N = len(xau)
    dxy = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/raw_dxy_1d.jsonl") if l.strip()]
    M.DXY_K = [b["t"] + 86400 for b in dxy]; M.DXY_C = [b["c"] for b in dxy]
    T1d = M.T; lab1d = M.build_layer1()
    import bisect
    T1d_close = [tt + 82800 for tt in T1d]

    def l1_at(i):
        j = bisect.bisect_right(T1d_close, T4[i]) - 1
        return lab1d[j] if 0 <= j < len(lab1d) else None
    res["layer1"] = confusion(l1_at, "Layer1 1D")

    # null: rotulador aleatório persistente (blocos) com MESMA fração RANGE do v5_new, 300 reps
    frac = sum(1 for i, g in enumerate(gt) if g and reg1(T4[i]) == "RANGE") / (n_r + n_t)
    baccs = []
    for _ in range(300):
        labs = []; state = rnd.random() < frac
        for i in range(len(gt)):
            if rnd.random() < 1 / 30:                              # persistência média 30 barras
                state = rnd.random() < frac
            labs.append("RANGE" if state else "TREND")
        tp = fp = fn = tn = 0
        for i, g in enumerate(gt):
            if g is None: continue
            isr = labs[i] == "RANGE"
            if g == "RANGE" and isr: tp += 1
            elif g == "RANGE": fn += 1
            elif isr: fp += 1
            else: tn += 1
        baccs.append(((tp / (tp + fn) if tp + fn else 0) + (tn / (tn + fp) if tn + fp else 0)) / 2)
    baccs.sort()
    res["null"] = dict(bacc_p95=round(baccs[int(.95 * len(baccs))], 2), bacc_med=round(baccs[len(baccs) // 2], 2))
    print(f"\nnull (rotulador aleatório persistente, mesma fração): bacc med {res['null']['bacc_med']} · p95 {res['null']['bacc_p95']}")

    # jackknife semestral do bacc do v5_new
    halves = {}
    for i, g in enumerate(gt):
        if g is None: continue
        h = dt.datetime.utcfromtimestamp(T4[i])
        halves.setdefault(f"{h.year}-H{1 if h.month <= 6 else 2}", []).append(i)
    jk = {}
    for hx, idxs in sorted(halves.items()):
        tp = fp = fn = tn = 0
        for i in idxs:
            g = gt[i]; isr = reg1(T4[i]) == "RANGE"
            if g == "RANGE" and isr: tp += 1
            elif g == "RANGE": fn += 1
            elif isr: fp += 1
            else: tn += 1
        jk[hx] = round(((tp / (tp + fn) if tp + fn else 0) + (tn / (tn + fp) if tn + fp else 0)) / 2, 2)
    res["v5_new_bacc_por_semestre"] = jk
    print(f"v5_new bacc por semestre: {jk}")

    # DESCRITIVO (não pontua): timeline jul-ago/2026 v5 atual vs new (os 2 ranges do Cris vivem aqui)
    print("\n=== DESCRITIVO jul-ago/2026 (v5 atual → v5 new; amostra diária 12:00) ===")
    tl = []
    for i in range(len(T4)):
        d = dt.datetime.utcfromtimestamp(T4[i])
        if d >= dt.datetime(2026, 7, 1) and d.hour == 14:   # grelha 4H = 02/06/10/14/18/22 UTC (12h não existe)
            a, b = reg0(T4[i]), reg1(T4[i])
            tl.append((d.strftime("%d/%m"), a, b))
    changes = [(d, a, b) for d, a, b in tl if a != b]
    print(f"  dias com rótulo DIFERENTE: {len(changes)}/{len(tl)}")
    for d, a, b in changes:
        print(f"    {d}: {a} → {b}")
    res["timeline_julago_mudancas"] = changes

    # impacto exploratório no censo A1/A2 (episodes.jsonl do deep audit)
    eps = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/a1a2_deep_audit_20260828/episodes.jsonl") if l.strip()]

    def panel(rl, cost=0.2):
        n = len(rl); w = sum(1 for r in rl if r > 0); s = sum(r - cost for r in rl)
        return dict(N=n, WR=round(100 * w / n) if n else None, sumR=round(s, 1),
                    avgR=round(s / n, 2) if n else None)
    for e in eps:
        e["v5n"] = reg1(e["t"])
    print("\n=== censo A1/A2 por rótulo v5_NEW (exploratório, custo 0.2) ===")
    res["censo_v5new"] = {}
    for lab in ("BULL", "RANGE", "BEAR"):
        p = panel([e["R"] for e in eps if e["v5n"] == lab])
        res["censo_v5new"][lab] = p
        print(f"  {lab:<6} {p}")

    (HERE / "results.json").write_text(json.dumps(res, indent=1, default=str))
    print("\ngravado results.json")


if __name__ == "__main__":
    main()
