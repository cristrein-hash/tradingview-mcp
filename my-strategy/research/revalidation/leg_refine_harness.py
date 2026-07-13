#!/usr/bin/env python3
"""BANCO DE ENSAIO — REFINO do balde ACUMULACAO do leg v2 (Opção A, árbitro B: escala fina + known_at).
Sessao 2026-07-13, engine multi-agente.

PROBLEMA: ~1/3 das barras 4H caem em ACUMULACAO (estrutura NEUTRA do zigzag R=6) — muitas são, na
verdade, impulso/pullback que a escala grossa não resolveu. OBJETIVO: resolver os bares AC em
direção (UP/DOWN) — SÓ quando genuinamente direcional — sem partir a coerência com o macro e sem
fragmentar.

SELADO (intocado): esqueleto de pivôs R=6 + rótulos base (leg_state_4h.build_leg_series). Só os
bares ACUMULACAO são PLUGÁVEIS. Um candidato resolve, por barra AC, a direção com features CAUSAIS.

ÁRBITRO (B, convergente RETROSPECTIVO = "GT" auto-gerado): a verdade de um bar AC vem da escala
FINA (zigzag R=3) medida sobre a série completa (retrospectiva, como um GT). O segmento fino que
contém a barra (por tempo do EXTREMO) dá truth_dir UP/DOWN; amplitude < k·ATR => NEUTRO (AC genuíno).
O candidato é CAUSAL (só vê <= i); a verdade é retrospectiva — o gap causal↔retrospectivo é real
(não é colapso trivial). Coerência é PRESERVADA por construção: direção mapeada sob o macro
(baixa-em-bull = PULLBACK, nunca IMPULSO_DOWN) => nunca cria anti-impulso.

INTERFACE do candidato (range_cand não; ficheiro legcand_<ID>.py):
  NAME="..."; LENS="..."
  def resolve(c) -> "UP" | "DOWN" | None     # só chamado em barras AC; None = manter AC
`c` = dict causal (ver CTX). Correr: python3 leg_refine_harness.py legcand_<ID>
Reporta: reducao-AC, PRECISAO/RECALL vs verdade fina, ESPECIFICIDADE (manter AC genuíno),
fragmentacao, coerencia (anti-impulso BULL/BEAR). RAW-only, sem P&L."""
import sys, bisect, importlib, datetime as dt
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gt_pivot_structural_harness as R1
from gt_pivot_structural_harness_r2 import zigzag, BAR_S
import leg_state_4h as LG
import macro_structural_v3 as M

TS4, H4, L4 = R1.TS4, R1.H4, R1.L4
C4 = R1.ENG.C4
N4 = len(TS4)
T2019 = int(dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc).timestamp())

# --- macro 1D (Layer1) causal por barra 4H ---
_lab1d = M.build_layer1(); _T1 = M.T; _KN1 = [t + 86400 for t in _T1]
def macro_at(t):
    j = bisect.bisect_right(_KN1, t) - 1
    return _lab1d[j] if j >= 0 else None

# --- base leg (macro-independente, R=6) ---
_base = LG.build_leg_series()
BASE_LEG = {r["t"]: r for r in _base}

# --- ext_time de um pivot (localizar barra do extremo por preço, causal-agnóstico p/ verdade) ---
def _ext_time(price, conf, arr):
    j = bisect.bisect_right(TS4, conf) - 1
    for k in range(j, max(0, j - 300), -1):
        if abs(arr[k] - price) < 1e-9: return TS4[k]
    return conf

# --- estrutura FINA CAUSAL a barra t (últimos 2 pivôs finos confirmados <= t) ---
def _fine_struct_causal(R):
    hi, lo = zigzag(R)
    hct = [p[0] for p in hi]; lct = [p[0] for p in lo]
    struct = {}; fdir = {}
    for t in TS4:
        j = bisect.bisect_right(hct, t); m = bisect.bisect_right(lct, t)
        hs = hi[max(0, j - 2):j]; ls = lo[max(0, m - 2):m]
        s = "NEUTRA"; dd = None
        if hs and ls:
            dd = "DOWN" if hct[j - 1] >= lct[m - 1] else "UP"
            if len(hs) == 2 and len(ls) == 2:
                if hs[1][1] > hs[0][1] and ls[1][1] > ls[0][1]: s = "UP"
                elif hs[1][1] < hs[0][1] and ls[1][1] < ls[0][1]: s = "DOWN"
        struct[t] = s; fdir[t] = dd
    return struct, fdir

FS3, FD3 = _fine_struct_causal(3)
FS4, FD4 = _fine_struct_causal(4)
FS2, FD2 = _fine_struct_causal(2)

# --- VERDADE RETROSPECTIVA (árbitro): segmento fino R=3 por tempo do EXTREMO, amplitude>=k·ATR ---
def _truth(R=3, k_atr=1.0):
    hi, lo = zigzag(R)
    piv = ([(_ext_time(p, c, H4), p, "H") for c, p, _ in hi] +
           [(_ext_time(p, c, L4), p, "L") for c, p, _ in lo])
    piv.sort()
    pt = [x[0] for x in piv]
    truth = {}
    for i, t in enumerate(TS4):
        j = bisect.bisect_right(pt, t) - 1
        if j < 0 or j + 1 >= len(piv):
            truth[t] = None; continue
        a, b = piv[j], piv[j + 1]
        a4 = R1.atr4(i) or 5.0
        amp = abs(b[1] - a[1])
        if amp < k_atr * a4:
            truth[t] = None                       # segmento pequeno = AC genuíno
        elif a[2] == "L" and b[2] == "H":
            truth[t] = "UP"
        elif a[2] == "H" and b[2] == "L":
            truth[t] = "DOWN"
        else:
            truth[t] = None
    return truth
