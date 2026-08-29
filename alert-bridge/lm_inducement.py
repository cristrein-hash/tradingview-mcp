#!/usr/bin/env python3
"""LM_INDUCEMENT — detetor de inducement (P2 do plano FSM aprovado Cris 29/08).
consolidation_check corrido (token .consolidation_token.json): capacidade inexistente no E0/código —
construção nova anunciada; consome context_structure.fractal_pivots (primitivo canónico do próprio E0),
não reconstrói estrutura paralela.

Doutrina (LIQUIDITY_METHOD §1/§3): "every time the market takes out a high, it's inducing buyers"
(espelho para lows). O induzido deixa stops atrás do extremo de ORIGEM da perna que rompeu — essa é a
liquidez que o sweep vai caçar. Multi-fatorial por construção: pivô confirmado (trajetória) + rompimento
na vela real (quebra) + origem estrutural.

Mecânica causal:
- BUYERS_INDUCED: barra fura (wick conta: H[i] > preço) o último swing-high confirmado (m=3).
  origem = último swing-low confirmado antes (stops dos induzidos ficam sob ele).
- SELLERS_INDUCED: espelho (L[i] < último swing-low; origem = swing-high anterior).
- Status: OPEN desde o rompimento; RESOLVED quando a ORIGEM é varrida (trap completo). Sem timer —
  morte só estrutural (regra do plano aprovado). py3.9 stdlib."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import context_structure as CS  # noqa: E402


def inducements(H, L, C, m=3):
    """Varre a série (causal) e devolve eventos de inducement com status no fim da série.
    [{t_idx, kind: BUYERS/SELLERS, broken_extreme, origin, origin_idx, status[, resolved_idx]}]"""
    piv = CS.fractal_pivots(H, L, m=m)
    events = []
    N = len(C)
    by_confirm = sorted(piv, key=lambda e: e[0])
    pi = 0
    last_high = None; last_low = None
    for i in range(N):
        while pi < len(by_confirm) and by_confirm[pi][0] <= i:
            e = by_confirm[pi]
            if e[1] == "H":
                last_high = e
            else:
                last_low = e
            pi += 1
        if last_high and H[i] > last_high[3]:
            if not any(ev["kind"] == "BUYERS" and ev["broken_extreme"] == last_high[3] for ev in events):
                events.append(dict(t_idx=i, kind="BUYERS", broken_extreme=last_high[3],
                                   origin=last_low[3] if last_low else None,
                                   origin_idx=last_low[2] if last_low else None, status="OPEN"))
            last_high = None
        if last_low and L[i] < last_low[3]:
            if not any(ev["kind"] == "SELLERS" and ev["broken_extreme"] == last_low[3] for ev in events):
                events.append(dict(t_idx=i, kind="SELLERS", broken_extreme=last_low[3],
                                   origin=last_high[3] if last_high else None,
                                   origin_idx=last_high[2] if last_high else None, status="OPEN"))
            last_low = None
        for ev in events:
            if ev["status"] != "OPEN" or ev["origin"] is None or ev["t_idx"] >= i:
                continue
            if ev["kind"] == "BUYERS" and L[i] < ev["origin"]:
                ev["status"] = "RESOLVED"; ev["resolved_idx"] = i
            elif ev["kind"] == "SELLERS" and H[i] > ev["origin"]:
                ev["status"] = "RESOLVED"; ev["resolved_idx"] = i
    return events


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        H = [10, 11, 12, 11, 10, 11, 12, 13, 14, 15, 14, 12, 10, 8, 7]
        L = [9, 10, 11, 10, 9, 10, 11, 12, 13, 14, 13, 11, 9, 7, 6]
        C = [9.5, 10.5, 11.5, 10.5, 9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 13.5, 11.5, 9.5, 7.5, 6.5]
        evs = inducements(H, L, C, m=2)
        t = []
        t.append(("gera eventos", len(evs) >= 1))
        b = [e for e in evs if e["kind"] == "BUYERS"]
        t.append(("buyers induced no rompimento do high", len(b) >= 1))
        t.append(("resolve quando origem varrida", any(e["status"] == "RESOLVED" for e in b)))
        t.append(("resolved_idx > t_idx (causal)", all(e.get("resolved_idx", 10**9) > e["t_idx"] for e in evs)))
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        print("selftest", "PASS" if all(r for _, r in t) else "FAIL")
        sys.exit(0 if all(r for _, r in t) else 1)
    print("lm_inducement: módulo P2 (usar via import)")
