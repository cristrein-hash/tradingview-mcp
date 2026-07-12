#!/usr/bin/env python3
"""CAMPO `leg` — OPÇÃO A (ordem Cris 2026-07-12): segundo nível de leitura PARALELO ao detector.
O rótulo macro (engine_4h_regime_gate_RAW.regime_at) fica BYTE-INTOCADO; este módulo adiciona,
por barra 4H, o ESTADO DA PERNA — a leitura hierárquica que o esquema plano não exprime
("pullback bear dentro de bull", "bear com pernas bull internas").

DEFINIÇÃO (congelada; só maquinaria já auditada — zigzag R=6 do harness r2, DA CAUSAL_OK):
- Pivots: máquina de ciclos zigzag R=6 (reversão ≥6·ATR14_4H confirma o extremo; confirmed_at =
  fecho da barra confirmadora; nunca revisto).
- Em t (só pivots confirmados ≤ t):
  · leg_dir = DOWN se o último pivot confirmado é HIGH, UP se é LOW (perna em curso desde ele)
  · estrutura = comparação dos 2 últimos HIGHs e 2 últimos LOWs confirmados:
      UP    se h1>h2 E l1>l2 · DOWN se h1<h2 E l1<l2 · senão NEUTRA
  · leg:
      estrutura UP   : perna UP → IMPULSO_UP   · perna DOWN → PULLBACK_BEAR
      estrutura DOWN : perna DOWN → IMPULSO_DOWN · perna UP  → PULLBACK_BULL
      estrutura NEUTRA: ACUMULACAO (leg_dir reportada à parte)
  · leg_age = barras 4H desde o extremo do último pivot confirmado
- A estrutura vem dos PRÓPRIOS pivots (âncora independente), não do rótulo macro — assim o campo
  leg NÃO herda o desfasamento do macro (nov/2024: estrutura ainda UP → PULLBACK_BEAR correto).
API: build_leg_series() → lista alinhada a TS4 de dicts {t, macro, leg, leg_dir, leg_age}.
Consumo: L1/L2/entry leem (macro, leg). Nada de produção. Sem P&L."""
import io, sys, bisect, contextlib, datetime as dt
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gt_pivot_structural_harness as R1
from gt_pivot_structural_harness_r2 import zigzag
R_LEG = 6

def build_leg_series():
    hi, lo = zigzag(R_LEG)          # (confirmed_at, price, atr) — extremos; confirmados causalmente
    # tempo do EXTREMO de cada pivot: zigzag guarda confirmed_at; para age precisamos do bar do
    # extremo — reconstruímos por preço: extremo é o high/low exato; localizar último bar <= conf
    # com H/L igual ao preço (mesma técnica do bos_gate, janela 300 barras).
    TS4, H4, L4 = R1.TS4, R1.H4, R1.L4
    def ext_time(p, conf, arr):
        j = bisect.bisect_right(TS4, conf)-1
        for k in range(j, max(0, j-300), -1):
            if abs(arr[k]-p) < 1e-9: return TS4[k]
        return conf
    HI = [(c, p, ext_time(p, c, H4)) for c, p, _ in hi]
    LO = [(c, p, ext_time(p, c, L4)) for c, p, _ in lo]
    hct = [x[0] for x in HI]; lct = [x[0] for x in LO]
    out = []
    for t in TS4:
        j = bisect.bisect_right(hct, t); m = bisect.bisect_right(lct, t)
        hs = HI[max(0, j-2):j]; ls = LO[max(0, m-2):m]
        macro = R1.BASE[t]
        if not hs or not ls:
            out.append({"t": t, "macro": macro, "leg": "WARMUP", "leg_dir": None, "leg_age": None})
            continue
        last_h, last_l = hs[-1], ls[-1]
        if last_h[0] >= last_l[0]:
            leg_dir, ext_t = "DOWN", last_h[2]
        else:
            leg_dir, ext_t = "UP", last_l[2]
        struct = "NEUTRA"
        if len(hs) == 2 and len(ls) == 2:
            if hs[1][1] > hs[0][1] and ls[1][1] > ls[0][1]: struct = "UP"
            elif hs[1][1] < hs[0][1] and ls[1][1] < ls[0][1]: struct = "DOWN"
        if struct == "UP":
            leg = "IMPULSO_UP" if leg_dir == "UP" else "PULLBACK_BEAR"
        elif struct == "DOWN":
            leg = "IMPULSO_DOWN" if leg_dir == "DOWN" else "PULLBACK_BULL"
        else:
            leg = "ACUMULACAO"
        age = max(0, bisect.bisect_right(TS4, t)-1 - (bisect.bisect_right(TS4, ext_t)-1))
        out.append({"t": t, "macro": macro, "leg": leg, "leg_dir": leg_dir, "leg_age": age})
    return out

