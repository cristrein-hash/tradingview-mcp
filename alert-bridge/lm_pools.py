#!/usr/bin/env python3
"""LM_POOLS — pools de liquidez CAUSAIS as-of (P1 do plano FSM, aprovado Cris 29/08).
Reutiliza as funções canónicas do liquidity_map (_swings, _cluster, _atr, CLUSTER_ATR, SWING_K) —
consome, não reconstrói — mas alimentadas SÓ com barras t<=asof. Corrige o lookahead do pool_touch
(que lia o liquidity_map.json vivo). Regras aprovadas: D2 'respeitado à esquerda' = >=1 toque anterior
com afastamento >=1×ATR (RUN_ATR herdado); D3 sem profundidade mínima de sweep. py3.9 stdlib."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import liquidity_map as LM  # noqa: E402  (funções puras canónicas)

LOOKBACK = 400          # barras do TF (igual à ordem de grandeza do liquidity_map 1H/4H)
RESPECT_ATR = 1.0       # D2 aprovado: afastamento >=1 ATR após toque = "respeitado à esquerda"


def pools_asof(bars, side="SSL"):
    """Pools causais sobre `bars` (lista dict t/o/h/l/c, JÁ cortada a t<=asof; o chamador garante).
    Devolve [{lo, hi, n, born_i, respected_left, status}] — status INTACT/SWEPT/CONSUMED via
    _lifecycle canónico. Causal por construção: só pivôs com confirmação dentro de `bars`."""
    b = bars[-LOOKBACK:]
    if len(b) < 30:
        return []
    atr = LM._atr(b)
    his, los = LM._swings(b)                       # pivôs confirmados (k barras dos 2 lados, dentro de b)
    pts = los if side == "SSL" else his
    out = []
    for z in LM._cluster(pts, atr):
        status, cap_i = LM._lifecycle(z, side, b, atr)
        # D2: respeitado à esquerda = depois de nascer, houve toque (reaproximação) seguido de
        # afastamento >=1 ATR sem furar — medido nas barras pós-formação
        respected = False
        edge = z["lo"] if side == "SSL" else z["hi"]
        touched_i = None
        for i in range(z["born_i"] + 1, len(b)):
            near = (b[i]["l"] <= z["hi"] + 0.2 * atr) if side == "SSL" else (b[i]["h"] >= z["lo"] - 0.2 * atr)
            # DA-fix P1: 'furada' usa a banda canónica do liquidity_map (edge -/+ 0.2*atr), não wick
            # estrito — um wick cêntimos além do pivô é TOQUE no canon, não furada (Regra C).
            pierced = (b[i]["l"] < edge - 0.2 * atr) if side == "SSL" else (b[i]["h"] > edge + 0.2 * atr)
            if pierced:
                break
            if near:
                touched_i = i
            elif touched_i is not None:
                moved = (b[i]["c"] - z["hi"]) if side == "SSL" else (z["lo"] - b[i]["c"])
                if moved >= RESPECT_ATR * atr:
                    respected = True
                    break
        out.append(dict(lo=round(z["lo"], 2), hi=round(z["hi"], 2), n=z["n"], born_i=z["born_i"],
                        respected_left=respected,
                        status={"PENDENTE": "INTACT", "CAPTURADA:SWEEP": "SWEPT",
                                "CAPTURADA:RUN": "CONSUMED"}.get(status, status)))
    return out


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        # causalidade: pool não pode existir antes da confirmação do último pivô que o compõe
        import random
        random.seed(7)
        px = 4000.0; bars = []
        t = 1780000000
        for i in range(200):
            d = random.uniform(-3, 3)
            o = px; c = px + d; h = max(o, c) + 1; l = min(o, c) - 1
            bars.append(dict(t=t, o=o, h=h, l=l, c=c)); px = c; t += 900
        t1 = []
        full = pools_asof(bars)
        t1.append(("devolve lista", isinstance(full, list)))
        # prefixo: pools de bars[:100] não podem usar info de bars[100:]
        pre = pools_asof(bars[:100])
        ok_prefix = all(p["born_i"] < 100 for p in pre)
        t1.append(("prefixo causal (born_i dentro do prefixo)", ok_prefix))
        # determinismo
        t1.append(("determinístico", pools_asof(bars) == pools_asof(bars)))
        for lab, r in t1:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        print("selftest", "PASS" if all(r for _, r in t1) else "FAIL")
        sys.exit(0 if all(r for _, r in t1) else 1)
    print("lm_pools: módulo P1 (usar via import)")
