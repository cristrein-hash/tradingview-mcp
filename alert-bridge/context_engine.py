#!/usr/bin/env python3
"""DAEMON E0 Context Engine (Camada 2, P3) — compõe o DOSSIÊ vivo market_context.json a partir dos readers
(MTF estrutura+zonas · micro 15M · macro/news). Determinístico, 0 tokens Claude, alerta-only=NÃO emite nada
(só produz o snapshot que o E1/E2 futuros consomem). Cadência event-driven + piso 60s: micro/macro todo
ciclo; MTF pesado recomputa no FECHO de barra 15M OU move>X·ATR. NUNCA toca a tab do P1 (readers pinam
tabs dedicadas). Honra monitor.pause / /tmp/claude_recheck.paused. Instância única (pidfile). py3.9.
Uso: python3 context_engine.py            (daemon)
     python3 context_engine.py --once      (1 ciclo completo, imprime resumo)
"""
import os, sys, json, time, datetime as dt
from pathlib import Path
BASE = Path(__file__).resolve().parent
REPO = BASE.parent
LOGS = BASE / "logs"; LOGS.mkdir(exist_ok=True)
sys.path.insert(0, str(BASE))
from context_mtf import read_mtf
from context_micro import read_micro
from context_macro import read_macro
from context_confluence import read_confluence

OUT = REPO / "external_factors_v2" / "snapshots" / "market_context.json"
PIDFILE = LOGS / "context_engine.pid"
PAUSE_LOCAL = LOGS / "monitor.pause"
PAUSE_GLOBAL = Path("/tmp/claude_recheck.paused")
FLOOR_S = 60
MTF_MOVE_ATR = 0.6            # recomputa MTF se preço mover > 0.6*ATR desde o último recompute
SCHEMA_VERSION = 1


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def log(m):
    print(f"{now_utc().strftime('%Y-%m-%dT%H:%M:%SZ')} {m}", flush=True)


def atomic_write(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    os.replace(tmp, path)


def paused():
    return PAUSE_LOCAL.exists() or PAUSE_GLOBAL.exists()


def _health(axis, age_s, stale_after):
    if axis is None or (isinstance(axis, dict) and axis.get("error")):
        return {"status": "absent", "age_s": age_s}
    return {"status": "fresh" if (age_s is None or age_s <= stale_after) else "stale", "age_s": age_s}


def build_context(mtf, mtf_age, micro, macro, confluence=None):
    t = int(time.time())
    return {
        "_meta": {"cycle_ts": t, "cycle_iso": now_utc().isoformat(), "schema_version": SCHEMA_VERSION,
                  "price_ref": (micro or {}).get("close")},
        "source_health": {
            "mtf": _health(mtf, mtf_age, 1800),
            "micro_15m": _health(micro, 0, 120),
            "macro": _health(macro, 0, 3600),
            "confluence": _health((confluence or {}).get("15"), mtf_age, 1800),
        },
        "axes": {
            "mtf": {tf: {"trend": (d.get("structure") or {}).get("trend"),
                         "leg": (d.get("structure") or {}).get("leg"),
                         "choch": (d.get("structure") or {}).get("choch"),
                         "swings": (d.get("structure") or {}).get("swings"),
                         "zones": d.get("zones"), "svp": d.get("svp"), "bars": d.get("bars")}
                    for tf, d in (mtf or {}).items() if isinstance(d, dict)},
            "micro_15m": micro,
            "macro": macro,
            "confluence": confluence,      # {"15": {act_dens, buy_dens, sell_dens, leg_sell, nas_n, ...}}
        },
    }


def once(state):
    """Um ciclo: micro+macro sempre; MTF em fecho de barra 15M ou move>ATR. Devolve o dossiê."""
    macro = read_macro()
    micro = read_micro()
    bar_t = (micro or {}).get("bar_time")
    close = (micro or {}).get("close")
    atr = None
    # ATR do 15M do último MTF (para o gate de movimento)
    m15 = (state.get("mtf") or {}).get("15") if state.get("mtf") else None
    if m15:
        atr = (m15.get("structure") or {}).get("atr14")
    need_mtf = (state.get("mtf") is None
                or bar_t != state.get("last_bar_t")
                or (atr and close and state.get("last_mtf_close")
                    and abs(close - state["last_mtf_close"]) > MTF_MOVE_ATR * atr))
    if need_mtf:
        log(f"[mtf] recompute (bar_close={bar_t!=state.get('last_bar_t')} first={state.get('mtf') is None})")
        state["mtf"] = read_mtf()
        state["confluence"] = {"15": read_confluence("15")}     # act_dens na perna 15M (Cp), mesma cadência
        state["last_bar_t"] = bar_t
        state["last_mtf_close"] = close
        state["mtf_ts"] = time.time()
    mtf_age = int(time.time() - state["mtf_ts"]) if state.get("mtf_ts") else None
    ctx = build_context(state["mtf"], mtf_age, micro, macro, state.get("confluence"))
    atomic_write(OUT, ctx)
    return ctx


def main_loop():
    if PIDFILE.exists():
        try:
            old = int(PIDFILE.read_text().strip()); os.kill(old, 0)
            log(f"FATAL: já corre (pid {old})"); sys.exit(1)
        except (ProcessLookupError, ValueError):
            pass
    PIDFILE.write_text(str(os.getpid()))
    state = {}
    log(f"[context_engine] ativo | out={OUT.name} | piso={FLOOR_S}s")
    try:
        while True:
            t0 = time.time()
            if paused():
                log("[paused] log-only"); time.sleep(FLOOR_S); continue
            try:
                ctx = once(state)
                sh = ctx["source_health"]
                log(f"[hb] mtf={sh['mtf']['status']} micro={sh['micro_15m']['status']} macro={sh['macro']['status']} "
                    f"| price={ctx['_meta']['price_ref']}")
            except Exception as e:
                log(f"[erro] ciclo falhou: {type(e).__name__}:{str(e)[:80]}")
            time.sleep(max(0, FLOOR_S - (time.time() - t0)))
    finally:
        PIDFILE.unlink(missing_ok=True)


if __name__ == "__main__":
    if "--once" in sys.argv:
        st = {}
        ctx = once(st)
        sh = ctx["source_health"]
        print(f"OK -> {OUT}")
        print(f"source_health: mtf={sh['mtf']['status']} micro={sh['micro_15m']['status']} macro={sh['macro']['status']}")
        mtf = ctx["axes"]["mtf"]
        for tf in ("1D", "240", "60", "15"):
            d = mtf.get(tf, {})
            leg = (d.get("leg") or {})
            print(f"  [{tf}] trend={d.get('trend')} pos={leg.get('pos_in_leg')} zones={(d.get('zones') or {}).get('n')}")
        print(f"  micro: RSI={ctx['axes']['micro_15m'].get('rsi')} ADX={ctx['axes']['micro_15m'].get('dmi',{}).get('adx')}")
        print(f"  macro: risk={ctx['axes']['macro'].get('risk_level')} vix={ctx['axes']['macro'].get('vix')}")
    else:
        main_loop()
