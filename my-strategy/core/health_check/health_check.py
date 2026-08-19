#!/usr/bin/env python3
"""HEALTH-CHECK ÚNICO da espinha essencial (Cris 2026-08-17 APROVADO). Grita no Telegram pessoal quando algo
essencial CONGELA — fecha o buraco de hoje: regime 1D preso 4 dias sem ninguém avisar.

Vigia (lista aprovada pelo Cris):
  1. DADOS    — bars_5m/15m frescos (horário de mercado) · bars_1d com barra nova pós-fecho diário
  2. CONTEXTO — market_context.json (E0) fresco · current_layer1.json (regime) fresco
  3. ESTRATÉGIAS/READER/ENTREGA/VIGIA — daemons essenciais CARREGADOS no launchd
Sem tocar em nada: read-only + alerta. Cooldown por chave (não spamma). Fim-de-semana (XAU fechado
sex 21:00 UTC → dom 22:00 UTC) suspende os checks de frescura de mercado. Fail-loud no próprio log.
Alerta = telegram_notify (o mesmo do bar-store), chat pessoal. py3 stdlib."""
import json, os, subprocess, sys, time
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
STATE = Path(__file__).resolve().parent / ".health_state"
STATE.mkdir(exist_ok=True)
LOG = STATE / "health.log"
COOLDOWN_S = 3600            # 1 alerta/h por chave no máximo

# (chave, ficheiro, idade máx em s DURANTE MERCADO ABERTO)
FRESH_FILES = [
    ("bars_5m",   REPO / "my-strategy/core/bar_store/store/bars_5m.jsonl",   15 * 60),
    ("bars_15m",  REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl",  45 * 60),
    ("dossier_E0", REPO / "external_factors_v2/snapshots/market_context.json", 20 * 60),
    ("layer1_regime", REPO / "my-strategy/core/layer1_service/.layer1_state/current_layer1.json", 2 * 3600),
]
BARS_1D = REPO / "my-strategy/core/bar_store/store/bars_1d.jsonl"

# daemons que têm de estar CARREGADOS (periódicos aparecem sem PID — carregado chega)
DAEMONS = [
    "com.cristrein.bar-store", "com.cristrein.gld-ws", "com.cristrein.price-sentinel",
    "com.cristrein.context-engine", "com.cristrein.external-factors-v2", "com.cristrein.regime-engine",
    "com.cristrein.xau-l1-cycle", "com.cristrein.xau-l2-cycle", "com.cristrein.xau-cp-cycle",
    "com.cristrein.xau-entry-router", "com.cristrein.xau-a1a2-cycle",
    "com.cristrein.e1-detector", "com.cristrein.e2-quality",
    "com.cristrein.telegram-assistant-bridge", "com.cristrein.tv-webhook-receiver",
    "com.cristrein.cloudflared-tunnel", "com.cristrein.stack-watchdog",
    "com.cristrein.price-shock",   # AUDIT-FIX 19/08 (F8): gatilho realtime estava fora do vigia redundante
]


def market_open(now_utc):
    """XAU: sessão CME/spot ancorada em NY — fecha sex 17:00 NY, reabre dom 18:00 NY; pausa diária de
    settlement 17:00-18:00 NY (seg-qui). AUDIT-FIX 19/08 (C5): antes usava 21:00 UTC hardcoded, que só é
    correto no horário de verão dos EUA — no inverno desfasava 1h (falsos congelamentos)."""
    from zoneinfo import ZoneInfo
    ny = now_utc.astimezone(ZoneInfo("America/New_York"))
    wd, hm = ny.weekday(), ny.hour + ny.minute / 60
    if wd == 4 and hm >= 17: return False
    if wd == 5: return False
    if wd == 6 and hm < 18: return False
    if 17 <= hm < 18: return False                 # pausa diária (o feed não produz barras -> não é congelamento)
    return True


def check_fresh(now):
    """Frescura dos ficheiros de mercado (só com mercado aberto)."""
    probs = []
    for key, f, max_age in FRESH_FILES:
        try:
            age = now - f.stat().st_mtime
        except Exception:
            probs.append((key, f"{key}: FICHEIRO AUSENTE {f.name}")); continue
        if age > max_age:
            probs.append((key, f"{key}: CONGELADO há {age/3600:.1f}h (máx {max_age/3600:.1f}h) — {f.name}"))
    return probs


def check_1d(now_utc):
    """A barra diária nova tem de existir até 1h após o fecho (22:00 UTC) de cada dia de semana.
    Stamp da barra = abertura da sessão (22:00 do dia anterior)."""
    try:
        last_t = max(json.loads(l)["t"] for l in BARS_1D.read_text().splitlines() if l.strip())
    except Exception:
        return [("bars_1d", "bars_1d: ilegível/ausente")]
    # última sessão FECHADA esperada: recua a partir de agora-23h até achar um fecho de dia de semana
    ts = now_utc - dt.timedelta(hours=23)
    while True:
        close = ts.replace(hour=22, minute=0, second=0, microsecond=0)
        if close > ts: close -= dt.timedelta(days=1)
        open_stamp = close - dt.timedelta(days=1)          # barra é stampada na ABERTURA
        if open_stamp.weekday() in (0, 1, 2, 3, 6):        # sessões dom-qui (abertura) = seg-sex (fecho)
            break
        ts -= dt.timedelta(days=1)
    expected = int(open_stamp.timestamp())
    if last_t < expected:
        return [("bars_1d", "bars_1d: última barra %s < esperada %s — feed 1D congelado" % (
            dt.datetime.utcfromtimestamp(last_t).strftime('%d/%m'), open_stamp.strftime('%d/%m')))]
    return []


def check_daemons():
    """Carregado E sem crash-loop: launchctl list = 'PID  LastExitStatus  Label'; exit != 0 = última corrida FALHOU."""
    try:
        out = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=15).stdout
    except Exception as e:
        return [("launchctl", f"launchctl falhou: {e}")]
    info = {}
    for ln in out.splitlines():
        parts = ln.split("\t")
        if len(parts) == 3:
            info[parts[2].strip()] = (parts[0].strip(), parts[1].strip())   # (PID, LastExitStatus)
    probs = []
    for d in DAEMONS:
        if d not in info:
            probs.append((d, f"daemon NÃO CARREGADO: {d}"))
            continue
        pid, ex = info[d]
        # a correr agora (PID) = saudável, ignora exit antigo (ex.: -15 de um kickstart).
        # Parado (PID '-') com exit != 0 = última corrida FALHOU -> crash-loop/erro.
        if pid == "-" and ex not in ("0", "-"):
            probs.append((d, f"daemon A FALHAR (last exit {ex}): {d}"))
    return probs


