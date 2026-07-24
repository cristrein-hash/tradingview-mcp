#!/usr/bin/env python3
"""VALIDAÇÃO do leitor de PERNA 1H (Cris 2026-07-24) nos 2 casos reais de hoje.
Regra: a perna atual (1H) manda a direção. Perna BULL → demanda=BUY (supply 15M/1H = só marca pullback p/ demanda
mais baixa, NÃO vende); perna BEAR → supply=SELL (demanda 15M/1H = só marca pullback p/ supply mais alto, NÃO compra).
Reversão (vender em bull / comprar em bear) só em OB 4H/1D + confluências.

Leitor da perna: pivô mais recente (low→viés up, high→viés down) CONFIRMADO por reclaim/perda das EMAs (15M pos).
Se pivô e EMA discordam = virada NÃO confirmada → mantém a direção dominante da perna 1H (leg.dir). py3.9.

Os 2 snapshots E0 abaixo são os do próprio dia (frozen dos reads desta sessão):
  AM 01:42 UTC (preço 4047, depois FLUSHOU a 4025.7)  |  PM 12:58 UTC (preço 4055, depois SUBIU a 4070)
"""

CASES = {
    "AM 01:42 (flush)": {
        "price": 4047.0,
        "mtf60": {"trend": "RANGE", "leg_dir": "down",
                  "last_high": 4141.2, "last_high_cbar": 300, "last_low": 4040.73, "last_low_cbar": 317,
                  "prev_high": 4166.19, "prev_low": 4040.16},
        "ema_pos": "below",        # close 4042.97 vs ema9 4046 / ema21 4047.6 / ema50 4056.4
        "actual": "FLUSH DOWN a 4025.7 (perna de baixa continuou)",
        "cris_expects": "BEAR (supply=sell, continuação)",
    },
    "PM 12:58 (up-leg)": {
        "price": 4055.29,
        "mtf60": {"trend": "DOWN", "leg_dir": "down",
                  "last_high": 4141.2, "last_high_cbar": 289, "last_low": 4021.88, "last_low_cbar": 316,
                  "prev_high": 4166.19, "prev_low": 4040.73},
        "ema_pos": "above",        # close 4055.29 vs ema21 4054.2 / ema50 4050.7 (reclaim)
        "actual": "SUBIU a 4070 (perna de alta; recuo a 4052 era pullback de compra)",
        "cris_expects": "BULL (demanda=buy; NÃO shortar supply 15M)",
    },
}


def leg_1h(c):
    m = c["mtf60"]
    recent_pivot = "low" if m["last_low_cbar"] > m["last_high_cbar"] else "high"
    pivot_bias = "up" if recent_pivot == "low" else "down"
    ema_confirm = "up" if c["ema_pos"] == "above" else "down"
    hh = m["last_high"] > m["prev_high"]; hl = m["last_low"] > m["prev_low"]
    lh = m["last_high"] < m["prev_high"]; ll = m["last_low"] < m["prev_low"]
    struct = "HH+HL" if (hh and hl) else "LH+LL" if (lh and ll) else ("LH+HL" if (lh and hl) else "misto")
    # virada confirmada só quando pivô-bias E ema concordam; senão mantém a dominante (leg.dir)
    if pivot_bias == "up" and ema_confirm == "up":
        leg = "BULL"; why = "pivô-recente=LOW + reclaim EMAs = virada de alta CONFIRMADA"
    elif pivot_bias == "down" and ema_confirm == "down":
        leg = "BEAR"; why = "pivô-recente=HIGH + perda EMAs = virada de baixa CONFIRMADA"
    else:
        leg = "BEAR" if m["leg_dir"] == "down" else "BULL"
        why = f"pivô({pivot_bias}) e EMA({ema_confirm}) DISCORDAM → virada não confirmada → mantém dominante leg.dir={m['leg_dir']}"
    return leg, struct, recent_pivot, pivot_bias, ema_confirm, why


def zone_rule(leg):
    if leg == "BULL":
        return ("demanda 15M/1H = BUY (na confluência) · supply 15M/1H = só marca pullback p/ demanda mais baixa, "
                "NÃO vende · SELL só em supply OB 4H/1D + confluências")
    return ("supply 15M/1H = SELL (na confluência) · demanda 15M/1H = só marca pullback p/ supply mais alto, "
            "NÃO compra · BUY só em demanda OB 4H/1D + confluências")


print("=== VALIDAÇÃO LEITOR DE PERNA 1H — 2 casos de hoje ===\n")
allok = True
for name, c in CASES.items():
    leg, struct, piv, pbias, emac, why = leg_1h(c)
    ok = c["cris_expects"].startswith(leg)
    allok &= ok
    print(f"● {name} · preço {c['price']}")
    print(f"    1H swings: last_high {c['mtf60']['last_high']}(cbar {c['mtf60']['last_high_cbar']}) / "
          f"last_low {c['mtf60']['last_low']}(cbar {c['mtf60']['last_low_cbar']}) · estrutura {struct}")
    print(f"    pivô recente = {piv} (viés {pbias}) · EMA 15M = {c['ema_pos']} ({emac}) · leg.dir 1H = {c['mtf60']['leg_dir']}")
    print(f"    → PERNA = {leg}  [{why}]")
    print(f"    → regra de zonas: {zone_rule(leg)}")
    print(f"    real: {c['actual']}")
    print(f"    esperado pelo Cris: {c['cris_expects']}  → {'✅ BATE' if ok else '❌ NÃO BATE'}\n")

print("RESULTADO:", "✅ leitor de perna 1H acerta os 2 casos" if allok else "❌ falha algum caso")
