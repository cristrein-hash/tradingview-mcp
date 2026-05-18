#!/usr/bin/env python3
"""Auto D2R daily backfill.

- Loops evaluate_r_outcomes.py in batches of 3 until no more eligible events
  or max wall-time budget reached.
- After loop: scans new D2R records for outliers.
- Sends Telegram summary with:
  - Daily volume (events evaluated, total R, win rate)
  - Big wins (>= +2.5R)
  - Big losses with retro-valid setup ("missed winners")
  - Wrong promotions (CANDIDATO_FORTE → loss)

Designed to be launched by launchd once per day.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_DIR = Path("/Users/cristrein/tradingview-mcp")
EVAL_SCRIPT = BASE_DIR / "alert-bridge" / "evaluate_r_outcomes.py"
R_OUTCOME_LOG = BASE_DIR / "alert-bridge" / "logs" / "setup_r_outcome_log.jsonl"
DAILY_LOG_DIR = BASE_DIR / "alert-bridge" / "logs" / "d2r_daily"
DAILY_LOG_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = BASE_DIR / "alert-bridge" / ".env"

MAX_WALL_TIME_SECONDS = 7200  # 2 hours hard cap
MAX_BATCHES = 40              # safety bound
BATCH_LIMIT = 3
BATCH_TIMEOUT = 900           # per-batch timeout

OUTLIER_WIN_R = 2.5           # flag wins >= +2.5R
OUTLIER_LOSS_R = -1.0         # flag losses (= -1R)
CLASSIFICATIONS = (
    "SETUP_CANDIDATO_FORTE,"
    "SETUP_CANDIDATO_FORTE_INTRADAY,"
    "SETUP_EM_OBSERVACAO,"
    "SETUP_EM_OBSERVACAO_INTRADAY,"
    "INTRADAY_EM_OBSERVACAO,"
    # 2026-05-18: variantes legacy com espaço/acento (pre-V3 vocabulário)
    "SETUP EM OBSERVAÇÃO,"
    "INTRADAY EM OBSERVAÇÃO,"
    # 2026-05-18: classifications de contextual state (incluídas no scope D2R)
    "SETUP_PERDIDO_NAO_PERSEGUIR,"
    "SETUP_ATRASADO_AGUARDAR_RETESTE"
)

# 2026-05-18: B.1 — indicator_signals outcomes pra appendix no Telegram daily
INDICATOR_SIGNALS_OUTCOMES_LOG = Path.home() / "tradingview-mcp" / "alert-bridge" / "logs" / "indicator_signals_outcomes.jsonl"


def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def send_telegram(text: str, parse_mode: str = "HTML"):
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_ids_raw = env.get("TELEGRAM_CHAT_IDS") or env.get("TELEGRAM_CHAT_ID")
    if not token or not chat_ids_raw:
        return {"ok": False, "error": "telegram_env_missing"}
    chat_ids = [x.strip() for x in chat_ids_raw.split(",") if x.strip()]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    results = []
    for chat_id in chat_ids:
        # Telegram limit: 4096 chars per message
        for i in range(0, len(text), 4000):
            chunk = text[i:i+4000]
            data = urlencode({
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": parse_mode,
                "disable_web_page_preview": "true"
            }).encode("utf-8")
            req = Request(url, data=data, method="POST")
            try:
                with urlopen(req, timeout=20) as resp:
                    results.append(json.loads(resp.read().decode("utf-8")))
            except Exception as e:
                results.append({"ok": False, "error": str(e), "chat_id": chat_id})
    return {"ok": all(r.get("ok") for r in results), "results": results}


def read_outcomes():
    if not R_OUTCOME_LOG.exists():
        return []
    rows = []
    with R_OUTCOME_LOG.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def run_batch(daily_log):
    cmd = [
        "python3", str(EVAL_SCRIPT),
        "--limit", str(BATCH_LIMIT),
        "--since", "2026-04-01",
        "--classifications", CLASSIFICATIONS,
        "--timeout", str(BATCH_TIMEOUT),
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR / "alert-bridge"),
            text=True,
            capture_output=True,
            timeout=BATCH_TIMEOUT + 60,
        )
    except subprocess.TimeoutExpired:
        daily_log.write(f"  [TIMEOUT] batch exceeded {BATCH_TIMEOUT+60}s\n")
        return "timeout", None
    daily_log.write(f"  exit={result.returncode}\n")
    if result.returncode != 0:
        daily_log.write(f"  STDERR: {result.stderr[-500:]}\n")
        return "error", result
    stdout = result.stdout or ""
    daily_log.write(f"  STDOUT (tail): {stdout[-300:]}\n")
    if "Nenhum evento elegível" in stdout:
        return "exhausted", result
    if "R outcomes novos salvos:" in stdout:
        return "success", result
    return "unknown", result


def detect_outliers(new_records):
    """Categorize new records into highlight buckets."""
    big_wins = []
    big_losses = []
    missed_winners = []      # high retro-valid but classified low
    wrong_promotions = []    # CANDIDATO_FORTE that turned loss

    for r in new_records:
        rval = r.get("theoretical_r_outcome")
        if rval is None:
            continue
        rval = float(rval)
        label = r.get("r_outcome_label", "")
        cls = r.get("classification_at_signal", "")
        sym = r.get("symbol", "?")
        tf = r.get("timeframe", "?")
        dir_ = r.get("direction", "?")
        retro = r.get("setup_valid_retro", False)
        tradeable = r.get("would_have_been_tradeable", False)

        # Big win
        if rval >= OUTLIER_WIN_R:
            big_wins.append((rval, sym, tf, dir_, cls))

        # Loss with retro-valid (missed winner)
        if label == "loss_1r" and retro and tradeable:
            missed_winners.append((sym, tf, dir_, cls))

        # CANDIDATO_FORTE that became loss
        if "CANDIDATO_FORTE" in cls and rval <= OUTLIER_LOSS_R:
            wrong_promotions.append((sym, tf, dir_, cls))

    return {
        "big_wins": big_wins,
        "missed_winners": missed_winners,
        "wrong_promotions": wrong_promotions,
    }


def build_telegram_message(stats, outliers, new_records):
    """Build compact daily summary."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    msg = [f"<b>🤖 D2R Daily Backfill — {today}</b>", ""]

    msg.append(f"<b>📊 Volume</b>")
    msg.append(f"  Eventos avaliados hoje: <b>{stats['n_new']}</b>")
    msg.append(f"  Total acumulado D2R: {stats['n_total']}")
    msg.append("")

    if stats['n_new'] == 0:
        msg.append("Sem novos eventos elegíveis hoje (D+2 cutoff).")
        return "\n".join(msg)

    msg.append(f"<b>📈 Outcomes (apenas tradeable hoje)</b>")
    msg.append(f"  Tradeable: {stats['n_tradeable']}")
    msg.append(f"  Sum R: <b>{stats['total_r']:+.2f}R</b>")
    if stats['n_tradeable'] > 0:
        msg.append(f"  Avg R: {stats['avg_r']:+.3f}")
        msg.append(f"  Win rate: {stats['win_rate']:.0%}")
    msg.append("")

    if outliers["big_wins"]:
        msg.append(f"<b>⭐ Big Wins ({len(outliers['big_wins'])})</b>")
        for r, sym, tf, dir_, cls in outliers["big_wins"][:5]:
            short_sym = sym.split(":")[-1]
            msg.append(f"  +{r:.2f}R  {short_sym} {tf}M {dir_} ({cls[:25]})")
        msg.append("")

    if outliers["missed_winners"]:
        msg.append(f"<b>⚠️ Missed Winners ({len(outliers['missed_winners'])})</b>")
        msg.append(f"  <i>(setup_valid_retro=True mas classificado baixo)</i>")
        for sym, tf, dir_, cls in outliers["missed_winners"][:5]:
            short_sym = sym.split(":")[-1]
            msg.append(f"  {short_sym} {tf}M {dir_} ({cls[:25]})")
        msg.append("")

    if outliers["wrong_promotions"]:
        msg.append(f"<b>❌ Wrong Promotions ({len(outliers['wrong_promotions'])})</b>")
        msg.append(f"  <i>(CANDIDATO_FORTE virou loss_1r)</i>")
        for sym, tf, dir_, cls in outliers["wrong_promotions"][:5]:
            short_sym = sym.split(":")[-1]
            msg.append(f"  {short_sym} {tf}M {dir_}")
        msg.append("")

    msg.append(f"<i>Run duration: {stats['duration_min']:.1f}min</i>")
    return "\n".join(msg)


