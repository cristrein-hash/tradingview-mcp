#!/usr/bin/env python3
"""STACK WATCHDOG — anti-cegueira-silenciosa (ordem Cris 2026-07-18). Verifica o heartbeat de CADA
componente live pelos SEUS ficheiros de evidência (logs jsonl/snapshots/pids — zero MCP, zero CDP) e
alerta Telegram na TRANSIÇÃO ok→blind e na recuperação blind→ok. Re-alerta se continuar cego (6h).
Pausas (monitor.pause/claude_recheck.paused) = "paused", não blind; alerta só se pausa >2h (esquecida).
Sem spam: 1 mensagem consolidada por corrida, só quando há mudanças. Horas humanas = Lisboa. py3.9.
CLI: (default) 1 corrida · --test envia 1 msg de ativação · --status imprime painel sem alertar."""
import os, sys, json, time, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
REPO = Path("/Users/cristrein/tradingview-mcp")
AB = REPO / "alert-bridge"
STRAT = REPO / "my-strategy/strategies"
STATE_DIR = Path(__file__).resolve().parent / ".watchdog_state"; STATE_DIR.mkdir(exist_ok=True)
STATE_F = STATE_DIR / "state.json"
LOG = STATE_DIR / "watchdog.log"
REALERT_S = 6 * 3600
PAUSE_ALERT_S = 2 * 3600
PAUSES = [AB / "logs/monitor.pause", Path("/tmp/claude_recheck.paused")]
now = lambda: int(time.time())
lx = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%H:%M")


def _last_jsonl(f):
    try:
        lines = f.read_text().splitlines()
        return json.loads(lines[-1]) if lines else None
    except Exception:
        return None


def _mtime(f):
    try: return f.stat().st_mtime
    except Exception: return None


def _pid_alive(pidfile):
    try:
        os.kill(int(pidfile.read_text().strip()), 0); return True
    except Exception:
        return False


def _iso_age(ts_iso):
    try:
        return now() - dt.datetime.fromisoformat(ts_iso).timestamp()
    except Exception:
        return None


# ---------- checks (devolvem (status, detalhe)) ----------
def chk_log_status(f, max_age_s, bad_prefixes=("HARD_STOP", "NO_TAB", "SEM_BARRAS")):
    r = _last_jsonl(f)
    if not r: return "blind", "sem log"
    age = _iso_age(r.get("ts") or "")
    if age is None or age > max_age_s: return "blind", f"log parado há {int((age or 0)/60)}min"
    st = str(r.get("status") or "")
    if any(st.startswith(b) for b in bad_prefixes): return "blind", st[:60]
    return "ok", st[:40]


def chk_mtime(f, max_age_s):
    m = _mtime(f)
    if m is None: return "blind", "ficheiro ausente"
    age = now() - m
    return ("ok", f"há {int(age/60)}min") if age <= max_age_s else ("blind", f"parado há {int(age/60)}min")


def chk_pid(pidfile):
    return ("ok", "pid vivo") if _pid_alive(pidfile) else ("blind", "processo morto")


def chk_http_health(url, timeout=6):
    """GET a um /health local — caminho de ENTRADA (webhook). (A da auditoria 2026-07-18)"""
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return ("ok", f"HTTP {r.status}") if r.status == 200 else ("blind", f"HTTP {r.status}")
    except Exception as e:
        return "blind", f"sem resposta ({type(e).__name__})"


def chk_process(pattern):
    """Processo vivo por assinatura (pgrep). Para daemons fora do launchd-cristrein (ex. cloudflared)."""
    import subprocess
    try:
        r = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True, timeout=5)
        return ("ok", f"pid {r.stdout.split()[0]}") if r.stdout.strip() else ("blind", "processo ausente")
    except Exception as e:
        return "blind", f"pgrep falhou ({type(e).__name__})"


