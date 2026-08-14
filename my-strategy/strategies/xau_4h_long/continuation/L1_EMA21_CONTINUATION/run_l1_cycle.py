#!/usr/bin/env python3
"""Runner mínimo do ciclo XAU-only L1 (Production v2). Orquestra scripts EXISTENTES.

Ciclo:
  0) (opcional --manage-chart) prepara o chart em PEPPERSTONE:XAUUSD 240 e restaura depois
  1) refresh_regime_l1_v4.py --write   (mantém regime D-1 fresco; already_fresh se nada novo)
  2) runtime_xau.py --once [--send-telegram] --dedup-path <persistente>

Default = DRY-RUN (sem Telegram). Telegram real só com --send-telegram, e só para
operational_candidate (o runtime decide). Dedup persistente garante ≤1 Telegram por signal_hash.
FALHA FECHADO: se chart-prep, refresh ou runtime der HARD_STOP, aborta sem Telegram.

--manage-chart: usa MCP (src/server.js via tv_read_adapter.MCPClient) só para LER/TROCAR symbol+timeframe
  para PEPPERSTONE:XAUUSD/240 antes do runtime e RESTAURAR o chart anterior depois. NUNCA dirige trade,
  nunca desenha, nunca toca broker, nunca troca para outro símbolo. Lock-guard evita chart-op simultânea.
--leave-chart-240: não restaura (deixa em 240). Sem isso, restaura o chart anterior.

NÃO reimplementa scanner/regime/telegram. NÃO toca legacy/broker/strategy_rules/catalog/RAW.
NÃO escreve em logs legacy (log próprio em .runtime_state/). DST-agnóstico (lê a barra live + dedup).
"""
import json, sys, subprocess, argparse, time, os
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
REPO = None
for d in [HERE] + list(HERE.parents):
    if (d / "my-strategy").is_dir() and (d / "alert-bridge").is_dir():
        REPO = d; break
REFRESH = REPO / "my-strategy/core/regime_l1/refresh_regime_l1_v4.py"
RUNTIME = HERE / "runtime_xau.py"
STATE_DIR = HERE / ".runtime_state"
DEDUP = STATE_DIR / "l1_dedup.txt"
LOG = STATE_DIR / "l1_cycle.log"
CHART_LOCK = STATE_DIR / "chart_op.lock"
LOG_MAX_BYTES = 2_000_000   # ~2 MB
LOG_BACKUPS = 3
WANT_SYMBOL, WANT_TF = "PEPPERSTONE:XAUUSD", "240"
LOCK_STALE_SEC = 600        # lock mais velho que 10 min = órfão, ignorável


def _rotate_log():
    """Rotação mínima sem dep externa: l1_cycle.log -> .1 -> .2 -> .3 (mantém 3 backups)."""
    try:
        if LOG.exists() and LOG.stat().st_size > LOG_MAX_BYTES:
            oldest = LOG.with_suffix(LOG.suffix + f".{LOG_BACKUPS}")
            if oldest.exists():
                oldest.unlink()
            for i in range(LOG_BACKUPS - 1, 0, -1):
                src = LOG.with_suffix(LOG.suffix + f".{i}")
                if src.exists():
                    src.rename(LOG.with_suffix(LOG.suffix + f".{i + 1}"))
            LOG.rename(LOG.with_suffix(LOG.suffix + ".1"))
    except Exception:
        pass  # rotação é best-effort; nunca derruba o ciclo


def _run(argv, env=None):
    return subprocess.run([sys.executable] + argv, capture_output=True, text=True, env=env)


# ---- tab-pinning (recurso geral, Cris 2026-07-17): ler a tab dedicada do TF via TVMCP_TARGET_CHART_ID ----
# 5 tabs XAUUSD abertas (5M/15M/1H/4H/1D). refresh lê a tab 1D pinada; runtime lê a tab 4H pinada.
# ZERO troca de symbol/TF, zero restore, zero pausa dos daemons E0/E1/E2 (coexistência total).
# Fallback fail-safe: se as tabs não existirem, cai no modo --manage-chart antigo (com pausa).

def _discover_tabs():
    """(tid_1D, tid_240) via helper partilhado my-strategy/core/tab_pin.py; (None, None) em falha."""
    try:
        sys.path.insert(0, str(REPO / "my-strategy/core"))
        import tab_pin
        return tab_pin.discover_tab("1D"), tab_pin.discover_tab("240")
    except Exception:
        return None, None


# ---- chart management (read/set symbol+timeframe via MCP; NUNCA trade/draw/broker) ----

class ChartError(Exception):
    pass


def _mcp_client():
    sys.path.insert(0, str(REPO / "my-strategy/core"))
    from tv_read_adapter import _MCP  # reusa o client JSON-RPC do adapter (mesmo server.js)
    c = _MCP(); c.start(); return c


