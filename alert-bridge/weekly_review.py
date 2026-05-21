#!/usr/bin/env python3
"""weekly_review.py — Dashboard semanal de frentes em validação.

Roda domingo 09:00 BRT via launchd. Lê logs e memories, identifica:
  - O que está coletando (n vs critério)
  - O que está PRONTO PRA REVISAR (n>=30 atingido OU prazo venceu)
  - O que ficou esquecido (sem update há X dias)

Envia Telegram com bloco compacto por frente. Reusa send_telegram() do claude_monitor.

Modes:
  --mode once : imprime no stdout, NÃO envia Telegram
  --mode cron : imprime + envia Telegram (usado pelo launchd)

Frentes monitoradas (atualizado 2026-05-21 pós-cleanup):
  1. V4 SHADOW classification — n SETUP_CONFIRMED_ENTRY vs 30+
  2. SMC V3d XAU 4H shadow — n events com v3d_shadow_event_present=true
  3. SMC V3d EUR 4H shadow — idem EUR
  4. MTF Gate Hybrid — n com mtf_shadow_aligned=true por módulo
  5. External Factors v1.2 — n events + calendar_active history (P0.3 audit)
  6. Enrich v2 (4 lentes) — n outcomes com outcomes_by_atr_mult
  7. XAU 4H Python monitor — n evaluations + matches últimos 7d
  8. D2R growth — total + records/dia últimos 7d
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import argparse, json, sys

BASE_DIR = Path(__file__).parent.parent
LOG_DIR = Path(__file__).parent / "logs"

SETUP_RESEARCH_LOG = LOG_DIR / "setup_research_log.jsonl"
SETUP_R_OUTCOME_LOG = LOG_DIR / "setup_r_outcome_log.jsonl"
INDICATOR_OUTCOMES_LOG = LOG_DIR / "indicator_signals_outcomes.jsonl"
STRATEGY_EVAL_LOG = LOG_DIR / "strategy_eval_log.jsonl"
STRATEGY_SIGNALS_LOG = LOG_DIR / "strategy_signals.jsonl"

# Critério institucional (memory feedback_sample_gate_for_rules)
SAMPLE_GATE_DIRECTIONAL = 30
SAMPLE_GATE_PRELIMINARY = 50
SAMPLE_GATE_SOLID = 100

# V4 SHADOW critério: ≥30 + win 70%
V4_TARGET_N = 30
V4_TARGET_WIN = 70.0

# SMC V3d, MTF Gate: ≥30 forward
SHADOW_TARGET_N = 30

# Days lookback pra "última semana"
LOOKBACK_DAYS = 7


def load_env():
    env_path = BASE_DIR / ".env"
    env = {}
    if not env_path.exists(): return env
    for line in env_path.read_text().splitlines():
        if not line or line.startswith("#") or "=" not in line: continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def send_telegram(text):
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_ids_raw = env.get("TELEGRAM_CHAT_IDS") or env.get("TELEGRAM_CHAT_ID")
    if not token or not chat_ids_raw:
        print("[WARN] Telegram não configurado"); return False
    chat_ids = [x.strip() for x in chat_ids_raw.split(",") if x.strip()]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    ok = True
    # Split em chunks de 4000 chars
    chunks = []
    while text:
        if len(text) <= 4000:
            chunks.append(text); break
        cut = text.rfind("\n", 0, 4000)
        if cut < 100: cut = 4000
        chunks.append(text[:cut]); text = text[cut:].lstrip()
    for chat_id in chat_ids:
        for chunk in chunks:
            try:
                data = urlencode({"chat_id":chat_id,"text":chunk,"disable_web_page_preview":"true"}).encode()
                req = Request(url, data=data, method="POST")
                with urlopen(req, timeout=20) as resp:
                    result = json.loads(resp.read().decode())
                ok = ok and bool(result.get("ok"))
            except Exception as e:
                print(f"[ERR] Telegram: {e}"); ok = False
    return ok


def parse_iso(s):
    if not s: return None
    try: return datetime.fromisoformat(s.replace("Z","+00:00"))
    except: return None


def read_jsonl(path):
    if not path.exists(): return []
    out = []
    try:
        with path.open() as f:
            for line in f:
                try: out.append(json.loads(line))
                except: pass
    except: pass
    return out


def is_recent(dt, days=LOOKBACK_DAYS):
    if dt is None: return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return dt >= cutoff


def fmt_pct(n, total):
    if total == 0: return "—"
    return f"{100*n/total:.1f}%"


# ─── Check functions ───────────────────────────────────────────────────────

def check_v4_shadow():
    """V4 SHADOW classification — n SETUP_CONFIRMED_ENTRY vs 30+ + win 70%."""
    records = read_jsonl(SETUP_RESEARCH_LOG)
    confirmed = [r for r in records if r.get("classification_v4_shadow") == "SETUP_CONFIRMED_ENTRY"]
    n_total = len(confirmed)
    # Cruzar com D2R pra win rate (matching by event_id parcial)
    # Simplification: cross com setup_r_outcome_log
    outcomes = read_jsonl(SETUP_R_OUTCOME_LOG)
    outcomes_by_event = {o.get("event_id"): o for o in outcomes if o.get("event_id")}
    matched = []
    for r in confirmed:
        eid = r.get("event_id")
        o = outcomes_by_event.get(eid)
        if o and o.get("r_outcome_label") != "no_trade":
            r_value = o.get("r_realized")
            if r_value is not None:
                matched.append(r_value)
    wins = sum(1 for r in matched if r > 0)
    win_pct = (100*wins/len(matched)) if matched else None
    status = "PRONTO" if (n_total >= V4_TARGET_N and win_pct and win_pct >= V4_TARGET_WIN) else "COLETANDO"
    return {
        "name": "V4 SHADOW (SETUP_CONFIRMED_ENTRY)",
        "n_total": n_total,
        "n_with_outcome": len(matched),
        "win_pct": win_pct,
        "target_n": V4_TARGET_N,
        "target_win": V4_TARGET_WIN,
        "status": status,
    }


def check_smc_v3d(asset):
    """SMC V3d shadow por asset — n events com v3d_shadow_event_present=true."""
    records = read_jsonl(SETUP_RESEARCH_LOG)
    n_total = sum(1 for r in records
                  if r.get("base_symbol") == asset
                  and r.get("timeframe") == "240"
                  and r.get("v3d_shadow_event_present") is True)
    n_recent = sum(1 for r in records
                   if r.get("base_symbol") == asset
                   and r.get("timeframe") == "240"
                   and r.get("v3d_shadow_event_present") is True
                   and is_recent(parse_iso(r.get("evaluated_at") or r.get("received_at"))))
    status = "PRONTO" if n_total >= SHADOW_TARGET_N else "COLETANDO"
    return {
        "name": f"SMC V3d {asset} 4H",
        "n_total": n_total,
        "n_last_7d": n_recent,
        "target_n": SHADOW_TARGET_N,
        "status": status,
    }


def check_mtf_gate():
    """MTF Gate Hybrid — n com mtf_shadow_aligned=true por módulo (XAU 4H, EUR 4H, EUR 1H)."""
    records = read_jsonl(SETUP_RESEARCH_LOG)
    out = []
    for asset, tf in [("XAUUSD","240"), ("EURUSD","240"), ("EURUSD","60")]:
        n_total = sum(1 for r in records
                      if r.get("base_symbol") == asset
                      and r.get("timeframe") == tf
                      and r.get("mtf_shadow_aligned") is True)
        n_recent = sum(1 for r in records
                       if r.get("base_symbol") == asset
                       and r.get("timeframe") == tf
                       and r.get("mtf_shadow_aligned") is True
                       and is_recent(parse_iso(r.get("evaluated_at") or r.get("received_at"))))
        status = "PRONTO" if n_total >= SHADOW_TARGET_N else "COLETANDO"
        tf_label = "4H" if tf=="240" else "1H"
        out.append({
            "name": f"MTF Gate {asset} {tf_label}",
            "n_total": n_total,
            "n_last_7d": n_recent,
            "target_n": SHADOW_TARGET_N,
            "status": status,
        })
    return out


def check_external_factors():
    """External Factors v1.2 — schema flatten (prefixo external_*) + calendar history (P0.3)."""
    records = read_jsonl(SETUP_RESEARCH_LOG)
    n_v12 = 0
    n_cal_active = 0
    n_recent = 0
    n_fetch_ok = 0
    for r in records:
        sv = r.get("external_schema_version", "") or ""
        if "v1.2" in sv or "v1_2" in sv:
            n_v12 += 1
            if r.get("external_calendar_active") is True:
                n_cal_active += 1
            if r.get("external_fetch_ok") is True:
                n_fetch_ok += 1
            if is_recent(parse_iso(r.get("evaluated_at") or r.get("received_at"))):
                n_recent += 1
    cal_pct = fmt_pct(n_cal_active, n_v12)
    p03_alert = (n_v12 >= 50 and n_cal_active == 0 and n_fetch_ok >= 30)
    return {
        "name": "External Factors v1.2",
        "n_total": n_v12,
        "n_last_7d": n_recent,
        "n_calendar_active": n_cal_active,
        "n_fetch_ok": n_fetch_ok,
        "calendar_active_pct": cal_pct,
        "target_n": 50,
        "p03_alert": p03_alert,
        "status": "PRONTO" if n_v12 >= 50 else "COLETANDO",
    }


def check_enrich_v2():
    """Enrich v2 — n outcomes com outcomes_by_atr_mult (lente B). Desde 2026-05-19."""
    records = read_jsonl(INDICATOR_OUTCOMES_LOG)
    n_total = sum(1 for r in records if r.get("outcomes_by_atr_mult"))
    n_recent = sum(1 for r in records
                   if r.get("outcomes_by_atr_mult")
                   and is_recent(parse_iso(r.get("evaluated_at") or r.get("ts_signal"))))
    # Critério: ~2 semanas após 2026-05-19 = 2026-06-02
    deadline = datetime(2026, 6, 2, tzinfo=timezone.utc)
    days_left = (deadline - datetime.now(timezone.utc)).days
    status = "PRAZO PRÓXIMO" if days_left <= 3 else "COLETANDO"
    return {
        "name": "Enrich v2 (4 lentes B/C/D/E)",
        "n_total": n_total,
        "n_last_7d": n_recent,
        "days_to_deadline": days_left,
        "status": status,
    }


def check_xau_4h_monitor():
    """XAU 4H Python monitor — count evals + matches últimos 7d."""
    evals = read_jsonl(STRATEGY_EVAL_LOG)
    signals = read_jsonl(STRATEGY_SIGNALS_LOG)
    n_evals_total = len(evals)
    n_evals_recent = sum(1 for r in evals if is_recent(parse_iso(r.get("ts"))))
    n_matches_total = len(signals)
    n_matches_recent = sum(1 for r in signals if is_recent(parse_iso(r.get("ts"))))
    # Por estratégia
    by_strategy = {}
    for r in signals:
        s = r.get("strategy", "?")
        by_strategy[s] = by_strategy.get(s, 0) + 1
    return {
        "name": "XAU 4H Python monitor",
        "n_evals_total": n_evals_total,
        "n_evals_last_7d": n_evals_recent,
        "n_matches_total": n_matches_total,
        "n_matches_last_7d": n_matches_recent,
        "matches_by_strategy": by_strategy,
        "status": "OPERACIONAL",
    }


def check_d2r_growth():
    """D2R outcomes — total + mediana records/dia últimos 7d (resistente a backfills).

    Mediana é melhor que média porque o D2R tem backfills periódicos (memory
    project_d2r_indicator_appendix) que processam dezenas de events legacy em 1 batch,
    inflando a média artificialmente. Mediana reflete ritmo real de processamento diário.
    """
    records = read_jsonl(SETUP_R_OUTCOME_LOG)
    n_total = len(records)
    # Agrupar por dia
    by_day = {}
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    for r in records:
        dt = parse_iso(r.get("evaluated_at"))
        if dt is None or dt < cutoff: continue
        day = dt.strftime("%Y-%m-%d")
        by_day[day] = by_day.get(day, 0) + 1
    counts = sorted(by_day.values()) if by_day else [0]
    n_recent = sum(counts)
    # Mediana
    n = len(counts)
    if n == 0:
        median_per_day = 0
    elif n % 2 == 1:
        median_per_day = counts[n // 2]
    else:
        median_per_day = (counts[n//2 - 1] + counts[n//2]) / 2
    max_day = max(counts) if counts else 0
    return {
        "name": "D2R outcomes",
        "n_total": n_total,
        "n_last_7d": n_recent,
        "median_per_day": median_per_day,
        "max_day": max_day,
        "active_days": n,
        "status": "OPERACIONAL",
    }


# ─── Telegram formatter ────────────────────────────────────────────────────

def format_status_emoji(status):
    return {
        "OPERACIONAL": "🟢",
        "COLETANDO": "🟡",
        "PRAZO PRÓXIMO": "🟠",
        "PRONTO": "✅",
    }.get(status, "⚪")


def format_telegram(checks):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"📊 WEEKLY REVIEW — {today}", "─" * 30, ""]

    # 1. V4 SHADOW
    c = checks["v4"]
    emoji = format_status_emoji(c["status"])
    wpct = f"{c['win_pct']:.1f}%" if c["win_pct"] is not None else "—"
    lines.append(f"{emoji} *{c['name']}*")
    lines.append(f"  n={c['n_total']}/{c['target_n']} · win={wpct}/{c['target_win']:.0f}% · com_outcome={c['n_with_outcome']}")
    lines.append("")

    # 2-3. SMC V3d XAU + EUR
    for c in checks["smc_v3d"]:
        emoji = format_status_emoji(c["status"])
        lines.append(f"{emoji} *{c['name']}*")
        lines.append(f"  n={c['n_total']}/{c['target_n']} · últ 7d={c['n_last_7d']}")
        lines.append("")

    # 4. MTF Gate (3 módulos)
    lines.append("📐 *MTF Gate Hybrid*")
    for c in checks["mtf"]:
        emoji = format_status_emoji(c["status"])
        lines.append(f"  {emoji} {c['name'].replace('MTF Gate ','')}: n={c['n_total']}/{c['target_n']} (últ 7d={c['n_last_7d']})")
    lines.append("")

    # 5. External Factors
    c = checks["external"]
    emoji = format_status_emoji(c["status"])
    lines.append(f"{emoji} *{c['name']}*")
    lines.append(f"  n={c['n_total']}/{c['target_n']} · fetch_ok={c['n_fetch_ok']} · cal_active={c['n_calendar_active']} ({c['calendar_active_pct']})")
    if c["p03_alert"]:
        lines.append(f"  ⚠️ P0.3 ALERT: calendar_active=0 em {c['n_fetch_ok']} fetches OK → verificar iMac config")
    lines.append("")

    # 6. Enrich v2
    c = checks["enrich"]
    emoji = format_status_emoji(c["status"])
    lines.append(f"{emoji} *{c['name']}*")
    days_str = f"{c['days_to_deadline']}d" if c['days_to_deadline'] >= 0 else f"VENCEU há {-c['days_to_deadline']}d"
    lines.append(f"  n={c['n_total']} · últ 7d={c['n_last_7d']} · prazo={days_str}")
    lines.append("")

    # 7. XAU 4H monitor
    c = checks["xau_4h"]
    emoji = format_status_emoji(c["status"])
    lines.append(f"{emoji} *{c['name']}*")
    lines.append(f"  evals 7d={c['n_evals_last_7d']} · matches 7d={c['n_matches_last_7d']} · total matches={c['n_matches_total']}")
    if c["matches_by_strategy"]:
        for s, n in c["matches_by_strategy"].items():
            lines.append(f"    {s}: {n}")
    lines.append("")

    # 8. D2R growth
    c = checks["d2r"]
    emoji = format_status_emoji(c["status"])
    lines.append(f"{emoji} *{c['name']}*")
    lines.append(f"  total={c['n_total']} · últ 7d={c['n_last_7d']} ({c['active_days']} dias ativos)")
    lines.append(f"  mediana/dia={c['median_per_day']} · pico={c['max_day']} (backfill se >>mediana)")
    lines.append("")

    # Pendências críticas (do MEMORY/Tasks)
    lines.append("─" * 30)
    lines.append("🔴 *Pendências críticas* (manuais)")
    lines.append("  • Comparar 4 lentes enrich_v2 — decidir oficial (Task #45, vence ~2026-06-02)")
    lines.append("  • Fase 0.5 — Validar 7 dias pós-cleanup (Task #4, vence 2026-05-26)")
    lines.append("  • P0.3 calendar config no iMac (high_impact_calendar.json)")

    return "\n".join(lines)


# ─── Main ──────────────────────────────────────────────────────────────────

def run_all_checks():
    return {
        "v4": check_v4_shadow(),
        "smc_v3d": [check_smc_v3d("XAUUSD"), check_smc_v3d("EURUSD")],
        "mtf": check_mtf_gate(),
        "external": check_external_factors(),
        "enrich": check_enrich_v2(),
        "xau_4h": check_xau_4h_monitor(),
        "d2r": check_d2r_growth(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["once","cron"], default="once",
                    help="once=imprime debug; cron=imprime + Telegram")
    args = ap.parse_args()

    print(f"[INIT] Weekly review (mode={args.mode})")
    checks = run_all_checks()
    msg = format_telegram(checks)
    print("─" * 50)
    print(msg)
    print("─" * 50)

    if args.mode == "cron":
        ok = send_telegram(msg)
        print(f"[TELEGRAM] sent={ok}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
