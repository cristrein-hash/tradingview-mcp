#!/usr/bin/env python3
"""ENTRY ROUTER 15M — ciclo LIVE em modo DRY (Cris 2026-07-19). Roteia, por REGIME MACRO (autoridade
única = Layer1 1D, current_layer1.json escrito pelo regime-engine), qual camada de entry é ELEGÍVEL:
  BEAR  -> território do Cp (já live, alert-only) — o router NÃO duplica, só regista.
  RANGE -> engine de B v1.1 (b_signal) — camada RANGE aprovada in-sample; DRY: deteta+loga, 0 Telegram.
  BULL  -> A1/A2 (pullback) — SEM detetor de fundo automático ainda (task #35) -> só regista pendência.
Roteamento (elegibilidade por contexto), NÃO hard-gate/veto. Store-first (bar-store, zero CDP próprio).
Fail-closed. py3.9 stdlib. SEM Telegram nesta versão (dry puro; forward-ledger). Go-live do B por camada
exige depois: montagem de 15M PROFUNDO (banda desde o onset do range) + paridade vs in-sample + prereg.

CAVEAT DECLARADO: a banda causal do B precisa do 15M desde o onset do range; o store retém 30 dias. Se o
range for mais antigo, a banda fica truncada -> flag 'band_truncated' no ledger. Dormente enquanto BEAR."""
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
LEDGER = STATE / "router_ledger.jsonl"
LOG = STATE / "router_cycle.log"
BAR_S = 900
FRESH_BARS = 2
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
iso = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%Y-%m-%d %H:%M")


def _log(o):
    with open(LOG, "a") as fh: fh.write(json.dumps(o, ensure_ascii=False) + "\n")


def _jl(f):
    try: return [json.loads(x) for x in Path(f).read_text().splitlines() if x.strip()]
    except Exception: return []


def read_regime():
    try:
        d = json.loads(LAYER1.read_text())
        return d.get("regime"), d.get("as_of")
    except Exception:
        return None, None


def build_S(rows):
    """Constrói o substrato S={T,O,H,L,C,EMA,ATR,N} do store 15M — MESMA matemática do load_series
    (EMA k=2/22, ATR14 causais), para o b_signal ler byte-consistente com o in-sample."""
    T = [r["t"] for r in rows]; O = [r["o"] for r in rows]; H = [r["h"] for r in rows]
    L = [r["l"] for r in rows]; C = [r["c"] for r in rows]; N = len(T)
    EMA = [None]*N; ATR = [None]*N; ema = None; kE = 2/22; trs = []
    for i in range(N):
        ema = C[i] if ema is None else C[i]*kE+ema*(1-kE); EMA[i] = ema
        if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
        ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
    return dict(T=T, O=O, H=H, L=L, C=C, EMA=EMA, ATR=ATR, N=N)


def _inject_fresh_macro():
    """Injeta 1D/DXY frescos nos globais de macro_structural_v3 ANTES de importar o b_engine (que computa
    _reg no import) — assim o gate/banda do B leem a AUTORIDADE fresca (Conexão 3). Matemática intocada."""
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


def run_B(S, out):
    """Ramo RANGE: engine de B v1.1 sobre o último 15M fechado. DRY: regista candidato ON no ledger."""
    if not _inject_fresh_macro():
        out["b"] = "SKIP: macro fresco insuficiente"; return
    import b_engine_v1 as BE                                  # importa DEPOIS da injeção (computa _reg fresco)
    last_t = S["T"][-1]
    r = BE.b_signal(last_t, S)
    if not r.get("engine"):
        out["b"] = f"off: {r.get('reason')}"; return
    e = r["entry"]; etime = S["T"][e["ei"]]
    onset = BE._onset(last_t)
    truncated = bool(onset is not None and onset < S["T"][0])   # banda precisa 15M desde o onset
    fresh = (last_t - etime) <= FRESH_BARS * BAR_S
    key = f"B:{etime}"
    if key in {r0.get("key") for r0 in _jl(LEDGER)}:
        out["b"] = f"ON (já no ledger) {iso(etime)}"; return
    rec = {"key": key, "layer": "B_range", "regime": "RANGE", "fresh": fresh, "band_truncated": truncated,
           "entry": e["ent"], "sl": e["sl"], "tgt": e["tgt"], "R": e["R"], "pos_pct": r.get("pos"),
           "band": r.get("band"), "spring": r.get("spring"), "entry_bar": iso(etime),
           "detected_ts": iso(int(time.time())), "outcome": "OPEN", "mode": "DRY"}
    with open(LEDGER, "a") as fh: fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    out["b"] = f"ON->ledger {iso(etime)} entry {e['ent']} SL {e['sl']} 3R {e['tgt']}" + (" [band_truncated]" if truncated else "")


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
    S = build_S(rows)
    regime, as_of = read_regime()
    out.update({"regime": regime, "as_of": as_of, "buf_bars": S["N"], "last_bar": iso(S["T"][-1])})
    if regime == "RANGE":
        run_B(S, out)
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