def _guard_conflict():
    """HARD STOP se houver coleta replay ativa OU lock de chart-op fresco (outra instância)."""
    try:
        pg = subprocess.run(["pgrep", "-fl", "safe_backtest_window|run_xau_replay"],
                            capture_output=True, text=True)
        if pg.stdout.strip():
            raise ChartError(f"chart-controlling process ativo: {pg.stdout.strip()[:80]}")
    except FileNotFoundError:
        pass
    if CHART_LOCK.exists():
        age = time.time() - CHART_LOCK.stat().st_mtime
        if age < LOCK_STALE_SEC:
            raise ChartError(f"chart_op.lock fresco ({int(age)}s) — outra chart-op em curso")


def prepare_chart():
    """Captura chart atual e troca para PEPPERSTONE:XAUUSD/240. Retorna (before, used, changed, client).
    Levanta ChartError em qualquer falha de confirmação."""
    _guard_conflict()
    STATE_DIR.mkdir(exist_ok=True)
    CHART_LOCK.write_text(str(os.getpid()))
    c = _mcp_client()
    st = c.call("chart_get_state")
    if not isinstance(st, dict) or st.get("_error"):
        raise ChartError(f"chart_get_state falhou: {st}")
    before = {"symbol": st.get("symbol"), "timeframe": str(st.get("resolution"))}
    changed = False
    if before["symbol"] != WANT_SYMBOL:
        c.call("chart_set_symbol", {"symbol": WANT_SYMBOL}); changed = True
    if str(before["timeframe"]) != WANT_TF:
        c.call("chart_set_timeframe", {"timeframe": WANT_TF}); changed = True
    # confirmar efetivamente
    chk = c.call("chart_get_state")
    sym, res = chk.get("symbol"), str(chk.get("resolution"))
    if not (str(sym).endswith("XAUUSD") and res == WANT_TF):
        raise ChartError(f"confirmação falhou após set: symbol={sym} tf={res}")
    used = {"symbol": sym, "timeframe": res}
    return before, used, changed, c


def restore_chart(c, before, changed, leave_240=False):
    """Restaura o chart anterior se foi alterado e !leave_240. Retorna dict de status."""
    res = {"restored": False, "left_240": leave_240}
    try:
        if changed and not leave_240:
            if before.get("symbol"):
                c.call("chart_set_symbol", {"symbol": before["symbol"]})
            if before.get("timeframe") and before["timeframe"] not in (None, "None"):
                c.call("chart_set_timeframe", {"timeframe": str(before["timeframe"])})
            chk = c.call("chart_get_state")
            res["restored"] = (chk.get("symbol") == before.get("symbol")
                               and str(chk.get("resolution")) == str(before.get("timeframe")))
            res["after"] = {"symbol": chk.get("symbol"), "timeframe": str(chk.get("resolution"))}
    finally:
        try: c.stop()
        except Exception: pass
        try: CHART_LOCK.unlink()
        except Exception: pass
    return res


def _run_refresh_and_runtime(send_telegram, ts, env_refresh=None, env_runtime=None):
    """Passos 1+2 (refresh + runtime). Mesma lógica fail-closed de sempre.
    env_refresh/env_runtime: ambientes com TVMCP_TARGET_CHART_ID pinado (modo tab-pinned)."""
    r = _run([str(REFRESH), "--write"], env=env_refresh)
    try:
        rj = json.loads(r.stdout)
    except Exception:
        return {"status": "HARD_STOP", "stage": "refresh", "reason": r.stdout.strip() or r.stderr.strip()}
    if rj.get("status") == "HARD_STOP":
        return {"status": "HARD_STOP", "stage": "refresh", "reason": rj.get("reason")}
    refresh_status = rj.get("status")
    rt_argv = [str(RUNTIME), "--once", "--dedup-path", str(DEDUP)]
    # GUARD-CHoCH ATIVO (Cris 2026-08-14): L1 é LONG (continuação 4H) — não enviar ao TG se CHoCH-down
    # (quebra do higher-low) no 4H E 1H (consome dossiê E0). Fail-open: sem dossiê = envia normal.
    _choch_block = False
    try:
        import sys as _sys
        _sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
        import choch_shadow_guard as _CHG
        _choch_block = _CHG.blocks_long()
    except Exception:
        _choch_block = False
    if send_telegram and not _choch_block:
        rt_argv.append("--send-telegram")
    elif send_telegram and _choch_block:
        print("(CHoCH-guard: L1 LONG bloqueado — choch_dn 4H+1H, sem --send-telegram)", flush=True)
    rt = _run(rt_argv, env=env_runtime)
    try:
        rtj = json.loads(rt.stdout)
    except Exception:
        return {"status": "HARD_STOP", "stage": "runtime", "reason": rt.stdout.strip() or rt.stderr.strip()}
    if rtj.get("runtime") == "HARD_STOP":
        return {"status": "HARD_STOP", "stage": "runtime", "reason": rtj.get("reason")}
    cand = rtj.get("candidate", {})
    notify = rtj.get("notify", {})
    state = cand.get("state")
    if isinstance(cand.get("reason"), str) and "regime_l1_v4_stale" in cand.get("reason"):
        return {"status": "STALE", "stage": "runtime", "reason": cand.get("reason")}
    return {"status": "OK", "refresh": refresh_status, "state": state,
            "symbol": cand.get("symbol"), "timeframe": cand.get("timeframe"),
            "candidate_timestamp": cand.get("candidate_timestamp"),
            "reason": cand.get("reason"),
            "telegram_real": bool(send_telegram), "notify_sent": notify.get("sent"),
            "notify_skip": notify.get("skip"), "signal_hash": cand.get("signal_hash")}


