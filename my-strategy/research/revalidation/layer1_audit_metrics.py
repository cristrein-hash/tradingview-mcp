#!/usr/bin/env python3
"""SCORER AUDITADO Layer 1 (protocolo feedback_audit_own_measurements). NUNCA reportar %-por-barra
sozinho. Recebe uma série de rótulos macro (1 por barra diária, alinhada a raw_1d_ohlc.jsonl) e
devolve: (1) estrutura-de-corridas (nº blocos + duração mediana — fragmentação denuncia-se aqui),
(2) onset-lag por BEAR (dias entre início da janela GT e 1º disparo BEAR), (3) per-janela recall,
(4) coerência 2026 (segura BEAR do crash 18-mar até ao fim?), (5) false-bear-em-bull (barras BEAR
dentro de janelas BULL do GT). Métrica composta de COERÊNCIA, não só balanced."""
import json, statistics, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
GT = json.load(open(HERE/"results/REGIME_GT_LAYER1_CRIS_1D_20260713.json"))
TOL = GT["border_tolerance_s"]
D1 = [json.loads(l) for l in open(HERE/"raw_1d_ohlc.jsonl")]
T = [b["t"] for b in D1]; N = len(T); KNOWN = [t+86400 for t in T]

def eff_label(t):
    hits = [w for w in GT["windows"] if w["t0"]+TOL <= t <= w["t1"]-TOL]
    return min(hits, key=lambda w: w["t1"]-w["t0"])["regime"] if hits else None
SCOPE_I = [(i, eff_label(KNOWN[i])) for i in range(N)]
SCOPE_I = [(i, g) for i, g in SCOPE_I if g is not None]

def audit(labels):
    """labels = lista de N rótulos (BULL/BEAR/RANGE) alinhada a T. Devolve dict de métricas auditadas."""
    assert len(labels) == N, f"len {len(labels)} != {N}"
    # (1) estrutura de corridas (só 2019+)
    t2019 = int(dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc).timestamp())
    runs = []
    for i in range(N):
        if runs and runs[-1][0] == labels[i]: runs[-1][2] = i
        else: runs.append([labels[i], i, i])
    runs = [r for r in runs if T[r[2]] >= t2019]
    durs = sorted((T[r[2]]-T[r[1]])/86400 for r in runs)
    n_runs = len(runs); med_dur = durs[len(durs)//2] if durs else 0
    # (2) onset-lag por BEAR
    onsets = {}
    for w in GT["windows"]:
        if w["regime"] != "BEAR": continue
        fire = None
        for i in range(N):
            if w["t0"]-5*86400 <= KNOWN[i] <= w["t1"] and labels[i] == "BEAR":
                fire = KNOWN[i]; break
        onsets[w["d0"]] = round((fire-w["t0"])/86400, 0) if fire is not None else None
    lags = [v for v in onsets.values() if v is not None]
    # (3) per-janela recall
    perwin = {}
    for w in GT["windows"]:
        sc = [i for i, g in SCOPE_I if w["t0"]+TOL <= KNOWN[i] <= w["t1"]-TOL and g == w["regime"]]
        perwin[w["d0"]] = round(100*sum(1 for i in sc if labels[i] == w["regime"])/len(sc), 0) if sc else None
    # (4) coerência 2026: fração BEAR de 18-mar-2026 ao fim dos dados
    ta = int(dt.datetime(2026, 3, 18, tzinfo=dt.timezone.utc).timestamp())
    seg = [labels[i] for i in range(N) if KNOWN[i] >= ta]
    bear_2026 = round(100*sum(1 for x in seg if x == "BEAR")/len(seg), 0) if seg else None
    # (5) transições falsas por contexto (bear-em-bull, bear-em-range, bull-em-bear)
    def false_in(gt_regime, wrong_label):
        f = n = 0
        for w in GT["windows"]:
            if w["regime"] != gt_regime: continue
            for i, g in SCOPE_I:
                if w["t0"]+TOL <= KNOWN[i] <= w["t1"]-TOL:
                    n += 1; f += (labels[i] == wrong_label)
        return round(100*f/n, 1) if n else None
    false_bear_in_bull = false_in("BULL", "BEAR")
    false_bear_in_range = false_in("RANGE", "BEAR")
    false_bull_in_bear = false_in("BEAR", "BULL")
    false_bull_in_range = false_in("RANGE", "BULL")
    # per-classe recall agregado
    per = {s: {"n": 0, "ok": 0} for s in ("BULL", "BEAR", "RANGE")}
    for i, g in SCOPE_I:
        per[g]["n"] += 1; per[g]["ok"] += (labels[i] == g)
    rec = {s: round(100*per[s]["ok"]/per[s]["n"], 0) if per[s]["n"] else None for s in per}
    bal = statistics.mean([v for v in rec.values() if v is not None])
    return {"n_runs": n_runs, "med_dur_d": round(med_dur, 0),
            "onset_lag_by_bear": onsets, "onset_lag_med": round(statistics.median(lags), 0) if lags else None,
            "bears_detected": f"{len(lags)}/5",
            "per_window": perwin, "recall": rec, "bal": round(bal, 1),
            "coherence_2026_bear_pct": bear_2026, "false_bear_in_bull_pct": false_bear_in_bull,
            "false_bear_in_range_pct": false_bear_in_range, "false_bull_in_bear_pct": false_bull_in_bear,
            "false_bull_in_range_pct": false_bull_in_range}

def coherence_score(m):
    """score composto de COERÊNCIA MACRO (não só balanced). Penaliza fragmentação, lag alto,
    false-bear-em-bull, e recompensa 2026 seguro + bears detectados."""
    s = 0.0
    s += m["bal"]                                              # base
    s += (m["coherence_2026_bear_pct"] or 0)*0.5              # 2026 tem de segurar bear
    s -= (m["false_bear_in_bull_pct"] or 0)*1.0              # penaliza bear-em-bull
    s -= (m["false_bear_in_range_pct"] or 0)*1.0            # penaliza bear-em-range (P2)
    s -= (m["false_bull_in_bear_pct"] or 0)*1.0            # penaliza bull-em-bear (P1)
    s -= max(0, m["n_runs"]-25)*1.0                          # penaliza fragmentação (>25 blocos)
    s += (0 if m["onset_lag_med"] is None else max(0, 30-m["onset_lag_med"]))*0.5   # onset rápido
    return round(s, 1)

if __name__ == "__main__":
    import sys
    # uso: passar um json {"labels":[...]} ou nome de ficheiro de labels
    print(f"scorer pronto · N={N} · GT {len([w for w in GT['windows']])} janelas · scope {len(SCOPE_I)} barras")
