# SKILL 05 — Production Safety

**Purpose:** Prevent research or chart work from damaging production.

## Core Rule

```text
Research must not mutate production unless explicitly authorized.
```

## Before Production-Adjacent Work

Ask/check:

1. Is this read-only?
2. Is chart interaction required?
3. Could daemon or cron interfere?
4. Is pause flag needed?
5. Is restore required after?

## Chart Work Protocol

Before plotting/drawing:

```text
pause xau daemon if needed
pause cron if needed
create /tmp/claude_recheck.paused
confirm PEPPERSTONE:XAUUSD
confirm timeframe
confirm drawing count
draw only requested items
leave drawings if user review needed
```

After review/when authorized:

```text
clear requested drawings
remove pause flag
restore daemon
restore cron if needed
verify health
```

## Health Checks

After any operational change:

```text
receiver /health local
public /health HTTP 200
xau daemon loaded + PID
expected server.js child only
pause flag absent unless intentionally paused
enrich absent
d2r_daily absent
zero orphan server.js
```

## Forbidden

Do not:

- restart old enrich;
- assume External Factors exists;
- leave daemon/cron paused without telling user;
- use launchctl casually;
- touch secrets;
- push production code without approval.

## Output

Use short status table:

```text
pause flag
daemon
cron
receiver
public health
server.js
what changed
what not touched
```
