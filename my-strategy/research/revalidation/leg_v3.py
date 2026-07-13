#!/usr/bin/env python3
"""LEG v3 = APROVADO Cris 2026-07-13 (SYNTH conservadora do engine multi-agente de refino do AC).
Segundo nível de leitura (4H) sob a luz do MACRO 1D (Layer1). Parte do leg base (macro-independente,
zigzag R=6) e RESOLVE os bares ACUMULACAO em direção — SÓ com alta confiança — pela confluência:
 (1) direção HERDADA da perna-em-curso (base_dir; não inventada por escalas finas = moeda-ao-ar);
 (2) momentum confirma (ret10) + persiste (ret5) no sentido da perna;
 (3) ACELERAÇÃO sustentada no horizonte longo (ret20 mesmo sinal, |ret20|>=2.5);
 (4) piso de amplitude |ret10|>=1.5 (reforçado 1.3× em pernas jovens <24 barras);
 (5) dupla escala fina fd3/fd4 NÃO contradiz (viragem incipiente => manter AC).
Coerência com o macro PRESERVADA por construção (baixa-em-bull => PULLBACK, nunca anti-impulso).
Auditado (árbitro fino R=3 retrospectivo): precisão 87% · especificidade 93% · recall 6% ·
AC 42%->39% · frag 260. CAVEAT registado: o árbitro é momentum-correlacionado (base_dir sozinho=57%),
logo a precisão está parcialmente embutida; o ganho robusto é a especificidade (separar plano de
direcional) + a lição estrutural (AC = continuação da perna). Causal close-only. RAW-only. Sem P&L.
API: build_leg_v3() -> lista alinhada a TS4 de {t, macro, leg, [leg_dir], resolved}."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import leg_refine_harness as H

FLOOR = 1.5; RET20_FLOOR = 2.5; AGE_MIN = 24; YOUNG_MULT = 1.3
def _sgn(x): return "UP" if x > 0 else "DOWN"

def _resolve(c):
    d = c["base_dir"]
    if d not in ("UP", "DOWN"): return None
    opp = "DOWN" if d == "UP" else "UP"
    if _sgn(c["ret10"]) != d or _sgn(c["ret5"]) != d: return None            # confirma + persiste
    if _sgn(c["ret20"]) != d or abs(c["ret20"]) < RET20_FLOOR: return None   # aceleração longa
    floor = FLOOR * (YOUNG_MULT if (c["base_age"] or 0) < AGE_MIN else 1.0)
    if abs(c["ret10"]) < floor: return None                                  # amplitude média
    if c["fd3"] == opp or c["fd4"] == opp: return None                       # fina não contradiz
    return d

def build_leg_v3():
    out = []
    for t in H.TS4:
        base = H.BASE_LEG.get(t, {}).get("leg"); mac = H.macro_at(t)
        if base is None or base == "WARMUP" or mac is None:
            out.append({"t": t, "macro": mac, "leg": base or "WARMUP", "resolved": False}); continue
        if base != "ACUMULACAO":
            out.append({"t": t, "macro": mac, "leg": base, "resolved": False}); continue
        d = _resolve(H.ctx(t))
        if d in ("UP", "DOWN"):
            out.append({"t": t, "macro": mac, "leg": H._map(mac, d), "leg_dir": d, "resolved": True})
        else:
            out.append({"t": t, "macro": mac, "leg": "ACUMULACAO", "resolved": False})
    return out

if __name__ == "__main__":
    # verificação: reproduz o harness+SYNTH nos bares AC 2019+ (byte-a-byte)?
    import importlib
    S = importlib.import_module("legcand_SYNTH")
    href = {r["t"]: r["leg"] for r in H.run(S)}
    v3 = {r["t"]: r["leg"] for r in build_leg_v3() if r["t"] in href}
    diff = sum(1 for t in href if href[t] != v3.get(t))
    print(f"leg_v3 vs harness+SYNTH (2019+): diffs {diff}/{len(href)}  -> {'IDÊNTICO' if diff == 0 else 'DIVERGE'}")
    from collections import Counter
    c = Counter(r["leg"] for r in build_leg_v3() if r["t"] >= H.T2019)
    tot = sum(c.values()) or 1
    print("distribuição leg v3 (2019+):", {k: f"{100*v/tot:.0f}%" for k, v in c.most_common()})
