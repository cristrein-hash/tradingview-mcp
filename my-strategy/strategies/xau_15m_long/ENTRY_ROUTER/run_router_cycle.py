#!/usr/bin/env python3
"""ENTRY ROUTER 15M — ciclo LIVE em modo DRY (Cris 2026-07-19). Roteia, por REGIME MACRO (autoridade
única = Layer1 1D, current_layer1.json escrito pelo regime-engine), qual camada de entry é ELEGÍVEL:
  BEAR  -> território do Cp (já live, alert-only) — o router NÃO duplica, só regista.
  RANGE -> engine de B v1.1 via b_forward_score (deep loader gz+store) — DRY: pontua+loga+resolve, 0 Telegram.
  BULL  -> A1/A2 (pullback) — SEM detetor de fundo automático ainda (task #35) -> só regista pendência.
Roteamento (elegibilidade por contexto), NÃO hard-gate/veto. Store-first (bar-store, zero CDP próprio).
Fail-closed. py3.9 stdlib. SEM Telegram nesta versão (dry puro).

CONSOLIDAÇÃO (feedback 2026-07-19): o ramo B DELEGA ao coletor forward existente b_forward_score (fonte
única do ledger, prereg §6, resolve SL-first) — não duplica. Injeta a autoridade fresca no macro antes de
o importar (Conexão 3). O deep loader load_series_live (gz desde o onset + cauda do store) RESOLVE o antigo
'band_truncated' — PARIDADE PROVADA 15/15 byte-a-byte vs in-sample (parity_b_live.py). Go-live do B ainda
exige: prereg N>=20 forward (b_forward_score --status §6) + só então B_PRODUCTION_AUTHORIZED. Dormente BEAR."""
import os, sys, json, time, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
CORE = Path("/Users/cristrein/tradingview-mcp/my-strategy/core")
REV = Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
sys.path.insert(0, str(CORE)); sys.path.insert(0, str(CORE / "layer1_service"))
sys.path.insert(0, str(REV))                      # macro_structural_v3 + b_engine_v1 vivem aqui
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
LAYER1 = CORE / "layer1_service/.layer1_state/current_layer1.json"
STATE = HERE / ".router_state"; STATE.mkdir(exist_ok=True)
LOG = STATE / "router_cycle.log"
# NOTA: o ledger forward do B vive em b_forward_score (my-strategy/research/revalidation/b_forward/) —
# fonte única, reusada (feedback consolidar-nao-proliferar 2026-07-19). O router só o alimenta/resolve.
BAR_S = 900
FRESH_BARS = 2
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
iso = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%Y-%m-%d %H:%M")


def _log(o):
    with open(LOG, "a") as fh: fh.write(json.dumps(o, ensure_ascii=False) + "\n")


def read_regime():
    try:
        d = json.loads(LAYER1.read_text())
        return d.get("regime"), d.get("as_of")
    except Exception:
        return None, None


def _inject_fresh_macro():
    """Injeta 1D/DXY frescos nos globais de macro_structural_v3 ANTES de importar o b_forward_score/b_engine
    (que computa _reg no import) — assim o gate/banda do B leem a AUTORIDADE fresca (Conexão 3). Matemática
    intocada. Tem de correr antes do 1º import de b_engine_v1 no processo."""
    import macro_structural_v3 as M
    import layer1_cycle as L1
    xau = L1._merge_xau_1d()
    dxy = L1._jl(REV / "raw_dxy_1d.jsonl")
    if len(xau) < 400 or len(dxy) < 400:
        return False
    M.T = [b["t"] for b in xau]; M.O = [b["o"] for b in xau]; M.H = [b["h"] for b in xau]
    M.L = [b["l"] for b in xau]; M.C = [b["c"] for b in xau]; M.N = len(xau)
    M.DXY_K = [b["t"] + 86400 for b in dxy]; M.DXY_C = [b["c"] for b in dxy]
    return True


def run_B(rows, out):
    """Ramo RANGE: DELEGA ao coletor forward existente b_forward_score (não duplica ledger — feedback
    consolidar 2026-07-19). Injeta a autoridade fresca -> pontua o último 15M fechado via BF.score (deep
    loader gz+store) -> upsert no forward log SE engine ON -> resolve PENDING. DRY (0 Telegram)."""
    if not _inject_fresh_macro():
        out["b"] = "SKIP: macro fresco insuficiente"; return
    import b_forward_score as BF                              # importa DEPOIS da injeção (b_engine _reg fresco)
    t0 = rows[-1]["t"]; fundo_dt = BF.ds(t0)                  # UTC (casa com BF.ep)
    logged = {r.get("fundo_dt") for r in BF.load_log()}
    if fundo_dt in logged:
        out["b"] = f"já pontuado {fundo_dt}"
    else:
        rec = BF.score(fundo_dt)                              # deep gz+store + b_signal + null
        if rec.get("engine"):
            BF.upsert(rec)
            e = rec.get("entry", {})
            out["b"] = f"B ON -> forward log {fundo_dt} entry {e.get('ent')} SL {e.get('sl')} [{rec.get('status')}]"
        else:
            out["b"] = f"off: {rec.get('reason') or rec.get('status')}"
    out["resolved"] = BF.resolve_pending()                   # árbitro forward: resolve OPEN->WIN/LOSS SL-first


def main():
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    out = {"ts": ts, "mode": "DRY"}
    # store-first (barras 15M do bar-store; zero CDP próprio)
    try:
        import store_reader as SR
        if not SR.fresh("15", mult=5):
            out["status"] = "SKIP: store 15M não-fresco (no-op)"; _log(out); print(json.dumps(out)); return
        rows = SR.bars("15")
    except Exception as e:
        out["status"] = f"SKIP: store indisponível ({type(e).__name__})"; _log(out); print(json.dumps(out)); return
    if not rows or len(rows) < 60:
        out["status"] = f"SKIP: 15M insuficiente (n={len(rows) if rows else 0})"; _log(out); print(json.dumps(out)); return
    regime, as_of = read_regime()
    out.update({"regime": regime, "as_of": as_of, "buf_bars": len(rows), "last_bar": iso(rows[-1]["t"])})
    if regime == "RANGE":
        run_B(rows, out)
    elif regime == "BEAR":
        out["route"] = "BEAR -> território do Cp (router dormante; sem duplicar)"
    elif regime == "BULL":
        out["route"] = "BULL -> A1/A2 pendente detetor de fundo (task #35)"
    else:
        out["route"] = f"regime desconhecido ({regime})"
    out["status"] = "OK"
    _log(out); print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