TRUTH = _truth(3, 1.0)

# --- momentum causal (retorno de close em k barras) ---
def _ret(t, k):
    i = bisect.bisect_right(TS4, t) - 1
    return (C4[i] / C4[i - k] - 1) * 100 if i >= k else 0.0

def ctx(t):
    r = BASE_LEG.get(t, {})
    return {
        "t": t, "macro": macro_at(t), "base_leg": r.get("leg"),
        "base_dir": r.get("leg_dir"), "base_age": r.get("leg_age"),
        "fs3": FS3[t], "fd3": FD3[t], "fs4": FS4[t], "fd4": FD4[t], "fs2": FS2[t], "fd2": FD2[t],
        "ret10": _ret(t, 10), "ret20": _ret(t, 20), "ret5": _ret(t, 5),
    }

# direção -> leg coerente sob o macro (baixa-em-bull = PULLBACK, nunca anti-impulso)
def _map(mac, d):
    if d == "UP":  return "IMPULSO_UP" if mac != "BEAR" else "PULLBACK_BULL"
    if d == "DOWN": return "IMPULSO_DOWN" if mac == "BEAR" else "PULLBACK_BEAR"
    return "ACUMULACAO"

def run(cand):
    """devolve lista alinhada a TS4 (só 2019+ conta) de dicts {t, macro, leg, resolved(bool)}."""
    out = []
    for t in TS4:
        if t < T2019: continue
        mac = macro_at(t); base = BASE_LEG.get(t, {}).get("leg")
        if mac is None or base is None or base == "WARMUP":
            continue
        if base != "ACUMULACAO":
            out.append({"t": t, "macro": mac, "leg": base, "resolved": False}); continue
        d = cand.resolve(ctx(t))
        if d in ("UP", "DOWN"):
            out.append({"t": t, "macro": mac, "leg": _map(mac, d), "dir": d, "resolved": True})
        else:
            out.append({"t": t, "macro": mac, "leg": "ACUMULACAO", "resolved": False})
    return out

def _anti(rows):
    # anti-impulso: IMPULSO_DOWN em BULL ou IMPULSO_UP em BEAR (não deveria existir)
    b = [r for r in rows if r["macro"] == "BULL"]; e = [r for r in rows if r["macro"] == "BEAR"]
    ab = 100 * sum(1 for r in b if r["leg"] == "IMPULSO_DOWN") / (len(b) or 1)
    ae = 100 * sum(1 for r in e if r["leg"] == "IMPULSO_UP") / (len(e) or 1)
    return round(ab, 1), round(ae, 1)

def _episodes(rows):
    eps = 0; prev = None
    for r in rows:
        if r["leg"] != prev: eps += 1; prev = r["leg"]
    return eps

def report(rows, name):
    n = len(rows) or 1
    ac0 = [r for r in rows if BASE_LEG[r["t"]]["leg"] == "ACUMULACAO"]  # bares originalmente AC
    resolved = [r for r in ac0 if r["resolved"]]
    kept = [r for r in ac0 if not r["resolved"]]
    ac_before = 100 * len(ac0) / n
    ac_after = 100 * sum(1 for r in rows if r["leg"] == "ACUMULACAO") / n
    # precisão: dos resolvidos, quantos batem a verdade fina
    prec_den = [r for r in resolved if TRUTH.get(r["t"]) in ("UP", "DOWN")]
    prec = 100 * sum(1 for r in prec_den if r["dir"] == TRUTH[r["t"]]) / (len(prec_den) or 1)
    # recall: dos AC com verdade direcional, quantos resolvidos com a direção certa
    rec_den = [r for r in ac0 if TRUTH.get(r["t"]) in ("UP", "DOWN")]
    rec = 100 * sum(1 for r in rec_den if r["resolved"] and r.get("dir") == TRUTH[r["t"]]) / (len(rec_den) or 1)
    # especificidade: dos AC com verdade NEUTRA, quantos mantidos AC (não sobre-resolver)
    spec_den = [r for r in ac0 if TRUTH.get(r["t"]) is None]
    spec = 100 * sum(1 for r in spec_den if not r["resolved"]) / (len(spec_den) or 1)
    ab, ae = _anti(rows)
    trava = "SIM" if (ab <= 0.5 and ae <= 2.0) else f"NAO (antiBULL {ab} antiBEAR {ae})"
    print(f"== {name} · REFINO AC · árbitro fino R=3 ==")
    print(f"  AC: {ac_before:.0f}% -> {ac_after:.0f}%  (resolvidos {len(resolved)}/{len(ac0)} bares AC)")
    print(f"  PRECISAO {prec:.0f}% · RECALL {rec:.0f}% · ESPECIFICIDADE {spec:.0f}% (manter AC genuíno)")
    print(f"  COERENCIA(trava): anti-impulso BULL {ab}% BEAR {ae}% -> PRESERVA={trava}")
    print(f"  fragmentação: {_episodes(rows)} episódios (2019+)")
    return dict(ac_before=round(ac_before), ac_after=round(ac_after), prec=round(prec),
                rec=round(rec), spec=round(spec), anti_bull=ab, anti_bear=ae,
                episodes=_episodes(rows), preserva=(trava == "SIM"))

if __name__ == "__main__":
    cand = importlib.import_module(sys.argv[1].replace(".py", ""))
    report(run(cand), getattr(cand, "NAME", sys.argv[1]))
