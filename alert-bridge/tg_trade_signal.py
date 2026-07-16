#!/usr/bin/env python3
"""Sinal de trade via Telegram (desafio Cris 2026-07-16) — formato simples/scannable + alarme repetido
(3-5× seguidas) para o Cris saber que é chamada de trade. Reusa send_telegram do auto_d2r_daily
(mesmo bot/chat, tokens do .env; nunca expostos). Uso:
  python3 tg_trade_signal.py --test
  from tg_trade_signal import send_trade_signal
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_d2r_daily import send_telegram

def build(direction, entry, sl, tp2, tp3, reason, test=False):
    arrow = "🟢 LONG" if direction.upper() == "LONG" else "🔴 SHORT"
    head = "🚨🚨 <b>SINAL DE TRADE</b> 🚨🚨" if not test else "🚨🚨 <b>SINAL DE TRADE (TESTE)</b> 🚨🚨"
    lines = [
        head, "<b>XAUUSD · Pepperstone</b>", "",
        f"Direção: <b>{arrow}</b>",
        f"Entry: <b>{entry}</b>",
        f"SL: <b>{sl}</b>  (risco ~100€)",
        f"TP 2R: <b>{tp2}</b>   |   ext 3R: <b>{tp3}</b>", "",
        f"Motivo: {reason}",
    ]
    if test:
        lines += ["", "⚠️ <b>TESTE — NÃO EXECUTAR</b>", "(No sinal real executas TU. Alarme = 3-5× seguidas.)"]
    else:
        lines += ["", "▶️ Executa TU (proxy). Não mexer nos limits."]
    return "\n".join(lines)

def send_trade_signal(direction, entry, sl, tp2, tp3, reason, test=False, repeat=3):
    text = build(direction, entry, sl, tp2, tp3, reason, test)
    oks = []
    for i in range(repeat):
        r = send_telegram(text)
        oks.append(bool(r.get("ok")))
        if i < repeat-1: time.sleep(1.2)
    return {"sent": repeat, "ok_all": all(oks), "oks": oks}

if __name__ == "__main__":
    if "--test" in sys.argv:
        res = send_trade_signal(
            direction="LONG", entry="4059.5", sl="4045.0", tp2="4087.5", tp3="4101.5",
            reason="exemplo — confluência fundo + regime BULL + EF alinhado (formato de demonstração)",
            test=True, repeat=3)
        print(res)
