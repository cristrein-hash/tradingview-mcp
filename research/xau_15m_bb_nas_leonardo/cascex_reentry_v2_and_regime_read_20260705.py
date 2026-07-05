#!/usr/bin/env python3
"""CASCEX — RE-ENTRY v2 (geometria correta) + leitura do REGIME DETECTOR v5 nos BEAR (2026-07-05).
Desafio do Cris à sonda de re-entry do DA (WR 11%, "impossível perante o gráfico"): a sonda ancorava
no flush ORIGINAL — após penetração de 5-9 ATR isso é geometria absurda. v2 = regra CASCEX
re-aplicada ao fundo NOVO:
  após o stop, rastreia o flush novo (mínimo pós-stop); gatilho = 1ª barra com close >= flush_novo
  + 0,3·ATR(barra); janela 96b pós-stop; entry=close; SL=flush_novo−0,1·ATR; alvo=entry+3·risco;
  1 re-entry máx; SL-first; custo SB. Aplicada aos 15 stops do CASCEX (não só BEAR).
PARTE B — detector v5 (validado) sobre os 9 CASCEX-BEAR (6W/3L): campos v5h/v5d/5dago/flip5d/
g_bear_pullback_ok/h4n_trend/h1n_trend + idade do regime BEAR (dias desde o último não-BEAR, via
sequência v5h dos candidatos CTX) — #30/31/32 separáveis dos 6 winners? Regra candidata (se houver)
replicada no CTX228-BEAR N52. Diagnóstico N9 = leitura, não inferência."""
import json, bisect
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])   # U, R3, S, TS, CTX, POCKET, _ml
CASCEX = sorted([u for u in POCKET if u["_ml"]["vel"] < 0.10 and u["_ml"]["recent_frac"] < 0.5],
                key=lambda u: u["cj_t"])
assert len(CASCEX) == 34

def fv(u, k, d=None):
    v = u.get(k)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d

# ---- PARTE A: re-entry v2 ----
print("PARTE A — RE-ENTRY v2 (ancorada no flush NOVO), por stop:")
print(f"{'#':>3} {'data stop':>16} {'reentrou?':>9} {'entry2':>8} {'SL2':>8} {'r2':>6}")
overlay = []; extra = []
for gid, u in enumerate(CASCEX, 1):
    i = bisect.bisect_right(TS, u["cj_t"]) - 1
    e, sl = u["g_entry"], u["g_sl"]; risk = e - sl; tgt = e + 3 * risk
    stop_k = None
    for k in range(i + 1, min(len(S), i + 193)):
        if S[k]["l"] <= sl:
            stop_k = k; break
        if S[k]["h"] >= tgt:
            break
    base_r = R3[u["cj_t"]]["net3"]
    overlay.append(base_r)
    if stop_k is None:
        continue
    nf = S[stop_k]["l"]; re_k = None
    for k in range(stop_k + 1, min(len(S), stop_k + 97)):
        if S[k]["l"] < nf:
            nf = S[k]["l"]
        atr2 = S[k].get("atr") or 5.0
        if S[k]["c"] >= nf + 0.3 * atr2:
            re_k = k; break
    if re_k is None:
        print(f"#{gid:>2} {dt.datetime.utcfromtimestamp(u['cj_t']).strftime('%Y-%m-%d %H:%M'):>16} {'nao':>9}")
        continue
    atr2 = S[re_k].get("atr") or 5.0
    e2 = S[re_k]["c"]; sl2 = nf - 0.1 * atr2; risk2 = e2 - sl2
    if risk2 <= 0:
        continue
    tgt2 = e2 + 3 * risk2; r2 = None
    for k in range(re_k + 1, min(len(S), re_k + 193)):
        if S[k]["l"] <= sl2:
            r2 = -1.0; break
        if S[k]["h"] >= tgt2:
            r2 = 3.0; break
    if r2 is None:
        k = min(len(S) - 1, re_k + 192); r2 = (S[k]["c"] - e2) / risk2
    r2n = r2 - 0.8 / risk2
    extra.append((gid, u["cj_t"], r2n))
    overlay.append(r2n)
    print(f"#{gid:>2} {dt.datetime.utcfromtimestamp(u['cj_t']).strftime('%Y-%m-%d %H:%M'):>16} "
          f"{'sim':>9} {e2:>8.2f} {sl2:>8.2f} {r2n:>+6.2f}")

