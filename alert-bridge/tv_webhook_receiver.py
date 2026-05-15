#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from html import escape
import json
import os
import subprocess
import sys
import threading

HOST = os.environ.get("TV_WEBHOOK_HOST", "127.0.0.1")
PORT = int(os.environ.get("TV_WEBHOOK_PORT", "8787"))
SECRET = os.environ.get("TV_WEBHOOK_SECRET", "local-test")

BASE_DIR = Path.home() / "tradingview-mcp" / "alert-bridge"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "tradingview_alerts.jsonl"
SETUP_RESEARCH_LOG = LOG_DIR / "setup_research_log.jsonl"
INTRADAY_QUASE_VALIDO_LOG = LOG_DIR / "intraday_quase_valido_log.jsonl"
WATCHLIST_REJECTIONS_LOG = LOG_DIR / "watchlist_rejections.jsonl"
ENV_FILE = BASE_DIR / ".env"
CLAUDE_RECHECK = BASE_DIR / "claude_recheck.py"
STRATEGY_RULES_PATH = Path.home() / "tradingview-mcp" / "my-strategy" / "strategy_rules.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Watchlist gate (added 2026-05-14) — hard enforce allowed_symbols from strategy_rules.json
# Why: USDJPY removed 2026-04-29 but receiver kept processing alerts because there was no
# gate in the webhook path. Whitelist was only a textual instruction to Claude.
_WATCHLIST_CACHE = {"symbols": None, "mtime": 0}

def _load_allowed_symbols() -> set:
    """Read allowed_symbols from strategy_rules.json with mtime-based cache.
    Returns empty set on any failure → fail-open (process all symbols) to avoid blocking real trades."""
    try:
        st = STRATEGY_RULES_PATH.stat()
        if _WATCHLIST_CACHE["mtime"] == st.st_mtime and _WATCHLIST_CACHE["symbols"] is not None:
            return _WATCHLIST_CACHE["symbols"]
        with STRATEGY_RULES_PATH.open() as f:
            rules = json.load(f)
        wl = rules.get("watchlist", {}) or {}
        allowed = wl.get("allowed_symbols", []) or []
        if not isinstance(allowed, list) or not allowed:
            return set()
        sym_set = {str(s).strip().upper() for s in allowed if s}
        _WATCHLIST_CACHE["symbols"] = sym_set
        _WATCHLIST_CACHE["mtime"] = st.st_mtime
        return sym_set
    except Exception:
        return set()  # fail-open


def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def split_text(text: str, limit: int = 3800):
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        chunks.append(text[:cut])
        text = text[cut:].lstrip()
    if text:
        chunks.append(text)
    return chunks


def send_telegram(text: str, parse_mode: str = "HTML"):
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_ids_raw = env.get("TELEGRAM_CHAT_IDS") or env.get("TELEGRAM_CHAT_ID")

    if not token or not chat_ids_raw:
        return {"ok": False, "error": "telegram_env_missing"}

    chat_ids = [x.strip() for x in chat_ids_raw.split(",") if x.strip()]
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    final_result = {"ok": True, "sent_to": []}

    for chat_id in chat_ids:
        for chunk in split_text(text):
            data = urlencode({
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": parse_mode,
                "disable_web_page_preview": "true"
            }).encode("utf-8")

            req = Request(url, data=data, method="POST")
            with urlopen(req, timeout=20) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            if not result.get("ok"):
                result["failed_chat_id"] = chat_id
                return result

        final_result["sent_to"].append(chat_id)

    return final_result