# === B.1 (2026-05-18): indicator_signals outcomes appendix ===
def build_indicator_outcomes_summary():
    """Read indicator_signals_outcomes.jsonl and produce compact summary block
    for Telegram daily message. Returns "" if file empty/missing."""
    if not INDICATOR_SIGNALS_OUTCOMES_LOG.exists():
        return ""
    rows = []
    try:
        with INDICATOR_SIGNALS_OUTCOMES_LOG.open() as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return ""
    if not rows:
        return ""

    # Today's records (UTC)
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_rows = [r for r in rows if r.get("enriched_at", "").startswith(today_str)]

    # Stats: count R outcomes per side
    long_outcomes = []
    short_outcomes = []
    for r in rows:
        lo = r.get("long_outcome") or {}
        so = r.get("short_outcome") or {}
        if lo.get("outcome_R") is not None:
            long_outcomes.append((lo["outcome_R"], r))
        if so.get("outcome_R") is not None:
            short_outcomes.append((so["outcome_R"], r))

    all_outcomes = long_outcomes + short_outcomes
    if not all_outcomes:
        return ""

    n_total = len(all_outcomes)
    n_today = len(today_rows)
    r_vals = [r for r, _ in all_outcomes]
    sum_r = sum(r_vals)
    wins = sum(1 for r in r_vals if r > 0.5)
    losses = sum(1 for r in r_vals if r < -0.5)
    win_rate = wins / n_total if n_total else 0

    msg = []
    msg.append("")
    msg.append(f"<b>🔬 Indicator Signals Pipeline</b>")
    msg.append(f"  Total outcomes acumulados: <b>{n_total}</b>")
    if n_today > 0:
        msg.append(f"  Novos hoje: {n_today}")
    msg.append(f"  Wins / Losses: {wins} / {losses} (WR={win_rate:.0%})")
    msg.append(f"  Sum R: <b>{sum_r:+.2f}R</b>")

    # Top 3 wins + top 3 losses
    all_outcomes_sorted = sorted(all_outcomes, key=lambda x: x[0], reverse=True)
    top_wins = all_outcomes_sorted[:3]
    top_losses = all_outcomes_sorted[-3:][::-1]

    if top_wins and top_wins[0][0] > 0.5:
        msg.append("")
        msg.append("  <i>Top wins:</i>")
        for r, rec in top_wins:
            if r <= 0.5: break
            sym = rec.get("base_symbol", "?")
            tf = rec.get("timeframe", "?")
            ind = rec.get("indicator_name", "?").replace("_", " ")
            sig = rec.get("signal_type", "?")
            msg.append(f"  +{r:.1f}R  {sym} TF{tf} | {ind} {sig[:20]}")

    if top_losses and top_losses[0][0] < -0.5:
        msg.append("")
        msg.append("  <i>Top losses:</i>")
        for r, rec in top_losses:
            if r >= -0.5: break
            sym = rec.get("base_symbol", "?")
            tf = rec.get("timeframe", "?")
            ind = rec.get("indicator_name", "?").replace("_", " ")
            sig = rec.get("signal_type", "?")
            msg.append(f"  {r:.1f}R  {sym} TF{tf} | {ind} {sig[:20]}")

    msg.append("")
    msg.append("  <i>Detalhes: report_indicator_edge.py --save</i>")
    return "\n".join(msg)


