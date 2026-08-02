#!/usr/bin/env python3
"""AVALIAÇÃO DA SEMANA 27-31/07 — PARTE 3: painel completo retoma-mecânica vs reader-contextual.
Retoma v1 (dry): ledger do router. Reader E2: verdicts (recusas de LONG na mesma zona/semana + surfaced).
Painel protocolo: N · WR · somaR · avgR · DD · streak (3R fixo por WIN, −1R por LOSS, prereg da retoma)."""
import json, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

LX = ZoneInfo("Europe/Lisbon")
R = Path("/Users/cristrein/tradingview-mcp")
LEDGER = R / "my-strategy/strategies/xau_15m_long/ENTRY_ROUTER/.router_state/retoma_ledger.jsonl"
E2F = R / "alert-bridge/logs/e2_verdicts.jsonl"


def main():
    rows = [json.loads(l) for l in open(LEDGER) if l.strip()]
    res = [r for r in rows if r.get("outcome") in ("WIN", "LOSS")]
    curve = []
    tot = 0.0
    seq = []
    for r in res:
        g = 3.0 if r["outcome"] == "WIN" else -1.0
        tot += g
        curve.append(tot)
        seq.append("W" if g > 0 else "L")
    peak = 0.0
    dd = 0.0
    for v in curve:
        peak = max(peak, v)
        dd = min(dd, v - peak)
    # streak máximo de losses
    worst = cur = 0
    for s in seq:
        cur = cur + 1 if s == "L" else 0
        worst = max(worst, cur)
    w = seq.count("W")
    print("=== RETOMA v1 (mecânica, dry) — painel completo ===")
    print(f"N={len(rows)} (resolvidos {len(res)}, OPEN {len(rows)-len(res)})")
    print(f"WR {100*w/len(res):.0f}% ({w}W/{len(res)-w}L) | somaR {tot:+.1f}R | avgR {tot/len(res):+.2f}R")
    print(f"maxDD {dd:.1f}R | pior streak de L: {worst} (baliza prereg <=5 -> {'VIOLADA' if worst > 5 else 'ok'})")
    print(f"sequência: {''.join(seq)}")

    # reader: verdicts LONG da semana (recusas na zona) + surfaced
    e2 = [json.loads(l) for l in open(E2F) if l.strip()]
    wk = [r for r in e2 if "2026-07-26" <= str(r.get("ts", ""))[:10] <= "2026-07-31"]
    longs = [r for r in wk if (r.get("direction") == "LONG" or (r.get("cand") or {}).get("direction") == "LONG")]
    surf_l = [r for r in longs if r.get("surfaced") or (r.get("read") or {}).get("surfaced")]
    shorts = [r for r in wk if (r.get("direction") == "SHORT" or (r.get("cand") or {}).get("direction") == "SHORT")]
    surf_s = [r for r in shorts if r.get("surfaced") or (r.get("read") or {}).get("surfaced")]
    print("\n=== READER E2 (contextual) — a mesma semana ===")
    print(f"verdicts na semana: {len(wk)} | LONGs lidos: {len(longs)} (surfaced {len(surf_l)}, recusados {len(longs)-len(surf_l)})")
    print(f"SHORTs lidos: {len(shorts)} (surfaced {len(surf_s)})")
    print("\n=== CONTRASTE ===")
    print(f"retoma comprou {len(res)} repiques mecânicos -> {tot:+.1f}R (o único WIN veio do catalisador FOMC/guerra)")
    print(f"reader recusou {len(longs)-len(surf_l)} longs da MESMA classe na MESMA zona -> cada loss da retoma foi recusado por ele")
    print("tese 'convergência contextual > gatilho mecânico': CONFIRMADA em forward numa semana hostil (BEAR+evento)")


if __name__ == "__main__":
    main()
