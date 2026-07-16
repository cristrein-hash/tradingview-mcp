#!/usr/bin/env python3
"""DAEMON de monitoração realtime XAU — FASE P1 (Camada 1-A: níveis estáticos).
Lê preço via MCP (quote_get) a cada ~5s, compara `last` vs NÍVEIS ARMADOS (logs/levels.json) e dispara
alerta Telegram no cruzamento (histerese/one-shot/cooldown). Watchdog: se o CDP morrer -> "🔴 MONITOR CEGO"
(nunca silêncio). Determinístico, 0 tokens Claude. Alerta-only, ZERO auto-trade.

Coexistência (quote_get lê o preço do GRÁFICO ATIVO): dupla defesa —
  (a) pausa: honra logs/monitor.pause E /tmp/claude_recheck.paused (todo chart-work pausa o daemon);
  (b) guarda: cada ciclo valida símbolo==XAUUSD + replay OFF; senão CHART_HIJACKED (não dispara).
Kill-switch: touch logs/monitor.pause · launchctl unload. NUNCA loga o token.
CLI: --test-telegram | --selftest-mcp | (default) corre o daemon.
"""
import os, sys, json, time, datetime as dt
from pathlib import Path

BASE = Path(__file__).resolve().parent          # alert-bridge/
REPO = BASE.parent
LOGS = BASE / "logs"; LOGS.mkdir(exist_ok=True)
sys.path.insert(0, str(BASE))
from auto_d2r_daily import send_telegram          # reusa envio (token do .env, nunca exposto)
from draw_xau_4h_trades import MCPClient           # reusa cliente MCP (spawn node stdio)

EXPECTED_SYMBOL = "XAUUSD"           # substring aceite (PEPPERSTONE:XAUUSD)
FLOOR_S = 5                          # cadência-piso (decisão Cris)
CALL_TIMEOUT = 10                    # timeout curto por call (não bloquear o laço)
MINTICK = 0.01
RESPAWN_MAX = 3                      # falhas MCP consecutivas antes de MONITOR CEGO
STALE_S = 120                        # preço sem avançar > isto (+ cdp) = suspeita
LEVELS_F = LOGS / "levels.json"
STATE_F = LOGS / "realtime_monitor_state.json"
ALERTS_F = LOGS / "realtime_monitor_alerts.jsonl"
PIDFILE = LOGS / "realtime_monitor.pid"
PAUSE_LOCAL = LOGS / "monitor.pause"
PAUSE_GLOBAL = Path("/tmp/claude_recheck.paused")


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def log(msg):
    print(f"{now_utc().strftime('%Y-%m-%dT%H:%M:%SZ')} {msg}", flush=True)