def _extract_stdout_field_local(stdout: str, field: str) -> str:
    import re
    pattern = rf"^\s*{re.escape(field)}\s*:\s*(.+?)\s*$"
    for line in (stdout or "").splitlines():
        m = re.match(pattern, line, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def is_explicit_setup_valid_stdout(stdout: str) -> bool:
    """
    Detecta SETUP_VALIDO somente quando a classificação afirma isso.
    Evita falso positivo em frases como:
    - "impede SETUP VÁLIDO"
    - "bloqueia upgrade para INTRADAY_SETUP_VALIDO"
    - "não permite classificação acima de OBSERVAÇÃO"
    """
    import re

    raw = stdout or ""
    lower = raw.lower()
    classification = _extract_stdout_field_local(raw, "Classificação").lower()

    if not classification:
        return False

    negative_markers = [
        "observação",
        "observacao",
        "no trade",
        "no_trade",
        "invalidado",
        "invalidada",
        "invalidação",
        "invalidacao",
        "bloqueado",
        "bloqueada",
        "inconclusiva",
        "inconclusivo",
        "falha",
    ]

    if any(marker in classification for marker in negative_markers):
        return False

    positive_patterns = [
        r"\bsetup[_\s-]*v[aá]lido\b",
        r"\bsetup[_\s-]*valido\b",
        r"\bintraday[_\s-]*setup[_\s-]*valido\b",
        r"\bintraday[_\s-]*setup[_\s-]*v[aá]lido\b",
        r"\bsetup[_\s-]*forte\b",
        r"\bsetup[_\s-]*excelente\b",
        r"\bintraday[_\s-]*setup[_\s-]*forte\b",
        r"\bintraday[_\s-]*setup[_\s-]*excelente\b",
    ]

    return any(re.search(p, classification, flags=re.IGNORECASE) for p in positive_patterns)


def is_explicit_invalidation_stdout(stdout: str) -> bool:
    """
    Detecta invalidação operacional real.
    Evita falso positivo quando 'invalidação' aparece apenas como nível de stop,
    bloqueio, R:R ou contexto.
    """
    import re

    raw = stdout or ""
    lower = raw.lower()

    alert_type = _extract_stdout_field_local(raw, "Alert type").lower()
    classification = _extract_stdout_field_local(raw, "Classificação").lower()

    if "monitor_invalidation" in alert_type or "price_hit_invalidation" in lower:
        return True

    explicit_class_markers = [
        "setup_invalidado",
        "setup invalidado",
        "setup invalidada",
        "invalidado",
        "invalidada",
        "invalidação confirmada",
        "invalidacao confirmada",
        "tese anterior arquivada",
        "tese intraday anterior arquivada",
    ]
    if any(marker in classification for marker in explicit_class_markers):
        return True

    explicit_line_patterns = [
        r"^\s*classifica[cç][aã]o\s*:\s*.*(invalidado|invalidada|setup_invalidado|invalida[cç][aã]o confirmada)",
        r"^\s*resumo\s*:\s*.*(invalida[cç][aã]o confirmada|breakdown t[eé]cnico confirmado|perdeu .*invalida[cç][aã]o)",
        r"^\s*a[cç][aã]o tomada\s*:\s*.*(setup arquivado|tese arquivada|invalida[cç][aã]o confirmada)",
    ]

    return any(re.search(p, raw, flags=re.IGNORECASE | re.MULTILINE) for p in explicit_line_patterns)


def is_explicit_critical_event_stdout(stdout: str) -> bool:
    raw = stdout or ""
    lower = raw.lower()

    # Não tratar bloqueio/regra/janela crítica como evento crítico.
    negative_contexts = [
        "bloqueio crítico",
        "bloqueio critico",
        "regra crítica",
        "regra critica",
        "janela macro crítica",
        "janela macro critica",
    ]
    if any(x in lower for x in negative_contexts):
        return False

    return (
        "evento crítico:" in lower
        or "evento critico:" in lower
        or "evento crítico confirmado" in lower
        or "evento critico confirmado" in lower
    )



def is_setup_candidato_forte_stdout(stdout: str) -> bool:
    """
    Detecta SETUP_CANDIDATO_FORTE somente quando o Claude afirma explicitamente.

    Aceita:
    - Classificação: SETUP_CANDIDATO_FORTE
    - Candidato forte: SIM

    Importante:
    "Candidato forte: SIM" prevalece mesmo se a linha Classificação ainda vier
    como INTRADAY_EM_OBSERVACAO durante a fase de transição.
    """
    import re

    raw = stdout or ""
    lower = raw.lower()

    negative_markers = [
        "candidato forte: não",
        "candidato forte: nao",
        "candidato forte: no",
        "candidato forte: false",
        "candidato forte: falso",
        "não é setup_candidato_forte",
        "nao e setup_candidato_forte",
        "não classificar como setup_candidato_forte",
        "nao classificar como setup_candidato_forte",
    ]
    if any(marker in lower for marker in negative_markers):
        return False

    positive_line_patterns = [
        r"^\s*candidato\s+forte\s*[:=\-]\s*(sim|yes|true|1)\b",
        r"^\s*setup_candidato_forte\s*[:=\-]\s*(sim|yes|true|1)\b",
        r"^\s*classifica[cç][aã]o\s*[:=\-]\s*setup[_\s-]*candidato[_\s-]*forte\b",
        r"^\s*classificacao\s*[:=\-]\s*setup[_\s-]*candidato[_\s-]*forte\b",
    ]

    # Primeiro: aceitar afirmação explícita linha-a-linha.
    # Isso permite:
    # Classificação: INTRADAY_EM_OBSERVACAO
    # Candidato forte: SIM
    for line in raw.splitlines():
        l = line.strip().lower()
        if not l:
            continue
        if any(re.search(pattern, l, flags=re.IGNORECASE) for pattern in positive_line_patterns):
            return True

    # Segundo: aceitar classificação explícita, mas bloquear classes negativas.
    classification = _extract_stdout_field_local(raw, "Classificação").lower()
    if classification:
        bad_class = [
            "observação",
            "observacao",
            "no trade",
            "no_trade",
            "invalidado",
            "invalidada",
            "inconclusivo",
            "inconclusiva",
            "falha",
        ]
        if any(marker in classification for marker in bad_class):
            return False

        if re.search(r"\bsetup[_\s-]*candidato[_\s-]*forte\b", classification, flags=re.IGNORECASE):
            return True

    return False



def extract_stdout_field(stdout: str, label: str) -> str:
    """Extracts a single 'Label: value' field from Claude stdout."""
    if not stdout:
        return ""
    label_l = label.lower().rstrip(":")
    for line in stdout.splitlines():
        clean = line.strip()
        if clean.lower().startswith(label_l + ":"):
            return clean.split(":", 1)[1].strip()
    return ""


def stdout_contains_any(stdout: str, terms: list[str]) -> bool:
    text = (stdout or "").lower()
    return any(t.lower() in text for t in terms)


def should_send_claude_recheck_to_telegram(stdout: str) -> tuple[bool, str]:
    """
    Decide whether Claude's recheck output should be sent to Telegram (V3).

    V3 routing (post MODULE_AWARE_GLOBAL_RULES_V3, shadow removed):
    - Connectivity/test messages: never sent.
    - SETUP_VALIDO / SETUP_VALIDO_INTRADAY: always sent (no cap).
    - SETUP_CANDIDATO_FORTE: sent (subject to daily cap of 5/asset/day — enforced at send time, see telegram_cap_for_candidato_forte).
    - SETUP_PERDIDO_NAO_PERSEGUIR / SETUP_ATRASADO_AGUARDAR_RETESTE: sent (contextually useful).
    - SETUP_EM_OBSERVACAO: only when relevant (trigger within 1 candle of closing — handled by upstream prompt).
    - NO_TRADE: not sent.
    - Critical invalidations: always sent.
    """
    text = (stdout or "").lower()

    if not text.strip():
        return False, "empty_stdout"

    # Do not send connectivity/non-operational tests.
    test_terms = [
        "teste recebido",
        "test_connectivity",
        "system_connectivity_check",
        "stack_start_public_webhook_check",
        "tradingview_real_alert_test",
        "análise operacional: não executada",
        "analise operacional: nao executada",
        "usar alert_type operacional",
    ]
    if any(term in text for term in test_terms):
        return False, "test_or_non_operational"

    # Fully valid setups (canonical V3) — always sent, no cap.
    valid_terms = [
        "classificação: setup_valido",
        "classificacao: setup_valido",
        "classificação: setup_validointraday",
        "classificacao: setup_validointraday",
        "classificação: setup_valido_intraday",
        "classificacao: setup_valido_intraday",
        "setup_validointraday",
        "setup_valido_intraday",
        "setup válido",
        "setup valido",
    ]
    if any(term in text for term in valid_terms):
        return True, "matched:setup_valido"

    # Strong candidates / human review (V3 — execution_tf field distinguishes swing/intraday).
    candidate_terms = [
        "setup_candidato_forte",
        "candidato forte: sim",
        "classificação: 🟠 setup_candidato_forte",
        "classificacao: 🟠 setup_candidato_forte",
        "classificação: setup_candidato_forte",
        "classificacao: setup_candidato_forte",
    ]
    if any(term in text for term in candidate_terms):
        return True, "matched:setup_candidato_forte"

    # Late entry / missed setup states — contextually useful.
    contextual_terms = [
        "setup_perdido_nao_perseguir",
        "setup_atrasado_aguardar_reteste",
    ]
    if any(term in text for term in contextual_terms):
        return True, "matched:setup_context_state"

    # Critical invalidation / danger states should be sent.
    critical_terms = [
        "setup_invalidado",
        "invalidated",
        "invalidation",
        "invalidação",
        "invalidacao",
        "evento crítico",
        "evento critico",
        "critical",
    ]
    if any(term in text for term in critical_terms):
        return True, "matched:critical_or_invalidation"

    return False, "not_relevant"


# --- V3 Telegram daily cap for SETUP_CANDIDATO_FORTE ---
#
# Policy: max 5 SETUP_CANDIDATO_FORTE per base_symbol per UTC day.
# Above the cap, count is incremented but Telegram send is suppressed (digest mode).
#
# Counter is persisted in logs/telegram_cf_daily_counter.json and reset at UTC day rollover.

TELEGRAM_CF_DAILY_CAP = 5
TELEGRAM_CF_COUNTER_PATH = LOG_DIR / "telegram_cf_daily_counter.json"


def _telegram_cf_counter_path():
    """Resolve telegram CF counter path. Uses module-level LOG_DIR."""
    return TELEGRAM_CF_COUNTER_PATH


# =============================================================
# External Market Factors integration (iMac analyst) — Fase 1 Passive Logging
# Activated 2026-05-12. Reads JSON per asset from iMac local HTTP server.
# Behavior: ALWAYS PASSIVE — never blocks, never boosts. Just logs context.
# Fallback safety: "neutral" on any error (fetch failure, parse error, stale).
# =============================================================

EXTERNAL_FACTORS_BASE_URL = "http://192.168.1.90:8765"
EXTERNAL_FACTORS_TIMEOUT_S = 3
EXTERNAL_FACTORS_MAX_FRESHNESS_MIN = 30

# Safe sentinel returned on any failure or staleness
# v1.2 additions (2026-05-13): direction-aware fields, calendar_risk, raw values, schema version
_EXTERNAL_NEUTRAL_FALLBACK = {
    # v1.0 fields
    "external_bias": "unknown",
    "external_risk_level": "unknown",
    "external_trade_validation": "neutral",
    "external_confidence": 0,
    "external_main_reasons": [],
    "external_supportive_factors": [],
    "external_risk_factors": [],
    "external_blocking_factors": [],
    "external_factor_scores": {},
    "external_decision_note": "",
    "external_source_links": [],
    "external_timestamp_utc": "",
    "external_fetch_ok": False,
    "external_stale": True,
    "external_fetch_error": "default_fallback_not_called",
    "external_age_minutes": None,
    "external_phase": "passive_logging_v1.2",
    # v1.2 — direction-aware validation
    "external_long_validation": "neutral",
    "external_short_validation": "neutral",
    "external_primary_driver": "neutral",
    "external_risk_flags": [],
    "external_support_flags": [],
    "external_context": "",
    "external_directional_notes": [],
    # v1.2 — calendar risk
    "external_calendar_active": False,
    "external_calendar_risk_level": "none",
    "external_calendar_score": 0,
    "external_calendar_events": [],
    # v1.2 — raw external values for cohort analysis
    "external_vix": None,
    "external_us10y_nominal": None,
    "external_us10y_real": None,
    "external_trade_weighted_usd": None,
    # v1.2 — schema tracking
    "external_schema_version": "unknown",
}


def fetch_external_factors(base_symbol: str) -> dict:
    """
    Fetch latest external market factors JSON from iMac analyst.
    Returns dict with normalized fields. Safe defaults on any error.

    Fase 1 Passive Logging: receiver and Claude only LOG these values.
    They MUST NOT alter technical classification or Telegram routing.

    Failure modes always return external_trade_validation='neutral'
    to ensure system never blocks on macro-side error.
    """
    import urllib.request
    import urllib.error
    from datetime import datetime as _dt, timezone as _tz

    result = dict(_EXTERNAL_NEUTRAL_FALLBACK)
    result["external_fetch_error"] = ""

    if not base_symbol:
        result["external_fetch_error"] = "empty_base_symbol"
        return result

    sym = base_symbol.strip().upper()
    url = f"{EXTERNAL_FACTORS_BASE_URL}/{sym}.json"

    try:
        with urllib.request.urlopen(url, timeout=EXTERNAL_FACTORS_TIMEOUT_S) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
    except urllib.error.URLError as e:
        result["external_fetch_error"] = f"url_error:{type(e).__name__}"
        return result
    except json.JSONDecodeError as e:
        result["external_fetch_error"] = f"json_decode:{type(e).__name__}"
        return result
    except Exception as e:
        result["external_fetch_error"] = f"unexpected:{type(e).__name__}"
        return result

    # Successfully fetched + parsed
    result["external_fetch_ok"] = True
    result["external_fetch_error"] = ""

    # === v1.0 fields (defensive — never trust upstream) ===
    result["external_bias"] = str(data.get("external_bias", "unknown"))
    result["external_risk_level"] = str(data.get("risk_level", "unknown"))

    _VALID_VALIDATIONS = ("confirm", "neutral", "caution", "block")

    def _sanitize_validation(raw_value):
        v = str(raw_value or "neutral").lower().strip()
        return v if v in _VALID_VALIDATIONS else "neutral"

    result["external_trade_validation"] = _sanitize_validation(data.get("trade_validation"))
    try:
        result["external_confidence"] = float(data.get("confidence", 0))
    except (ValueError, TypeError):
        result["external_confidence"] = 0
    result["external_main_reasons"] = list(data.get("main_reasons", []) or [])[:5]
    result["external_supportive_factors"] = list(data.get("supportive_factors", []) or [])[:5]
    result["external_risk_factors"] = list(data.get("risk_factors", []) or [])[:5]
    result["external_blocking_factors"] = list(data.get("blocking_factors", []) or [])[:5]
    result["external_factor_scores"] = data.get("scores", {}) or {}
    result["external_decision_note"] = str(data.get("decision_note", ""))[:500]
    result["external_source_links"] = list(data.get("source_links", []) or [])[:10]
    result["external_timestamp_utc"] = str(data.get("timestamp_utc", "") or data.get("timestamp", ""))

    # === v1.2 — direction-aware validation ===
    result["external_long_validation"] = _sanitize_validation(data.get("long_validation"))
    result["external_short_validation"] = _sanitize_validation(data.get("short_validation"))
    result["external_primary_driver"] = str(data.get("primary_driver", "neutral"))[:50]
    result["external_risk_flags"] = list(data.get("risk_flags", []) or [])[:10]
    result["external_support_flags"] = list(data.get("support_flags", []) or [])[:10]
    result["external_context"] = str(data.get("context", ""))[:200]
    result["external_directional_notes"] = list(data.get("directional_notes", []) or [])[:5]

    # === v1.2 — calendar risk (extract from nested object) ===
    cal_risk = data.get("calendar_risk", {}) or {}
    if isinstance(cal_risk, dict):
        result["external_calendar_active"] = bool(cal_risk.get("active", False))
        result["external_calendar_risk_level"] = str(cal_risk.get("risk_level", "none"))[:40]
        try:
            result["external_calendar_score"] = float(cal_risk.get("calendar_score", 0))
        except (ValueError, TypeError):
            result["external_calendar_score"] = 0
        events = list(cal_risk.get("events", []) or [])[:5]
        # Compact each event to essentials
        compact_events = []
        for ev in events:
            if not isinstance(ev, dict):
                continue
            compact_events.append({
                "id": str(ev.get("id", ""))[:80],
                "name": str(ev.get("name", ""))[:80],
                "impact": str(ev.get("impact", ""))[:20],
                "asset_relevance": str(ev.get("asset_relevance", ""))[:20],
                "hours_to_event": ev.get("hours_to_event"),
                "hours_since_event": ev.get("hours_since_event"),
                "phase": str(ev.get("phase", ""))[:40],
            })
        result["external_calendar_events"] = compact_events

    # === v1.2 — raw external values (for cohort analysis) ===
    raw_vals = data.get("raw_external_values", {}) or {}
    if isinstance(raw_vals, dict):
        def _safe_float(v):
            if v is None: return None
            try: return float(v)
            except (ValueError, TypeError): return None
        result["external_vix"] = _safe_float(raw_vals.get("vix"))
        result["external_us10y_nominal"] = _safe_float(raw_vals.get("us10y_nominal"))
        result["external_us10y_real"] = _safe_float(raw_vals.get("us10y_real"))
        result["external_trade_weighted_usd"] = _safe_float(raw_vals.get("trade_weighted_usd"))

    # === v1.2 — schema version tracking ===
    result["external_schema_version"] = str(data.get("schema_version", "unknown"))[:40]

    # === Freshness check — stale JSON gets coerced to neutral (incl. v1.2 validations) ===
    age_min = None
    ts_str = result["external_timestamp_utc"]
    if ts_str:
        try:
            dt = _dt.fromisoformat(ts_str.replace("Z", "+00:00"))
            age_min = (_dt.now(_tz.utc) - dt).total_seconds() / 60.0
            result["external_age_minutes"] = round(age_min, 1)
        except Exception:
            age_min = None

    if age_min is None:
        # No timestamp = assume stale = safe fallback for ALL validation fields
        result["external_stale"] = True
        result["external_trade_validation"] = "neutral"
        result["external_long_validation"] = "neutral"
        result["external_short_validation"] = "neutral"
    elif age_min > EXTERNAL_FACTORS_MAX_FRESHNESS_MIN:
        result["external_stale"] = True
        # Stale data should not influence — coerce all validations to neutral
        result["external_trade_validation"] = "neutral"
        result["external_long_validation"] = "neutral"
        result["external_short_validation"] = "neutral"
    else:
        result["external_stale"] = False

    return result


def _load_cf_counter() -> dict:
    p = _telegram_cf_counter_path()
    if not p or not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cf_counter(data: dict):
    p = _telegram_cf_counter_path()
    if not p:
        return
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def check_telegram_cap_for_candidato_forte(base_symbol: str) -> tuple[bool, int, int]:
    """
    READ-ONLY check: would this CF message exceed the daily cap?

    Returns (allowed, current_count_BEFORE_send, cap).
    - allowed=True: under or at cap, can send.
    - allowed=False: at/above cap; suppress (digest mode).

    NOTE: Does NOT increment the counter. Call commit_telegram_cap_for_candidato_forte()
    only AFTER a successful Telegram send.
    """
    from datetime import datetime as _dt, timezone as _tz
    today_key = _dt.now(_tz.utc).strftime("%Y-%m-%d")
    data = _load_cf_counter()

    sym = (base_symbol or "UNKNOWN").upper()
    bucket = data.get(today_key, {})
    current = int(bucket.get(sym, 0))

    # If current count is already at cap, next send would push to cap+1 → block.
    allowed = current < TELEGRAM_CF_DAILY_CAP
    return allowed, current, TELEGRAM_CF_DAILY_CAP


def commit_telegram_cap_for_candidato_forte(base_symbol: str) -> int:
    """
    Increment the daily cap counter AFTER a successful Telegram send.

    Returns the post-increment count.
    Should only be called when send_telegram() returned ok=True.
    """
    from datetime import datetime as _dt, timezone as _tz
    today_key = _dt.now(_tz.utc).strftime("%Y-%m-%d")
    data = _load_cf_counter()

    # Reset stale days: keep only today's bucket.
    data = {k: v for k, v in data.items() if k == today_key}
    if today_key not in data:
        data[today_key] = {}

    sym = (base_symbol or "UNKNOWN").upper()
    bucket = data[today_key]
    bucket[sym] = int(bucket.get(sym, 0)) + 1
    _save_cf_counter(data)
    return bucket[sym]


# Legacy alias for backward compat — DO NOT use in new code (increments unconditionally).
def telegram_cap_for_candidato_forte(base_symbol: str) -> tuple[bool, int, int]:
    """DEPRECATED: use check_ + commit_ pair instead. This one increments on every call."""
    allowed, current, cap = check_telegram_cap_for_candidato_forte(base_symbol)
    new_count = commit_telegram_cap_for_candidato_forte(base_symbol)
    return (new_count <= cap), new_count, cap


def format_tradingview_message(event: dict) -> str:
    payload = event.get("payload", {})

    symbol = escape(str(payload.get("symbol", "desconhecido")))
    timeframe = escape(str(payload.get("timeframe", "desconhecido")))
    alert_event = escape(str(payload.get("event", "alerta")))
    message = escape(str(payload.get("message", "")))
    price = escape(str(payload.get("price", "")))

    lines = [
        "🚨 <b>[TRADINGVIEW] Alerta recebido</b>",
        "",
        f"<b>Ativo:</b> {symbol}",
        f"<b>Timeframe:</b> {timeframe}",
        f"<b>Evento:</b> {alert_event}",
    ]

    if price:
        lines.append(f"<b>Preço:</b> {price}")

    if message:
        lines.extend(["", f"<b>Mensagem:</b> {message}"])

    lines.extend([
        "",
        "Status: alerta recebido pelo alert-bridge local.",
        "Claude será acionado automaticamente para reavaliar o contexto."
    ])

    return "\n".join(lines)


def extract_field(stdout: str, field: str) -> str:
    prefix = field + ":"
    for line in stdout.splitlines():
        if line.strip().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def compact_text(value: str, limit: int) -> str:
    value = " ".join((value or "").split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


def build_short_claude_recheck_message(stdout: str) -> str:
    if stdout.strip().startswith("TESTE RECEBIDO"):
        return (
            "🤖 <b>[CLAUDE] Teste recebido</b>\n\n"
            "Canal TradingView → webhook → Claude → Telegram funcionando."
        )

    ativo = extract_field(stdout, "Ativo") or "não identificado"
    timeframe = extract_field(stdout, "Timeframe") or "não identificado"
    alert_type = extract_field(stdout, "Alert type") or "não informado"
    classificacao = extract_field(stdout, "Classificação") or "não informado"
    direcao = extract_field(stdout, "Direção") or "não informado"
    resumo = extract_field(stdout, "Resumo")
    bloqueio = extract_field(stdout, "Bloqueio principal")
    proxima = extract_field(stdout, "Próxima ação")
    acao = extract_field(stdout, "Ação tomada")

    is_candidato_forte = is_setup_candidato_forte_stdout(stdout)
    is_critical = (
        is_candidato_forte
        or is_explicit_setup_valid_stdout(stdout)
        or is_explicit_invalidation_stdout(stdout)
        or is_explicit_critical_event_stdout(stdout)
    )

    is_quase = is_intraday_quase_valido_stdout(stdout)
    if is_candidato_forte:
        title = "🟠 <b>[CLAUDE]</b>"
        event_label = "SETUP_CANDIDATO_FORTE — REVISÃO HUMANA"
    elif is_quase:
        title = "🟡 <b>[CLAUDE]</b>"
        event_label = "QUASE_VALIDO — REVISÃO HUMANA"
    else:
        title = "🚨 <b>[CLAUDE]</b>"
        event_label = "Mudança importante" if is_critical else "Reavaliação relevante"

    # Limpar ativo/timeframe para título curto
    ativo_short = ativo.replace("PEPPERSTONE:", "").replace("VANTAGE:", "")
    timeframe_short = timeframe.split()[0]

    lines = [
        f"{title} {escape(ativo_short)} {escape(timeframe_short)} — {escape(event_label)}",
        "",
        f"<b>Classificação:</b> {escape(compact_text(classificacao, 80))}",
        f"<b>Direção:</b> {escape(compact_text(direcao, 80))}",
        f"<b>Alerta:</b> {escape(compact_text(alert_type, 60))}",
    ]

    if resumo:
        lines.extend([
            "",
            f"<b>Leitura:</b>\n{escape(compact_text(resumo, 230))}"
        ])

    if bloqueio:
        lines.extend([
            "",
            f"<b>Bloqueio:</b>\n{escape(compact_text(bloqueio, 190))}"
        ])

    # Conclusão operacional curta inferida
    conclusion = ""
    lower = stdout.lower()
    if is_explicit_setup_valid_stdout(stdout):
        conclusion = "Setup válido. Revisar execução manual."
    elif is_setup_candidato_forte_stdout(stdout):
        conclusion = "SETUP_CANDIDATO_FORTE. Revisão humana; não é entrada automática."
    elif is_intraday_quase_valido_stdout(stdout):
        conclusion = "QUASE_VALIDO experimental. Revisão humana; não é entrada automática."
    elif "quase válido" in lower or "faltando apenas" in lower or "muito próximo" in lower:
        conclusion = "Setup quase válido. Vale revisar o gráfico."
    elif "no trade" in lower or "setup invalidado" in lower or "invalida" in lower:
        conclusion = "Não operar agora. Tese anterior invalidada ou bloqueada."
    elif "observação" in lower or "observacao" in lower:
        conclusion = "Evento relevante, mas ainda em observação."
    else:
        conclusion = "Reavaliação feita. Aguardar confirmação."

    lines.extend([
        "",
        f"<b>Conclusão:</b>\n{escape(conclusion)}"
    ])

    if proxima:
        lines.extend([
            "",
            f"<b>Próxima ação:</b>\n{escape(compact_text(proxima, 300))}"
        ])

    # Só mostrar ação tomada se não for trivial
    if acao and not any(x in acao.lower() for x in ["nenhuma", "apenas reavaliação", "reavaliação apenas"]):
        lines.extend([
            "",
            f"<b>Ação tomada:</b>\n{escape(compact_text(acao, 140))}"
        ])

    return "\n".join(lines)


def base_symbol_from_symbol(symbol: str) -> str:
    if not symbol:
        return ""
    return symbol.split(":", 1)[-1]


def truthy_contains(text: str, terms: list[str]) -> bool:
    lower = (text or "").lower()
    return any(term.lower() in lower for term in terms)


def build_setup_research_record(
    event: dict,
    stdout: str,
    stderr: str,
    returncode: int,
    telegram_sent: bool,
    telegram_reason: str,
    external_factors: dict = None,
) -> dict:
    payload = event.get("payload", {}) or {}
    symbol = payload.get("symbol", "")
    received_at = event.get("received_at", "")
    # Default external_factors to safe neutral if None
    if external_factors is None:
        external_factors = dict(_EXTERNAL_NEUTRAL_FALLBACK)

    classification = extract_field(stdout, "Classificação")
    classification_v4 = extract_field(stdout, "Classificação V4")  # SHADOW MODE 2026-05-14
    oracle_score_raw = extract_field(stdout, "Oracle Score")  # SHADOW MODE 2026-05-14 — pre-flight check 0-3
    # Coerce to int if numeric, else None
    try:
        oracle_score = int(str(oracle_score_raw).strip()) if oracle_score_raw and str(oracle_score_raw).strip().isdigit() else None
        if oracle_score is not None and not (0 <= oracle_score <= 3):
            oracle_score = None
    except (ValueError, AttributeError):
        oracle_score = None

    # V3D SHADOW (2026-05-15) — Leonardo OB structural, APENAS XAUUSD 4H
    v3d_asset = extract_field(stdout, "V3d shadow asset")
    v3d_event_present_raw = extract_field(stdout, "V3d shadow event present")
    v3d_event_type = extract_field(stdout, "V3d shadow event type")
    v3d_ob_zone = extract_field(stdout, "V3d shadow OB zone")
    v3d_lvb_stop = extract_field(stdout, "V3d shadow LVB stop")
    v3d_in_zone_raw = extract_field(stdout, "V3d shadow in zone now")
    v3d_r_potential = extract_field(stdout, "V3d shadow R potential pts")
    def _bool_or_none(s):
        if not s:
            return None
        sl = str(s).strip().lower()
        if sl in ("true", "yes", "sim"):
            return True
        if sl in ("false", "no", "nao", "não"):
            return False
        return None
    v3d_event_present = _bool_or_none(v3d_event_present_raw)
    v3d_in_zone = _bool_or_none(v3d_in_zone_raw)
    direction = extract_field(stdout, "Direção") or extract_field(stdout, "Direção possível")
    health = extract_field(stdout, "Health")
    summary = extract_field(stdout, "Resumo")
    main_blocker = extract_field(stdout, "Bloqueio principal")
    action_taken = extract_field(stdout, "Ação tomada")
    next_action = extract_field(stdout, "Próxima ação")

    lower = (stdout or "").lower()

    record = {
        "event_id": f"{received_at}_{symbol}_{payload.get('timeframe', '')}_{payload.get('alert_type', '')}",
        "received_at": received_at,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "base_symbol": base_symbol_from_symbol(symbol),
        "timeframe": payload.get("timeframe", ""),
        "alert_type": payload.get("alert_type", ""),
        "event": payload.get("event", ""),
        "drawing_type": payload.get("drawing_type", ""),
        "drawing_name": payload.get("drawing_name", ""),
        "strategy_layer": payload.get("strategy_layer", ""),
        "source_timeframe": payload.get("source_timeframe", ""),
        "price_at_alert": payload.get("price", ""),
        "alert_message": payload.get("message", ""),
        "reason": payload.get("reason", ""),
        "expected_recheck": payload.get("expected_recheck", ""),

        "classification": classification,
        "classification_v4_shadow": classification_v4,  # SHADOW MODE 2026-05-14 — new naming scheme, not yet routed to Telegram
        "oracle_score_shadow": oracle_score,  # SHADOW MODE 2026-05-14 — int 0-3 or None; pre-flight check
        "oracle_score_raw": oracle_score_raw,  # raw string for audit (in case parsing fails)
        # V3D SHADOW (2026-05-15) — Leonardo OB structural, only XAUUSD 4H
        "v3d_shadow_asset": v3d_asset,
        "v3d_shadow_event_present": v3d_event_present,
        "v3d_shadow_event_type": v3d_event_type,
        "v3d_shadow_ob_zone": v3d_ob_zone,
        "v3d_shadow_lvb_stop": v3d_lvb_stop,
        "v3d_shadow_in_zone": v3d_in_zone,
        "v3d_shadow_r_potential_pts": v3d_r_potential,
        "direction": direction,
        "health": health,
        "summary": summary,
        "main_blocker": main_blocker,
        "action_taken": action_taken,
        "next_action": next_action,

        "telegram_sent": telegram_sent,
        "telegram_reason": telegram_reason,

        "is_setup_valid": truthy_contains(stdout, [
            "SETUP VÁLIDO",
            "SETUP VALIDO",
            "INTRADAY_SETUP_VALIDO",
            "INTRADAY SETUP VALIDO",
            "INTRADAY_SETUP_VÁLIDO"
        ]),
        "is_near_setup": truthy_contains(stdout, [
                            "muito proximo"
        ]),
        "is_observation": truthy_contains(stdout, [
            "SETUP EM OBSERVAÇÃO",
            "SETUP EM OBSERVACAO",
            "INTRADAY EM OBSERVAÇÃO",
            "INTRADAY EM OBSERVACAO"
        ]),
        "is_no_trade": truthy_contains(stdout, [
            "NO TRADE",
            "não operar",
            "nao operar"
        ]),
        "is_invalidated": truthy_contains(stdout, [
            "invalidado",
            "invalidação",
            "invalidacao",
            "perdeu",
            "price_hit_invalidation"
        ]),
        "is_critical": truthy_contains(stdout, [
                "CRITICO",
            "SETUP VÁLIDO",
            "SETUP VALIDO",
            "SETUP FORTE",
            "SETUP EXCELENTE",
            "INTRADAY_SETUP_VALIDO",
            "price_hit_invalidation",
            "invalidação",
            "invalidacao"
        ]),
        "has_rsi_extreme_text": truthy_contains(stdout, [
            "RSI",
            "sobrevenda",
            "sobrecompra",
            "extremo"
        ]),
        "has_bubbles_text": truthy_contains(stdout, [
            "Bubbles",
            "MOB",
            "Market Order Bubbles",
            "cluster"
        ]),
        "has_top_bottom_text": truthy_contains(stdout, [
            "TOP",
            "BOTTOM",
            "LONG",
            "SHORT"
        ]),
        "has_rejection_text": truthy_contains(stdout, [
            "rejeição",
            "rejeicao",
            "pavio",
            "engolfo"
        ]),
        "has_rr_text": truthy_contains(stdout, [
            "R:R",
            "RR",
            "2:1"
        ]),
        "macro_mentioned": truthy_contains(stdout, [
            "macro",
            "FOMC",
            "PCE",
            "GDP",
            "ECB",
            "BoE",
            "BoJ",
            "OPEC",
            "Hormuz"
        ]),

        "returncode": returncode,
        
    "module_applied": extract_stdout_field(stdout, "Strategy Module"),
    "module_backtest_n": extract_stdout_field(stdout, "Module backtest n"),
    "global_hard_blocks": extract_stdout_field(stdout, "Global hard blocks"),
    "module_checklist": extract_stdout_field(stdout, "Module checklist"),
    "module_checklist_notes": extract_stdout_field(stdout, "Module checklist notes"),
    "module_score": extract_stdout_field(stdout, "Module score"),
    "operational_signal": extract_stdout_field(stdout, "Operational signal"),
    "d2r_required": extract_stdout_field(stdout, "D2R required"),
    "hard_block_triggered": extract_stdout_field(stdout, "Hard block triggered"),
    "module_checklist_failed_on": extract_stdout_field(stdout, "Module checklist failed on"),
    "promotion_trigger_fired": extract_stdout_field(stdout, "Promotion trigger"),
    "promotion_status": extract_stdout_field(stdout, "Promotion status"),
    "priority_score": extract_stdout_field(stdout, "Priority"),
    "trigger": extract_stdout_field(stdout, "Trigger"),
    "execution_tf": extract_stdout_field(stdout, "Execution TF"),
    "ideal_entry_price_text": extract_stdout_field(stdout, "Entrada ideal"),
    "current_price_at_eval_text": extract_stdout_field(stdout, "Preço atual"),
    "entry_late": extract_stdout_field(stdout, "Entrada atrasada"),
    "entry_late_distance_r": extract_stdout_field(stdout, "Entry late distance R"),
    "is_shadow_valid": False,  # DEPRECATED v3 — kept for backward compat with readers; shadow mode removed.

    # === External Market Factors — Passive Logging (v1.2 since 2026-05-13) ===
    # Source: iMac analyst (Kimi Code + Skill). Behavior: passive only, never alters classification.
    # Persisted to enable post-hoc correlation analysis between macro context and outcomes.
    # v1.0 fields:
    "external_bias": external_factors.get("external_bias", "unknown"),
    "external_risk_level": external_factors.get("external_risk_level", "unknown"),
    "external_trade_validation": external_factors.get("external_trade_validation", "neutral"),
    "external_confidence": external_factors.get("external_confidence", 0),
    "external_main_reasons": external_factors.get("external_main_reasons", []),
    "external_supportive_factors": external_factors.get("external_supportive_factors", []),
    "external_risk_factors": external_factors.get("external_risk_factors", []),
    "external_blocking_factors": external_factors.get("external_blocking_factors", []),
    "external_factor_scores": external_factors.get("external_factor_scores", {}),
    "external_decision_note": external_factors.get("external_decision_note", ""),
    "external_source_links": external_factors.get("external_source_links", []),
    "external_timestamp_utc": external_factors.get("external_timestamp_utc", ""),
    "external_age_minutes": external_factors.get("external_age_minutes"),
    "external_fetch_ok": external_factors.get("external_fetch_ok", False),
    "external_stale": external_factors.get("external_stale", True),
    "external_fetch_error": external_factors.get("external_fetch_error", ""),
    "external_phase": external_factors.get("external_phase", "passive_logging_v1.2"),
    # v1.2 — direction-aware validation:
    "external_long_validation": external_factors.get("external_long_validation", "neutral"),
    "external_short_validation": external_factors.get("external_short_validation", "neutral"),
    "external_primary_driver": external_factors.get("external_primary_driver", "neutral"),
    "external_risk_flags": external_factors.get("external_risk_flags", []),
    "external_support_flags": external_factors.get("external_support_flags", []),
    "external_context": external_factors.get("external_context", ""),
    "external_directional_notes": external_factors.get("external_directional_notes", []),
    # v1.2 — calendar risk:
    "external_calendar_active": external_factors.get("external_calendar_active", False),
    "external_calendar_risk_level": external_factors.get("external_calendar_risk_level", "none"),
    "external_calendar_score": external_factors.get("external_calendar_score", 0),
    "external_calendar_events": external_factors.get("external_calendar_events", []),
    # v1.2 — raw values for cohort analysis:
    "external_vix": external_factors.get("external_vix"),
    "external_us10y_nominal": external_factors.get("external_us10y_nominal"),
    "external_us10y_real": external_factors.get("external_us10y_real"),
    "external_trade_weighted_usd": external_factors.get("external_trade_weighted_usd"),
    # v1.2 — schema tracking:
    "external_schema_version": external_factors.get("external_schema_version", "unknown"),

"claude_stdout": stdout,
        "claude_stderr": stderr
    }

    return record


def append_setup_research_record(record: dict):
    try:
        with SETUP_RESEARCH_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:
        print(json.dumps({
            "setup_research_log_error": str(exc)
        }, ensure_ascii=False), flush=True)


def is_intraday_quase_valido_stdout(stdout: str) -> bool:
    """
    Detecta QUASE_VALIDO experimental somente quando o Claude afirma explicitamente.
    Evita falso positivo em frases negativas ou bloqueadas.
    """
    import re

    raw = stdout or ""
    lower = raw.lower()

    global_negative_markers = [
        "falha técnica",
        "falha tecnica",
        "chart mcp não trocou",
        "chart mcp nao trocou",
        "bloqueia classificação",
        "bloqueia classificacao",
        "bloqueado",
        "máximo setup em observação",
        "maximo setup em observacao",
        "não classificar como quase",
        "nao classificar como quase",
        "não é quase válido",
        "nao e quase valido",
        "não é quase valido",
        "nao é quase válido",
        "não promova intraday_quase_valido",
        "nao promova intraday_quase_valido",
    ]

    if any(marker in lower for marker in global_negative_markers):
        return False

    positive_line_patterns = [
        r"^\s*quase\s+v[aá]lido\s+experimental\s*[:=\-]\s*(sim|yes|true|1)\b",
        r"^\s*quase\s+valido\s+experimental\s*[:=\-]\s*(sim|yes|true|1)\b",
        r"^\s*intraday_quase_valido\s*[:=\-]\s*(sim|yes|true|1)\b",
        r"^\s*quase_valid[oa]?\s*[:=\-]\s*(sim|yes|true|1)\b",
        r"^\s*classifica[cç][aã]o\s*[:=\-]\s*(intraday_)?quase_valid[oa]?\b",
        r"^\s*classificacao\s*[:=\-]\s*(intraday_)?quase_valid[oa]?\b",
    ]

    negative_line_markers = [
        "não",
        "nao",
        "no",
        "false",
        "falso",
        "não aplicável",
        "nao aplicavel",
        "bloqueado",
        "observação",
        "observacao",
        "no trade",
    ]

    for line in raw.splitlines():
        l = line.strip().lower()
        if not l:
            continue
        if any(re.search(pattern, l, flags=re.IGNORECASE) for pattern in positive_line_patterns):
            if not any(marker in l for marker in negative_line_markers):
                return True

    return False


def append_intraday_quase_valido_record(event: dict, stdout: str, telegram_sent: bool, telegram_reason: str):
    try:
        payload = event.get("payload", {}) or {}
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": f"{event.get('received_at', '')}_{payload.get('symbol', '')}_{payload.get('timeframe', '')}_{payload.get('alert_type', '')}",
            "symbol": payload.get("symbol", ""),
            "timeframe": payload.get("timeframe", ""),
            "alert_type": payload.get("alert_type", ""),
            "drawing_type": payload.get("drawing_type", ""),
            "drawing_name": payload.get("drawing_name", ""),
            "strategy_layer": payload.get("strategy_layer", ""),
            "source_timeframe": payload.get("source_timeframe", ""),
            "price_at_alert": payload.get("price", ""),
            "direction": extract_field(stdout, "Direção"),
            "classification": extract_field(stdout, "Classificação"),
            "summary": extract_field(stdout, "Resumo"),
            "confluences": extract_field(stdout, "Confluências"),
            "main_blocker": extract_field(stdout, "Bloqueio principal"),
            "rr_estimated": extract_field(stdout, "R:R estimado"),
            "missing_trigger": extract_field(stdout, "Gatilho faltante"),
            "next_action": extract_field(stdout, "Próxima ação"),
            "telegram_sent": telegram_sent,
            "telegram_reason": telegram_reason,
            "status": "experimental_revisao_humana",
            "not_setup_valido": True,
            "claude_stdout": stdout
        }

        with INTRADAY_QUASE_VALIDO_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(json.dumps({
            "intraday_quase_valido_logged": True,
            "symbol": record["symbol"],
            "drawing_name": record["drawing_name"]
        }, ensure_ascii=False), flush=True)

    except Exception as exc:
        print(json.dumps({
            "intraday_quase_valido_log_error": str(exc)
        }, ensure_ascii=False), flush=True)


def run_claude_recheck_background(event: dict):
    payload = event.get("payload", {})
    started_at = datetime.now(timezone.utc).isoformat()

    # === Fase 1 Passive Logging: fetch external market factors (iMac analyst) ===
    # Behavior: enrichment only. Never blocks trade, never boosts.
    # On any error: neutral fallback. On stale: neutral fallback.
    try:
        base_symbol = (payload.get("symbol") or "").split(":")[-1].strip()
        external_factors = fetch_external_factors(base_symbol)
    except Exception as _ext_err:
        # Defensive: even if our own fetch func raises, never crash receiver
        external_factors = dict(_EXTERNAL_NEUTRAL_FALLBACK)
        external_factors["external_fetch_error"] = f"wrapper_exception:{type(_ext_err).__name__}"

    # Enrich payload with external_factors so claude_recheck can read it as alert.external_factors
    payload_enriched = dict(payload)
    payload_enriched["external_factors"] = external_factors

    try:
        result = subprocess.run(
            ["python3", str(CLAUDE_RECHECK), json.dumps(payload_enriched, ensure_ascii=False)],
            cwd=str(BASE_DIR),
            text=True,
            capture_output=True,
            timeout=360
        )

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()

        log_payload = {
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "alert_payload": payload
        }

        recheck_log = LOG_DIR / "claude_recheck_events.jsonl"
        with recheck_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_payload, ensure_ascii=False) + "\n")

        telegram_sent = False
        telegram_reason = "not_evaluated"

        if result.returncode == 0:
            should_send, reason = should_send_claude_recheck_to_telegram(stdout)
            telegram_reason = reason

            # V3 cap enforcement for SETUP_CANDIDATO_FORTE (5/asset/day).
            # READ-ONLY check before send; commit increment AFTER successful send.
            # This avoids losing a slot when Telegram API fails.
            cap_check_base_symbol = None
            cap_check_current = None
            cap_check_max = None
            if should_send and reason == "matched:setup_candidato_forte":
                cap_check_base_symbol = (payload.get("symbol") or "").split(":")[-1]
                allowed, current, cap = check_telegram_cap_for_candidato_forte(cap_check_base_symbol)
                cap_check_current = current
                cap_check_max = cap
                if not allowed:
                    should_send = False
                    telegram_reason = f"capped:candidato_forte_daily_cap_{current}_of_{cap}"
                    print(json.dumps({
                        "telegram_capped": True,
                        "base_symbol": cap_check_base_symbol,
                        "current_count": current,
                        "cap": cap,
                        "policy": "MODULE_AWARE_GLOBAL_RULES_V3.telegram_caps"
                    }, ensure_ascii=False), flush=True)
                else:
                    telegram_reason = f"{reason}|pre_send_count={current}/{cap}"

            if should_send:
                text = build_short_claude_recheck_message(stdout)
                send_result = send_telegram(text)
                telegram_sent = bool(send_result.get("ok")) if isinstance(send_result, dict) else bool(send_result)

                # COMMIT counter only if send actually succeeded.
                if telegram_sent and cap_check_base_symbol is not None:
                    post_count = commit_telegram_cap_for_candidato_forte(cap_check_base_symbol)
                    telegram_reason = f"{reason}|post_send_count={post_count}/{cap_check_max}"
                elif not telegram_sent and cap_check_base_symbol is not None:
                    # Send failed; do NOT increment. Log the missed slot.
                    print(json.dumps({
                        "telegram_send_failed_no_increment": True,
                        "base_symbol": cap_check_base_symbol,
                        "current_count": cap_check_current,
                        "cap": cap_check_max,
                    }, ensure_ascii=False), flush=True)
            else:
                print(json.dumps({
                    "claude_recheck_suppressed": True,
                    "reason": telegram_reason,
                    "alert_payload": payload
                }, ensure_ascii=False), flush=True)
        else:
            telegram_reason = "claude_recheck_failed"
            text = (
                "⚠️ <b>[CLAUDE] Reavaliação falhou</b>\n\n"
                f"<b>Return code:</b> {result.returncode}\n\n"
                f"<b>STDOUT:</b>\n<pre>{escape(stdout)}</pre>\n\n"
                f"<b>STDERR:</b>\n<pre>{escape(stderr)}</pre>"
            )
            send_result = send_telegram(text)
            telegram_sent = bool(send_result.get("ok")) if isinstance(send_result, dict) else bool(send_result)

        research_record = build_setup_research_record(
            event=event,
            stdout=stdout,
            stderr=stderr,
            returncode=result.returncode,
            telegram_sent=telegram_sent,
            telegram_reason=telegram_reason,
            external_factors=external_factors,
        )
        append_setup_research_record(research_record)

        if result.returncode == 0 and is_intraday_quase_valido_stdout(stdout):
            append_intraday_quase_valido_record(
                event=event,
                stdout=stdout,
                telegram_sent=telegram_sent,
                telegram_reason=telegram_reason
            )

    except subprocess.TimeoutExpired:
        text = (
            "⚠️ <b>[CLAUDE] Reavaliação excedeu timeout</b>\n\n"
            "O alerta foi recebido, mas Claude Code headless não concluiu em 360s."
        )
        send_telegram(text)

    except Exception as e:
        text = (
            "⚠️ <b>[CLAUDE] Erro na reavaliação</b>\n\n"
            f"<pre>{escape(str(e))}</pre>"
        )
        send_telegram(text)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {
                "ok": True,
                "service": "tv_webhook_receiver",
                "claude_recheck": CLAUDE_RECHECK.exists()
            })
            return
        self._send(404, {"ok": False, "error": "not_found"})

    def do_POST(self):
        expected_path = f"/webhook/{SECRET}"
        if self.path != expected_path:
            self._send(403, {"ok": False, "error": "forbidden"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")

        try:
            parsed = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            parsed = {"raw_message": raw}

        event = {
            "received_at": datetime.now(timezone.utc).isoformat(),
            "source": "tradingview",
            "path": self.path,
            "payload": parsed
        }

        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        # === Watchlist gate (2026-05-14) ===
        # Reject symbols not in strategy_rules.json::watchlist.allowed_symbols.
        # Fail-open: if rules file unreadable or list empty, allow everything.
        allowed_set = _load_allowed_symbols()
        sym = (parsed.get("symbol") or "") if isinstance(parsed, dict) else ""
        base_sym = base_symbol_from_symbol(sym).upper().strip()
        if allowed_set and base_sym and base_sym not in allowed_set:
            rejection = {
                "received_at": event["received_at"],
                "symbol": sym,
                "base_symbol": base_sym,
                "allowed_symbols": sorted(allowed_set),
                "reason": "symbol_not_in_watchlist",
                "payload": parsed,
            }
            try:
                with WATCHLIST_REJECTIONS_LOG.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rejection, ensure_ascii=False) + "\n")
            except Exception:
                pass
            print(json.dumps({
                "rejected_by_watchlist": True,
                "base_symbol": base_sym,
                "allowed": sorted(allowed_set),
            }, ensure_ascii=False), flush=True)
            self._send(200, {
                "ok": True,
                "rejected_by_watchlist": True,
                "base_symbol": base_sym,
            })
            return

        send_raw = os.environ.get("TV_SEND_RAW_TRADINGVIEW_ALERTS", "0") == "1"
        if send_raw:
            telegram_result = send_telegram(format_tradingview_message(event))
        else:
            telegram_result = {"ok": True, "skipped": "raw_tradingview_alert_suppressed"}

        thread = threading.Thread(
            target=run_claude_recheck_background,
            args=(event,),
            daemon=True
        )
        thread.start()

        print(json.dumps({
            "event": event,
            "telegram_ok": telegram_result.get("ok", False),
            "claude_recheck_queued": True
        }, ensure_ascii=False), flush=True)

        self._send(200, {
            "ok": True,
            "saved_to": str(LOG_FILE),
            "telegram_ok": telegram_result.get("ok", False),
            "claude_recheck_queued": True
        })

    def log_message(self, format, *args):
        return


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Receiver ativo em http://{HOST}:{PORT}/webhook/{SECRET}", flush=True)
    print(f"Health check: http://{HOST}:{PORT}/health", flush=True)
    print(f"Log: {LOG_FILE}", flush=True)
    print("Telegram: habilitado via .env" if ENV_FILE.exists() else "Telegram: .env não encontrado", flush=True)
    print("Claude recheck:", CLAUDE_RECHECK, "OK" if CLAUDE_RECHECK.exists() else "NÃO ENCONTRADO", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando receiver.", flush=True)
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()
