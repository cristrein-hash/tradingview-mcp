#!/usr/bin/env python3
"""VIGIA R10 (Cris 2026-08-03): avisa quando o E1 gerar candidato top_fade (R10) — o fade de exaustão no
reteste da supply — e também ob_touch_hold SHORT (R9 na supply) e bos_continuation SHORT (R8), para cobertura
do reteste completo. Tail do e1_candidates.jsonl; dedup por (rule,entry~2pts). Read-only, poll 30s."""
import json, time, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

LX = ZoneInfo("Europe/Lisbon")
F = Path("/Users/cristrein/tradingview-mcp/alert-bridge/logs/e1_candidates.jsonl")
WATCH_RULES = {"top_fade": "R10 TOP_FADE", "ob_touch_hold": "R9 OB_TOUCH", "bos_continuation": "R8 CONTINUAÇÃO"}


def hm(x):
    try: return dt.datetime.fromisoformat(str(x).replace("Z", "+00:00")).astimezone(LX).strftime("%d/%m %H:%M")
    except Exception: return str(x)[:16]


def main():
    print("vigia R10/R9/R8 armado: aviso em qualquer candidato top_fade (prioridade), ob_touch_hold SHORT ou bos_continuation SHORT")
    pos = F.stat().st_size if F.exists() else 0
    seen = set()
    while True:
        try:
            size = F.stat().st_size
            if size < pos: pos = 0                      # rotação
            if size > pos:
                with open(F) as f:
                    f.seek(pos)
                    for line in f:
                        if not line.strip(): continue
                        try: r = json.loads(line)
                        except Exception: continue
                        c = r if "rule" in r else (r.get("cand") or {})
                        rule = c.get("rule")
                        if rule not in WATCH_RULES: continue
                        dirn = c.get("direction")
                        if rule != "top_fade" and dirn != "SHORT": continue   # R9/R8 só lado short (reteste)
                        en = c.get("entry")
                        k = (rule, dirn, round((en or 0) / 2) * 2)
                        if k in seen: continue
                        seen.add(k)
                        print(f"🔔 {WATCH_RULES[rule]} {dirn} gerado @ {hm(r.get('ts'))} | entry {en} SL {c.get('sl')} "
                              f"alvo {c.get('target')} RR {c.get('rr')} | src: {str(c.get('src'))[:90]}")
                    pos = f.tell()
        except Exception as e:
            print(f"vigia-r10 erro transitório: {type(e).__name__}")
        time.sleep(30)


if __name__ == "__main__":
    main()
