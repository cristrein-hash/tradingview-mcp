#!/usr/bin/env python3
"""monitor_xau_4h_strategies.py — Caminho D Python monitor for XAU 4H reversal strategies.

Modes:
  --mode once   : avalia state atual UMA VEZ, imprime resultado (debug, NO telegram dispatch)
  --mode cron   : avalia + dispara Telegram + loga (usado por launchd cron 4h)
  --mode daemon : tail -f indicator_signals.jsonl, dispara avaliação em NAS LONG XAU 4H

Estratégias avaliadas (independentes, podem matchar em paralelo):
  1. XAU_4H_REVERSAL_CAPITULATION_LONG  (83.7% win histórico, ALTA CONVICÇÃO)
  2. XAU_4H_REVERSAL_DISCRETIONARY_SWEEP (100% win raríssimo, URGENTE)
  3. XAU_4H_REVERSAL_DISCRETIONARY_BASE  (60% win, NORMAL — sinalizador)

Reusa MCPClient (run_xau_4h_backtest.py pattern), chart lock (claude_recheck.py)
e telegram (claude_monitor.py).
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import argparse, fcntl, json, subprocess, sys, time

def repo_root():
    """Resolve the tradingview-mcp repo root robustly (survives file moves)."""
    import os
    from pathlib import Path as _Path
    env = os.environ.get("TVMCP_ROOT")
    if env and _Path(env).expanduser().is_dir():
        return _Path(env).expanduser().resolve()
    cur = _Path(__file__).resolve().parent
    for d in (cur, *cur.parents):
        if (d / ".git").exists() or (d / "src" / "server.js").exists() \
           or ((d / "alert-bridge").is_dir() and (d / "my-strategy").is_dir()):
            return d
    raise RuntimeError(f"TVMCP repo root not found from {__file__}; set TVMCP_ROOT or run inside the repo")


BASE_DIR = repo_root()
MCP_SERVER_PATH = BASE_DIR / "src" / "server.js"
NODE_BIN = "/opt/homebrew/bin/node"
LOG_DIR = repo_root() / "alert-bridge" / "logs"
SIGNALS_JSONL = LOG_DIR / "indicator_signals.jsonl"
STRATEGY_SIGNALS_JSONL = LOG_DIR / "strategy_signals.jsonl"
EVAL_LOG_JSONL = LOG_DIR / "strategy_eval_log.jsonl"
CHART_LOCK_PATH = "/tmp/tradingview_chart.lock"
# TELEGRAM_DISPATCH_ALLOWLIST: central default-deny dispatch permission (2026-06-15).
# Only strategy 'name's listed here may dispatch a live Telegram alert; anything NOT
# listed is still computed + logged but SUPPRESSED. Replaces the prior NO_TELEGRAM_DISPATCH
# denylist (block-by-exception) — safer because a newly-added strategy stays silent unless
# explicitly permitted (default-deny). EMPTY today = nothing dispatches:
#   - all 4 monitor strategies (discr_sweep, discr_base, capitulation, demand_breakout) are
#     REJECTED/WATCH_ONLY in catalog.json → stay suppressed.
#   - L1 EMA21 Continuation (USER_APPROVED_FINAL / HUMAN_DISCRETIONARY) is intentionally NOT
#     added: scanner / human-review only, no live Telegram now.
# Live dispatch stays OFF until the future Strategy Registry grants permission by status.
TELEGRAM_DISPATCH_ALLOWLIST = set()
CHART_LOCK_TIMEOUT_S = 120
PER_CALL_TIMEOUT_S = 60

LUX_BULL = 4286683400
LUX_BEAR = 4282726130

SYMBOL = "PEPPERSTONE:XAUUSD"
TIMEFRAME_4H = "240"
TIMEFRAME_D = "D"

# External Factors bridge (iMac HTTP server)
EXTERNAL_FACTORS_BASE_URL = "http://192.168.1.90:8765"
EXTERNAL_FACTORS_TIMEOUT_S = 5

# Sample sizes per memory project_xau_4h_reversal_capitulation_long.md & discretionary
CAPIT_ATR_RATIO_THRESHOLD = 1.3
CAPIT_RSI1D_MAX = 50.0
DISCR_NAS_DIST_MAX = -1.0
DISCR_DIST14D_MAX = -5.0
DISCR_T1_MAX_DELTA = 2
DISCR_T3_MAX_DELTA = 5
SWEEP_STRONG_LOW_MAX_DELTA = 10
SWEEP_EQL_MAX_DELTA = 20
NAS_LONG_MAX_DELTA = 5


def acquire_chart_lock(timeout_s=CHART_LOCK_TIMEOUT_S):
    fd = open(CHART_LOCK_PATH, "w")
    deadline = time.monotonic() + timeout_s
    start = time.monotonic()
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd, round(time.monotonic() - start, 2)
        except BlockingIOError:
            if time.monotonic() >= deadline:
                fd.close()
                raise TimeoutError(f"chart lock timeout {timeout_s}s")
            time.sleep(0.5)


def release_chart_lock(fd):
    if fd is None: return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN); fd.close()
    except Exception: pass


def load_env():
    env_path = BASE_DIR / "alert-bridge" / ".env"
    env = {}
    if not env_path.exists(): return env
    for line in env_path.read_text().splitlines():
        if not line or line.startswith("#") or "=" not in line: continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def send_telegram(text):
    import os
    if os.path.exists("/Users/cristrein/tradingview-mcp/.telegram_muted"):
        return False                                    # 🔇 MUTE GLOBAL — Cris pausou os sinais (2026-07-21)
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_ids_raw = env.get("TELEGRAM_CHAT_IDS") or env.get("TELEGRAM_CHAT_ID")
    if not token or not chat_ids_raw:
        print("[WARN] Telegram não configurado"); return False
    chat_ids = [x.strip() for x in chat_ids_raw.split(",") if x.strip()]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    ok = True
    for chat_id in chat_ids:
        try:
            data = urlencode({"chat_id":chat_id,"text":text,"disable_web_page_preview":"true"}).encode()
            req = Request(url, data=data, method="POST")
            with urlopen(req, timeout=20) as resp:
                result = json.loads(resp.read().decode())
            ok = ok and bool(result.get("ok"))
        except Exception as e:
            print(f"[ERR] Telegram: {e}"); ok = False
    return ok


def fetch_external_factors(symbol="XAUUSD"):
    """Fetch External Factors v1.2 do iMac via LAN HTTP.
    Returns dict com calendar_risk parseado + fallback graceful.
    Não bloqueia o monitor se iMac offline."""
    url = f"{EXTERNAL_FACTORS_BASE_URL}/{symbol}.json"
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=EXTERNAL_FACTORS_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        cal = data.get("calendar_risk") or {}
        return {
            "ok": True,
            "calendar_active": bool(cal.get("active")),
            "calendar_risk_level": cal.get("risk_level", "none"),
            "calendar_events": cal.get("events", []) or [],
            "calendar_score": cal.get("calendar_score", 0),
            "external_bias": data.get("external_bias", "neutral"),
            "risk_level_overall": data.get("risk_level", "medium"),
            "raw_external_values": data.get("raw_external_values") or {},
        }
    except Exception as e:
        print(f"[WARN] external_factors fetch failed: {e}")
        return {
            "ok": False,
            "calendar_active": False,
            "calendar_risk_level": "none",
            "calendar_events": [],
            "calendar_score": 0,
            "external_bias": "neutral",
            "risk_level_overall": "unknown",
            "raw_external_values": {},
        }


def format_calendar_warning(ext):
    """Retorna linha de warning Telegram se calendar_active, senão string vazia."""
    if not ext.get("calendar_active"):
        return ""
    events = ext.get("calendar_events", [])
    level = ext.get("calendar_risk_level", "unknown")
    if not events:
        return f"\n⚠️ CALENDAR ALERT: risk={level}"
    # Pega primeiro evento (mais próximo geralmente)
    ev = events[0] if events else {}
    name = ev.get("name") or ev.get("event") or "evento"
    when = ev.get("time_until") or ev.get("when") or ev.get("scheduled_at") or ""
    when_str = f" em {when}" if when else ""
    return f"\n⚠️ CALENDAR ALERT: {name}{when_str} (risk={level})"


# === WebSearch macro check sob demanda (complementa iMac calendar) ===
# Invocado APENAS quando estratégia match. Custo: ~$0.03/match × ~25 matches/ano = ~$1/ano.
# Latência: 10-15s por match. Cached em memória pelo bar_iso (1 search por bar mesmo
# com múltiplas estratégias matching).

_macro_check_cache = {}  # bar_iso -> string
WEBSEARCH_TIMEOUT_S = 90


def get_macro_events_check(bar_iso):
    """Invoca Claude headless com WebSearch pra checar eventos US high-impact próximos 24h.

    Retorna string formatada (ex: "FOMC Decision em 4h") ou empty se NONE/erro.
    Cacheado por bar_iso (in-memory na execução atual).
    """
    if bar_iso in _macro_check_cache:
        return _macro_check_cache[bar_iso]

    prompt = (
        "Use WebSearch para responder: há algum dos seguintes eventos US high-impact "
        "agendado nas próximas 24 horas a partir de agora? "
        "Lista: FOMC Decision, FOMC Minutes, US CPI, US PCE, US GDP, US NFP "
        "(Non-Farm Payrolls), ECB Decision, ISM Manufacturing PMI, ISM Services PMI, US PPI. "
        "Responda em UMA linha apenas, NO formato exato:\n"
        "  NONE\n"
        "ou:\n"
        "  <nome do evento> em <X>h\n"
        "Sem texto adicional, sem explicação. Apenas a linha de resposta."
    )

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--allowedTools", "WebSearch"],
            text=True, capture_output=True, timeout=WEBSEARCH_TIMEOUT_S
        )
        output = (result.stdout or "").strip()
        # Parse: pega primeira linha não vazia
        first_line = next((l for l in output.split("\n") if l.strip()), "")
        if "NONE" in first_line.upper() or not first_line:
            res = ""
        else:
            res = first_line[:120]
        _macro_check_cache[bar_iso] = res
        return res
    except subprocess.TimeoutExpired:
        print(f"[WARN] WebSearch macro check timeout ({WEBSEARCH_TIMEOUT_S}s)")
        _macro_check_cache[bar_iso] = ""
        return ""
    except Exception as e:
        print(f"[WARN] WebSearch macro check failed: {e}")
        _macro_check_cache[bar_iso] = ""
        return ""


class MCPClient:
    def __init__(self):
        self.proc = None; self._req_id = 0

    def start(self):
        self.proc = subprocess.Popen(
            [NODE_BIN, str(MCP_SERVER_PATH)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1
        )
        resp = self._call_raw("initialize", {
            "protocolVersion":"2024-11-05","capabilities":{},
            "clientInfo":{"name":"xau-4h-monitor","version":"1.0.0"},
        })
        if "error" in resp: raise RuntimeError(f"MCP init: {resp['error']}")
        self._notify("notifications/initialized", {})

    def stop(self):
        if not self.proc: return
        try: self.proc.stdin.close()
        except: pass
        try: self.proc.terminate(); self.proc.wait(timeout=5)
        except: self.proc.kill()

    def _next_id(self): self._req_id += 1; return self._req_id

    def _notify(self, method, params):
        self.proc.stdin.write(json.dumps({"jsonrpc":"2.0","method":method,"params":params})+"\n")
        self.proc.stdin.flush()

    def _call_raw(self, method, params, timeout=PER_CALL_TIMEOUT_S):
        rid = self._next_id()
        self.proc.stdin.write(json.dumps({"jsonrpc":"2.0","id":rid,"method":method,"params":params})+"\n")
        self.proc.stdin.flush()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            line = self.proc.stdout.readline()
            if not line: raise RuntimeError("MCP stdout closed")
            try: resp = json.loads(line)
            except: continue
            if resp.get("id") == rid: return resp
        raise TimeoutError(f"MCP {method} timeout")

    def call(self, name, arguments=None, timeout=PER_CALL_TIMEOUT_S):
        resp = self._call_raw("tools/call", {"name":name,"arguments":arguments or {}}, timeout=timeout)
        if "error" in resp: return {"_error":resp["error"]}
        result = resp.get("result", {})
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            try: return json.loads(content[0]["text"])
            except: return {"_raw":content[0]["text"]}
        return result


# === State reader ===

def _parse_float(v):
    if v is None: return None
    try: return float(str(v).replace("−","-"))
    except: return None


def read_state(mcp):
    """Lê todo state necessário pra avaliar as estratégias.
    Custo: ~10 MCP calls + 2 trocas de TF + 1 HTTP fetch external_factors.
    Returns dict completo."""
    state = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME_4H,
    }

    # 0. External Factors (iMac HTTP, fallback graceful)
    state["external"] = fetch_external_factors("XAUUSD")

    # 1. Garantir chart no XAU 4H
    mcp.call("chart_set_symbol", {"symbol": SYMBOL})
    mcp.call("chart_set_timeframe", {"timeframe": TIMEFRAME_4H})
    time.sleep(2)

    # 2. Quote (preço atual)
    q = mcp.call("quote_get")
    state["close"] = q.get("last") if isinstance(q, dict) else None

    # 3. OHLCV (200 bars pra ATR + dist 14d)
    o = mcp.call("data_get_ohlcv", {"count": 200})
    bars = o.get("bars", []) if isinstance(o, dict) else []
    state["last_bar_ts"] = bars[-1].get("time") if bars else None
    state["last_bar_iso"] = None
    if state["last_bar_ts"]:
        state["last_bar_iso"] = datetime.fromtimestamp(state["last_bar_ts"], tz=timezone.utc).isoformat()

    # ATR(14) atual + ATR média(30) dos ATRs históricos
    atr_ratio = atr14_now = atr_ma30 = None
    if len(bars) >= 45:
        closed = bars[:-1]  # excluir bar atual não fechado
        trs = []
        for i in range(1, len(closed)):
            h = closed[i].get("high"); l = closed[i].get("low"); pc = closed[i-1].get("close")
            if None in (h, l, pc): continue
            trs.append(max(h-l, abs(h-pc), abs(l-pc)))
        if len(trs) >= 14:
            atr14_now = mean(trs[-14:])
            atr_series = [mean(trs[i-14:i]) for i in range(14, len(trs)+1)]
            if len(atr_series) >= 30:
                atr_ma30 = mean(atr_series[-30:])
                atr_ratio = atr14_now / atr_ma30 if atr_ma30 > 0 else None
    state["atr14"] = atr14_now
    state["atr_ma30"] = atr_ma30
    state["atr_ratio"] = atr_ratio

    # Dist 14d high: 14 dias ≈ 84 candles 4H (XAU 6 candles/dia 24h)
    dist_14d_pct = None
    if bars and state["close"]:
        last_84 = bars[-84:] if len(bars) >= 84 else bars
        h14 = max((b.get("high") or 0) for b in last_84)
        if h14 > 0:
            dist_14d_pct = (state["close"] - h14) / h14 * 100
    state["dist_14d_pct"] = dist_14d_pct

    # 3b. pine_boxes (Custom OB v11 DEMAND zones)
    pb = mcp.call("data_get_pine_boxes")
    box_studies = pb.get("studies", []) if isinstance(pb, dict) else []
    in_ob_zone = False
    best_demand = None  # {high, low}
    for s in box_studies:
        if "Custom OB" not in s.get("name", ""): continue
        for box in (s.get("all_boxes") or []):
            hi = box.get("high"); lo = box.get("low"); txt = box.get("text")
            if txt != "DEMAND" or hi is None or lo is None: continue
            # close DENTRO da DEMAND box: low <= close <= high
            if state["close"] is not None and lo <= state["close"] <= hi:
                in_ob_zone = True
                # Tracking da DEMAND mais "envolvente" (maior altura) pra mensagem
                if best_demand is None or (hi - lo) > (best_demand["high"] - best_demand["low"]):
                    best_demand = {"high": hi, "low": lo}
        break
    state["in_ob_zone"] = in_ob_zone
    state["best_demand"] = best_demand

    # 4. study_values (NAS_DIST)
    sv = mcp.call("data_get_study_values")
    studies = sv.get("studies", []) if isinstance(sv, dict) else []
    nas_dist = None
    for s in studies:
        if "NAS" in s.get("name", ""):
            v = (s.get("values") or {}).get("NAS_DISTANCE_FROM_EMA_ATR")
            nas_dist = _parse_float(v)
            if nas_dist is not None: break
    state["nas_dist"] = nas_dist

    # 5. pine_labels (NAS LONG, LuxAlgo BOS/CHoCH/Strong Low/EQL)
    pl = mcp.call("data_get_pine_labels")
    label_studies = pl.get("studies", []) if isinstance(pl, dict) else []

    nas_long_recent = False
    for s in label_studies:
        if "NAS" not in s.get("name","").upper(): continue
        labels = s.get("labels") or []
        xs = [l.get("x") for l in labels if l.get("x") is not None]
        if not xs: break
        max_x = max(xs)
        for l in labels:
            lx = l.get("x"); txt = (l.get("text") or "").upper()
            if lx is None: continue
            if txt == "LONG" and 0 <= max_x - lx <= NAS_LONG_MAX_DELTA:
                nas_long_recent = True; break
        break
    state["nas_long_recent"] = nas_long_recent

    lux_t1 = False; lux_t3 = False
    strong_low_recent = False; eql_sweep_recent = False
    last_low = (bars[-1].get("low") if bars else None)

    for s in label_studies:
        if "LUXALGO" not in s.get("name","").upper(): continue
        labels = s.get("labels") or []
        xs = [l.get("x") for l in labels if l.get("x") is not None]
        if not xs: break
        max_x = max(xs)
        for l in labels:
            lx = l.get("x"); txt = l.get("text",""); tc = l.get("textColor"); price = l.get("price")
            if lx is None: continue
            delta = max_x - lx
            if delta < 0: continue
            direction = "BULL" if tc == LUX_BULL else "BEAR" if tc == LUX_BEAR else "?"
            if txt in ("BOS","CHoCH"):
                if direction == "BEAR" and delta <= DISCR_T1_MAX_DELTA: lux_t1 = True
                if direction == "BULL" and txt == "BOS" and delta <= DISCR_T3_MAX_DELTA: lux_t3 = True
            if txt == "Strong Low" and delta <= SWEEP_STRONG_LOW_MAX_DELTA:
                strong_low_recent = True
            if txt == "EQL" and delta <= SWEEP_EQL_MAX_DELTA and price is not None and state["close"] is not None and last_low is not None:
                # Sweep: low atual <= EQL.price (penetrou) e close > EQL.price (sustentou)
                if last_low <= price and state["close"] > price:
                    eql_sweep_recent = True
        break
    state["lux_t1"] = lux_t1
    state["lux_t3"] = lux_t3
    state["strong_low_recent"] = strong_low_recent
    state["eql_sweep_recent"] = eql_sweep_recent

    # 5b. Drift desde último bar fechado (LOGGING PASSIVO — não bloqueia)
    # Compara close atual (bar não fechado / quote) vs close do último bar 4H fechado.
    # Validar forward em 30-60d se "late entry" correlaciona com win (Oracle data sugere SIM).
    drift_atr = None
    drift_pct = None
    atr_for_drift = state.get("atr14")
    if len(bars) >= 2 and atr_for_drift and state.get("close"):
        last_closed_close = bars[-2].get("close")
        if last_closed_close:
            drift_pts = state["close"] - last_closed_close
            drift_atr = drift_pts / atr_for_drift if atr_for_drift > 0 else None
            drift_pct = drift_pts / last_closed_close * 100 if last_closed_close > 0 else None
    state["drift_since_last_close_atr"] = drift_atr
    state["drift_since_last_close_pct"] = drift_pct

    # 6. RSI 1D (troca TF momentâneo)
    rsi_1d = None
    try:
        mcp.call("chart_set_timeframe", {"timeframe": TIMEFRAME_D})
        time.sleep(2)
        sv_d = mcp.call("data_get_study_values")
        studies_d = sv_d.get("studies", []) if isinstance(sv_d, dict) else []
        for s in studies_d:
            name = s.get("name","").lower()
            if "rsi" in name or "relative strength" in name:
                vals = s.get("values") or {}
                for k, v in vals.items():
                    if "RSI" in k.upper() or "rsi" in k:
                        rsi_1d = _parse_float(v)
                        if rsi_1d is not None: break
                if rsi_1d is not None: break
    finally:
        # Restaurar TF 4H sempre
        mcp.call("chart_set_timeframe", {"timeframe": TIMEFRAME_4H})
        time.sleep(2)
    state["rsi_1d"] = rsi_1d

    return state


# === Hard blocks (pre-eval gates) ===

def check_mcp_reliable(state):
    """MCP_UNRELIABLE — bloqueia avaliação se leitura via MCP veio inconsistente.

    Retorna (ok: bool, reasons: list). Se ok=False, NÃO avaliar estratégias e NÃO dispatch Telegram.
    Apenas grava entry em eval_log com hard_block_triggered='MCP_UNRELIABLE'.

    Critérios FAIL (qualquer um suficiente):
      - close indef ou <=0
      - atr14 indef ou <=0
      - last_bar_ts indef (sem OHLCV)
      - nas_dist E dist_14d_pct ambos None (dois indicadores macro críticos indef)
      - atr_ratio indef quando atr14 tem valor (cálculo bugado, dataset insuficiente é OK)
    """
    reasons = []
    if not state.get("close") or state["close"] <= 0:
        reasons.append("close inválido")
    if not state.get("atr14") or state["atr14"] <= 0:
        reasons.append("atr14 inválido")
    if not state.get("last_bar_ts"):
        reasons.append("last_bar_ts ausente")
    if state.get("nas_dist") is None and state.get("dist_14d_pct") is None:
        reasons.append("nas_dist E dist_14d_pct ambos None")
    if state.get("atr14") and state.get("atr_ratio") is None and len(state.get("_bars_count", "")) > 50:
        # só sinaliza se temos dados suficientes (45+ bars) mas atr_ratio bugou
        reasons.append("atr_ratio bugado mesmo com atr14 ok")
    return (len(reasons) == 0, reasons)


# === Strategy evaluators ===

def eval_capitulation(state):
    """3 condições: NAS LONG ≤5, RSI 1D < 50, ATR ratio > 1.3."""
    reasons = []
    matched = True
    if not state.get("nas_long_recent"):
        matched = False; reasons.append("NAS LONG não recente (≤5)")
    rsi = state.get("rsi_1d")
    if rsi is None or rsi >= CAPIT_RSI1D_MAX:
        matched = False; reasons.append(f"RSI 1D = {rsi} (>= {CAPIT_RSI1D_MAX} ou indef)")
    atr_r = state.get("atr_ratio")
    if atr_r is None or atr_r <= CAPIT_ATR_RATIO_THRESHOLD:
        matched = False; reasons.append(f"ATR ratio = {atr_r} (<= {CAPIT_ATR_RATIO_THRESHOLD} ou indef)")
    return matched, reasons


def eval_discretionary_base(state):
    """NAS LONG ≤5 + NAS_DIST ≤ -1 + dist14d ≤ -5% + (T1 OU T3)."""
    reasons = []
    matched = True
    if not state.get("nas_long_recent"):
        matched = False; reasons.append("NAS LONG não recente")
    nd = state.get("nas_dist")
    if nd is None or nd > DISCR_NAS_DIST_MAX:
        matched = False; reasons.append(f"NAS_DIST = {nd} (> {DISCR_NAS_DIST_MAX})")
    d14 = state.get("dist_14d_pct")
    if d14 is None or d14 > DISCR_DIST14D_MAX:
        matched = False
        reasons.append(f"dist_14d = {d14:.2f}% (> {DISCR_DIST14D_MAX}%)" if d14 is not None else "dist_14d indef")
    if not (state.get("lux_t1") or state.get("lux_t3")):
        matched = False; reasons.append("LuxAlgo T1/T3 ausente")
    return matched, reasons


def eval_discretionary_sweep(state):
    """BASE + (Strong Low ≤10 OU EQL sweep recente)."""
    base_m, base_r = eval_discretionary_base(state)
    if not base_m:
        return False, ["BASE não match"] + base_r
    if not (state.get("strong_low_recent") or state.get("eql_sweep_recent")):
        return False, ["Strong Low / EQL sweep ausente"]
    return True, []


def eval_demand_breakout(state):
    """XAU_4H_DEMAND_BREAKOUT_LONG (V0 + V3').

    Condições:
      - V0a: IN_OB_ZONE (close dentro de DEMAND box do Custom OB v11)
      - V0b: NAS:1to2 → NAS_DIST entre +1.0 e +2.0 (preço esticado pra CIMA)
      - V3': dist_14d entre -1.0% e 0% (PRATICAMENTE no topo recente)

    Stats: n=80/3a, 83.8% win, +2.43R, 4/5 janelas PASS gate 70%.
    """
    reasons = []
    matched = True
    if not state.get("in_ob_zone"):
        matched = False; reasons.append("close fora de DEMAND box (Custom OB)")
    nd = state.get("nas_dist")
    if nd is None or not (1.0 <= nd <= 2.0):
        matched = False
        reasons.append(f"NAS_DIST = {nd} (fora 1.0..2.0)")
    d14 = state.get("dist_14d_pct")
    if d14 is None or not (-1.0 <= d14 <= 0.0):
        matched = False
        reasons.append(f"dist_14d = {d14:.2f}% (fora -1.0..0)" if d14 is not None else "dist_14d indef")
    return matched, reasons


# === Telegram formatters ===

def fmt_capitulation(state):
    cal_warn = format_calendar_warning(state.get("external") or {})
    return ("#SETUP_XAU_4H ✅ ALTA CONVICÇÃO\n"
            "CAPITULAÇÃO ATIVA (83.7% win histórico, ~25/ano)\n"
            f"Preço: ${state['close']:.2f} · RSI1D: {state['rsi_1d']:.1f} · ATR ratio: {state['atr_ratio']:.2f}\n"
            "Trigger: NAS LONG + volatilidade explodindo"
            f"{cal_warn}")


def fmt_discretionary_sweep(state):
    sweep_kind = "Strong Low" if state.get("strong_low_recent") else "EQL sweep"
    cal_warn = format_calendar_warning(state.get("external") or {})
    return ("#SETUP_XAU_4H 🚨 URGENTE\n"
            "SWEEP HIGH-CONVICTION (100% win histórico, raríssimo n=6 em 8a)\n"
            f"Preço: ${state['close']:.2f} · NAS_DIST: {state['nas_dist']:.2f} · D14: {state['dist_14d_pct']:.1f}%\n"
            f"Trigger: {sweep_kind} recente"
            f"{cal_warn}")


def fmt_discretionary_base(state):
    trigger = "T1 (BOS/CHoCH bear ≤2)" if state.get("lux_t1") else "T3 (BOS bull ≤5)"
    cal_warn = format_calendar_warning(state.get("external") or {})
    return ("#SETUP_XAU_4H ⚠️ NORMAL\n"
            "REGIÃO POTENCIAL REVERSÃO (sinalizador, 60% win histórico, ~22/ano)\n"
            f"Preço: ${state['close']:.2f} · NAS_DIST: {state['nas_dist']:.2f} · D14: {state['dist_14d_pct']:.1f}%\n"
            f"Trigger: {trigger}\n"
            "→ Desenhar OB macro, avaliar entrada"
            f"{cal_warn}")


def fmt_demand_breakout(state):
    d = state.get("best_demand") or {}
    d_str = f"DEMAND ${d.get('low',0):.0f}-${d.get('high',0):.0f}" if d else "DEMAND ativa"
    cal_warn = format_calendar_warning(state.get("external") or {})
    return ("#SETUP_XAU_4H ✅ ALTA CONVICÇÃO\n"
            "DEMAND BREAKOUT (83.8% win histórico, ~25/ano)\n"
            f"Preço: ${state['close']:.2f} · NAS_DIST: {state['nas_dist']:.2f} · D14: {state['dist_14d_pct']:.2f}%\n"
            f"Trigger: breakout ativo em {d_str}"
            f"{cal_warn}")


# === Logger / dedup ===

def append_jsonl(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def already_evaluated_for_bar(bar_iso, strategy_name):
    """Check if (bar_iso, strategy_name) already in EVAL_LOG (scans last 300 lines)."""
    if not EVAL_LOG_JSONL.exists(): return False
    try:
        with EVAL_LOG_JSONL.open() as f:
            lines = f.readlines()[-300:]
        for line in lines:
            try:
                j = json.loads(line)
                if j.get("bar_iso") == bar_iso and j.get("strategy") == strategy_name and j.get("matched") is not None:
                    return True
            except: pass
    except: pass
    return False


# === Main eval+dispatch ===

def evaluate_and_dispatch(mcp, trigger_source, dispatch_telegram=True):
    """Lê state via MCP, avalia 3 estratégias, dispara Telegram + log se match.
    Retorna lista de strategies que matched."""
    try:
        state = read_state(mcp)
    except Exception as e:
        print(f"[ERR] read_state: {e}")
        return []

    ext = state.get("external") or {}
    drift_atr = state.get("drift_since_last_close_atr")
    drift_str = f"{drift_atr:+.2f}" if drift_atr is not None else "—"
    print(f"[STATE] close={state.get('close')} nas_long={state.get('nas_long_recent')} "
          f"nas_dist={state.get('nas_dist')} dist14d={state.get('dist_14d_pct')} "
          f"rsi1d={state.get('rsi_1d')} atr_ratio={state.get('atr_ratio')} "
          f"in_ob={state.get('in_ob_zone')} "
          f"t1={state.get('lux_t1')} t3={state.get('lux_t3')} "
          f"strong_low={state.get('strong_low_recent')} eql_sweep={state.get('eql_sweep_recent')} "
          f"cal_active={ext.get('calendar_active')} cal_risk={ext.get('calendar_risk_level')} "
          f"drift_atr={drift_str}")

    bar_iso = state.get("last_bar_iso") or state["ts"]

    # Hard block check: MCP_UNRELIABLE — antes de qualquer eval
    mcp_ok, mcp_reasons = check_mcp_reliable(state)
    if not mcp_ok:
        print(f"[HARD_BLOCK] MCP_UNRELIABLE: {', '.join(mcp_reasons)} — skip avaliações")
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "bar_iso": bar_iso,
            "strategy": "all",
            "matched": False,
            "trigger_source": trigger_source,
            "hard_block_triggered": "MCP_UNRELIABLE",
            "hard_block_reasons": mcp_reasons,
            "state": state,
        }
        append_jsonl(EVAL_LOG_JSONL, entry)
        return []

    strategies = [
        ("demand_breakout", eval_demand_breakout, fmt_demand_breakout),
        ("capitulation", eval_capitulation, fmt_capitulation),
        ("discr_sweep", eval_discretionary_sweep, fmt_discretionary_sweep),
        ("discr_base", eval_discretionary_base, fmt_discretionary_base),
    ]

    matched_list = []
    for name, eval_fn, fmt_fn in strategies:
        matched, reasons = eval_fn(state)
        if already_evaluated_for_bar(bar_iso, name):
            print(f"  [DEDUP] {name} já avaliada pra bar {bar_iso}")
            continue
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "bar_iso": bar_iso,
            "strategy": name,
            "matched": matched,
            "trigger_source": trigger_source,
            "state": state,
            "reasons": reasons if not matched else [],
        }
        append_jsonl(EVAL_LOG_JSONL, entry)
        if matched:
            matched_list.append(name)
            msg = fmt_fn(state)
            # WebSearch macro check sob demanda (cached por bar_iso)
            macro_event = get_macro_events_check(bar_iso)
            if macro_event:
                msg = msg + f"\n⚠️ MACRO (24h): {macro_event}"
            print(f"\n=== MATCH {name} ===\n{msg}\n")
            # Default-deny: only strategies in TELEGRAM_DISPATCH_ALLOWLIST may dispatch; keep computing/logging.
            if dispatch_telegram and name in TELEGRAM_DISPATCH_ALLOWLIST:
                send_telegram(msg)
            else:
                print(f"  [NO_TELEGRAM] {name}: matched — Telegram suppressed (default-deny; not in TELEGRAM_DISPATCH_ALLOWLIST).")
            entry["macro_event_check"] = macro_event
            append_jsonl(STRATEGY_SIGNALS_JSONL, entry)
        else:
            print(f"  [no match] {name}: {', '.join(reasons)}")

    return matched_list


# === Daemon (event-driven) ===

def daemon_mode(mcp):
    print(f"[DAEMON] Tail {SIGNALS_JSONL}")
    if not SIGNALS_JSONL.exists():
        print(f"[ERR] {SIGNALS_JSONL} não existe"); sys.exit(1)
    with SIGNALS_JSONL.open() as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(2); continue
            try: ev = json.loads(line)
            except: continue
            base_sym = ev.get("base_symbol","")
            tf = str(ev.get("timeframe",""))
            sig = ev.get("signal_type","")
            ind = ev.get("indicator_name","")
            if base_sym == "XAUUSD" and tf == "240" and "NAS" in ind and sig in ("NAS_LONG","NAS_BOTTOM"):
                print(f"\n[TRIGGER] NAS LONG XAU 4H @ {ev.get('ts_received')}")
                try:
                    fd, wait = acquire_chart_lock()
                except TimeoutError as e:
                    print(f"[ERR] lock: {e}"); continue
                try:
                    evaluate_and_dispatch(mcp, trigger_source="daemon_nas_long")
                finally:
                    release_chart_lock(fd)


# === Main ===

def main():
    ap = argparse.ArgumentParser(description="XAU 4H reversal strategies monitor")
    ap.add_argument("--mode", choices=["once","cron","daemon"], default="once",
                    help="once=eval debug (no telegram), cron=eval+telegram, daemon=tail+trigger")
    args = ap.parse_args()

    mcp = MCPClient()
    print(f"[INIT] Starting MCP server...")
    mcp.start()
    print(f"[INIT] MCP ready (mode={args.mode})")

    try:
        if args.mode == "once":
            try: fd, wait = acquire_chart_lock()
            except TimeoutError as e:
                print(f"[ERR] lock: {e}"); return 1
            try:
                evaluate_and_dispatch(mcp, trigger_source="once", dispatch_telegram=False)
            finally:
                release_chart_lock(fd)
        elif args.mode == "cron":
            try: fd, wait = acquire_chart_lock()
            except TimeoutError as e:
                print(f"[ERR] lock: {e}"); return 1
            try:
                evaluate_and_dispatch(mcp, trigger_source="cron", dispatch_telegram=True)
            finally:
                release_chart_lock(fd)
        elif args.mode == "daemon":
            daemon_mode(mcp)
    finally:
        mcp.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
