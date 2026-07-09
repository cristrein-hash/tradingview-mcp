#!/usr/bin/env python3
"""FASE 2 — chart-state fix mínimo do NAS (autorizado: tornar estudo visível/computado).
NÃO plota trades, NÃO draw, NÃO screenshot, NÃO muda layout além do estudo NAS, NÃO liga cycle/Telegram.
Passos: confirma XAU 4H -> localiza NAS TOP BOTTOM DETECTOR -> se visible:false, setVisible(true) ->
re-lê data_get_study_values_at_bar (série por barra) + data-window. Salva antes/depois.
Output: l1_nas_chart_state_fix_probe_result.json."""
import sys, json
from pathlib import Path
HERE=Path(__file__).resolve().parent; L1=HERE.parent
sys.path.insert(0,str(L1.parents[4]/"my-strategy/core"))
from tv_read_adapter import _MCP
BAR=14400
def find_nas(state):
    """Procura o estudo NAS na lista de indicadores do chart_get_state."""
    inds = state.get("indicators") or state.get("studies") or []
    for it in inds:
        nm = (it.get("name") or it.get("title") or "")
        if "NAS" in nm.upper():
            return it.get("id") or it.get("entity_id") or it.get("entityId"), nm
    return None, None
def series_for(c, filt):
    r=c.call("data_get_study_values_at_bar",{"study_filter":filt,"count":8})
    studies=(r or {}).get("studies") or []
    out=[]
    for s in studies:
        bars=s.get("bars") or []
        def dist(b):
            v=b.get("values") or {}
            for k in v:
                if "DISTANCE" in k.upper(): return v[k]
            return None
        out.append({"name":s.get("name"),"last_index":s.get("last_index"),"n_bars":len(bars),
                    "sample":[{"time":b.get("time"),"dist":dist(b),"values_keys":list((b.get("values") or {}).keys())} for b in bars[-3:]]})
    return out
res={"phase":"chart_state_fix"}
c=_MCP(); c.start()
try:
    st=c.call("chart_get_state")
    sym=(st or {}).get("symbol"); tf=(st or {}).get("resolution") or (st or {}).get("timeframe")
    res["chart_symbol"]=sym; res["chart_tf"]=tf
    res["is_xau_4h"]=(sym=="PEPPERSTONE:XAUUSD" and str(tf)=="240")
    nas_id,nas_name=find_nas(st or {})
    res["nas_entity_from_state"]=nas_id; res["nas_name_from_state"]=nas_name
    # fallback: entity conhecido do diagnóstico
    if not nas_id: nas_id="pkqE7L"
    res["nas_entity_used"]=nas_id
    # visibilidade ANTES
    di=c.call("data_get_indicator",{"entity_id":nas_id})
    res["visible_before"]=(di or {}).get("visible")
    res["series_before"]=series_for(c,"NAS")
    # AÇÃO: tornar visível se estava oculto
    if res["visible_before"] is False:
        tg=c.call("indicator_toggle_visibility",{"entity_id":nas_id,"visible":True})
        res["toggle_result"]=tg
    else:
        res["toggle_result"]="skip (já visível ou visible desconhecido)"
    # re-ler DEPOIS
    di2=c.call("data_get_indicator",{"entity_id":nas_id})
    res["visible_after"]=(di2 or {}).get("visible")
    res["series_after"]=series_for(c,"NAS")
    res["rsi_control"]=series_for(c,"Relative Strength")
    # data-window depois
    sv=c.call("data_get_study_values")
    txt=json.dumps(sv)
    res["nas_in_datawindow_after"]=("NAS" in txt); res["distance_in_datawindow_after"]=("DISTANCE" in txt.upper())
    # veredito da fase
    sa=res["series_after"]
    nas_ok=any(("NAS" in (s.get("name") or "").upper()) and s.get("n_bars",0)>1 and
               any(x.get("dist") is not None for x in s.get("sample",[])) for s in sa)
    res["phase_pass"]=bool(nas_ok)
    ts_ok=False
    for s in sa:
        if "NAS" in (s.get("name") or "").upper():
            times=[x.get("time") for x in s.get("sample",[]) if x.get("time")]
            ts_ok = len(times)>=2 and len(set(times))==len(times)
    res["timestamps_ok"]=ts_ok
finally:
    try: c.stop()
    except Exception: pass
(HERE/"l1_nas_chart_state_fix_probe_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False,default=str))
print(json.dumps(res,indent=2,ensure_ascii=False,default=str))
