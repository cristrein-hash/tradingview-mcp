#!/usr/bin/env python3
"""CASCEX v0.1 — diagnóstico dos losers #25/26/30/31/32 + ajuste de entradas em MACRO-BEAR (2026-07-05).
Hipótese do Cris: em regime BEAR os aprofundamentos são mais intensos → a geometria padrão
(SL=flush−0,1ATR) é clipada por wicks mais fundos; losers "por detalhe" quase viram winners.

PARTE 1 — ANATOMIA (todos os 34; foco nos 5 losers): por trade, calcula
  MFE_R           máxima excursão favorável antes do stop (em R)
  sl_exceed_atr   quanto o preço penetrou ABAIXO do SL (ATR) antes de reverter (mín low pós-stop 32b)
  stopped_ran     o alvo 3R ORIGINAL foi atingido nas 192b apesar do stop? (1 = "por detalhe")
PARTE 2 — AJUSTES BEAR-INTERNOS (ledger DECLARADO, aplicados SÓ a membros v5h==BEAR; não-BEAR intacto):
  A1 SL fundo 0,3   SL = flush − 0,3·ATR (alvo = 3R do risco novo)
  A2 SL fundo 0,5   SL = flush − 0,5·ATR
  A3 retest 0,5     entrada LIMIT flush+0,5·ATR nas 16b seguintes (sem fill → SKIP); SL flush−0,1; 3R
  A4 retest 0,5+SL3 A3 com SL flush−0,3
Simulação barra-a-barra nas primitives (first-touch, SL-primeiro na barra ambígua, timeout 192b a
mercado, custo SB 0,80/risk). Réplica de poder: mesmos ajustes no CTX228-BEAR. Painel completo."""
import json, bisect, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])   # U, R3, S, TS, CTX(228), POCKET(56), _ml
CASCEX = sorted([u for u in POCKET if u["_ml"]["vel"] < 0.10 and u["_ml"]["recent_frac"] < 0.5],
                key=lambda u: u["cj_t"])
assert len(CASCEX) == 34

def sim(u, sl, entry=None, entry_mode="close", limit=None, wait=16):
    """simula: retorna (r_net, filled). entry_mode close: entra em cj; limit: fill se low<=limit em <=wait barras."""
    i = bisect.bisect_right(TS, u["cj_t"]) - 1
    if entry_mode == "limit":
        fi = None
        for k in range(i + 1, min(len(S), i + 1 + wait)):
            if S[k]["l"] <= limit:
                fi = k; break
            if S[k]["l"] <= sl:   # stop antes do fill = sem trade
                return None, 0
        if fi is None:
            return None, 0
        e = limit; start = fi
    else:
        e = u["g_entry"]; start = i
    risk = e - sl
    if risk <= 0:
        return None, 0
    tgt = e + 3 * risk; r = None
    for k in range(start + 1, min(len(S), start + 193)):
        if S[k]["l"] <= sl:
            r = -1.0; break
        if S[k]["h"] >= tgt:
            r = 3.0; break
    if r is None:
        k = min(len(S) - 1, start + 192); r = (S[k]["c"] - e) / risk
    return r - 0.8 / risk, 1

def flush_of(u):
    return u["g_sl"] + 0.1 * u["g_atr"]

# ---- PARTE 1: anatomia ----
print("PARTE 1 — ANATOMIA DOS 34 (foco losers):")
print(f"{'#':>3} {'data':>16} {'reg':>6} {'res':>4} {'MFE_R':>6} {'slExc':>6} {'stopRan':>7}")
diag = []
for gid, u in enumerate(CASCEX, 1):
    i = bisect.bisect_right(TS, u["cj_t"]) - 1
    e, sl, atr = u["g_entry"], u["g_sl"], u["g_atr"]
    risk = e - sl; tgt = e + 3 * risk
    win = R3[u["cj_t"]]["R3"] >= 3
    mfe = 0.0; stop_k = None
    for k in range(i + 1, min(len(S), i + 193)):
        if S[k]["l"] <= sl:
            stop_k = k; break
        mfe = max(mfe, (S[k]["h"] - e) / risk)
        if S[k]["h"] >= tgt:
            break
    exc = 0.0; ran = 0
    if stop_k:
        lows = [S[k]["l"] for k in range(stop_k, min(len(S), stop_k + 32))]
        exc = (sl - min(lows)) / atr
        for k in range(stop_k, min(len(S), i + 193)):
            if S[k]["h"] >= tgt:
                ran = 1; break
    d = dict(gid=gid, t=u["cj_t"], reg=u.get("g_v5h"), win=win, mfe=round(mfe, 2),
             exc=round(exc, 2), ran=ran)
    diag.append(d)
    if not win or gid in (25, 26, 30, 31, 32):
        print(f"#{gid:>2} {dt.datetime.utcfromtimestamp(u['cj_t']).strftime('%Y-%m-%d %H:%M'):>16} "
              f"{str(u.get('g_v5h')):>6} {'WIN' if win else 'LOSS':>4} {d['mfe']:>6.2f} {d['exc']:>6.2f} {d['ran']:>7}")

# ---- PARTE 2: ajustes BEAR ----
def panel(rs, tag):
    if not rs:
        print(f"  {tag:<26} vazio"); return None
    n = len(rs); w = sum(1 for x in rs if x > 0); s = sum(rs)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in rs:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    print(f"  {tag:<26} N{n:>3} WR {100*w/n:>5.1f}% sumR {s:>+7.1f} avgR {s/n:>+.3f} DD {dd:>6.1f} stk-{mL}")
    return {"n": n, "wr": w / n, "sum": round(s, 1), "dd": round(dd, 1), "stk": mL}

VARIANTS = {
    "A0_base (ref)": lambda u: sim(u, u["g_sl"]),
    "A1_SL_0.3": lambda u: sim(u, flush_of(u) - 0.3 * u["g_atr"]),
    "A2_SL_0.5": lambda u: sim(u, flush_of(u) - 0.5 * u["g_atr"]),
    "A3_retest0.5": lambda u: sim(u, flush_of(u) - 0.1 * u["g_atr"], entry_mode="limit",
                                  limit=flush_of(u) + 0.5 * u["g_atr"]),
    "A4_retest0.5_SL0.3": lambda u: sim(u, flush_of(u) - 0.3 * u["g_atr"], entry_mode="limit",
                                        limit=flush_of(u) + 0.5 * u["g_atr"]),
}
out = {"diag": diag}
for scope, rows in (("CASCEX", CASCEX), ("CTX228", CTX)):
    B = [u for u in rows if u.get("g_v5h") == "BEAR"]
    NB = [u for u in rows if u.get("g_v5h") != "BEAR"]
    print(f"\nPARTE 2 — {scope}: BEAR N{len(B)} · não-BEAR N{len(NB)} (intacto)")
    for nm, fn in VARIANTS.items():
        res = []; skipped = 0
        for u in B:
            r, filled = fn(u)
            if not filled:
                skipped += 1; continue
            res.append(r)
        st = panel(res, f"{nm} (BEAR)")
        if st and scope == "CASCEX" and nm != "A0_base (ref)":
            # painel total CASCEX com o ajuste aplicado só ao BEAR
            allr = list(res) + [sim(u, u["g_sl"])[0] for u in NB]
            panel(allr, f"  → CASCEX total c/ {nm}")
        if skipped:
            print(f"    ({nm}: {skipped} sem fill = SKIP)")
        out[f"{scope}_{nm}"] = st
json.dump(out, open(HERE / "results" / "cascex_bear_adjust_20260705.json", "w"), indent=1, default=str)
print("\nOK → results/cascex_bear_adjust_20260705.json")
