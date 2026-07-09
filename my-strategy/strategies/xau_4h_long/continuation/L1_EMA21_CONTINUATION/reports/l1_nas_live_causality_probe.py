#!/usr/bin/env python3
"""L1_NAS_LIVE_CAUSALITY_GATE — probe report-only (NÃO produção, NÃO Telegram, NÃO altera chart).
Parte 1 (offline, sempre): valida a consistência do ledger real l1_feature_history.jsonl
  (append-only NAS por barra fechada) — prova que o ledger path captura NAS(i-1) causalmente.
Parte 2 (best-effort read-only MCP): confirma se data_get_study_values_at_bar devolve série
  timestamped per-bar p/ NAS (=> history path consegue i-1 direto). SÓ leitura; sem draw/screenshot/
  symbol-change. Se TV down OU chart != XAU/NAS => inconclusivo (não falha).
Output: l1_nas_live_causality_probe_result.json."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent
LEDGER=L1/".runtime_state/l1_feature_history.jsonl"
BAR=14400  # 4H em segundos
out={"part1_ledger":{}, "part2_mcp_readonly":{}}

# ---------- Parte 1: consistência do ledger (offline) ----------
p1={}
if not LEDGER.exists():
    p1={"status":"ABSENT","note":"ledger não existe"}
else:
    rows=[json.loads(l) for l in open(LEDGER) if l.strip()]
    bts=[r.get("bar_time") for r in rows]
    p1["n_entries"]=len(rows)
    p1["distinct_bar_times"]=len(set(bts))
    p1["dedup_ok"]=(len(bts)==len(set(bts)))
    p1["monotonic_increasing"]=all(bts[k]<bts[k+1] for k in range(len(bts)-1))
    # spacings entre barras consecutivas (múltiplos de 4H? gaps de sessão/fim-de-semana permitidos)
    gaps=[bts[k+1]-bts[k] for k in range(len(bts)-1)]
    p1["gap_all_multiple_of_4H"]=all(g%BAR==0 for g in gaps)
    p1["gap_min_bars"]=min(g//BAR for g in gaps) if gaps else None
    p1["gap_max_bars"]=max(g//BAR for g in gaps) if gaps else None
    # persisted_at DEPOIS do fecho da barra? (bar_time = abertura; fecho = bar_time+4H; persist deve ser >= fecho)
    late=[]
    for r in rows:
        bt=r.get("bar_time"); pa=r.get("persisted_at")
        if bt and pa:
            pat=datetime.fromisoformat(pa).timestamp()
            if pat < bt+BAR: late.append({"bar_time":bt,"persisted_at":pa,"delta_s":round(pat-(bt+BAR))})
    p1["persist_after_bar_close_ok"]=(len(late)==0)
    p1["persist_violations"]=late[:5]
    p1["nas_values_are_real_floats"]=all(isinstance(r.get("nas_dist"),(int,float)) for r in rows)
    p1["first_bar_iso"]=datetime.utcfromtimestamp(bts[0]).isoformat() if bts else None
    p1["last_bar_iso"]=datetime.utcfromtimestamp(bts[-1]).isoformat() if bts else None
    p1["sample_head"]=rows[0] if rows else None
    p1["sample_tail"]=rows[-1] if rows else None
    p1["status"]="CONSISTENT" if (p1["dedup_ok"] and p1["monotonic_increasing"]
                                  and p1["gap_all_multiple_of_4H"] and p1["persist_after_bar_close_ok"]
                                  and p1["nas_values_are_real_floats"]) else "INCONSISTENT"
out["part1_ledger"]=p1

# ---------- Parte 2: read-only MCP (best-effort) ----------
p2={"attempted":True}
try:
    sys.path.insert(0,str(L1.parents[4]/"my-strategy/core"))
    from tv_read_adapter import _MCP
    c=_MCP(); c.start()
    try:
        st=c.call("chart_get_state")
        sym=(st or {}).get("symbol"); tf=(st or {}).get("resolution") or (st or {}).get("timeframe")
        p2["chart_symbol"]=sym; p2["chart_tf"]=tf
        r=c.call("data_get_study_values_at_bar",{"study_filter":"NAS","count":8})
        studies=(r or {}).get("studies") or []
        nas=None
        for s in studies:
            if "NAS" in (s.get("name") or ""): nas=s; break
        if nas:
            bars=nas.get("bars") or []
            times=[b.get("time") for b in bars]
            # extrai o campo de distância
            def dist(b):
                v=b.get("values") or {}
                for k in v:
                    if "DISTANCE" in k.upper() or "nas_dist" in k.lower(): return v[k]
                return None
            series=[{"time":b.get("time"),"nas_dist":dist(b)} for b in bars]
            p2["returns_per_bar_series"]=len(bars)>1
            p2["distinct_timestamps"]=len(set(times))==len(times) and len(times)>1
            p2["timestamps_are_4H_spaced"]=all((times[k+1]-times[k])%BAR==0 for k in range(len(times)-1)) if len(times)>1 else None
            p2["has_dist_field"]=all(x["nas_dist"] is not None for x in series)
            p2["series_sample"]=series[-3:]
            p2["can_get_i_minus_1_direct"]=bool(len(bars)>1 and len(set(times))==len(times))
            p2["status"]="HISTORY_SERIES_CONFIRMED" if p2["can_get_i_minus_1_direct"] else "SERIES_INCOMPLETE"
        else:
            p2["status"]="NO_NAS_ON_CHART"; p2["note"]="chart não tem NAS (símbolo/estudo diferente) — inconclusivo, não falha"
    finally:
        try: c.stop()
        except Exception: pass
except Exception as e:
    p2["status"]="MCP_UNAVAILABLE"; p2["error"]=str(e)[:200]
    p2["note"]="TV/CDP indisponível — history path não verificado ao vivo; ledger path (Parte 1) é a evidência primária"
out["part2_mcp_readonly"]=p2

(HERE/"l1_nas_live_causality_probe_result.json").write_text(json.dumps(out,indent=2,ensure_ascii=False,default=str))
print(json.dumps(out,indent=2,ensure_ascii=False,default=str))
