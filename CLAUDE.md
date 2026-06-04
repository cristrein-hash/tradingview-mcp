# TradingView MCP — Claude Instructions

68 tools for reading and controlling a live TradingView Desktop chart via CDP (port 9222).

## Decision Tree — Which Tool When

### "What's on my chart right now?"
1. `chart_get_state` → symbol, timeframe, chart type, list of all indicators with entity IDs
2. `data_get_study_values` → current numeric values from all visible indicators (RSI, MACD, BBands, EMAs, etc.)
3. `quote_get` → real-time price, OHLC, volume for current symbol

### "What levels/lines/labels are showing?"
Custom Pine indicators draw with `line.new()`, `label.new()`, `table.new()`, `box.new()`. These are invisible to normal data tools. Use:

1. `data_get_pine_lines` → horizontal price levels drawn by indicators (deduplicated, sorted high→low)
2. `data_get_pine_labels` → text annotations with prices (e.g., "PDH 24550", "Bias Long ✓")
3. `data_get_pine_tables` → table data formatted as rows (e.g., session stats, analytics dashboards)
4. `data_get_pine_boxes` → price zones / ranges as {high, low} pairs

Use `study_filter` parameter to target a specific indicator by name substring (e.g., `study_filter: "Profiler"`).

### "Give me price data"
- `data_get_ohlcv` with `summary: true` → compact stats (high, low, range, change%, avg volume, last 5 bars)
- `data_get_ohlcv` without summary → all bars (use `count` to limit, default 100)
- `data_get_ohlcv` with `from_time`/`to_time` (unix epoch seconds) → paginate historical bars by time window. Iterates full in-memory buffer. Requires chart history loaded first (user scroll). Used for cross-asset coverage (DXY, US10Y, BTC, XAG, etc.) over multi-year backtests.
- `quote_get` → single latest price snapshot

### "Analyze my chart" (full report workflow)
1. `quote_get` → current price
2. `data_get_study_values` → all indicator readings
3. `data_get_pine_lines` → key price levels from custom indicators
4. `data_get_pine_labels` → labeled levels with context (e.g., "Settlement", "ASN O/U")
5. `data_get_pine_tables` → session stats, analytics tables
6. `data_get_ohlcv` with `summary: true` → price action summary
7. `capture_screenshot` → visual confirmation

### "Change the chart"
- `chart_set_symbol` → switch ticker (e.g., "AAPL", "ES1!", "NYMEX:CL1!")
- `chart_set_timeframe` → switch resolution (e.g., "1", "5", "15", "60", "D", "W")
- `chart_set_type` → switch chart style (Candles, HeikinAshi, Line, Area, Renko, etc.)
- `chart_manage_indicator` → add or remove studies (use full name: "Relative Strength Index", not "RSI")
- `chart_scroll_to_date` → jump to a date (ISO format: "2025-01-15")
- `chart_set_visible_range` → zoom to exact date range (unix timestamps)

### "Work on Pine Script"
1. `pine_set_source` → inject code into editor
2. `pine_smart_compile` → compile with auto-detection + error check
3. `pine_get_errors` → read compilation errors
4. `pine_get_console` → read log.info() output
5. `pine_get_source` → read current code back (WARNING: can be very large for complex scripts)
6. `pine_save` → save to TradingView cloud
7. `pine_new` → create blank indicator/strategy/library
8. `pine_open` → load a saved script by name

### "Practice trading with replay"
1. `replay_start` with `date: "2025-03-01"` → enter replay mode
2. `replay_step` → advance one bar
3. `replay_autoplay` → auto-advance (set speed with `speed` param in ms)
4. `replay_trade` with `action: "buy"/"sell"/"close"` → execute trades
5. `replay_status` → check position, P&L, current date
6. `replay_stop` → return to realtime

### "Screen multiple symbols"
- `batch_run` with `symbols: ["ES1!", "NQ1!", "YM1!"]` and `action: "screenshot"` or `"get_ohlcv"`

### "Draw on the chart"
- `draw_shape` → horizontal_line, trend_line, rectangle, text (pass point + optional point2)
- `draw_list` → see what's drawn
- `draw_remove_one` → remove by ID
- `draw_clear` → remove all

