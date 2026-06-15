#!/usr/bin/env python3
"""Dry-run live input adapter — Production v2 core primitive.

Recebe um evento bruto estilo TradingView/webhook (dict), normaliza via
`input_normalization.classify_input_event` (whitelist + quarantine), e produz um
payload de candidato DRY-RUN compatível com o fluxo L1 — SEM conectar ao receiver,
SEM rodar o scanner, SEM Telegram/broker/MCP.

Puro/headless: sem Flask/server, sem receiver importado, sem IO real, sem side
effects no import, sem escrita em logs. Apenas transforma o evento em payload.

Roteamento: XAUUSD em 4H → route 'L1_EMA21_CONTINUATION' (NÃO aciona o scanner
aqui; só marca a rota). Símbolo aceito mas fora de XAUUSD/4H → route None
(unsupported_route). Símbolo não autorizado → accepted=false + quarantine_reason.
"""
from input_normalization import classify_input_event

L1_ROUTE = "L1_EMA21_CONTINUATION"
_TF_4H = {"4H", "4h", "240", "240M", "240m", "h4", "H4"}


def _norm_tf(raw):
    """Normaliza timeframe para '240' se for 4H; senão devolve o valor cru (str)."""
    if raw is None:
        return ""
    s = str(raw).strip()
    return "240" if s in _TF_4H else s


def adapt_live_event(event):
    """Transforma um evento bruto em payload de candidato DRY-RUN (sem side effects)."""
    if not isinstance(event, dict):
        return {"accepted": False, "dry_run": True, "review_required": True,
                "telegram_allowed": False, "execution_mode": "NONE",
                "quarantine_reason": "event_not_a_dict", "signal_hash": None}

    timeframe = event.get("timeframe") or event.get("interval") or ""
    timestamp = event.get("timestamp") or event.get("time") or event.get("ts_signal") or ""
    indicator = event.get("indicator") or event.get("indicator_name") or ""
    signal_type = event.get("signal_type") or ""

    # sub-evento canônico p/ classify (nomes de campo consistentes -> hash determinístico)
    canon = {
        "symbol": event.get("symbol") or event.get("ticker") or "",
        "timeframe": timeframe,
        "ts_signal": timestamp,
        "indicator_name": indicator,
        "signal_type": signal_type,
    }
    cls = classify_input_event(canon)

    out = {
        "accepted": cls["accepted"],
        "signal_hash": cls["signal_hash"],
        "normalized_symbol": cls["normalized_symbol"],
        "base_symbol": cls["base_symbol"],
        "provider": cls["provider"],
        "timeframe": timeframe,
        "timestamp": timestamp,
        "review_required": True,
        "telegram_allowed": False,
        "execution_mode": "NONE",
        "dry_run": True,
    }

    if not cls["accepted"]:
        out["strategy_route"] = None
        out["quarantine_reason"] = cls.get("quarantine_reason")
        return out

    # aceito: decidir rota (SEM rodar scanner)
    if cls["base_symbol"] == "XAUUSD" and _norm_tf(timeframe) == "240":
        out["strategy_route"] = L1_ROUTE
    else:
        out["strategy_route"] = None
        out["route_note"] = "unsupported_route"
    return out
