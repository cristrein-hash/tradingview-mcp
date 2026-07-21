#!/usr/bin/env python3
"""Telegram CANDIDATE NOTIFICATION (real) — L1 · EMA21 CONTINUATION (Production v2).

Envia uma NOTIFICAÇÃO DE CANDIDATO ("revise o chart") — NUNCA uma ordem de entrada.
A entrada é 100% decisão humana. Default = DRY-RUN (só imprime). Envio real exige --send.

Segurança:
- allowlist EXPLÍCITA: só `L1_EMA21_CONTINUATION` pode notificar.
- só notifica candidato OPERACIONAL (scanner: operational=true; bloqueado pelo gate RSI = NÃO notifica).
- credenciais lidas de `alert-bridge/.env` (gitignored) — nunca expostas/hardcoded.
- a mensagem NÃO pode conter "entre comprado" / "entrada aprovada" / "trade validado" / comando de ordem.
- não aciona broker/MCP/ordem.

Uso:
  python3 scanner.py --at <ts> | python3 telegram_notify.py            # dry-run (imprime)
  python3 scanner.py --at <ts> | python3 telegram_notify.py --send     # envio real (1 candidato operacional)
  python3 telegram_notify.py --test --send                             # 1 envio de teste marcado
"""
import json, sys, argparse, os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _production_authorized():
    """HARD-LOCK (2026-07-09): envio real de Telegram exige env L1_PRODUCTION_AUTHORIZED=1.
    Fecha o escape manual `--send` — mesmo invocado diretamente, NÃO envia sem autorização de produção.
    Telegram disabled until Cris explicitly authorizes production. Só PREVINE envio, nunca ativa."""
    return os.environ.get("L1_PRODUCTION_AUTHORIZED", "") == "1"

ALLOWLIST = {"L1_EMA21_CONTINUATION"}
STRATEGY_LABEL = "L1 · EMA21 CONTINUATION"
SUITE = "XAU 4H LONG — CONTINUATION"
TEST_BANNER = "TEST L1 XAU 4H RUNTIME CANDIDATE NOTIFICATION — DO NOT TRADE"

# frases proibidas (guard de segurança da mensagem)
FORBIDDEN = ("entre comprado", "entrada aprovada", "trade validado", "buy now", "comprar agora")


def _repo_root(p):
    for d in [p] + list(p.parents):
        if (d / "my-strategy").is_dir() and (d / "alert-bridge").is_dir():
            return d
    return p.parents[5]


def load_env():
    """Lê alert-bridge/.env (gitignored). Retorna dict; nunca imprime valores."""
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


def build_message(cand):
    return "\n".join([
        f"🔔 {SUITE}",
        f"   {STRATEGY_LABEL}",
        f"{cand.get('symbol','PEPPERSTONE:XAUUSD')} · {cand.get('timeframe','240')} · {cand.get('timestamp','?')}",
        "",
        "CANDIDATE — revise o chart.",
        "Alerta de candidato para revisão. A entrada é decisão 100% humana; este aviso não é sinal de compra.",
        f"signal_hash: {cand.get('signal_hash')}",
    ])


def send_telegram(text):
    import os
    if os.path.exists("/Users/cristrein/tradingview-mcp/.telegram_muted"):
        return False                                    # 🔇 MUTE GLOBAL — Cris pausou os sinais (2026-07-21)
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_raw = env.get("TELEGRAM_CHAT_IDS") or env.get("TELEGRAM_CHAT_ID")
    if not token or not chat_raw:
        print("error: Telegram não configurado em alert-bridge/.env", file=sys.stderr)
        return False
    chat_ids = [x.strip() for x in chat_raw.split(",") if x.strip()]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    ok = True
    for cid in chat_ids:
        data = urlencode({"chat_id": cid, "text": text, "disable_web_page_preview": "true"}).encode()
        try:
            with urlopen(Request(url, data=data, method="POST"), timeout=20) as resp:
                ok = ok and bool(json.loads(resp.read().decode()).get("ok"))
        except Exception as e:
            print(f"error: Telegram send falhou: {e}", file=sys.stderr); ok = False
    return ok


def main():
    ap = argparse.ArgumentParser(description="L1 candidate notification (real, allowlist-gated).")
    ap.add_argument("--send", action="store_true", help="envio real (default: dry-run, só imprime)")
    ap.add_argument("--test", action="store_true", help="envia a mensagem de teste marcada (sem candidato)")
    args = ap.parse_args()

    if args.test:
        text = TEST_BANNER + f"\n{SUITE}\n   {STRATEGY_LABEL}\nCanal/format/segurança — validação. NÃO É ORDEM."
    else:
        raw = sys.stdin.read().strip()
        if not raw:
            print("error: no candidate JSON on stdin", file=sys.stderr); return 2
        cand = json.loads(raw)
        route = cand.get("strategy_route") or "L1_EMA21_CONTINUATION"  # scanner candidate = L1 por construção
        if route not in ALLOWLIST:
            print(f"[notify] strategy '{route}' fora da allowlist — não notifica."); return 0
        if not cand.get("operational"):
            print(f"[notify] candidato NÃO operacional (state={cand.get('state')}) — bloqueado, sem notificação Telegram."); return 0
        text = build_message(cand)

    # guard de conteúdo: nunca enviar/imprimir mensagem com frase proibida
    low = text.lower()
    bad = [p for p in FORBIDDEN if p in low]
    if bad:
        print(f"error: mensagem contém frase proibida {bad} — abortado.", file=sys.stderr); return 2

    if args.send and not _production_authorized():
        print("[notify] PRODUCTION_NOT_AUTHORIZED — envio bloqueado (env L1_PRODUCTION_AUTHORIZED!=1). "
              "Telegram disabled until Cris explicitly authorizes production.")
        print("=== DRY-RUN FORÇADO (hard-lock) ===")
        print(text)
        return 0
    if args.send:
        ok = send_telegram(text)
        print(f"[notify] SENT={ok} (TELEGRAM_LIVE)")
        return 0 if ok else 1
    else:
        print("=== DRY-RUN (não enviado; use --send para enviar) ===")
        print(text)
        return 0


if __name__ == "__main__":
    sys.exit(main())
