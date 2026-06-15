#!/usr/bin/env python3
"""Group model XAU-only (Production v2). Agrupa estratégias por (símbolo, timeframe, layout).

Escopo: APENAS XAU. Sem multi-ativo. 240 ativo (L1); 60/15 RESERVADOS (sem estratégia
aprovada, sem Telegram). Sem side effects no import.
"""

SYMBOL = "PEPPERSTONE:XAUUSD"

GROUPS = {
    "XAU_240": {
        "symbol": SYMBOL, "timeframe": "240", "layout": "XAU_LAYOUT",
        "active": True,
        "consumers": ["L1_EMA21_CONTINUATION"],          # única estratégia ativa
        "telegram_allowed_consumers": ["L1_EMA21_CONTINUATION"],
    },
    # RESERVADOS — preparação multi-timeframe XAU. NÃO ativos, NÃO podem enviar Telegram.
    "XAU_60": {
        "symbol": SYMBOL, "timeframe": "60", "layout": "XAU_LAYOUT",
        "active": False, "consumers": [], "telegram_allowed_consumers": [],
        "note": "reservado p/ futura estratégia XAU 1H — sem estratégia aprovada, sem Telegram",
    },
    "XAU_15": {
        "symbol": SYMBOL, "timeframe": "15", "layout": "XAU_LAYOUT",
        "active": False, "consumers": [], "telegram_allowed_consumers": [],
        "note": "reservado p/ futura estratégia XAU 15M — sem estratégia aprovada, sem Telegram",
    },
}


def active_groups():
    return {g: cfg for g, cfg in GROUPS.items() if cfg["active"]}


def telegram_allowed(group_id, consumer):
    cfg = GROUPS.get(group_id)
    return bool(cfg and cfg["active"] and consumer in cfg.get("telegram_allowed_consumers", []))