### "Manage alerts"
- `alert_create` → set price alert (condition: "crossing", "greater_than", "less_than")
- `alert_list` → view active alerts
- `alert_delete` → remove alerts

### "Navigate the UI"
- `ui_open_panel` → open/close pine-editor, strategy-tester, watchlist, alerts, trading
- `ui_click` → click buttons by aria-label, text, or data-name
- `layout_switch` → load a saved layout by name
- `ui_fullscreen` → toggle fullscreen
- `capture_screenshot` → take a screenshot (regions: "full", "chart", "strategy_tester")

### "TradingView isn't running"
- `tv_launch` → auto-detect and launch TradingView with CDP on Mac/Win/Linux
- `tv_health_check` → verify connection is working

## Context Management Rules

These tools can return large payloads. Follow these rules to avoid context bloat:

1. **Always use `summary: true` on `data_get_ohlcv`** unless you specifically need individual bars
2. **Always use `study_filter`** on pine tools when you know which indicator you want — don't scan all studies unnecessarily
3. **Never use `verbose: true`** on pine tools unless the user specifically asks for raw drawing data with IDs/colors
4. **Avoid calling `pine_get_source`** on complex scripts — it can return 200KB+. Only read if you need to edit the code.
5. **Avoid calling `data_get_indicator`** on protected/encrypted indicators — their inputs are encoded blobs. Use `data_get_study_values` instead for current values.
6. **Use `capture_screenshot`** for visual context instead of pulling large datasets — a screenshot is ~300KB but gives you the full visual picture
7. **Call `chart_get_state` once** at the start to get entity IDs, then reference them — don't re-call repeatedly
8. **Cap your OHLCV requests** — `count: 20` for quick analysis, `count: 100` for deeper work, `count: 500` only when specifically needed

### Output Size Estimates (compact mode)
| Tool | Typical Output |
|------|---------------|
| `quote_get` | ~200 bytes |
| `data_get_study_values` | ~500 bytes (all indicators) |
| `data_get_pine_lines` | ~1-3 KB per study (deduplicated levels) |
| `data_get_pine_labels` | ~2-5 KB per study (capped at 50) |
| `data_get_pine_tables` | ~1-4 KB per study (formatted rows) |
| `data_get_pine_boxes` | ~1-2 KB per study (deduplicated zones) |
| `data_get_ohlcv` (summary) | ~500 bytes |
| `data_get_ohlcv` (100 bars) | ~8 KB |
| `capture_screenshot` | ~300 bytes (returns file path, not image data) |

## Tool Conventions

- All tools return `{ success: true/false, ... }`
- Entity IDs (from `chart_get_state`) are session-specific — don't cache across sessions
- Pine indicators must be **visible** on chart for pine graphics tools to read their data
- `chart_manage_indicator` requires **full indicator names**: "Relative Strength Index" not "RSI", "Moving Average Exponential" not "EMA", "Bollinger Bands" not "BB"
- Screenshots save to `screenshots/` directory with timestamps
- OHLCV capped at 500 bars, trades at 20 per request
- Pine labels capped at 50 per study by default (pass `max_labels` to override)

## Architecture

```
Claude Code ←→ MCP Server (stdio) ←→ CDP (localhost:9222) ←→ TradingView Desktop (Electron)
```

Pine graphics path: `study._graphics._primitivesCollection.dwglines.get('lines').get(false)._primitivesDataById`

## Pre-Change Discipline (added 2026-05-18)

Before proposing ANY code change to production files (`alert-bridge/*.py`, prompt sections in `claude_recheck.py`, strategy modules, pipeline scripts, daemons, hooks), answer these 4 questions **in order, before writing any code**:

1. **What INPUT does this change operate on?** (specific `alert_type`, webhook channel, log field, etc.)
2. **Is that input alive in the last 7 days?** Validate with `grep`/`wc` on the affected log, or `jq` on a recent snapshot. Don't assume — query.
3. **How many events/day arrive through the affected channel?** (last 24–48h).
4. **If < 5 events/day OR channel dormant: STOP.** Re-examine architecture before proposing a fix. The fix may be targeting dead infrastructure.