def audit(rec):
    rec["ts"] = now_utc().isoformat()
    try:
        with open(ALERTS_F, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def atomic_write(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    os.replace(tmp, path)


def load_env_presence():
    """Valida presença das chaves Telegram sem imprimir valores."""
    env = {}
    for line in (BASE / ".env").read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k = line.split("=", 1)[0].strip()
            env[k] = True
    return ("TELEGRAM_BOT_TOKEN" in env) and ("TELEGRAM_CHAT_ID" in env)


# ---------- comparador de nível (puro, unit-testável offline) ----------
def crossed(prev_last, last, price, side, hyst):
    if prev_last is None:
        return False
    if side == "cross_below":
        return prev_last >= price + hyst and last <= price - hyst
    if side == "cross_above":
        return prev_last <= price - hyst and last >= price + hyst
    return False


# ---------- levels.json (hot-reload por mtime) ----------
class Levels:
    def __init__(self):
        self._mtime = 0
        self.levels = []

    def maybe_reload(self):
        try:
            m = LEVELS_F.stat().st_mtime
        except FileNotFoundError:
            self.levels = []; self._mtime = 0; return
        if m != self._mtime:
            try:
                d = json.loads(LEVELS_F.read_text())
                self.levels = [l for l in d.get("levels", []) if EXPECTED_SYMBOL in str(l.get("symbol", "")).upper()]
                self._mtime = m
                log(f"[levels] recarregado: {sum(1 for l in self.levels if l.get('state')=='armed')} armado(s)")
            except Exception as e:
                log(f"[levels] parse falhou ({type(e).__name__}) — mantém anterior")

    def mark_fired(self, level_id):
        try:
            d = json.loads(LEVELS_F.read_text())
            for l in d.get("levels", []):
                if l.get("id") == level_id:
                    l["state"] = "fired"; l["fired_ts"] = int(time.time())
            atomic_write(LEVELS_F, d)
            self._mtime = LEVELS_F.stat().st_mtime  # evita reload imediato
        except Exception as e:
            log(f"[levels] mark_fired falhou ({type(e).__name__})")


# ---------- MCP resiliente ----------
class SafeMCP:
    def __init__(self):
        self.c = None; self.fails = 0

    def start(self):
        self.c = MCPClient(); self.c.start()

    def stop(self):
        try:
            if self.c: self.c.stop()
        except Exception:
            pass
        self.c = None

    def call(self, name, args=None):
        """Devolve dict resultado, ou None se falhar após respawn."""
        for attempt in range(2):
            try:
                if self.c is None:
                    self.start()
                r = self.c.call_tool(name, args or {}, timeout=CALL_TIMEOUT)
                if isinstance(r, dict) and r.get("_error"):
                    raise RuntimeError(r["_error"])
                self.fails = 0
                return r
            except Exception as e:
                log(f"[mcp] {name} falhou ({type(e).__name__}) — respawn {attempt+1}")
                self.stop(); time.sleep(1.5 * (attempt + 1))
        self.fails += 1
        return None


# ---------- Telegram alerta de nível ----------
def send_level_alert(level, last, repeat=3):
    side_txt = "abaixo de" if level["side"] == "cross_below" else "acima de"
    arrow = "🔻" if level["side"] == "cross_below" else "🔺"
    text = (f"🔔🔔 <b>NÍVEL ARMADO CRUZADO — Camada 1</b> {arrow}\n\n"
            f"<b>XAUUSD</b> cruzou <b>{side_txt} {level['price']}</b>\n"
            f"Preço agora: <b>{last}</b>\n"
            + (f"Nota: {level.get('note')}\n" if level.get("note") else "")
            + "\n▶️ Avalia e executa TU (alerta-only, não é ordem).")
    oks = []
    for i in range(repeat):
        r = send_telegram(text)
        oks.append(bool(r.get("ok")))
        if i < repeat - 1:
            time.sleep(1.2)
    return all(oks)


# ---------- watchdog state ----------
def load_state():
    try:
        return json.loads(STATE_F.read_text())
    except Exception:
        return {"health": "INIT", "last_price_time": None, "last_price_wall": 0}


def save_state(s):
    atomic_write(STATE_F, s)


MIN_HEALTH_TG_S = 180   # backstop anti-flap: no máx 1 Telegram de saúde por 3 min


def transition(state, new_health, reason, token_ok=True):
    """Atualiza estado; Telegram só na TRANSIÇÃO, com cooldown anti-flap."""
    old = state.get("health")
    if old == new_health:
        return
    state["health"] = new_health
    log(f"[watchdog] {old} -> {new_health} ({reason})")
    audit({"event": "state", "from": old, "to": new_health, "reason": reason})
    if not token_ok:
        return
    msg = None
    if new_health == "BLIND":
        msg = "🔴🔴 <b>MONITOR CEGO</b> — perdeu o CDP/preço. Níveis NÃO vigiados. Verifica TradingView/Mac."
    elif new_health == "DEGRADED":
        msg = f"⚠️ <b>Monitor degradado</b>: {reason}."
    elif new_health == "CHART_HIJACKED":
        msg = f"⚠️ <b>Gráfico fora de XAUUSD/replay</b> — pausa defensiva ({reason})."
    elif new_health == "OK" and old in ("BLIND", "DEGRADED", "CHART_HIJACKED"):
        msg = "🟢 <b>Monitor recuperado</b>."
    if not msg:
        return
    # backstop: nunca mais de 1 Telegram de saúde por MIN_HEALTH_TG_S (anti-spam)
    if time.time() - state.get("last_health_tg", 0) < MIN_HEALTH_TG_S:
        return
    state["last_health_tg"] = time.time()
    for _ in range(3 if new_health == "BLIND" else 1):
        send_telegram(msg)
        time.sleep(1.2)


def paused():
    return PAUSE_LOCAL.exists() or PAUSE_GLOBAL.exists()


# ---------- CLI selftests ----------
def cli_test_telegram():
    if not load_env_presence():
        print("FALTA TELEGRAM_* no .env"); return
    r = send_telegram("🔔 <b>TESTE — realtime_monitor</b>\nPonte de alerta de nível operacional. NÃO EXECUTAR.")
    print("test-telegram ok:", r.get("ok"))


def cli_selftest_mcp():
    m = SafeMCP()
    h = m.call("tv_health_check")
    q = m.call("quote_get")
    print("tv_health_check:", {k: h.get(k) for k in ("success", "cdp_connected", "chart_symbol", "chart_resolution")} if h else None)
    print("quote_get last:", (q or {}).get("last"), "| symbol lbl:", (q or {}).get("symbol"))
    m.stop()


# ---------- loop principal ----------
def main_loop():
    if not load_env_presence():
        log("FATAL: .env sem TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID"); sys.exit(1)
    # instância única
    if PIDFILE.exists():
        try:
            old = int(PIDFILE.read_text().strip()); os.kill(old, 0)
            log(f"FATAL: já corre (pid {old})"); sys.exit(1)
        except (ProcessLookupError, ValueError):
            pass
    PIDFILE.write_text(str(os.getpid()))

    m = SafeMCP()
    lv = Levels()
    state = load_state()
    prev_last = None
    log(f"[bridge] realtime_monitor ativo | símbolo={EXPECTED_SYMBOL} | piso={FLOOR_S}s")
    try:
        while True:
            t0 = time.time()
            if paused():
                if state.get("health") != "PAUSED":
                    transition(state, "PAUSED", "flag de pausa"); save_state(state)
                    prev_last = None  # invalida sequência
                log("[paused] log-only")
                time.sleep(FLOOR_S); continue

            lv.maybe_reload()
            h = m.call("tv_health_check")
            if h is None or not h.get("cdp_connected", False):
                if m.fails >= RESPAWN_MAX:
                    transition(state, "BLIND", "CDP morto após respawns"); save_state(state)
                prev_last = None
                time.sleep(FLOOR_S); continue

            # guarda de símbolo/replay
            sym = str(h.get("chart_symbol", "")).upper()
            rp = m.call("replay_status") or {}
            if EXPECTED_SYMBOL not in sym or rp.get("is_replay_started"):
                transition(state, "CHART_HIJACKED", f"symbol={sym} replay={rp.get('is_replay_started')}"); save_state(state)
                prev_last = None
                time.sleep(FLOOR_S); continue

            q = m.call("quote_get")
            last = (q or {}).get("last") or (q or {}).get("close")
            if last is None:
                time.sleep(FLOOR_S); continue
            last = float(last)

            # saúde: cdp ok + símbolo ok + preço válido = OK.
            # (REMOVIDA a staleness por bar-time: quote_get.time = open da barra 15M, estável ~15min ->
            #  gerava DEGRADED falso a cada ciclo = flap/spam. cdp_connected + quote válido bastam.)
            if state.get("health") not in ("OK",):
                transition(state, "OK", "normalizado"); save_state(state)

            # comparação de níveis
            for level in lv.levels:
                if level.get("state") != "armed":
                    continue
                hyst = level.get("hysteresis_ticks", 10) * MINTICK
                if crossed(prev_last, last, float(level["price"]), level["side"], hyst):
                    ok = send_level_alert(level, last)
                    audit({"event": "level_cross", "id": level.get("id"), "price": level["price"],
                           "side": level["side"], "last": last, "prev_last": prev_last, "tg_ok": ok})
                    log(f"[ALERTA] {level.get('id')} {level['side']} {level['price']} | last={last} tg={ok}")
                    if level.get("one_shot", True):
                        lv.mark_fired(level.get("id"))

            prev_last = last
            log(f"[hb] {state.get('health')} last={last} armados={sum(1 for l in lv.levels if l.get('state')=='armed')}")
            time.sleep(max(0, FLOOR_S - (time.time() - t0)))
    finally:
        m.stop()
        PIDFILE.unlink(missing_ok=True)


def cli_selftest_levels():
    """Testa o comparador crossed() com sequências sintéticas (offline, sem CDP)."""
    hyst = 10 * MINTICK  # 0.10
    seq = [4025.0, 4020.0, 4013.0, 4011.5, 4008.0, 4000.0]  # atravessa 4012 de cima p/ baixo
    fired = []
    prev = None
    for x in seq:
        if crossed(prev, x, 4012.0, "cross_below", hyst):
            fired.append((prev, x))
        prev = x
    ok1 = len(fired) == 1 and fired[0][0] >= 4012.1 and fired[0][1] <= 4011.9
    # ruído dentro da histerese não dispara
    prev = 4012.5; noise = crossed(prev, 4011.95, 4012.0, "cross_below", hyst)  # 4011.95 > 4011.9 -> não
    # primeiro ciclo (prev None) não dispara
    first = crossed(None, 4000.0, 4012.0, "cross_below", hyst)
    # cross_above
    prev = None; up = []
    for x in [3990.0, 4005.0, 4013.0]:
        if crossed(prev, x, 4012.0, "cross_above", hyst): up.append(x)
        prev = x
    print(f"cross_below 4012 na sequência 4025->4000: disparou={len(fired)}x (esperado 1) PASS={ok1}")
    print(f"ruído dentro histerese (4011.95): disparou={noise} (esperado False) PASS={not noise}")
    print(f"primeiro ciclo prev=None: disparou={first} (esperado False) PASS={not first}")
    print(f"cross_above 4012: disparou={len(up)}x (esperado 1) PASS={len(up)==1}")
    allpass = ok1 and (not noise) and (not first) and len(up) == 1
    print("RESULTADO:", "TODOS PASS ✅" if allpass else "FALHA ❌")
    return 0 if allpass else 1


if __name__ == "__main__":
    if "--test-telegram" in sys.argv:
        cli_test_telegram()
    elif "--selftest-mcp" in sys.argv:
        cli_selftest_mcp()
    elif "--selftest-levels" in sys.argv:
        sys.exit(cli_selftest_levels())
    else:
        main_loop()
