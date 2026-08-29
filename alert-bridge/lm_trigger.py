#!/usr/bin/env python3
"""LM_TRIGGER — P3 da máquina (5 regras da união Cris×trader, CRIS_VS_TRADER_GRAMMAR.md, aprovadas).
Candidato LONG nasce quando: POOL SSL válido (lm_pools: wick respeitado à esquerda, intacto) está a ser
VARRIDO na barra corrente (wick penetra, regra 5) + existe ALVO (pool BSL real acima, regra 4, cap 5R)
→ entrada = TAP-LIMIT no topo do pool (regra 2, fill no wick, sem esperar fecho); STOP = além do extremo
do pool − 0.1 ATR (regra 3); inválido se alvo já tomado (regra 4). Consome lm_pools/liquidity_map.
py3.9 stdlib. Módulo puro (sem side effects) — usado pelo replay e futuro live."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import lm_pools as LP  # noqa: E402
import liquidity_map as LM  # noqa: E402

MAX_R = 5.0            # D5 aprovado
SL_BUF = 0.1           # regra 3 (canónico)


def candidates_at(bars):
    """Candidatos LONG na ÚLTIMA barra de `bars` (causal). Devolve lista de
    {limit, sl, target, r, pool, sweeping, respected} — sweeping=True se o wick da barra corrente
    está a penetrar o pool (momento do tap-limit)."""
    if len(bars) < 120:
        return []
    atr = LM._atr(bars[-400:])
    cur = bars[-1]
    ssl = LP.pools_asof(bars, side="SSL")
    bsl = LP.pools_asof(bars, side="BSL")
    out = []
    for p in ssl:
        # Cris 29/08 (c): pool só morre por RUN confirmado (atravessou-e-ficou); fura-e-volta = vivo
        if p["status"] == "CONSUMED":
            continue
        limit = p["hi"]
        sl = p["lo"] - SL_BUF * atr
        risk = limit - sl
        if risk <= 0.05 * atr or risk > 2.5 * atr:
            continue
        # Cris 29/08 (a): ALVO FIXO 3R (gestão é dele); (b): check de ESPAÇO = existe nível BSL
        # nunca-tocado (INTACT) acima do alvo mínimo? (não define o preço do alvo, só valida espaço)
        tgt = limit + 3.0 * risk
        room = any(b["lo"] > limit for b in bsl if b["status"] == "INTACT")
        if not room:
            continue
        sweeping = cur["l"] <= limit                     # wick a penetrar o pool AGORA (tap possível)
        out.append(dict(limit=round(limit, 2), sl=round(sl, 2), target=round(tgt, 2),
                        r=3.0, pool=[p["lo"], p["hi"]], sweeping=bool(sweeping),
                        respected=p["respected_left"]))
    return out


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        import random
        random.seed(3)
        px = 4000.0; bars = []
        t = 1780000000
        for i in range(300):
            d = random.uniform(-2.5, 2.8)
            o = px; c = px + d; h = max(o, c) + 1.2; l = min(o, c) - 1.2
            bars.append(dict(t=t, o=o, h=h, l=l, c=c)); px = c; t += 900
        cs = candidates_at(bars)
        t1 = [("devolve lista", isinstance(cs, list))]
        for c in cs:
            t1.append(("sl<limit<target", c["sl"] < c["limit"] < c["target"]))
            t1.append(("r em [1,5]", 1.0 <= c["r"] <= 5.0))
        t1.append(("determinístico", candidates_at(bars) == candidates_at(bars)))
        for lab, r in t1:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        print("selftest", "PASS" if all(r for _, r in t1) else "FAIL")
        sys.exit(0 if all(r for _, r in t1) else 1)
    print("lm_trigger: módulo P3 (usar via import)")