def main():
    started_at = datetime.now(timezone.utc)
    day_str = started_at.strftime("%Y-%m-%d")
    log_path = DAILY_LOG_DIR / f"auto_d2r_{day_str}.log"

    with log_path.open("a") as daily_log:
        daily_log.write(f"\n=== Auto D2R run started: {started_at.isoformat()} ===\n")

        baseline = read_outcomes()
        n_baseline = len(baseline)
        baseline_ids = {r.get("event_id") for r in baseline}
        daily_log.write(f"Baseline D2R records: {n_baseline}\n")

        deadline = started_at + timedelta(seconds=MAX_WALL_TIME_SECONDS)
        batch_count = 0
        consecutive_errors = 0

        while datetime.now(timezone.utc) < deadline and batch_count < MAX_BATCHES:
            batch_count += 1
            t_batch = datetime.now(timezone.utc).strftime("%H:%M:%S")
            daily_log.write(f"\n[{t_batch}] Batch {batch_count} starting...\n")
            daily_log.flush()
            status, _ = run_batch(daily_log)
            if status == "exhausted":
                daily_log.write("  → No more eligible events. Stopping.\n")
                break
            if status in ("error", "timeout"):
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    daily_log.write("  → 3 consecutive errors. Stopping.\n")
                    break
                daily_log.write("  → Pausing 30s before retry.\n")
                import time
                time.sleep(30)
                continue
            consecutive_errors = 0

        # Post-run analysis
        final = read_outcomes()
        new_records = [r for r in final if r.get("event_id") not in baseline_ids]
        finished_at = datetime.now(timezone.utc)

        n_new = len(new_records)
        tradeable_new = [r for r in new_records
                         if r.get("r_outcome_label") != "no_trade"
                         and r.get("theoretical_r_outcome") is not None]

        stats = {
            "n_new": n_new,
            "n_total": len(final),
            "n_tradeable": len(tradeable_new),
            "duration_min": (finished_at - started_at).total_seconds() / 60,
        }

        if tradeable_new:
            r_vals = [float(r["theoretical_r_outcome"]) for r in tradeable_new]
            stats["total_r"] = sum(r_vals)
            stats["avg_r"] = sum(r_vals) / len(r_vals)
            stats["win_rate"] = sum(1 for r in r_vals if r > 0) / len(r_vals)
        else:
            stats["total_r"] = 0.0
            stats["avg_r"] = 0.0
            stats["win_rate"] = 0.0

        outliers = detect_outliers(new_records)

        daily_log.write(f"\n=== Auto D2R run finished: {finished_at.isoformat()} ===\n")
        daily_log.write(f"  Total D2R records now: {len(final)}\n")
        daily_log.write(f"  New records: {n_new}\n")
        daily_log.write(f"  Big wins: {len(outliers['big_wins'])}\n")
        daily_log.write(f"  Missed winners: {len(outliers['missed_winners'])}\n")
        daily_log.write(f"  Wrong promotions: {len(outliers['wrong_promotions'])}\n")

    # Send Telegram
    # 2026-05-18 B.1: indicator_signals appendix sent even if D2R had 0 new records
    indicator_summary = build_indicator_outcomes_summary()

    if stats["n_new"] > 0:
        msg = build_telegram_message(stats, outliers, new_records)
        if indicator_summary:
            msg = msg + "\n" + indicator_summary
        try:
            send_telegram(msg)
        except Exception as e:
            with log_path.open("a") as f:
                f.write(f"Telegram send error: {e}\n")
    elif indicator_summary:
        # D2R sem novos, mas indicator pipeline tem outcomes — manda só o indicator block
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        msg = f"<b>🤖 D2R Daily — {today}</b>\n\nSem novos eventos D2R hoje.\n{indicator_summary}"
        try:
            send_telegram(msg)
        except Exception as e:
            with log_path.open("a") as f:
                f.write(f"Telegram send error: {e}\n")


if __name__ == "__main__":
    main()
