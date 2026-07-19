#!/usr/bin/env python3
"""LAYER1 LIVE SERVICE — regime macro 1D (BULL/BEAR/RANGE) causal, servido para router 15M + E0/E2.
Opção A (Cris 2026-07-19): NÃO toca a matemática congelada de macro_structural_v3.build_layer1() (a
aprovação + paridade dos preregs dependem dela). O service só troca a FONTE dos dados por versões
FRESCAS, injetando-as nos globais do módulo em runtime, e valida com um GATE DE PARIDADE (labels nos
dias de dados idênticos têm de bater byte-a-byte ao que o módulo daria sozinho). Se divergir = HARD_STOP,
não escreve. Zero MCP/CDP/Telegram — pura computação sobre ficheiros que o bar-store mantém frescos.

Fonte fresca:
  XAU 1D = REV/raw_1d_ohlc.jsonl (histórico profundo 2014→) + store/bars_1d.jsonl (cauda fresca do
           bar-store; store OVERRIDE em conflito -> corrige a última barra provisória do REV). Só CLOSED.
  DXY 1D = REV/raw_dxy_1d.jsonl (o bar-store já mantém fresco via tab TVC:DXY pinada).
Saída: .layer1_state/current_layer1.json (regime atual do último 1D FECHADO, consumido causal em t+86400)
       + layer1_transitions.jsonl (viradas). Horas humanas = Lisboa. py3.9 stdlib.
CLI: (default) 1 ciclo · --status imprime o estado atual sem recomputar pesado."""
import os, sys, json, time, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
CORE = HERE.parent
REPO = CORE.parents[1]
REV = REPO / "my-strategy/research/revalidation"
STORE = CORE / "bar_store/store"
STATE = HERE / ".layer1_state"; STATE.mkdir(exist_ok=True)
CUR = STATE / "current_layer1.json"
TRANS = STATE / "layer1_transitions.jsonl"
LOG = STATE / "layer1_cycle.log"
LX = ZoneInfo("Europe/Lisbon")
lx = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%Y-%m-%d %H:%M")
NOWT = lambda: int(time.time())


def _jl(f):
    try: return [json.loads(x) for x in Path(f).read_text().splitlines() if x.strip()]
    except Exception: return []


def _log(o):
    o = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(), **o}
    with open(LOG, "a") as fh: fh.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(json.dumps(o, ensure_ascii=False))


def _merge_xau_1d():
    """Histórico profundo REV + cauda fresca do store (store OVERRIDE em conflito). Só barras fechadas."""
    base = {b["t"]: b for b in _jl(REV / "raw_1d_ohlc.jsonl")}
    for b in _jl(STORE / "bars_1d.jsonl"):
        base[b["t"]] = b                                   # store corrige/estende (valor final fechado)
    now = NOWT()
    rows = [base[t] for t in sorted(base) if t + 86400 <= now]  # exclui barra diária em formação
    return rows


def compute_and_write():
    """Computa o regime Layer1 1D (fonte fresca + gate de paridade) e escreve current_layer1.json.
    Chamado pelo REGIME-ENGINE (autoridade única de regime desde 2026-07-19 — consolidação Cris).
    Devolve dict de estado; NUNCA lança (fail-closed -> HARD_STOP não escreve)."""
    sys.path.insert(0, str(REV))
    try:
        import macro_structural_v3 as M
    except Exception as e:
        r = {"status": "HARD_STOP", "err": f"import macro_structural_v3: {str(e)[:80]}"}; _log(r); return r

    # 1) labels BASE (o que o módulo daria sozinho, dados como importados) — para o gate de paridade.
    base_T = list(M.T)
    try:
        base_lab = M.build_layer1()
    except Exception as e:
        r = {"status": "HARD_STOP", "err": f"build_layer1 base: {str(e)[:80]}"}; _log(r); return r
    base_by_t = dict(zip(base_T, base_lab))
    base_last = base_T[-1] if base_T else None            # última barra BASE (pode ser provisória) = excluída da paridade

    # 2) injeta FONTE fresca nos globais (matemática intocada).
    xau = _merge_xau_1d()
    if len(xau) < 400:
        r = {"status": "HARD_STOP", "err": f"XAU 1D fresco insuficiente (n={len(xau)})"}; _log(r); return r
    M.T = [b["t"] for b in xau]; M.O = [b["o"] for b in xau]; M.H = [b["h"] for b in xau]
    M.L = [b["l"] for b in xau]; M.C = [b["c"] for b in xau]; M.N = len(xau)
    dxy = _jl(REV / "raw_dxy_1d.jsonl")
    if len(dxy) < 400:
        r = {"status": "HARD_STOP", "err": f"DXY 1D insuficiente (n={len(dxy)})"}; _log(r); return r
    M.DXY_K = [b["t"] + 86400 for b in dxy]; M.DXY_C = [b["c"] for b in dxy]

    # 3) labels FRESCOS.
    try:
        fresh_lab = M.build_layer1()
    except Exception as e:
        r = {"status": "HARD_STOP", "err": f"build_layer1 fresh: {str(e)[:80]}"}; _log(r); return r
    fresh_by_t = dict(zip(M.T, fresh_lab))

    # 4) GATE DE PARIDADE: nos dias de dados IDÊNTICOS (todos os base exceto a última barra provisória),
    #    o label fresco tem de bater o base. Divergência = a fonte mudou a matemática -> HARD_STOP.
    mism = [t for t in base_T if t != base_last and t in fresh_by_t and base_by_t[t] != fresh_by_t[t]]
    if mism:
        r = {"status": "HARD_STOP", "parity_ok": False, "n_mismatch": len(mism),
             "primeiros": [lx(t) for t in mism[:5]]}; _log(r); return r

    # 5) regime atual = label do último 1D FECHADO.
    regime = fresh_lab[-1]; as_of_t = M.T[-1]
    prev = None
    try: prev = json.loads(CUR.read_text()).get("regime")
    except Exception: pass
    out = {"regime": regime, "as_of_bar_t": as_of_t, "as_of": lx(as_of_t), "n_bars": M.N,
           "parity_ok": True, "n_parity_checked": sum(1 for t in base_T if t != base_last and t in fresh_by_t),
           "source": "layer1_1d macro_structural_v3.build_layer1 (REV hist + store tail + DXY store)",
           "built_ts": NOWT()}
    tmp = CUR.with_suffix(".json.tmp"); tmp.write_text(json.dumps(out, ensure_ascii=False)); os.replace(tmp, CUR)
    if prev is not None and prev != regime:
        with open(TRANS, "a") as fh:
            fh.write(json.dumps({"ts": dt.datetime.now(dt.timezone.utc).isoformat(),
                                 "from": prev, "to": regime, "as_of_bar_t": as_of_t, "as_of": lx(as_of_t)}) + "\n")
    r = {"status": "OK", "regime": regime, "as_of": lx(as_of_t), "n": M.N,
         "parity_checked": out["n_parity_checked"], "transition": (f"{prev}->{regime}" if prev != regime else None)}
    _log(r); return r


def main():
    if "--status" in sys.argv:
        try:
            d = json.loads(CUR.read_text())
            print(f"  regime={d.get('regime')} as_of={d.get('as_of')} n={d.get('n_bars')} parity={d.get('parity_ok')} built={lx(d.get('built_ts',0))}")
        except Exception:
            print("  (sem current_layer1.json ainda)")
        return 0
    r = compute_and_write()
    return 0 if r.get("status") == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