**Architectural changes require the Plan agent.** When the change touches prompt operacional, strategy module, webhook routing, pipeline logic, or schema of logs/events: invoke `Agent` with `subagent_type=Plan` BEFORE writing code. Plan agent is specialized for design — it forces premise verification that fast-fix mode skips.

This discipline exists because on 2026-05-18 a fix was proposed and implemented for the "Caminho B" (Zone Touch SMC) path in the operational prompt before discovering the drawings channel (`monitor_zone`, `monitor_dynamic_bb_zone`, etc.) had been silent for 3+ days post-indicators migration. The fix targeted dead architecture, had to be reverted, and eroded trust. **Skipping these 4 questions = repeating that mistake.**

## Workflow Orchestration (added 2026-05-26)

Complements — does not replace — the Karpathy rules in `alert-bridge/CLAUDE.md`, the Pre-Change Discipline above, and the project memory protocols (`PRINCIPAL_1` / `PRINCIPAL_2`). Only the missing deltas are listed here.

- **Plan before non-trivial work.** Any task with 3+ steps or a design decision requires a short, checkable plan and scope confirmation before implementation. Architectural changes still require the Plan agent. Plan the VERIFICATION, not only the build. If reality diverges from the plan, stop and re-plan instead of pushing forward.
- **Subagents for fan-out, not for depth.** Use subagents for broad search, parallel research, and independent analysis to keep the main context clean — one focused task per subagent. Exception: faithful code replication still requires direct source reading in chunks; `Explore` is too shallow for that (`PRINCIPAL_2.E`).
- **Track progress on multi-step work.** For long tasks, maintain a visible task list and update status as work progresses. Summarize what changed at each step.
- **Verification before “done”.** Never mark work complete without demonstrating it works: run the test, open the resulting log/file, confirm the real record, and compare before/after when relevant. This extends `PRINCIPAL_2.A`.
- **Autonomy is bounded.** Within already-authorized scope and with clear evidence (logs, failing test, deterministic error), proceed without asking for confirmation on every micro-step. However, consequential actions, irreversible changes, production impact, new code, deletions, data movement, LaunchAgents, secrets, and scope changes still require Pre-Change Discipline and explicit authorization. Never “fix autonomously” outside the approved scope.
- **Prefer the simplest robust solution.** Choose the simplest change that actually addresses root cause. Do not over-engineer, but also do not ship fragile shortcuts.

## Session Bootstrap & Skill Selection

How every session should start and how to choose skills. Workflow Orchestration above = *how to think/work*; this = *how to begin each session and pick the right skills*.

### 1. Read current state before acting
At the start of every new session, or before any operational task, read the current state before suggesting commands or changes. Relevant files:
- `CLAUDE.md`
- `alert-bridge/CLAUDE.md` (if present)
- `docs/architecture/OPERATIONAL_INVENTORY.md`
- `docs/architecture/DATA_STORAGE_POLICY.md`
- `docs/architecture/SESSION_STATE_BEFORE_XAU_15M_BACKTEST.md` (if still relevant)
- latest `git status`
- latest `git log --oneline -5`

Do not assume memory alone is sufficient. Confirm current repo/system state.

### 2. Inventory available skills
Before selecting skills, inventory all available Claude Code skills from both locations:
```bash
find ~/.claude/skills -maxdepth 2 -name SKILL.md 2>/dev/null | sort
find skills -maxdepth 2 -name SKILL.md 2>/dev/null | sort
```
Read the `name` and `description` fields. **Do not load all skills blindly** — select the relevant ones based on the task.

### 3. Select skills based on task
User-level operational skills (`~/.claude/skills/`):
- **replay-backtest-manager** — TradingView Replay collection, `safe_backtest_window.sh`, XAU 15M/30M/1H datasets, external cold storage, gzip, manifests, checksums, production restore.
- **trading-system-operator** — receiver, cloudflared, LaunchAgents, external factors, Telegram, health checks, daemon status, preflight, operational status.
- **incident-response** — failures, hangs, outages, unsafe loops, public webhook issues, MCP/CDP failures, orphan `server.js`, restore-first workflows.
- **repo-governance-cleanup** — repo cleanup, archive decisions, retention, cold storage, git hygiene, documentation, safe deletion/migration.
- **strategy-research-analyst** — datasets/research logs → strategy hypotheses, expectancy analysis, candidate packets, promotion gates, multi-timeframe research plans.

