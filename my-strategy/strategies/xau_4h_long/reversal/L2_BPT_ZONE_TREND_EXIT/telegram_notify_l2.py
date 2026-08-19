#!/usr/bin/env python3
"""Telegram CANDIDATE/EXIT NOTIFICATION — L2/BPT ZONE TREND-EXIT (espelho do telegram_notify.py L1).

ADVISORY SEMPRE, NUNCA ORDEM. Dois formatos:
  ENTRY — "candidato L2/BPT — revise o chart": entry/SL/risk_pts/zona/regime (+WIDE_STOP se risk>80)
  EXIT  — "saída L2/BPT": motivo REGIME_FLIP/STOP/CAP (+LATE) + signal_hash da entrada

Segurança (guards replicados da L1):
- allowlist EXPLÍCITA: só `L2_BPT_ZONE_TREND_EXIT`.
- só notifica payload operacional (runtime decide); frases proibidas bloqueiam o envio.
- HARD-LOCK: envio real exige env L2_PRODUCTION_AUTHORIZED=1 (NASCE TRAVADO — mesmo com --send,
  dry-run forçado). Telegram disabled until Cris explicitly authorizes production.
- credenciais de alert-bridge/.env (gitignored); nunca expostas. Não aciona broker/MCP/ordem.

Uso: echo '<payload json>' | python3 telegram_notify_l2.py [--send]
     python3 telegram_notify_l2.py --test [--send]
"""
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ALLOWLIST = {"L2_BPT_ZONE_TREND_EXIT"}
STRATEGY_LABEL = "L2 · BPT ZONE TREND-EXIT"
SUITE = "XAU 4H LONG — REVERSAL"
TEST_BANNER = "TEST L2 XAU 4H RUNTIME NOTIFICATION — DO NOT TRADE"
WIDE_STOP_PTS = 80

# frases proibidas (guard de conteúdo — nunca linguagem de ordem)
FORBIDDEN = ("entre comprado", "entrada aprovada", "trade validado", "buy now", "comprar agora",
             "feche agora", "venda agora", "sell now")


def _production_authorized():
    """HARD-LOCK: envio real exige env L2_PRODUCTION_AUTHORIZED=1. Só PREVINE envio, nunca ativa."""
    return os.environ.get("L2_PRODUCTION_AUTHORIZED", "") == "1"


def _repo_root(p):
    for d in [p] + list(p.parents):
        if (d / "my-strategy").is_dir() and (d / "alert-bridge").is_dir():
            return d
    return p.parents[5]


def load_env():
    """Lê alert-bridge/.env (gitignored). Nunca imprime valores."""
    env = {}
    envp = _repo_root(Path(__file__).resolve().parent) / "alert-bridge" / ".env"
    if envp.exists():
        for line in envp.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def build_entry_message(c):
    zona = c.get("zona") or {}
    zdesc = ""
    if zona.get("regime") == "BEAR" and zona.get("zdeep"):
        zdesc = f"zona bear_deep: {zona['zdeep'][0]}–{zona['zdeep'][1]}"
    elif zona.get("regime") == "BULL" and zona.get("ztop"):
        zdesc = f"zona top: {zona['ztop'][0]}–{zona['ztop'][1]}"
    elif zona.get("regime") == "RANGE":
        zdesc = f"pos no range: {zona.get('pos')}"
    late = f" · LATE ({c.get('late_bars')} barras)" if c.get("late_bars") else ""
    wide = "\n⚠️ WIDE_STOP (risk > 80 pts)" if c.get("wide_stop") else ""
    # formato único notify.py (Cris 2026-08-19); signal_hash/risk_pts ficam no ledger
    ev = "CANDIDATO" + late + (" · ⚠️ WIDE_STOP" if c.get("wide_stop") else "")
    return "\n".join([
        "🎯 ENTRADA · L2 BPT · 4H",
        "──────────────",
        f"🟢 LONG XAUUSD — {ev}",
        f"entry   {c.get('entry')}",
        f"SL      {c.get('sl')}",
        f"regime  {c.get('regime')} · {zdesc}",
        "──────────────",
        "decisão humana · #N",
    ])


def build_exit_message(c):
    late = f" · LATE ({c.get('late_bars')} barras)" if c.get("late_bars") else ""
    return "\n".join([
        "⚡ AVISO · L2 BPT SAÍDA · 4H",
        "──────────────",
        f"saída {c.get('mot')}{late} · R {c.get('R')}",
        "gestão advisory — decisão humana",
        "──────────────",
    ])


def send_telegram(text):
    # 2026-08-19: prefixo removido + AUDIT-FIX RC1: transporte delegado ao notify.py (rota única).
    # Hard-lock L2_PRODUCTION_AUTHORIZED continua no main() deste módulo. Saída L2 (header ⚡) vai a
    # shadow automaticamente via notify (decisão Cris 19/08).
    try:
        sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
        import notify as NF
        return NF._send(text, "group") is True
    except Exception as e:
        print(f"error: Telegram send falhou: {e}", file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser(description="L2 notification (advisory, allowlist-gated).")
    ap.add_argument("--send", action="store_true", help="envio real (default: dry-run)")
    ap.add_argument("--test", action="store_true", help="mensagem de teste marcada")
    args = ap.parse_args()

    if args.test:
        text = TEST_BANNER + f"\n{SUITE}\n   {STRATEGY_LABEL}\nCanal/format/segurança — validação. NÃO É ORDEM."
    else:
        raw = sys.stdin.read().strip()
        if not raw:
            print("error: no payload JSON on stdin", file=sys.stderr)
            return 2
        c = json.loads(raw)
        route = c.get("strategy_route")
        if route not in ALLOWLIST:
            print(f"[notify-l2] strategy '{route}' fora da allowlist — não notifica.")
            return 0
        if not c.get("operational"):
            print(f"[notify-l2] payload NÃO operacional — bloqueado, sem Telegram.")
            return 0
        kind = c.get("kind")
        if kind == "entry":
            text = build_entry_message(c)
        elif kind == "exit":
            text = build_exit_message(c)
        else:
            print(f"error: kind desconhecido '{kind}'", file=sys.stderr)
            return 2

    low = text.lower()
    bad = [p for p in FORBIDDEN if p in low]
    if bad:
        print(f"error: mensagem contém frase proibida {bad} — abortado.", file=sys.stderr)
        return 2

    if args.send and not _production_authorized():
        print("[notify-l2] PRODUCTION_NOT_AUTHORIZED — envio bloqueado (env L2_PRODUCTION_AUTHORIZED!=1). "
              "Telegram disabled until Cris explicitly authorizes production.")
        print("=== DRY-RUN FORÇADO (hard-lock) ===")
        print(text)
        return 0
    if args.send:
        ok = send_telegram(text)
        print(f"[notify-l2] SENT={ok} (TELEGRAM_LIVE)")
        return 0 if ok else 1
    print("=== DRY-RUN (não enviado; use --send p/ enviar — hard-lock continua a mandar) ===")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