def panel(rs, tag):
    n = len(rs); w = sum(1 for x in rs if x > 0); s = sum(rs)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in rs:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    print(f"  {tag:<30} N{n:>3} WR {100*w/n:>5.1f}% sumR {s:>+7.1f} avgR {s/n:>+.3f} DD {dd:>6.1f} stk-{mL}")

rr = [x for _, _, x in extra]
print()
panel([R3[u["cj_t"]]["net3"] for u in CASCEX], "CASCEX base (34)")
if rr:
    panel(rr, f"re-entries v2 ({len(rr)})")
    panel(overlay, "OVERLAY base + re-entries")

# ---- PARTE B: leitura do detector v5 nos 9 BEAR ----
print("\nPARTE B — DETECTOR v5 nos 9 CASCEX-BEAR (6W/3L):")
# idade do regime: dias desde o último candidato CTX com v5h != BEAR (proxy da sequência do detector)
CTX_sorted = sorted(CTX, key=lambda x: x["cj_t"])
def bear_age_days(cj):
    last_nb = None
    for v in CTX_sorted:
        if v["cj_t"] >= cj:
            break
        if v.get("g_v5h") != "BEAR":
            last_nb = v["cj_t"]
    return round((cj - last_nb) / 86400, 1) if last_nb else 99.0
print(f"{'#':>3} {'data':>16} {'res':>4} {'v5d':>6} {'5dago':>6} {'flip':>4} {'bpOK':>4} {'h4n':>4} {'h1n':>4} {'ageBEARd':>8}")
B = [(gid, u) for gid, u in enumerate(CASCEX, 1) if u.get("g_v5h") == "BEAR"]
for gid, u in B:
    win = R3[u["cj_t"]]["R3"] >= 3
    print(f"#{gid:>2} {dt.datetime.utcfromtimestamp(u['cj_t']).strftime('%Y-%m-%d %H:%M'):>16} "
          f"{'WIN' if win else 'LOSS':>4} {str(u.get('g_v5d')):>6} {str(u.get('g_v5h_5dago')):>6} "
          f"{fv(u,'g_regime_flip5d',-1):>4} {fv(u,'g_bear_pullback_ok',-1):>4} "
          f"{fv(u,'h4n_trend',9):>4} {fv(u,'h1n_trend',9):>4} {bear_age_days(u['cj_t']):>8}")
# replica de qualquer separador aparente no CTX-BEAR
CB = [u for u in CTX if u.get("g_v5h") == "BEAR" and u["cj_t"] in R3]
print(f"\nréplica CTX-BEAR N{len(CB)} — hit-3R por campo do detector:")
for f, thr in (("g_bear_pullback_ok", 1), ("g_regime_flip5d", 1)):
    for val in (0, 1):
        g = [u for u in CB if fv(u, f, -1) == val]
        if len(g) < 5:
            continue
        h = sum(1 for u in g if R3[u["cj_t"]]["R3"] >= 3); s = sum(R3[u["cj_t"]]["net3"] for u in g)
        print(f"  {f}=={val:<2} N{len(g):>3} hit {100*h/len(g):>5.1f}% NET {s:>+7.1f}")
for lo, hi, tag in ((0, 30, "age<30d"), (30, 999, "age>=30d")):
    g = [u for u in CB if lo <= bear_age_days(u["cj_t"]) < hi]
    if len(g) >= 5:
        h = sum(1 for u in g if R3[u["cj_t"]]["R3"] >= 3); s = sum(R3[u["cj_t"]]["net3"] for u in g)
        print(f"  {tag:<18} N{len(g):>3} hit {100*h/len(g):>5.1f}% NET {s:>+7.1f}")