Project skills (`skills/`): **chart-analysis**, **pine-develop**, **replay-practice**, **strategy-report**, **multi-symbol-scan**.

If new skills exist, consider their description and select appropriately. Before acting, explicitly state: which skills are being applied; why they're relevant; which state docs were read; whether the task touches production.

### 4. Safety defaults before operations
Before any operational command, evaluate whether the task touches: receiver; cloudflared; external factors; XAU monitor daemon; enrich/evaluator; TradingView/MCP/CDP; LaunchAgents; secrets; data deletion/migration.

Safety defaults:
- Never expose `.env`, tokens, webhook secrets, or secret URLs.
- Never start the receiver directly with `python3`.
- Never run TradingView Replay collection outside `safe_backtest_window.sh`.
- Never run multiple collection blocks without explicit user authorization.
- Never delete local RAW before external gzip + SHA256 + `gzip -t` + roundtrip + manifest + explicit approval.
- If something fails, restore production first, then diagnose.
- If reality diverges from the plan, stop and re-plan.

### 5. Replay-specific preflight
Before any Replay collection:
- Confirm `enrich_indicator_outcomes.py` and `OUTCOME EVALUATOR` are absent (or explicitly stopped with user authorization).
- Clean orphan `server.js` processes.
- Confirm receiver `/health` OK.
- Confirm public `/health` returns 200.
- Confirm pause flag absent.
- Confirm XAU monitor daemon loaded.
- Ask the user to confirm TradingView chart symbol, timeframe, and indicators manually.

### 6. Response format
For operational tasks, keep output concise and separated: what was checked; what changed; what was not touched; PASS/FAIL; production restore status; next action requiring user authorization.

Never continue into the next destructive, long-running, or operationally risky step without explicit user confirmation.

## Plugin & Skill Routing Policy (added 2026-05-27)

At session start, inventory available skills/plugins/MCPs, but **do not use all of them blindly**. Available ≠ used. Do not use every plugin on every task. Before acting, pick only the relevant skills/plugins, declare which and why.

Routing rules:
- **replay-backtest-manager** — TradingView Replay collection, `safe_backtest_window.sh`, RAW datasets, gzip, manifests, HD externo, production restore.
- **trading-system-operator** — receiver, cloudflared, LaunchAgents, external factors, daemon status, health checks.
- **incident-response** — when failures, hangs, outages, MCP/CDP issues, orphan `server.js`, or unsafe loops occur.
- **repo-governance-cleanup** — archive, retention, storage, git hygiene, docs, safe cleanup.
- **strategy-research-analyst** — hypotheses, expectancy, backtest interpretation, candidate packets, multi-timeframe research.
- **sequential-thinking** (MCP) — complex planning, architecture decisions, multi-step reasoning, or when uncertainty is high.
- **superpowers** (plugin) — only for brainstorming, subagent fan-out, or complex architectural exploration. Do NOT use during active Replay collection, production incidents, or simple linear tasks.
- **code-review** (plugin) — before/after meaningful code changes, especially before commits touching scripts, data pipelines, or production-adjacent code.
- **code-simplifier** (plugin) — only for deliberate refactoring/simplification after expected behavior is clear and tests/validation are known.
- **skill-creator** (plugin) — when creating, auditing, or improving Claude skills.

Default behavior:
- Simple operational task → no plugin unless needed.
- Risky production task → prefer incident-response or trading-system-operator.
- Data collection → prefer replay-backtest-manager.
- Code change → sequential-thinking for the plan, code-review before commit.
- Research/backtesting → strategy-research-analyst.

Superpowers policy:
- Keep installed. Do NOT use by default.
- Use only when the user asks for broad ideation, subagents, multiple competing approaches, or architectural exploration.
- **Never spawn broad subagent fan-out while Replay collection, enrich, or production-sensitive processes are running.**

Before using any plugin/tool: state which one will be used; state why it is relevant; state whether it touches production; ask for confirmation if the action is risky, long-running, destructive, or production-adjacent.
