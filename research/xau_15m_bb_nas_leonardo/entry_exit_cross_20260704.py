#!/usr/bin/env python3
"""CRUZAMENTO ENTRY × EXIT (2026-07-04, ordem Cris: não parar antes do objetivo).
Correção da leitura: as entradas manuais do Cris A PREÇO DE MERCADO seguem positivas; a hipótese
central agora é que o EXIT TRAIL (aperta pós +1R) estrangula estilos grind — os movimentos chegam
aos alvos 3-10R mas o trail embolsa fração. Teste sistemático DECLARADO (ledger = 4 exits × 5 sets
de entrada = 20 painéis; zero otimização escondida):
EXITS: T (trail let-run aprovado) · F3 (alvo fixo 3R first-touch, sem trail) · F5 (alvo fixo 5R) ·
H (híbrido: sem trail até +3R; depois trail swing-low) — todos com SL estrutural do set, RCAP 20, HMAX 480.
ENTRADAS: CRIS35_mkt (t0 dele, ENTRY=close real, SL=NÍVEL ABSOLUTO desenhado por ele) ·
CRIS35_alvos_abs (mesmo, alvo = nível absoluto desenhado — mede a afirmação '3R-20R' dele honestamente) ·
BASE435 · SISTEMA_A_53 · RECLAIM157. Painel duplo bruto+NET-SB $0,80.
STATUS: EXPLORATORY (ledger declarado; alvos absolutos do Cris = níveis hindsight-desenhados, rotulados)."""
import json, glob, bisect, hashlib
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SB = 0.80

# timeline global + fractais (idêntico ao one-shot)
series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; N = len(S)
L = [b["l"] for b in S]; H = [b["h"] for b in S]; C = [b["c"] for b in S]
ISLOW = [False] * N
for p in range(2, N - 2):
    if L[p] == min(L[p - 2:p + 3]): ISLOW[p] = True
PREV_FR = [None] * N; last = None
for k in range(N):
    p = k - 2
    if p >= 2 and ISLOW[p]: last = p
    PREV_FR[k] = last

def exit_T(i, entry, sl, atr):
    risk = entry - sl; trail = sl; r1 = False; end = min(i + 480, N - 1)
    for k in range(i + 1, end + 1):
        if L[k] <= trail: return max(-1.0, min(20.0, (trail - entry) / risk))
        if (H[k] - entry) / risk >= 1: r1 = True
        if r1:
            p = PREV_FR[k]
            if p is not None and p >= k - 120: trail = max(trail, L[p] - 0.1 * atr)
    return max(-1.0, min(20.0, (C[end] - entry) / risk))
def exit_fixed(mult):
    def fn(i, entry, sl, atr):
        risk = entry - sl; tgt = entry + mult * risk; end = min(i + 480, N - 1)
        for k in range(i + 1, end + 1):
            hit_sl = L[k] <= sl; hit_tp = H[k] >= tgt
            if hit_sl and hit_tp: return -1.0          # ambíguo same-bar = conservador
            if hit_sl: return -1.0
            if hit_tp: return float(mult)
        return max(-1.0, min(20.0, (C[end] - entry) / risk))
    return fn
def exit_H(i, entry, sl, atr):
    """sem trail até +3R atingido; depois trail swing-low −0,1ATR (nunca abaixo do breakeven+?não — puro)."""
    risk = entry - sl; trail = sl; armed = False; end = min(i + 480, N - 1)
    for k in range(i + 1, end + 1):
        if L[k] <= trail: return max(-1.0, min(20.0, (trail - entry) / risk))
        if (H[k] - entry) / risk >= 3: armed = True
        if armed:
            p = PREV_FR[k]
            if p is not None and p >= k - 120: trail = max(trail, L[p] - 0.1 * atr)
    return max(-1.0, min(20.0, (C[end] - entry) / risk))
EXITS = {"T_trail": exit_T, "F3_alvo3R": exit_fixed(3), "F5_alvo5R": exit_fixed(5), "H_trail_pos3R": exit_H}

def asof(t):
    return bisect.bisect_right(TS, t) - 1
def panel(trades):
    trades = sorted(trades); n = len(trades)
    if not n: return None
    out = {"N": n}
    for tag, R in (("g", [x[1] for x in trades]), ("q", [x[1] - SB / x[2] for x in trades])):
        eq = pk = dd = 0.0; mL = cl = 0
        for x in R:
            eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
            if x <= 0: cl += 1; mL = max(mL, cl)
            else: cl = 0
        w = sum(1 for x in R if x > 0)
        out[tag] = dict(sum=round(sum(R), 1), wr=round(100 * w / n, 1), avg=round(sum(R) / n, 3),
                        dd=round(dd, 1), rdd=round(abs(sum(R) / dd), 2) if dd < 0 else 99, stk=mL)
    out["run3"] = sum(1 for x in trades if x[1] >= 3)
    return out

