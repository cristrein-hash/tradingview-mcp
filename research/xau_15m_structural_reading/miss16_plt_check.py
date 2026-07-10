#!/usr/bin/env python3
"""MISS #16 × DEMANDA PLT (ordem Cris 2026-07-10). SEM métricas/estatísticas (proibidas) —
verificação ESTRUTURAL causal de um episódio único:
 (1) ler via MCP o retângulo 'DEMANDA PLT' desenhado pelo Cris (coordenadas exatas);
 (2) do RAW (F0): o degrau anterior (topo da pausa pré-rompimento) estava FORMADO e ROMPIDO
     ANTES do fundo #16 (2025-10-15 09:00)? (causalidade: a zona era conhecível antes do toque)
 (3) o low do #16 toca o retângulo dele?
 (4) diagnóstico A2: existia TOP region r=4 nessa área? foi convertida antes do #16? onde estava a
     banda vs o retângulo dele? (porquê do MISS)
Sem entry, sem backtest, sem tuning. Factos de datas/preços apenas."""
import json, sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"alert-bridge"))
sys.path.insert(0, str(REPO/"research/xau_15m_structural_leg_engine"))
from draw_xau_4h_trades import MCPClient
from f1_structural_leg_machine import Data

M16_T = int(dt.datetime(2025, 10, 15, 9, 0, tzinfo=dt.timezone.utc).timestamp())
M16_PX = 4162.4

def main():
    out = {"miss16": {"utc": "2025-10-15 09:00", "px": M16_PX}}
    # (1) retângulo do Cris via MCP
    c = MCPClient(); c.start()
    try:
        st = c.call_tool("chart_get_state")
        out["chart"] = {"symbol": st.get("symbol"), "tf": str(st.get("resolution"))}
        dl = c.call_tool("draw_list")
        shapes = dl.get("drawings") or dl.get("shapes") or []
        rects = [s for s in shapes if "rect" in str(s.get("name", s.get("type", ""))).lower()]
        out["rects_found"] = len(rects)
        out["rects"] = rects[:6]
    finally:
        try: c.stop()
        except Exception: pass
    # (2)(3) estrutura do degrau anterior no RAW
    D = Data()
    i16 = bisect.bisect_right(D.TS, M16_T)-1
    lo16 = D.L[i16]
    # janela estrutural: 13-15 out (a pausa pré-rompimento visível no print)
    t_a = int(dt.datetime(2025, 10, 13, 0, 0, tzinfo=dt.timezone.utc).timestamp())
    t_b = int(dt.datetime(2025, 10, 15, 9, 0, tzinfo=dt.timezone.utc).timestamp())
    ia = bisect.bisect_left(D.TS, t_a); ib = bisect.bisect_right(D.TS, t_b)-1
    # descrever o caminho: máximo da pausa de 14-out (antes do push de 15-out) e o rompimento
    t_p0 = int(dt.datetime(2025, 10, 14, 0, 0, tzinfo=dt.timezone.utc).timestamp())
    t_p1 = int(dt.datetime(2025, 10, 14, 23, 59, tzinfo=dt.timezone.utc).timestamp())
    ip0 = bisect.bisect_left(D.TS, t_p0); ip1 = bisect.bisect_right(D.TS, t_p1)-1
    pausa_top = max(D.H[ip0:ip1+1]); pausa_top_t = D.TS[ip0+max(range(ip1+1-ip0), key=lambda k: D.H[ip0+k])]
    # primeiro close acima do topo da pausa (rompimento) antes do #16?
    brk = None
    for k in range(ip1+1, ib+1):
        if D.C[k] > pausa_top: brk = D.TS[k]; break
    # low REAL do pullback (marca -> +27h), correção DA: lo16 da barra 09:00 não é o low do pullback
    t1 = M16_T+27*3600
    a2_, b2_ = bisect.bisect_left(D.TS, M16_T), bisect.bisect_right(D.TS, t1)-1
    kmin = a2_+min(range(b2_+1-a2_), key=lambda q: D.L[a2_+q])
    low_pullback = D.L[kmin]
    out["degrau_anterior"] = {
        "pausa_top_px": round(pausa_top, 1),
        "pausa_top_utc": dt.datetime.utcfromtimestamp(pausa_top_t).strftime("%Y-%m-%d %H:%M"),
        "rompido_antes_do_16": (dt.datetime.utcfromtimestamp(brk).strftime("%Y-%m-%d %H:%M") if brk else None),
        "low_barra_da_marca": round(lo16, 1),
        "low_REAL_pullback": round(low_pullback, 1),
        "low_REAL_utc": dt.datetime.utcfromtimestamp(D.TS[kmin]).strftime("%Y-%m-%d %H:%M")}
    lo16 = low_pullback
    # (4) A2 r=4: TOP regions com extremo entre 12-15 out; convertidas antes do #16?
    tops = []
    inval = {}
    for l in open(REPO/"research/xau_15m_structural_leg_engine/results/a2_events_r4.jsonl"):
        e = json.loads(l)
        if e["event"] == "converted_support": inval.setdefault(e["region_id"], {})["conv"] = e["known_at"]
        if e["event"] == "invalidated": inval.setdefault(e["region_id"], {})["inv"] = e["known_at"]
    for l in open(REPO/"research/xau_15m_structural_leg_engine/results/a2_regions_r4.jsonl"):
        r = json.loads(l)
        if r["kind"] == "TOP" and t_a-5*86400 <= r["extreme_t"] <= t_b:
            ev = inval.get(r["region_id"], {})
            tops.append({"id": r["region_id"], "extreme_px": r["extreme_px"],
                         "extreme_utc": dt.datetime.utcfromtimestamp(r["extreme_t"]).strftime("%m-%d %H:%M"),
                         "band": [r["price_low"], r["price_high"]],
                         "known_utc": dt.datetime.utcfromtimestamp(r["known_at"]).strftime("%m-%d %H:%M"),
                         "converted_utc": (dt.datetime.utcfromtimestamp(ev["conv"]).strftime("%m-%d %H:%M") if "conv" in ev else None),
                         "conv_antes_16": ("conv" in ev and ev["conv"] < M16_T),
                         "invalidated_utc": (dt.datetime.utcfromtimestamp(ev["inv"]).strftime("%m-%d %H:%M") if "inv" in ev else None),
                         "inv_antes_16": ("inv" in ev and ev["inv"] < M16_T),
                         "banda_contem_low16": r["price_low"] <= lo16 <= r["price_high"]})
    out["a2_tops_na_area"] = tops
    (HERE/"results/miss16_plt_check.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

def retest_facts():
    """Facto adicional: onde foi o low REAL do pullback pós-marca e que bandas tocou (sem métricas)."""
    D = Data()
    t0 = int(dt.datetime(2025, 10, 15, 9, 0, tzinfo=dt.timezone.utc).timestamp())
    t1 = int(dt.datetime(2025, 10, 16, 12, 0, tzinfo=dt.timezone.utc).timestamp())
    a = bisect.bisect_left(D.TS, t0); b = bisect.bisect_right(D.TS, t1)-1
    k = a+min(range(b+1-a), key=lambda q: D.L[a+q])
    print("low real do pullback:", round(D.L[k], 1), "em",
          dt.datetime.utcfromtimestamp(D.TS[k]).strftime("%Y-%m-%d %H:%M"))
    print("toca T00942 [4171.8, 4180.9]?", 4171.83 <= D.L[k] <= 4180.85 or D.L[k] <= 4180.85)
    print("dentro do retângulo aprox do Cris [~4156, ~4172]?", D.L[k] <= 4172)

if "RETEST" in str(sys.argv):
    retest_facts()
