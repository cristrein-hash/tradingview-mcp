#!/usr/bin/env python3
"""DA EXIT FAMILY LAB — ataque 1: implementação independente dos 4 exits (spec do prereg,
código reescrito do zero, estilo diferente), comparação por-trade vs lab, contagem de
same-bar ambíguos (E2/E3) e same-bar arm+stop (E1), traces bar-a-bar de 5 trades.
READ-ONLY. Sem commit. Sem chart/RAW/produção."""
import json, glob, bisect, hashlib
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SB = 0.80
HMAX, RCAP, FR_WIN = 480, 20.0, 120

# ---- timeline (loader compartilhado; fractais recomputados de forma independente) ----
series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]:
        series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"])
TS = [b["t"] for b in S]
N = len(S)
L = [b["l"] for b in S]
H = [b["h"] for b in S]
C = [b["c"] for b in S]

# fractal low 2-2 independente: p é fractal se L[p] <= todos L[p-2..p+2] (== min é equivalente)
FRAC = [p for p in range(2, N - 2)
        if L[p] <= L[p-2] and L[p] <= L[p-1] and L[p] <= L[p+1] and L[p] <= L[p+2]]
FRSET = set(FRAC)

def last_fractal_confirmed_at(k):
    """último fractal p com confirmação até a barra k (precisa de L[p+2] => p <= k-2)."""
    # varre para trás a partir de k-2 (independente do PREV_FR do lab)
    p = k - 2
    lo = max(2, k - FR_WIN)  # janela de recência checada depois; varredura limitada
    while p >= 2:
        if p in FRSET:
            return p
        p -= 1
        if p < k - 4000:  # guarda
            break
    return None

# pré-computa último fractal confirmado por barra (varredura única, O(N))
LASTFR = [None] * N
_last = None
for k in range(N):
    q = k - 2
    if q >= 2 and q in FRSET:
        _last = q
    LASTFR[k] = _last

def run_trail(i, entry, sl, atr, arm_R, trace=None):
    """Spec prereg: trail=SL; após TOQUE de +arm_R (high), trail=max(trail, fractal_low[<=k-2,
    recência 120b] - 0.1*ATR); stop checado ANTES do update (barra k usa trail da barra k-1);
    same-bar SL+arm resolve como SL (contra a variante). HMAX 480, clamp [-1, 20]."""
    risk = entry - sl
    stop = sl
    armed = False
    end = min(i + HMAX, N - 1)
    for k in range(i + 1, end + 1):
        if L[k] <= stop:
            r = max(-1.0, min(RCAP, (stop - entry) / risk))
            if trace is not None:
                trace.append((k, "STOP", stop, round(r, 3)))
            return r, k, "stop"
        if not armed and (H[k] - entry) >= arm_R * risk:
            armed = True
            if trace is not None:
                trace.append((k, "ARM", H[k], round((H[k]-entry)/risk, 2)))
        if armed:
            p = LASTFR[k]
            if p is not None and p >= k - FR_WIN:
                new = L[p] - 0.1 * atr
                if new > stop:
                    stop = new
                    if trace is not None:
                        trace.append((k, "TRAIL", round(stop, 2), f"fr@{p}"))
    r = max(-1.0, min(RCAP, (C[end] - entry) / risk))
    if trace is not None:
        trace.append((end, "TIMEOUT", C[end], round(r, 3)))
    return r, end, "timeout"

def run_fixed(i, entry, sl, atr, mult, trace=None):
    """Alvo fixo first-touch; same-bar ambíguo (SL e TP na mesma barra) = -1 (conservador)."""
    risk = entry - sl
    tgt = entry + mult * risk
    end = min(i + HMAX, N - 1)
    ambiguous = False
    for k in range(i + 1, end + 1):
        sl_hit = L[k] <= sl
        tp_hit = H[k] >= tgt
        if sl_hit:
            if tp_hit:
                ambiguous = True
            if trace is not None:
                trace.append((k, "SL" + ("+TP_AMBIG" if tp_hit else ""), sl, -1.0))
            return -1.0, k, ("ambiguous" if ambiguous else "sl")
        if tp_hit:
            if trace is not None:
                trace.append((k, "TP", tgt, float(mult)))
            return float(mult), k, "tp"
    r = max(-1.0, min(RCAP, (C[end] - entry) / risk))
    if trace is not None:
        trace.append((end, "TIMEOUT", C[end], round(r, 3)))
    return r, end, "timeout"

# ---- universo selado ----
CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == \
    (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0], "checksum universo"
U = [json.loads(l) for l in open(CANON)]
def fv(r, k, d=0):
    v = r.get(k)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def sysA(r):
    return (r["g_v5h"] == "BULL" and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0) and r["g_knife"] == 0)
def asof(t):
    return bisect.bisect_right(TS, t) - 1