def alert(probs, now):
    """SEM Telegram (Cris 2026-08-17: 'não quero ser alertado — é para o Claude se auto-corrigir').
    PENDING.json espelha SEMPRE o estado atual (aparece quando há problema, some quando resolve);
    o hook UserPromptSubmit injeta-o no contexto do Claude a cada turno — o Claude ouve, o Cris não."""
    p = STATE / "PENDING.json"
    if probs:
        p.write_text(json.dumps({"ts": now, "problems": [m for _, m in probs]}, ensure_ascii=False))
        return len(probs)
    if p.exists():
        p.unlink()
    return 0


def _log(o):
    with open(LOG, "a") as fh:
        fh.write(json.dumps(o, ensure_ascii=False) + "\n")


def run(now=None):
    now = now or time.time()
    now_utc = dt.datetime.utcfromtimestamp(now)
    probs = []
    if market_open(now_utc):
        probs += check_fresh(now)
        probs += check_1d(now_utc)
    probs += check_daemons()                       # daemons têm de estar carregados sempre
    sent = alert(probs, now)
    rec = {"ts": now_utc.isoformat(), "market_open": market_open(now_utc),
           "problems": [m for _, m in probs], "alerted": sent}
    _log(rec)
    return rec


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        # puro, sem rede: market_open + check_1d em cenários fixos
        t = []
        t.append(("sáb=fechado", market_open(dt.datetime(2026, 8, 15, 12)) is False))
        t.append(("dom 23h=aberto", market_open(dt.datetime(2026, 8, 16, 23)) is True))
        t.append(("qui 12h=aberto", market_open(dt.datetime(2026, 8, 13, 12)) is True))
        t.append(("sex 22h=fechado", market_open(dt.datetime(2026, 8, 14, 22)) is False))
        # 1D: com o ficheiro real (última barra 16/08 open-stamp) na seg 17/08 21:00 -> esperada 13/08(qui-open)?
        # Nota: às 21:00 de seg a sessão de seg ainda NÃO fechou; esperada = barra da sexta (stamp qui 22:00).
        r = check_1d(dt.datetime(2026, 8, 17, 21, 0))
        t.append(("seg 21:00 (sexta já no store) -> sem alarme", r == []))
        r2 = check_1d(dt.datetime(2026, 8, 21, 12, 0))       # sex 21/08: esperada barra qua->qui; store parou 16/08
        t.append(("sex 21/08 (store parado) -> alarme", len(r2) == 1))
        for lab, ok in t:
            print("  [%s] %s" % ("OK" if ok else "FAIL", lab))
        sys.exit(0 if all(ok for _, ok in t) else 1)
    if "--dry" in sys.argv:                          # corre tudo mas NÃO alerta
        globals()["alert"] = lambda probs, now: 0
        print(json.dumps(run(), ensure_ascii=False, indent=1))
        sys.exit(0)
    run()