def chk_network(host="api.telegram.org", timeout=6):
    """Alcance da INTERNET a partir do Mac — a dependência do canal de aviso. Se isto está cego, o próprio
    Telegram do watchdog NÃO entrega (lição 2026-07-21: queda de rede ~35h, tunnel+ponte caíram, alerta gerado
    mas nunca chegou porque a rede que o levaria estava down). Por isso o aviso LOCAL (osascript) cobre este caso."""
    import urllib.request
    try:
        urllib.request.urlopen(f"https://{host}", timeout=timeout)
        return "ok", host
    except Exception as e:
        # 4xx/302 = alcançável (servidor respondeu); só falha de rede/DNS = cego
        import urllib.error
        if isinstance(e, urllib.error.HTTPError):
            return "ok", f"{host} (HTTP {e.code})"
        return "blind", f"sem rede ({type(e).__name__})"


def chk_gld_ws(f, max_age_s=180):
    """WebSocket GLD (persistente): heartbeat ≤3min E status conectado/idle/live (não reconnecting/NO_KEY)."""
    r = _last_jsonl_or_json(f)
    if not r: return "blind", "sem heartbeat"
    age = now() - (r.get("ts") or 0)
    if age > max_age_s: return "blind", f"heartbeat parado há {int(age/60)}min"
    st = str(r.get("status") or "")
    if st in ("NO_KEY", "reconnecting"): return "blind", st
    return "ok", st                                   # connected / idle / live


def _last_jsonl_or_json(f):
    try: return json.loads(Path(f).read_text())      # gld heartbeat = json único
    except Exception: return None


def chk_ef_news(f, max_age_s):
    try: d = json.loads(f.read_text())
    except Exception: return "blind", "snapshot ilegível"
    age = now() - (d.get("fetch_ts") or 0)
    if age > max_age_s: return "blind", f"fetch parado há {int(age/60)}min"
    if not d.get("fetch_ok"): return "blind", f"fetch_ok=false ({str(d.get('error'))[:40]})"
    return "ok", f"há {int(age/60)}min"


def _market_closed(ts):
    """XAUUSD spot fechado (em horas de NOVA IORQUE, DST-robusto): Sex ≥17:00 ET → Dom 17:00 ET (fim-de-
    semana) + break diário de rollover 17:00-18:00 ET. Nestes períodos não há barras novas = NÃO é cegueira."""
    e = dt.datetime.fromtimestamp(ts, ZoneInfo("America/New_York"))
    wd, hh = e.weekday(), e.hour                        # Mon=0..Sun=6
    if wd == 4 and hh >= 17: return True               # Sexta ≥17:00 ET
    if wd == 5: return True                            # Sábado
    if wd == 6 and hh < 17: return True                # Domingo antes das 17:00 (reabre 17:00 ET)
    if hh == 17: return True                           # rollover diário 17:00-17:59 ET
    return False


def chk_bar_fresh(f, dur_s, max_stale_s):
    """Frescura da ÚLTIMA barra FECHADA de UM TF no store (por-TF). Apanha a morte silenciosa de um feed
    (ex. tab sumida como o 15M hoje) que o log-status GLOBAL do bar-store não vê (o log segue a correr em
    PARTIAL). Ciente de mercado fechado = não alarma ao fim-de-semana/rollover."""
    r = _last_jsonl(f)
    if not r: return "blind", "store vazio"
    if _market_closed(now()): return "ok", "mercado fechado"
    age = now() - ((r.get("t") or 0) + dur_s)          # tempo desde o fecho da última barra que temos
    if age <= max_stale_s: return "ok", f"última barra há {int(age/60)}min"
    return "blind", f"sem barra nova há {int(age/60)}min (tab sumida?)"


