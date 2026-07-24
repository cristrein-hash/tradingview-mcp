#!/usr/bin/env python3
"""SMOKE-TEST da classify_zone nova (perna 1H + regra de zonas + gate reversão 4H/1D). Monkeypatch _e0 com os
snapshots reais AM(BEAR)/PM(BULL) de 2026-07-24 e alimenta zonas sintéticas. Verifica direção/modo/qualidade. py3.9."""
import sys
CORE = "/Users/cristrein/tradingview-mcp/my-strategy/core/price_shock"
sys.path.insert(0, CORE)
import price_shock_cycle as M

E0_PM = {  # 12:58 UTC — perna de alta (preço reclamou EMAs)
    "regime": {"v5_4h": {"regime": "BEAR"}},
    "mtf": {"60": {"leg": {"dir": "down"}, "swings": {
        "last_high": {"confirm_bar": 289, "price": 4141.2}, "last_low": {"confirm_bar": 316, "price": 4021.88}}}},
    "micro_15m": {"ema": {"pos": "above"}},
    "macro": {"real_yield_10y": 2.39}, "confluence": {"15": {"buy": {"n": 4}, "sell": {"n": 0}}},
}
E0_AM = {  # 01:42 UTC — perna de baixa (preço abaixo das EMAs)
    "regime": {"v5_4h": {"regime": "BEAR"}},
    "mtf": {"60": {"leg": {"dir": "down"}, "swings": {
        "last_high": {"confirm_bar": 300, "price": 4141.2}, "last_low": {"confirm_bar": 317, "price": 4040.73}}}},
    "micro_15m": {"ema": {"pos": "below"}},
    "macro": {"real_yield_10y": 2.39}, "confluence": {"15": {"buy": {"n": 0}, "sell": {"n": 0}}},
}
IM = {"bubbles": {"buy": 0, "sell": 0}, "regime": {"regime": "BEAR"},
      "momentum": {"rsi_5m": 50, "rsi_15m": 50, "rsi_1h": 50}}

def Z(ty, htf=None, inst=None):
    return {"type": ty, "ob_htf": htf or [], "institutional": bool(inst if inst is not None else (htf and len(htf) >= 1)),
            "nas_agree": False, "bub_agree": None, "svp": []}

CASES = [
    ("PM/BULL", E0_PM, Z("DEMAND"),               (8, "ALTA"),  "LONG", "continuação"),
    ("PM/BULL", E0_PM, Z("SUPPLY"),               (8, "BAIXA"), "LONG", "pullback-marker"),
    ("PM/BULL", E0_PM, Z("SUPPLY", ["4H"]),       (8, "BAIXA"), "SHORT", "reversão"),
    ("AM/BEAR", E0_AM, Z("SUPPLY"),               (8, "BAIXA"), "SHORT", "continuação"),
    ("AM/BEAR", E0_AM, Z("DEMAND"),               (8, "ALTA"),  "SHORT", "pullback-marker"),
    ("AM/BEAR", E0_AM, Z("DEMAND", ["1D"]),       (8, "ALTA"),  "LONG", "reversão"),
]

print("=== SMOKE classify_zone nova ===\n")
allok = True
for name, e0, z, exc, exp_want, exp_mode in CASES:
    M._e0 = lambda e=e0: e
    want, mode, q, ck = M.classify_zone(z, (exc[0], exc[1], None, None), IM)
    ok = (want == exp_want and mode == exp_mode)
    allok &= ok
    print(f"● {name} zona {z['type']:6} ob_htf={z['ob_htf']}")
    print(f"    → {want}/{mode}/{q}  (esperado {exp_want}/{exp_mode})  {'✅' if ok else '❌'}")
    print(f"    {ck}\n")
print("RESULTADO:", "✅ TUDO PASS" if allok else "❌ revisar")