PAUSE_FLAG = Path("/Users/cristrein/tradingview-mcp/alert-bridge/logs/monitor.pause")


def cycle(send_telegram=False, manage_chart=False, leave_240=False, pin_tabs=False):
    STATE_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()

    # MODO TAB-PINNED (preferido, Cris 2026-07-17): refresh na tab 1D, runtime na tab 4H —
    # sem trocar chart, sem lock, sem pausar daemons. Fallback: modo manage-chart antigo.
    fell_back = False
    if pin_tabs:
        tid_d, tid_4h = _discover_tabs()
        if tid_d and tid_4h:
            env_d = dict(os.environ); env_d["TVMCP_TARGET_CHART_ID"] = tid_d
            env_4h = dict(os.environ); env_4h["TVMCP_TARGET_CHART_ID"] = tid_4h
            out = _run_refresh_and_runtime(send_telegram, ts, env_refresh=env_d, env_runtime=env_4h)
            out = {**out, "chart_mode": "pinned", "tab_1d": tid_d[:8], "tab_240": tid_4h[:8]}
            _log(ts, out)
            return {"ts": ts, **out}
        manage_chart = True; fell_back = True   # tabs ausentes -> modo antigo (com pausa própria)

    # MODO MANAGE-CHART (antigo / fallback): troca a tab default p/ 240 e restaura.
    # Pausa os daemons do alert-bridge durante o chart-op (respeita pausa pré-existente do operador).
    pause_created = False
    if manage_chart and not PAUSE_FLAG.exists():
        try:
            PAUSE_FLAG.write_text(ts); pause_created = True
            time.sleep(5)   # daemons (floor 20-60s) veem a pausa antes do chart-op
        except Exception:
            pass
    try:
        chart_info = {"chart_mode": "manage_chart_fallback" if fell_back else "manage_chart"}
        client = None
        if manage_chart:
            # 0) preparar chart; falha aqui = HARD_STOP sem Telegram
            try:
                before, used, changed, client = prepare_chart()
                chart_info.update({"chart_before": before, "chart_used": used, "chart_changed": changed})
            except Exception as e:
                try:
                    if client: client.stop()
                except Exception: pass
                try: CHART_LOCK.unlink()
                except Exception: pass
                out = {"status": "HARD_STOP", "stage": "chart_prepare", "reason": str(e), "notify_sent": False,
                       **chart_info}
                _log(ts, out); return {"ts": ts, **out}

        out = _run_refresh_and_runtime(send_telegram, ts)

        if manage_chart and client is not None:
            try:
                chart_info["chart_restore"] = restore_chart(client, before, changed, leave_240)
            except Exception as e:
                chart_info["chart_restore"] = {"restored": False, "error": str(e)}
        if manage_chart:
            out = {**out, **chart_info}

        _log(ts, out)
        return {"ts": ts, **out}
    finally:
        if pause_created:
            try: PAUSE_FLAG.unlink()
            except Exception: pass


def _log(ts, out):
    _rotate_log()
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": ts, **out}, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Minimal XAU L1 cycle runner.")
    ap.add_argument("--once", action="store_true", help="roda 1 ciclo (default já é 1 ciclo)")
    ap.add_argument("--send-telegram", action="store_true", help="envio real (opt-in; default dry-run)")
    ap.add_argument("--manage-chart", action="store_true",
                    help="prepara o chart em PEPPERSTONE:XAUUSD/240 via MCP e restaura depois")
    ap.add_argument("--leave-chart-240", action="store_true",
                    help="com --manage-chart: deixa o chart em 240 (não restaura)")
    ap.add_argument("--pin-tabs", action="store_true",
                    help="lê as tabs dedicadas 1D/4H via TVMCP_TARGET_CHART_ID (sem trocar chart); "
                         "fallback automático p/ --manage-chart se as tabs não existirem")
    args = ap.parse_args()
    res = cycle(send_telegram=args.send_telegram, manage_chart=args.manage_chart,
                leave_240=args.leave_chart_240, pin_tabs=args.pin_tabs)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 2 if res.get("status") in ("HARD_STOP", "STALE") else 0


if __name__ == "__main__":
    sys.exit(main())