def build_leg_series_v2():
    """v2 (4 correções, ordem Cris 2026-07-12):
    C1 estrutura por QUEBRA DE NÍVEL causal: fecho da barra j acima do último HIGH confirmado =
       evento UP conhecido no fecho de j (consumido a partir da barra j+1); espelho para LOW.
       Um evento por nível (re-arma quando novo pivot confirma). Mata a cegueira em impulso.
    C2 âncora macro: evento CONTRA o macro exige confirmação dupla (2 eventos na mesma direção);
       a favor ou com macro RANGE, imediata. Mata IMPULSO_UP dentro de bear.
    C3 estrutura NEUTRA → ACUMULACAO se macro != BEAR, DISTRIBUICAO se macro == BEAR.
    C4 (plot) fica no replot: borda = macro, preenchimento = leg.
    Eventos de par de pivots (como v1) continuam: avaliados quando um pivot confirma."""
    hi, lo = zigzag(R_LEG)
    TS4, C4 = R1.TS4, R1.ENG.C4
    H4, L4 = R1.H4, R1.L4
    def ext_time(p, conf, arr):
        j = bisect.bisect_right(TS4, conf)-1
        for k in range(j, max(0, j-300), -1):
            if abs(arr[k]-p) < 1e-9: return TS4[k]
        return conf
    HI = [(c, p, ext_time(p, c, H4)) for c, p, _ in hi]
    LO = [(c, p, ext_time(p, c, L4)) for c, p, _ in lo]
    out = []
    struct = "NEUTRA"; pending = None
    lastH = lastL = None; brokenH = brokenL = True
    hprices, lprices = [], []
    ih = il = 0
    last_pivot = None       # ('H'|'L', ext_t) mais recente confirmado
    for i, t in enumerate(TS4):
        macro = R1.BASE[t]
        def apply(ev):
            nonlocal struct, pending
            if ev == "NEUTRA":
                struct = "NEUTRA"; pending = None; return
            if ev == struct: pending = None; return
            contra = (ev == "UP" and macro == "BEAR") or (ev == "DOWN" and macro == "BULL")
            if contra:
                if pending == ev: struct = ev; pending = None
                else: pending = ev
            else:
                struct = ev; pending = None
        # 1) pivots confirmados até t
        while ih < len(HI) and HI[ih][0] <= t:
            lastH = HI[ih][1]; brokenH = False
            hprices.append(lastH); last_pivot = ("H", HI[ih][2]); ih += 1
            if len(hprices) >= 2 and len(lprices) >= 2:
                if hprices[-1] > hprices[-2] and lprices[-1] > lprices[-2]: apply("UP")
                elif hprices[-1] < hprices[-2] and lprices[-1] < lprices[-2]: apply("DOWN")
                else: apply("NEUTRA")
        while il < len(LO) and LO[il][0] <= t:
            lastL = LO[il][1]; brokenL = False
            lprices.append(lastL); last_pivot = ("L", LO[il][2]); il += 1
            if len(hprices) >= 2 and len(lprices) >= 2:
                if hprices[-1] > hprices[-2] and lprices[-1] > lprices[-2]: apply("UP")
                elif hprices[-1] < hprices[-2] and lprices[-1] < lprices[-2]: apply("DOWN")
                else: apply("NEUTRA")
        # 2) quebras de nível no fecho da barra ANTERIOR (i-1 fechou em t)
        if i >= 1:
            c_prev = C4[i-1]
            if lastH is not None and not brokenH and c_prev > lastH:
                brokenH = True; apply("UP")
            if lastL is not None and not brokenL and c_prev < lastL:
                brokenL = True; apply("DOWN")
        # 3) leg_dir + rótulo
        if last_pivot is None:
            out.append({"t": t, "macro": macro, "leg": "WARMUP", "leg_dir": None, "leg_age": None})
            continue
        leg_dir = "DOWN" if last_pivot[0] == "H" else "UP"
        # quebra recente domina a direção da perna em curso (BOS_up => perna UP em curso)
        if brokenH and not brokenL and struct == "UP": leg_dir = "UP"
        if brokenL and not brokenH and struct == "DOWN": leg_dir = "DOWN"
        if struct == "UP":
            leg = "IMPULSO_UP" if leg_dir == "UP" else "PULLBACK_BEAR"
        elif struct == "DOWN":
            leg = "IMPULSO_DOWN" if leg_dir == "DOWN" else "PULLBACK_BULL"
        else:
            leg = "ACUMULACAO" if macro != "BEAR" else "DISTRIBUICAO"
        age = max(0, i - (bisect.bisect_right(TS4, last_pivot[1])-1))
        out.append({"t": t, "macro": macro, "leg": leg, "leg_dir": leg_dir, "leg_age": age})
    return out

def _fmt(t): return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")

def main():
    ser = build_leg_series()
    from collections import Counter
    print("distribuição leg:", dict(Counter(r["leg"] for r in ser)))
    print("macro × leg (barras):")
    cnt = Counter((r["macro"], r["leg"]) for r in ser)
    for (mac, leg), n in sorted(cnt.items()):
        print(f"  {mac:<6} {leg:<14} {n}")
    # leitura dos dois trechos de revisão (Cris): nov/2024→jan/2025 e bear gigante ago/20→abr/21
    for a, b, tag in (("2024-10-20", "2025-02-15", "TRECHO nov/24 (pullback+acumulação em bull)"),
                      ("2020-08-01", "2021-04-15", "TRECHO bear gigante (pernas bull internas)")):
        ta = int(dt.datetime.strptime(a, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
        tb = int(dt.datetime.strptime(b, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
        print(f"\n== {tag} ==")
        runs = []
        for r in ser:
            if not (ta <= r["t"] <= tb): continue
            key = (r["macro"], r["leg"])
            if runs and runs[-1][0] == key: runs[-1][2] = r["t"]
            else: runs.append([key, r["t"], r["t"]])
        for (mac, leg), t0, t1 in runs:
            print(f"  {_fmt(t0)}→{_fmt(t1)}  macro={mac:<6} leg={leg}")

if __name__ == "__main__":
    main()