def components():
    paused = any(p.exists() for p in PAUSES)
    c = {
        "Cp 15M":      chk_log_status(STRAT / "xau_15m_long/reversal/CP_CAPITULATION/.cp_state/cp_cycle.log", 35*60),
        "Router 15M":  chk_log_status(STRAT / "xau_15m_long/ENTRY_ROUTER/.router_state/router_cycle.log", 35*60),
        "AMD live":    chk_log_status(STRAT / "xau_amd/amd_live/.amd_state/amd_cycle.log", 35*60),
        "Journal cap": chk_log_status(REPO / "copilot/journal/.state/capture.log", 12*60),
        "Journal day": chk_mtime(REPO / "copilot/journal/.state/daily_out.log", 26*3600),   # cron 22:00 Lisboa (1×/dia)
        "Regime":      chk_log_status(REPO / "my-strategy/core/regime_engine/.regime_state/regime_cycle.log", 130*60),
        "Layer1 1D":   chk_mtime(REPO / "my-strategy/core/layer1_service/.layer1_state/current_layer1.json", 130*60),  # escrito pelo regime-engine (autoridade única, horário)
        "L1 4H":       chk_log_status(STRAT / "xau_4h_long/continuation/L1_EMA21_CONTINUATION/.runtime_state/l1_cycle.log", 6*3600),
        "L2 4H":       chk_log_status(STRAT / "xau_4h_long/reversal/L2_BPT_ZONE_TREND_EXIT/.runtime_state/l2_cycle.log", 270*60),  # cadência real: 4/4h (:12 pós-fecho 4H)
        "E0 dossiê":   chk_mtime(REPO / "external_factors_v2/snapshots/market_context.json", 15*60),
        "E1 detector": chk_pid(AB / "logs/e1_detector.pid"),
        "E2 quality":  chk_pid(AB / "logs/e2_quality.pid"),
        "EF news":     chk_ef_news(REPO / "external_factors_v2/snapshots/investinglive_news.json", 15*60),
        "Polymarket":  chk_ef_news(REPO / "external_factors_v2/snapshots/polymarket.json", 20*60),
        "EF v2":       chk_mtime(REPO / "external_factors_v2/snapshots/latest.json", 70*60),
        "Backfill":    chk_mtime(AB / "logs/e2_outcome_backfill.log", 130*60),
        "Bar-store":   chk_log_status(REPO / "my-strategy/core/bar_store/store/store_cycle.log", 10*60, bad_prefixes=("HARD_STOP",)),
        "Bars 5M":     chk_bar_fresh(REPO / "my-strategy/core/bar_store/store/bars_5m.jsonl", 300, 20*60),   # tab 5M viva? (entry timing + price-shock)
        "Bars 15M":    chk_bar_fresh(REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl", 900, 45*60),  # tab 15M viva? (o susto de hoje)
        "PriceShock":  chk_log_status(REPO / "my-strategy/core/price_shock/.shock_state/shock_cycle.log", 5*60, bad_prefixes=("HARD_STOP",)),
        "GLD-ws":      chk_gld_ws(REPO / "my-strategy/core/price_shock/.shock_state/gld_ws_heartbeat.json"),
        # FJ-ws REMOVIDO do painel (Cris 2026-08-02): daemon DESLIGADO por decisão 31/07 (403/plano caro,
        # fonte secundária) — vigiá-lo gerava "ainda cego" a cada 6h a poluir o Telegram. Ver project_fj_ws_disabled.
        "Receiver":    chk_http_health("http://127.0.0.1:8787/health"),      # webhook ENTRADA (A auditoria)
        "Cloudflared": chk_process("cloudflared tunnel run"),               # túnel público ENTRADA
        "Bridge":      chk_process("telegram_assistant_bridge"),            # ponte Cris↔Claude (o canal que caiu 2026-07-21)
        "Rede":        chk_network(),                                       # internet do Mac (raiz da queda ~35h; se cego, Telegram não entrega → aviso local)
    }
    if (STRAT / "xau_amd/amd_live/.amd_state/PAUSED_BY_ORDER").exists():
        c["AMD live"] = ("paused", "em repouso por ordem Cris (range) — não é cegueira")
    if paused:   # pipeline E0/E1/E2 honra pausa: não é cegueira
        for k in ("E0 dossiê", "E1 detector", "E2 quality"):
            if c[k][0] == "blind": c[k] = ("paused", "pausado (monitor.pause)")
    return c


def _notify(text):
    """SÓ para o chat pessoal Trading Assistant Trein (AUTHORIZED_CHAT_ID) — ordem Cris 05/08:
    watchdog NUNCA no grupo. SILENCIADO por default (Cris 2026-08-16: poluía o pessoal). Vigia+log continuam;
    Telegram só se WATCHDOG_TELEGRAM=on no ambiente/plist."""
    import os
    if os.environ.get("WATCHDOG_TELEGRAM", "off") != "on":
        return "SILENCED (WATCHDOG_TELEGRAM!=on)"
    try:
        env = {}
        for line in (REPO / "alert-bridge/.env").read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("="); env[k.strip()] = v.strip()
        tok = env.get("TELEGRAM_BOT_TOKEN"); cid = env.get("AUTHORIZED_CHAT_ID")
        if not tok or not cid:
            return "ERR sem credenciais"
        from urllib.parse import urlencode
        from urllib.request import Request, urlopen
        data = urlencode({"chat_id": cid, "text": text}).encode()
        with urlopen(Request(f"https://api.telegram.org/bot{tok}/sendMessage", data=data), timeout=15) as r:
            return r.status == 200
    except Exception as e:
        return f"ERR {str(e)[:60]}"


def _local_notify(title, text):
    """Aviso LOCAL no Mac via osascript — funciona OFFLINE. Cobre o caso em que a rede caiu e o Telegram NÃO
    entrega (2026-07-21). Dispara em toda cegueira, além do Telegram. Best-effort, nunca levanta."""
    import subprocess
    try:
        safe = text.replace('"', "'").replace("\\", "")[:200]
        subprocess.run(["osascript", "-e",
                        f'display notification "{safe}" with title "{title}" sound name "Basso"'],
                       capture_output=True, timeout=6)
        return True
    except Exception:
        return False


def main():
    if "--status" in sys.argv:
        for k, (st, d) in components().items():
            print(f"  {k:<12} {st:<7} {d}")
        return 0
    if "--test" in sys.argv:
        r = _notify("🩺 Stack watchdog ATIVO — vigio Cp/Regime/L1/L2/E0/E1/E2/EF/backfill a cada 5min; alerto na cegueira e na recuperação.")
        print("teste telegram:", r); return 0
    try: st_prev = json.loads(STATE_F.read_text())
    except Exception: st_prev = {}
    cur = components()
    changes, still_blind = [], []
    for k, (st, det) in cur.items():
        p = st_prev.get(k) or {}
        if st != p.get("status"):
            st_prev[k] = {"status": st, "since": now(), "last_alert": 0}
            if st == "blind":
                changes.append(f"🔴 {k}: CEGO — {det}")
            elif st == "ok" and p.get("status") in ("blind", "paused"):
                changes.append(f"🟢 {k}: recuperado ({det})")
        else:
            since = p.get("since") or now(); last_a = p.get("last_alert") or 0
            if st == "blind" and now() - last_a > REALERT_S:
                still_blind.append(f"🔴 {k}: ainda cego desde {lx(since)} — {det}")
                st_prev[k]["last_alert"] = now()
            if st == "paused" and now() - since > PAUSE_ALERT_S and now() - last_a > REALERT_S:
                still_blind.append(f"⏸️ {k}: pausado há {int((now()-since)/3600)}h (esquecido?)")
                st_prev[k]["last_alert"] = now()
    msgs = changes + still_blind
    out = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(),
           "panel": {k: v[0] for k, v in cur.items()}, "alerts": len(msgs)}
    if msgs:
        for m in changes:
            if m.startswith("🔴"):
                k = m.split(":")[0][2:].strip()
                st_prev[k]["last_alert"] = now()
        r = _notify("🩺 STACK WATCHDOG\n" + "\n".join(msgs))
        out["telegram"] = str(r)
        # aviso LOCAL sempre que há cegueira NOVA — offline-safe (Telegram pode não entregar se a rede caiu)
        blind_now = [m for m in changes if m.startswith("🔴")]
        if blind_now:
            out["local"] = _local_notify("🩺 STACK WATCHDOG — cegueira", " · ".join(b[2:] for b in blind_now))
    tmp = STATE_F.with_suffix(".json.tmp"); tmp.write_text(json.dumps(st_prev)); os.replace(tmp, STATE_F)
    with open(LOG, "a") as fh:
        fh.write(json.dumps(out, ensure_ascii=False) + "\n")
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