# ---- sets de entrada ----
SETS = {}
raw = json.load(open(HERE / "results" / "cris_manual_trades_20260704.json"))
cris = []
for sh in raw["shapes"]:
    if sh.get("name") != "long_position": continue
    pts = sh["props"]["points"]; pr = sh["props"]["properties"]
    t0 = pts[0]["time"]; drawn = pts[0]["price"]
    sl_abs = round(drawn - pr["stopLevel"] * 0.01, 2)
    tgt_abs = round(drawn + pr["profitLevel"] * 0.01, 2)
    i = asof(t0)
    entry = C[i]                                   # MERCADO: close real na barra do t0 dele
    if entry - sl_abs <= 0: continue               # SL absoluto acima do mercado → sem trade (contado)
    cris.append({"i": i, "t": S[i]["t"], "entry": entry, "sl": sl_abs, "tgt": tgt_abs,
                 "atr": S[i].get("atr") or 1.0})
SETS["CRIS35_mkt"] = [(c["i"], c["entry"], c["sl"], c["atr"], c["t"]) for c in cris]
print(f"CRIS35_mkt: {len(cris)}/35 com risco válido a mercado (SL absoluto desenhado; entry=close real)")

CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def sysA(r):
    return (r["g_v5h"] == "BULL" and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0) and r["g_knife"] == 0)
SETS["BASE435"] = [(asof(r["cj_t"]), r["g_entry"], r["g_sl"], r["g_atr"], r["cj_t"])
                   for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR"]
SETS["SISTEMA_A_53"] = [(asof(r["cj_t"]), r["g_entry"], r["g_sl"], r["g_atr"], r["cj_t"]) for r in U if sysA(r)]
RQ = json.load(open(HERE / "results" / "reclaim_quieto_v1_signals_20260704.json"))
SETS["RECLAIM157"] = [(s["i"], s["c"], s["sl"], S[s["i"]].get("atr") or 1.0, s["t"]) for s in RQ]

print("\n" + "=" * 118)
print(f"{'SET':<14} | {'EXIT':<13} | {'N':>4} {'WRliq':>6} {'BRUTO':>8} {'NET':>8} {'avg':>7} {'DD':>7} {'r/DD':>6} {'stk':>4} {'R>=3':>4}")
print("-" * 118)
RES = []
for sname, sset in SETS.items():
    for ename, efn in EXITS.items():
        tr = [(t, efn(i, e, sl, atr), e - sl) for i, e, sl, atr, t in sset]
        st = panel(tr)
        q = st["q"]
        print(f"{sname:<14} | {ename:<13} | {st['N']:>4} {q['wr']:>6.1f} {st['g']['sum']:>8.1f} {q['sum']:>8.1f} "
              f"{q['avg']:>7.3f} {q['dd']:>7.1f} {q['rdd']:>6.2f} {q['stk']:>4} {st['run3']:>4}")
        RES.append(dict(set=sname, exit=ename, N=st["N"], WR=q["wr"], bruto=st["g"]["sum"], NET=q["sum"],
                        avg=q["avg"], DD=q["dd"], rDD=q["rdd"], stk=q["stk"], run3=st["run3"]))
    print("-" * 118)

# afirmação do Cris '3R-20R': alvos ABSOLUTOS desenhados, a mercado (rotulado hindsight-levels)
tr = []
for c in cris:
    risk = c["entry"] - c["sl"]; end = min(c["i"] + 480, N - 1); R = None
    for k in range(c["i"] + 1, end + 1):
        if L[k] <= c["sl"]: R = -1.0; break
        if H[k] >= c["tgt"]: R = (c["tgt"] - c["entry"]) / risk; break
    if R is None: R = max(-1.0, (C[end] - c["entry"]) / risk)
    tr.append((c["t"], R, risk))
st = panel(tr)
q = st["q"]
print(f"{'CRIS35_mkt':<14} | {'ALVO_ABS_dele':<13} | {st['N']:>4} {q['wr']:>6.1f} {st['g']['sum']:>8.1f} {q['sum']:>8.1f} "
      f"{q['avg']:>7.3f} {q['dd']:>7.1f} {q['rdd']:>6.2f} {q['stk']:>4} {st['run3']:>4}  [níveis hindsight-desenhados; rotulado]")
RES.append(dict(set="CRIS35_mkt", exit="ALVO_ABS_dele", N=st["N"], WR=q["wr"], bruto=st["g"]["sum"], NET=q["sum"],
                avg=q["avg"], DD=q["dd"], rDD=q["rdd"], stk=q["stk"], run3=st["run3"]))
json.dump(RES, open(HERE / "results" / "entry_exit_cross_20260704.json", "w"), indent=1)
print("\nOK → results/entry_exit_cross_20260704.json")
