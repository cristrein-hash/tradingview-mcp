#!/usr/bin/env python3
"""B MACRO GATE — subtipo de RANGE acum-vs-distrib (aprovado Cris 2026-07-15). Envolve o detector
macro aprovado (`macro_structural_v3.build_layer1`) SEM o modificar. Adiciona, causalmente, o subtipo
do RANGE fixado no ONSET:
  RANGE_POST_CRASH  = o range nasceu de um CRASH (ret 2d <= -6%, o MESMO limiar do engine) na janela
                      [onset-15, onset] -> distribuição catastrófica -> b_long_allowed=False (SKIP).
  RANGE_ORDERLY     = range nascido de stall/drift -> re-acumulação assumida -> b_long_allowed=True.

PORQUÊ (estudo de caso 2026-07-15, `range_accum_distrib_test.py`): accum-vs-distrib NÃO é discriminável
no macro de forma geral (pred/dom-break/dd252 REFUTADOS; overlap total — 2021 acum dd 14,6% == 2026
distrib dd 14,6%). O ÚNICO sinal com precisão 1,00 no histórico (15 episódios) foi crashPre: dispara em
1/15 (só 2026), NUNCA skipou uma acumulação -> seguro ASSIMÉTRICO (custa oportunidade, não capital) que
apanha o caso catastrófico (2026 -> bear até hoje). Recall baixo (0,20): distribuições QUIETAS passam e
são geridas por invalidação apertada + o flip macro->BEAR fecha o gate. FORWARD = árbitro da precisão.

Causal: o subtipo é fixado no onset (que é passado no instante da query); crash mid-range é tratado
pelo próprio override crash->BEAR do detector (o range termina, gate fecha). Query alinhada a T+86400
(regime close-only conhecido 1 dia após o close 1D), consistente com o resto do stack."""
import bisect
import macro_structural_v3 as M

CRASH_THR = -6.0        # idêntico ao crash_thr do engine (NÃO afinar)
CRASH_WIN = 15          # janela de pré-formação (dias 1D) onde procuramos o crash que gerou o range
# SKIP do crash-born DESATIVADO 2026-07-15 (ordem Cris): o crash é CONTEXT-DEPENDENT — crash-no-topo =
# distribuição (skip), mas crash-no-fundo = CAPITULAÇÃO que reverte (LONG, camada Cp). A regra "crash=skip"
# foi generalizada de n=1 (2026). Fica o subtipo (informativo); o skip revisita-se no estudo das camadas C.
SKIP_CRASH_BORN = False
_GATE = None

def build_b_gate():
    """Série alinhada a M.T: por barra 1D dict(regime, range_subtype, b_long_allowed).
    range_subtype in {None, 'ORDERLY', 'POST_CRASH'} — fixado no ONSET do range (causal)."""
    T, H, L, C, Nn = M.T, M.H, M.L, M.C, M.N
    reg = M.build_layer1()
    crash_at = [((C[i]/C[i-2]-1)*100 <= CRASH_THR) if i >= 2 else False for i in range(Nn)]
    out = []; subtype = None
    for i in range(Nn):
        if reg[i] == "RANGE":
            if i == 0 or reg[i-1] != "RANGE":                 # onset de novo range
                onset = i
                subtype = "POST_CRASH" if any(crash_at[j] for j in range(max(2, onset-CRASH_WIN), onset+1)) else "ORDERLY"
            allowed = (subtype == "ORDERLY") if SKIP_CRASH_BORN else True   # skip desativado: qualquer RANGE
            out.append({"regime": "RANGE", "range_subtype": subtype, "b_long_allowed": allowed})
        else:
            subtype = None
            out.append({"regime": reg[i], "range_subtype": None, "b_long_allowed": False})
    return out

def gate_at(t):
    """Consulta causal por timestamp (epoch s). Regime conhecido 1 dia após o close 1D (T+86400)."""
    global _GATE
    if _GATE is None: _GATE = build_b_gate()
    KN = [x+86400 for x in M.T]
    i = bisect.bisect_right(KN, t)-1
    return _GATE[i] if i >= 0 else {"regime": None, "range_subtype": None, "b_long_allowed": False}

def b_long_allowed(t):
    return gate_at(t)["b_long_allowed"]

if __name__ == "__main__":
    import json, datetime as dt
    from pathlib import Path
    ds = lambda x: dt.datetime.utcfromtimestamp(int(x)).strftime("%Y-%m-%d")
    T, H, L, C, Nn = M.T, M.H, M.L, M.C, M.N
    gate = build_b_gate()
    # 1) episódios de RANGE históricos: subtipo vs resolução (evidência selada)
    epis = []
    for i in range(Nn):
        if epis and epis[-1][0] == gate[i]["regime"]: epis[-1][2] = i
        else: epis.append([gate[i]["regime"], i, i])
    print("== RANGE episódios (subtipo do gate vs resolução real) ==")
    ok = tot = 0
    for k, (s, a, b) in enumerate(epis):
        if s != "RANGE" or (T[b]-T[a]) < 5*86400 or a < 260: continue
        ex = epis[k+1][0] if k+1 < len(epis) else None
        if ex not in ("BULL", "BEAR"): continue
        sub = gate[a]["range_subtype"]; allow = gate[a]["b_long_allowed"]
        down = ex == "BEAR"; tot += 1
        # acerto do gate: SKIP(post_crash) sse distrib, ALLOW(orderly) coincide com acum? (recall parcial)
        good = "✓" if (sub == "POST_CRASH" and down) or (sub == "ORDERLY" and not down) else ("QUIET-DISTRIB(passa)" if down else "")
        ok += 1 if good == "✓" else 0
        print(f"  {ds(T[a])}  {sub:11} allow={str(allow):5} -> resolve {ex:4} {good}")
    print(f"  gate coincide com resolução: {ok}/{tot} (ORDERLY↔acum, POST_CRASH↔distrib); distrib-quietas passam por design")
    # 2) os 15 B fundos: KEEP vs SKIP
    GT = json.load(open(Path(__file__).resolve().parent/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
    B = sorted([f for f in GT["fundos"] if f.get("subclasse") == "B_range"], key=lambda x: x["t"])
    print("\n== 15 B fundos sob o gate ==")
    keep = 0
    for n, f in enumerate(B, 1):
        g = gate_at(int(f["t"])); allow = g["b_long_allowed"]; keep += allow
        print(f"  B#{n:2d} {ds(f['t'])}  {str(g['range_subtype']):11} -> {'KEEP (long-viável)' if allow else 'SKIP (distribuição)'}")
    print(f"  KEEP {keep}/15 · SKIP {15-keep}/15")