SETS = {
    "BASE435": [(asof(r["cj_t"]), r["g_entry"], r["g_sl"], r["g_atr"], r["cj_t"], r["yr"])
                for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR"],
    "SISTEMA_A_53": [(asof(r["cj_t"]), r["g_entry"], r["g_sl"], r["g_atr"], r["cj_t"], r["yr"])
                     for r in U if sysA(r)],
}

EXITS = {
    "E0_trail":   lambda i, e, sl, a, tr=None: run_trail(i, e, sl, a, 1, tr),
    "E1_trail3R": lambda i, e, sl, a, tr=None: run_trail(i, e, sl, a, 3, tr),
    "E2_alvo3R":  lambda i, e, sl, a, tr=None: run_fixed(i, e, sl, a, 3, tr),
    "E3_alvo5R":  lambda i, e, sl, a, tr=None: run_fixed(i, e, sl, a, 5, tr),
}

# valores esperados do CSV do lab
EXPECT = {
    ("BASE435", "E0_trail"): (292.2, 234.3), ("BASE435", "E1_trail3R"): (374.6, 316.7),
    ("BASE435", "E2_alvo3R"): (243.6, 185.7), ("BASE435", "E3_alvo5R"): (356.1, 298.2),
    ("SISTEMA_A_53", "E0_trail"): (29.8, 25.9), ("SISTEMA_A_53", "E1_trail3R"): (46.1, 42.2),
    ("SISTEMA_A_53", "E2_alvo3R"): (51.0, 47.1), ("SISTEMA_A_53", "E3_alvo5R"): (45.9, 42.0),
}

print("=" * 100)
print("A) REPRODUÇÃO INDEPENDENTE (impl reescrita) vs CSV do lab")
RESULTS = {}
for sname, sset in SETS.items():
    for ename, efn in EXITS.items():
        rows = []
        for i, e, sl, atr, t, yr in sset:
            r, kend, why = efn(i, e, sl, atr)
            rows.append((t, r, e - sl, yr, kend - i, why))
        RESULTS[(sname, ename)] = rows
        g = sum(x[1] for x in rows)
        q = sum(x[1] - SB / x[2] for x in rows)
        wr = 100 * sum(1 for x in rows if x[1] - SB / x[2] > 0) / len(rows)
        run3 = sum(1 for x in rows if x[1] >= 3)
        eg, eq = EXPECT[(sname, ename)]
        ok = "MATCH" if abs(g - eg) < 0.15 and abs(q - eq) < 0.15 else f"DIVERGE (esp {eg}/{eq})"
        dur = sum(x[4] for x in rows) / len(rows)
        print(f"  {sname:<13} {ename:<11} bruto {g:>7.1f} NET {q:>7.1f} WRliq {wr:4.1f} "
              f"run3 {run3:>3} dur_média {dur:5.1f} barras → {ok}")

print("\nB) SAME-BAR AMBÍGUOS")
for sname in SETS:
    for ename in ("E2_alvo3R", "E3_alvo5R"):
        rows = RESULTS[(sname, ename)]
        amb = [x for x in rows if x[5] == "ambiguous"]
        mult = 3.0 if ename == "E2_alvo3R" else 5.0
        # impacto: cada ambíguo contado -1; se fosse resolvido a favor (TP) seria +mult
        worst_penalty = len(amb) * (mult + 1)
        print(f"  {sname:<13} {ename}: {len(amb)} ambíguos (contados -1); "
              f"upper-bound se todos fossem TP: +{worst_penalty:.0f}R no delta do fixo")
# E1: same-bar SL(original)+toque3R → resolvido como -1 (contra E1)
for sname, sset in SETS.items():
    n_amb = 0
    for i, e, sl, atr, t, yr in sset:
        risk = e - sl
        end = min(i + HMAX, N - 1)
        stop = sl
        armed = False
        for k in range(i + 1, end + 1):
            if L[k] <= stop:
                if not armed and (H[k] - e) >= 3 * risk:
                    n_amb += 1  # mesma barra: tocaria 3R mas SL decide primeiro
                break
            if not armed and (H[k] - e) >= 3 * risk:
                armed = True
            if armed:
                p = LASTFR[k]
                if p is not None and p >= k - FR_WIN:
                    stop = max(stop, L[p] - 0.1 * atr)
    print(f"  {sname:<13} E1_trail3R: {n_amb} barras same-bar (toque 3R + SL) resolvidas como SL (contra E1)")

print("\nC) TRACE BAR-A-BAR — 5 trades da BASE435 (mix win/loss), 4 exits cada")
sel = sorted(SETS["BASE435"])[:: max(1, len(SETS["BASE435"]) // 5)][:5]
# escolhe 5 espalhados: 1º, e depois por resultado E1 diverso
rowsE1 = RESULTS[("BASE435", "E1_trail3R")]
rowsE0 = RESULTS[("BASE435", "E0_trail")]
bytime = {t: j for j, (t, *_rest) in enumerate(sorted(rowsE0))}
sortedset = sorted(SETS["BASE435"])
# picks: maior delta E1-E0, menor delta, um loss-loss, um timeout, primeiro trade
sr0 = sorted(rowsE0); sr1 = sorted(rowsE1)
deltas = [(sr1[j][1] - sr0[j][1], j) for j in range(len(sr0))]
picks = {max(deltas)[1], min(deltas)[1], 0}
for j in range(len(sr0)):
    if sr0[j][5] == "timeout":
        picks.add(j); break
for j in range(len(sr0)):
    if sr0[j][1] <= -0.99 and sr1[j][1] <= -0.99:
        picks.add(j); break
for j in sorted(picks)[:6]:
    i, e, sl, atr, t, yr = sortedset[j]
    d = dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")
    print(f"\n  trade#{j} {d} entry {e} sl {sl} risk {e-sl:.2f} atr {atr:.2f}")
    for ename, efn in EXITS.items():
        tr = []
        r, kend, why = efn(i, e, sl, atr, tr)
        ev = " · ".join(f"b+{k-i}:{tag}@{v}" for k, tag, v, _x in tr[:4])
        more = f" (+{len(tr)-4} eventos)" if len(tr) > 4 else ""
        print(f"    {ename:<11} R={r:+.2f} saída b+{kend-i} ({why})  {ev}{more}")

print("\nD) PAREAMENTO: cj_t únicos?", len({t for _i, _e, _sl, _a, t, _y in SETS['BASE435']}) == 435)
print("OK — DA impl independente concluído.")
