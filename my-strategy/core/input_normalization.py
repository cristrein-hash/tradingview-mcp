#!/usr/bin/env python3
"""Pure input normalization + whitelist + quarantine — Production v2 core primitive.

Módulo PURO extraído da lógica provada-segura do receiver legacy
(`tv_webhook_receiver.py::_normalize_indicator_parsed` + `_compute_signal_hash`,
hardening 2026-05-28). Prepara live input FUTURO sem conectar ao receiver.

Garantias:
- headless, sem IO real, sem Flask/server, sem import do receiver;
- sem side effects no import; funções puras e determinísticas;
- NÃO escreve quarantine em arquivo — só retorna o payload de quarantine.

HARD WHITELIST GATE: símbolos fora da whitelist são REJEITADOS (não recebem
`PEPPERSTONE:<BASE>`; nunca inventamos autorização). Comportamento idêntico ao legacy.

Decisão sobre provider externo (documentada): para base AUTORIZADA, um provider
externo (ex.: OANDA:XAUUSD) é normalizado para `PEPPERSTONE:<BASE>` — este é o
comportamento PROVADO SEGURO do hardening 2026-05-28 (forçar PEPPERSTONE, nunca
deixar resolver para OANDA downstream). Para base NÃO autorizada, rejeita sempre.
"""
import hashlib

ALLOWED_PROVIDER = "PEPPERSTONE"

# Whitelist operacional (2026-05-28). HARD GATE.
KNOWN_BASE_SYMBOLS = frozenset({
    "XAUUSD",
    "XAGUSD",
    "ETHUSD",
    "US500",
    "EURUSD",
    "USOUSD",
})


def is_authorized_symbol(base_symbol):
    """True se o ticker-base (sem provider) está na whitelist operacional."""
    return isinstance(base_symbol, str) and base_symbol.upper() in KNOWN_BASE_SYMBOLS


def normalize_symbol(raw_symbol):
    """Normaliza um símbolo bruto para canônico `PEPPERSTONE:<BASE>` com HARD WHITELIST GATE.

    Retorna dict: ok, raw_symbol, base_symbol, provider, normalized_symbol, reason.
    - vazio/None         -> ok=False, reason='empty_symbol'
    - base não-whitelist -> ok=False, reason='unauthorized_base_symbol:<BASE>'
                            (ou 'unauthorized_provider_and_symbol:<PROV>:<BASE>')
    - base whitelisted   -> ok=True, normalized='PEPPERSTONE:<BASE>', reason=método
                            ('added_pepperstone_prefix'|'kept_pepperstone'|
                             'replaced_<provider>_with_pepperstone')
    """
    if not raw_symbol or not isinstance(raw_symbol, str):
        return {"ok": False, "raw_symbol": raw_symbol or "", "base_symbol": "",
                "provider": "", "normalized_symbol": "", "reason": "empty_symbol"}

    if ":" in raw_symbol:
        incoming_provider, base = raw_symbol.split(":", 1)
        incoming_provider = incoming_provider.upper()
        base = base.upper()
    else:
        incoming_provider = None
        base = raw_symbol.upper()

    if base not in KNOWN_BASE_SYMBOLS:
        reason = f"unauthorized_base_symbol:{base}"
        if incoming_provider and incoming_provider != ALLOWED_PROVIDER:
            reason = f"unauthorized_provider_and_symbol:{incoming_provider}:{base}"
        return {"ok": False, "raw_symbol": raw_symbol, "base_symbol": base,
                "provider": "", "normalized_symbol": "", "reason": reason}

    if incoming_provider is None:
        method = "added_pepperstone_prefix"
    elif incoming_provider == ALLOWED_PROVIDER:
        method = "kept_pepperstone"
    else:
        method = f"replaced_{incoming_provider.lower()}_with_pepperstone"

    return {"ok": True, "raw_symbol": raw_symbol, "base_symbol": base,
            "provider": ALLOWED_PROVIDER, "normalized_symbol": f"{ALLOWED_PROVIDER}:{base}",
            "reason": method}


def compute_signal_hash(event):
    """Hash determinístico de sinal (idêntico ao legacy `_compute_signal_hash`):
    sha256[:16] de `{ts_signal}|{base_symbol}|{timeframe}|{indicator_name}|{signal_type}`.
    base_symbol é derivado do símbolo do evento se ausente."""
    base = (event.get("base_symbol") or "").upper()
    if not base:
        base = normalize_symbol(event.get("symbol") or event.get("ticker") or "")["base_symbol"]
    ts_signal = event.get("ts_signal") or event.get("time") or ""
    timeframe = str(event.get("timeframe") or "")
    indicator_name = event.get("indicator_name") or ""
    signal_type = event.get("signal_type") or ""
    key = f"{ts_signal}|{base}|{timeframe}|{indicator_name}|{signal_type}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def classify_input_event(event):
    """Classifica um evento de input (dict) sem side effects.

    Retorna dict:
      accepted: bool
      normalized_symbol, base_symbol, provider
      signal_hash: determinístico (sempre computável)
      quarantine_reason: só presente se accepted=False (payload de quarantine,
                         NÃO escrito em arquivo)
    """
    if not isinstance(event, dict):
        return {"accepted": False, "normalized_symbol": "", "base_symbol": "",
                "provider": "", "signal_hash": None, "quarantine_reason": "event_not_a_dict"}

    raw = event.get("symbol") or event.get("ticker") or ""
    norm = normalize_symbol(raw)
    sig = compute_signal_hash({**event, "base_symbol": norm["base_symbol"]})

    out = {
        "accepted": norm["ok"],
        "normalized_symbol": norm["normalized_symbol"],
        "base_symbol": norm["base_symbol"],
        "provider": norm["provider"],
        "signal_hash": sig,
    }
    if not norm["ok"]:
        out["quarantine_reason"] = norm["reason"]
    return out
