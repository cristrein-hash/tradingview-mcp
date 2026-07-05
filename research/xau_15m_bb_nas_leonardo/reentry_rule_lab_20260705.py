#!/usr/bin/env python3
"""LAB DE REGRA DE RE-ENTRY — mandato Cris: "descobre a regra válida de re-entry ou skip" (2026-07-05).
Diagnóstico v2: gatilho 0,3ATR degenera em re-entrada imediata (13/15 em 1 barra) — zero confirmação.
As 5 boas (#4/9/13/25/26) vs 10 más sugerem que falta a MESMA confirmação do motor original.

LEDGER DECLARADO (4 regras, thresholds do próprio motor, zero tuning):
  R0 v2-ref       close >= flush_novo + 0,3·ATR (referência)
  R1 reclaim1.5   close >= flush_novo + 1,5·ATR (o gate de reclaim do MOTOR original)
  R2 estab8       R0 mas só após >=8 barras SEM low novo (fundo estabilizou)
  R3 choch_preco  close > max(high 12b) pós-stop (virada estrutural por preço)
  R4 R1+estab8    reclaim forte E estabilização
EXECUÇÃO comum: janela 96b pós-stop, rastreia flush novo; entry=close do gatilho; SL=flush_novo−0,1·ATR;
alvo 3R; 1 re-entry máx; SL-first; custo SB 0,80/risk.
EXIT: convenção CANÓNICA da base (480b, timeout capado [−1,+3]) = primária; 192b = sensibilidade.
PODER: avaliado em TODOS os stops do CTX228 (réplica primária) + subset CASCEX (o alvo).
GATE DECLARADO p/ adoção: sumR>0 em AMBOS + overlay CASCEX não piora P(streak>5) materialmente."""
import json, bisect, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])   # U, R3, S, TS, CTX(228), POCKET(56), _ml
CASCEX = sorted([u for u in POCKET if u["_ml"]["vel"] < 0.10 and u["_ml"]["recent_frac"] < 0.5],
                key=lambda u: u["cj_t"])

def stop_bar(u):
    i = bisect.bisect_right(TS, u["cj_t"]) - 1
    e, sl = u["g_entry"], u["g_sl"]; tgt = e + 3 * (e - sl)
    for k in range(i + 1, min(len(S), i + 481)):
        if S[k]["l"] <= sl:
            return k
        if S[k]["h"] >= tgt:
            return None
    return None

def sim_re(stop_k, rule, horizon=480):
    nf = S[stop_k]["l"]; since_low = 0; re_k = None
    hi12 = None
    for k in range(stop_k + 1, min(len(S), stop_k + 97)):
        if S[k]["l"] < nf:
            nf = S[k]["l"]; since_low = 0
        else:
            since_low += 1
        atr = S[k].get("atr") or 5.0
        hi12 = max(S[j]["h"] for j in range(max(stop_k, k - 12), k))
        trig = False
        if rule == "R0":
            trig = S[k]["c"] >= nf + 0.3 * atr
        elif rule == "R1":
            trig = S[k]["c"] >= nf + 1.5 * atr
        elif rule == "R2":
            trig = S[k]["c"] >= nf + 0.3 * atr and since_low >= 8
        elif rule == "R3":
            trig = S[k]["c"] > hi12
        elif rule == "R4":
            trig = S[k]["c"] >= nf + 1.5 * atr and since_low >= 8
        if trig:
            re_k = k; break
    if re_k is None:
        return None
    atr = S[re_k].get("atr") or 5.0
    e2 = S[re_k]["c"]; sl2 = nf - 0.1 * atr; risk2 = e2 - sl2
    if risk2 <= 0:
        return None
    tgt2 = e2 + 3 * risk2
    for k in range(re_k + 1, min(len(S), re_k + 1 + horizon)):
        if S[k]["l"] <= sl2:
            return -1.0 - 0.8 / risk2
        if S[k]["h"] >= tgt2:
            return 3.0 - 0.8 / risk2
    k = min(len(S) - 1, re_k + horizon)
    return max(-1.0, min(3.0, (S[k]["c"] - e2) / risk2)) - 0.8 / risk2

def panel(rs, tag):
    if not rs:
        print(f"  {tag:<28} sem re-entries"); return None
    n = len(rs); w = sum(1 for x in rs if x > 0); s = sum(rs)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in rs:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    print(f"  {tag:<28} N{n:>4} WR {100*w/n:>5.1f}% sumR {s:>+8.1f} avgR {s/n:>+.3f} DD {dd:>6.1f} stk-{mL}")
    return {"n": n, "wr": round(w / n, 3), "sum": round(s, 1), "dd": round(dd, 1), "stk": mL}

STOPS = {"CASCEX": [(u, stop_bar(u)) for u in CASCEX], "CTX228": [(u, stop_bar(u)) for u in CTX]}
STOPS = {k: [(u, s) for u, s in v if s is not None] for k, v in STOPS.items()}
print(f"stops: CASCEX {len(STOPS['CASCEX'])} · CTX228 {len(STOPS['CTX228'])}")
out = {}
for scope in ("CTX228", "CASCEX"):
    print(f"\n{scope} — re-entry por regra (exit canónico 480b; sensibilidade 192b):")
    for rule in ("R0", "R1", "R2", "R3", "R4"):
        rs = [sim_re(s, rule) for _, s in STOPS[scope]]
        rs = [x for x in rs if x is not None]
        st = panel(rs, f"{rule} (480b)")
        rs192 = [x for x in (sim_re(s, rule, horizon=192) for _, s in STOPS[scope]) if x is not None]
        st192 = panel(rs192, f"{rule} (192b sens.)")
        out[f"{scope}_{rule}"] = {"480": st, "192": st192}

# overlay CASCEX com a melhor regra que passar sumR>0 em ambos (ordem do ledger)
best = None
for rule in ("R4", "R1", "R2", "R3"):
    a = out[f"CTX228_{rule}"]["480"]; b = out[f"CASCEX_{rule}"]["480"]
    if a and b and a["sum"] > 0 and b["sum"] > 0:
        best = rule; break
print(f"\nGATE sumR>0 em ambos: {'regra ' + best if best else 'NENHUMA regra passa'}")
if best:
    rs = [sim_re(s, best) for _, s in STOPS["CASCEX"]]
    rs = [x for x in rs if x is not None]
    base = [R3[u["cj_t"]]["net3"] for u in CASCEX]
    overlay = base + rs
    panel(base, "CASCEX base")
    panel(overlay, f"OVERLAY base + {best}")
    random.seed(3)
    def pstk(nets):
        cnt = 0
        for _ in range(2000):
            sq = random.choices(nets, k=len(nets)); c2 = m2 = 0
            for x in sq:
                c2 = c2 + 1 if x <= 0 else 0; m2 = max(m2, c2)
            if m2 > 5:
                cnt += 1
        return cnt / 2000
    print(f"  P(streak>5): base {pstk(base):.2f} → overlay {pstk(overlay):.2f}")
json.dump(out, open(HERE / "results" / "reentry_rule_lab_20260705.json", "w"), indent=1, default=str)
print("OK → results/reentry_rule_lab_20260705.json")
