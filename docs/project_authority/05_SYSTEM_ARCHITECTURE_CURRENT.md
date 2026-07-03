# 05 — System Architecture Current

**Project:** Trading System  
**Purpose:** Maintain a clear snapshot of the current architecture before cleanup/restructure.  
**Rule:** This file describes current known state. It is not permission to modify production.

---

## 1. System Purpose

The Trading System is an analyst/operator-assist stack.

It is **not** an auto-trading system.

Canonical flow:

```text
TradingView alerts / chart context
→ webhook receiver
→ Claude recheck / analysis layer
→ selective Telegram / human review
```

The user makes final trading decisions.

---

## 2. Hardware Roles

### MacBook

Current primary machine.

Runs the full trading system stack unless explicitly changed.

### iMac

Previously used for External Factors.

Current state:

```text
External Factors intentionally decommissioned.
Do not assume iMac bridge is available.
```

---

## 3. Production Components

### 3.1 Webhook Receiver

Role:

```text
Receives TradingView alerts.
Normalizes payloads.
Routes to logs/recheck paths.
Exposes /health.
```

Safety:

- Must stay healthy during research.
- Do not restart unless task explicitly requires it.
- Always verify `/health` after operational changes.

---

### 3.2 Cloudflared Tunnel

Role:

```text
Public access for TradingView webhook.
```

Known state:

- LaunchAgent supervised.
- Public `/health` should return HTTP 200.
- If public health fails, distinguish receiver failure from tunnel failure.

---

### 3.3 Claude Recheck

Role:

```text
Evaluates incoming alerts according to prompt/rules.
May classify as observation/review/valid depending on enabled module.
```

Important:

- Recheck prompt has had several governance patches.
- Do not assume a module can emit live/valid alerts just because the code exists.
- Check current catalog/rules/recheck blocks before making statements.

---

### 3.4 XAU 4H Monitor Daemon

Role:

```text
Runs XAU 4H monitoring logic.
May spawn TradingView MCP/CDP child process.
```

Before chart interaction:

```text
Pause daemon if chart-controlling actions may conflict.
Also pause cron when applicable.
Create pause flag.
```

After chart work:

```text
Restore daemon/cron unless user explicitly says not to.
Verify health.
```

**XAU 15M (reconciliação 2026-07-02):** NÃO existe runtime 15M — nenhum daemon, monitor, cron ou LaunchAgent executa a estratégia XAU 15M LONG (`USER_APPROVED_NOT_PRODUCTION`, research-only). `run_xau_15m_pullback_ohlcv.py` é coletor histórico offline, não runtime. Não assumir nem criar runtime 15M sem autorização explícita.

---

### 3.5 Cron / Scheduled Monitor

Role:

```text
May re-trigger monitor activity.
```

Lesson:

```text
Pausing daemon alone is not enough if cron can relaunch or trigger chart activity.
Pause daemon AND cron when chart safety requires it.
```

---

### 3.6 TradingView MCP / CDP

Role:

```text
Used for chart state, drawings, screenshots, and data extraction.
```

Rules:

- Do not call MCP unless task explicitly requires chart interaction.
- Validate symbol/timeframe before drawing.
- Use canonical drawing format for Long Position.
- Never assume current chart state.

Canonical symbol/timeframe for most XAU chart work:

```text
PEPPERSTONE:XAUUSD
4H or 1H depending task
15M for XAU 15M LONG research (approved strategy, not production)
```

**RAW 15M coverage (reconciliação 2026-07-02):** dataset RAW 15M sancionado = `raw_replay/XAUUSD/15M` no HD externo, cobertura **2024-05 → 2026-02**. Extensão mar→jun-2026 = bloco futuro autorizado separadamente (`RAW_15M_EXTENSION_PLAN_MAR_JUN_2026`); nunca coletar fora do `safe_backtest_window.sh`.

---

### 3.7 Telegram

Role:

```text
Human-facing notification channel.
```

Important:

- Some modules are deliberately suppressed.
- Watch-only/research modules must not emit urgent live entry alerts.
- `NO_TELEGRAM_DISPATCH` / recheck prompt status must be respected.

---

## 4. Data Architecture

### 4.1 RAW Replay Data

Current rule:

```text
RAW replay/source data is the source of truth for strategy validation.
```

Stored externally under the TradingData drive structure.

RAW is required for:

- indicator semantics;
- labels;
- zones;
- Bubbles;
- SMC;
- NAS;
- Auction Theory context;
- threshold calibration;
- serious strategy validation.

---

### 4.2 Dataset Registry

Role:

```text
Tracks known RAW datasets, timeframes, active/superseded status, checksums/manifests.
```

Use for locating source data, not as proof of strategy validity.

---

### 4.3 Extractor

Role:

```text
Transforms RAW into derived features.
```

Current caution:

- Extractor outputs are not automatically validation-grade.
- Each field must be traced to RAW/source semantics before serious use.
- Proxy/derived fields are suspect by default.

---

### 4.4 SLIM Features

Current policy:

```text
SLIM is not a validation source.
SLIM must not define zones, thresholds, gates, or strategy validity.
```

May only be referenced as contaminated historical artifact or for explicitly authorized non-validatory screening.

---

### 4.5 PDFs / Reports / Temporary Outputs

Generated PDFs, `/tmp` scripts, and lab outputs are research artifacts.

They are not operational truth unless promoted through a formal, RAW-traced process.

---

## 5. Strategy Governance Files

Known governance areas:

```text
my-strategy/strategies/catalog.json
my-strategy/strategy_rules.json
alert-bridge/claude_recheck.py
my-strategy/research/
docs/research/
```

Rules:

- Do not modify governance files without explicit authorization.
- Catalog status and actual behavior may diverge; verify both.
- `strategy_rules.json` is high-impact and must be handled with caution.

---

## 6. Known Decommissioned / Deprecated Components

### External Factors

Status:

```text
Decommissioned on iMac.
Do not assume available.
```

### Enrich / Outcome Evaluator

Status:

```text
Deprecated/decommissioned.
Do not restart old enrich logic.
Future outcome lab must be redesigned cleanly.
```

### d2r-daily

Status:

```text
Absent/paused in recent production sanity checks.
Do not assume active.
```

---

## 7. Production Health Checklist

After operational changes, verify:

```text
receiver local /health ok
public /health HTTP 200
xau daemon loaded + PID
expected child server.js only
pause flag absent unless intentionally paused
enrich absent
d2r-daily absent
zero orphan server.js
working tree not unexpectedly changed
```

---

## 8. Chart Work Checklist

Before chart drawing/plotting:

```text
1. Confirm task requires chart.
2. Pause daemon and cron if needed.
3. Create pause flag.
4. Confirm TradingView symbol/timeframe.
5. Confirm current drawings.
6. Plot only requested sample.
7. Leave drawings if user needs review.
8. Do not screenshot/PDF unless asked.
9. Restore only when user confirms or task requires.
```

---

## 9. Current Architectural Problem

The system accumulated too many research artifacts, temporary scripts, outdated docs, and proxy-based assumptions.

The current project goal is:

```text
cleaner architecture
fewer moving parts
RAW-first validation
clear status governance
minimum safe execution
```

---

## 10. Current Cleanup Priority

1. Separate source-of-truth from derived/proxy artifacts.
2. Mark contaminated strategy work as suspect.
3. Preserve RAW and manifests.
4. Remove or archive stale helper artifacts only after inventory.
5. Simplify workflow before new validation/promotion.
