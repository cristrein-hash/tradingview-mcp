#!/usr/bin/env python3
"""DA independente — reprodução do zero das 6 coortes marginais da EXPANSÃO DO FUNIL
(sysA_funnel_expansion_20260705). Predicados re-escritos, sem importar o script alvo.
Read-only. Não toca chart/RAW. Sem commit."""
import json, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
# selo do universo
canon = HERE / "results" / "lab_g_candidates.jsonl"
sha = hashlib.sha256(canon.read_bytes()).hexdigest()
assert sha == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0], "SELO QUEBRADO"
U = [json.loads(l) for l in open(canon)]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
missing = [r["cj_t"] for r in U if r["cj_t"] not in R3]
print(f"universo N={len(U)} · R3 alvo cobre {len(R3)} · faltantes no R3: {len(missing)}")

def num(r, k):
    v = r.get(k)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None

# ---- predicados independentes (re-escritos da spec pré-declarada) ----
def p_regime_bull(r):   return r.get("g_v5h") == "BULL"
def p_regime_br(r):     return r.get("g_v5h") in ("BULL", "RANGE")
def p_h1(r, thr=0.33):
    t, p = num(r, "h1_trend"), num(r, "h1_pos")
    return t == 1 and p is not None and p >= thr
def p_ema(r, maxbars=3):
    a = num(r, "above_ema21"); b = num(r, "reclaim_ema_bars")
    if a == 0: return True                      # abaixo da EMA: passa
    return b is not None and b <= maxbars       # acima (ou missing=acima no original): exige reclaim rápido
def p_viol(r):
    s, d = num(r, "g_atr_spike"), num(r, "g_downrun")
    return (s is not None and s >= 1.27) or (d is not None and d >= 3)
def p_dem(r):  return num(r, "in_demand") == 1 or num(r, "htf_demand_any") == 1
def p_resp(r):
    v, a = num(r, "g_rec_speed"), num(r, "reclaim_atr")
    return (v is not None and v >= 0.69) or (a is not None and a >= 2.0)
def p_knife(r): return r.get("g_knife") == 0

BASE = dict(regime=p_regime_bull, h1=p_h1, ema=p_ema, viol=p_viol, dem=p_dem, resp=p_resp, knife=p_knife)

def passes(r, override=None):
    o = override or {}
    for k, fn in BASE.items():
        if not (o[k](r) if k in o else fn(r)):
            return False
    return True

def stats(rows):
    if not rows: return dict(n=0)
    rs = sorted(rows, key=lambda r: r["cj_t"])
    nets = [R3[r["cj_t"]]["net3"] for r in rs]
    hit = sum(1 for r in rs if R3[r["cj_t"]]["R3"] >= 3)
    eq = pk = dd = 0.0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
    return dict(n=len(rs), hit=hit, hitpc=round(100 * hit / len(rs), 1),
                net=round(sum(nets), 1), dd=round(dd, 1))

A = [r for r in U if passes(r)]
sA = stats(A)
weeks = len({r["g_week"] for r in U})
print(f"\nA semente: N={sA['n']} hit3R={sA['hitpc']}% NET={sA['net']} · {sA['n']/weeks:.2f}/sem (weeks={weeks})")

# cascata (mesma ordem declarada)
print("\ncascata sequencial sobre BULL:")
casc = [r for r in U if p_regime_bull(r)]
print(f"  BULL: {len(casc)}")
for k in ("h1", "ema", "viol", "dem", "resp", "knife"):
    casc = [r for r in casc if BASE[k](r)]
    print(f"  +{k:<6}: {len(casc)}")

AX = {
    "X1_sem_violencia": {"viol": lambda r: True},
    "X2_sem_resposta":  {"resp": lambda r: True},
    "X3_h1pos_020":     {"h1": lambda r: p_h1(r, 0.20)},
    "X4_ema_rec8":      {"ema": lambda r: p_ema(r, 8)},
    "X5_mais_range":    {"regime": p_regime_br},
    "X6_sem_demanda":   {"dem": lambda r: True},
}
CLAIM = {"X1_sem_violencia": (134, 31.3), "X2_sem_resposta": (178, 28.1),
         "X3_h1pos_020": (1, None), "X4_ema_rec8": (0, None),
         "X5_mais_range": (39, 43.6), "X6_sem_demanda": (5, 20.0)}
Aset = {r["cj_t"] for r in A}
print("\ncoortes marginais (independente) vs claim:")
approved = []
for nm, ov in AX.items():
    marg = [r for r in U if passes(r, ov) and r["cj_t"] not in Aset]
    s = stats(marg)
    cn, ch = CLAIM[nm]
    okN = s["n"] == cn
    okH = (ch is None) or (s.get("hitpc") == ch)
    extra = f" NET={s.get('net')}" if s["n"] else ""
    print(f"  {nm:<18} N={s['n']:>3} hit={s.get('hitpc','—')}%{extra}  claim N={cn}/{ch}%  {'OK' if okN and okH else 'DIVERGE'}")
    if s["n"] >= 15 and s.get("hit", 0) / max(s["n"], 1) >= 0.491:
        approved.append(nm)
print(f"\nregra congelada (hit>=49,1% E N>=15) → aprovados: {approved or 'NENHUM'}")

# ---- X4: por que vazio? quem tem reclaim_ema_bars em 4..8 e falha o quê ----
print("\nX4 forense — BULL com above_ema21=1 e reclaim_ema_bars em 4..8:")
cand = [r for r in U if p_regime_bull(r) and num(r, "above_ema21") == 1
        and num(r, "reclaim_ema_bars") is not None and 4 <= num(r, "reclaim_ema_bars") <= 8]
print(f"  pool bruto: {len(cand)}")
fails = {}
for r in cand:
    f = [k for k in ("h1", "viol", "dem", "resp", "knife") if not BASE[k](r)]
    fails[tuple(f)] = fails.get(tuple(f), 0) + 1
for f, c in sorted(fails.items(), key=lambda x: -x[1]):
    print(f"  falha {f or '(nenhum — entraria!)'}: {c}")

# X5 breakeven sanity: exit 3R c/ SB, breakeven bruto 25%
x5 = [r for r in U if passes(r, AX["X5_mais_range"]) and r["cj_t"] not in Aset]
s5 = stats(x5)
if s5["n"]:
    avg = s5["net"] / s5["n"]
    print(f"\nX5 marginal: N={s5['n']} hit={s5['hitpc']}% NET={s5['net']} avg={avg:+.2f}R/trade (breakeven 3R bruto=25%)")
print("\nDA verify DONE (read-only)")
