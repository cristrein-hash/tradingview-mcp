#!/usr/bin/env python3
"""VERIFICAÇÃO INDEPENDENTE do achado central do DA (FAIL): as entries do N96 disparam ANTES da
confirmação do pivô de demanda (conf_i do zz r=6)? Se j < conf_i, o trader live NÃO sabia que aquele
low era 'demanda de perna' no momento do entry — a população foi selecionada por um rally FUTURO de
6 ATR (survivorship). Mede: quantos j<conf_i, mediana de barras de antecedência, e quantos eventos
mantidos imprimem lower-low entre entry e confirmação (assinatura de survivorship: esperado 0).
Output: xau_15m_n83_confirmation_leak_check_result.json."""
import json, sys
import datetime as dt
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import xau_15m_n83_sl_exit_lib as L

# reconstruir eventos COM conf_i (a lib descarta; refazemos o legwalk aqui igual mas guardando ci)
def legwalk_ci(r=6):
    piv=L.zz(r); ev=[]; prevH=prevL=None; lastH=None
    for tp,i,pr,ci in piv:
        if tp=="H": prevH=pr; lastH=pr
        else:
            if prevH is not None and lastH is not None:
                kind="MARKUP" if (prevL is None or pr>prevL) else "CORRECAO"
                ev.append({"i":i,"lo":pr,"conf_i":ci,"kind":kind})
            prevL=pr
    return ev
W0=dt.datetime(2025,8,1).timestamp(); W1=dt.datetime(2026,7,4).timestamp()
ev=[e for e in legwalk_ci(6) if W0<=L.TS[e["i"]]<=W1]
built=[]
for e in ev:
    en=L.build_entry(e)
    if en is None: continue
    if e["kind"]=="MARKUP":
        en["conf_i"]=e["conf_i"]; built.append(en)
assert len(built)==96, f"N={len(built)}"
regmap,cut,fam=L.load_context()
pre=[]; lower_low_after_entry=0
for k,tr in enumerate(built,1):
    tr["trade_id"]=k
    early=tr["conf_i"]-tr["j"]
    if tr["j"]<tr["conf_i"]:
        pre.append(early)
        # survivorship: low abaixo do demand low entre entry e confirmação?
        if min(L.LO[tr["j"]:tr["conf_i"]+1])<tr["lo"]: lower_low_after_entry+=1
n83=[t for t in built if t["trade_id"] not in cut]
pre83=[t["conf_i"]-t["j"] for t in n83 if t["j"]<t["conf_i"]]
pre_s=sorted(pre)
res={"N96":len(built),
     "entries_before_confirmation_n96":len(pre),
     "entries_before_confirmation_n83":len(pre83),
     "bars_early_median":pre_s[len(pre_s)//2] if pre else 0,
     "bars_early_max":pre_s[-1] if pre else 0,
     "kept_events_with_lower_low_entry_to_conf":lower_low_after_entry,
     "interpretation":("se ~todas as entries precedem conf_i e 0 eventos mantidos imprimem lower-low "
        "entre entry e confirmação, a população foi FILTRADA por um rally futuro de 6 ATR = "
        "event-selection lookahead (o preço/SL são causais; a SELEÇÃO do evento não é)"),
     "attribution":"defeito herdado da base APROVADA entry_engine_master_20260707.py; a maquinaria SL/exit deste bloco não introduziu leak (byte-match PASS)"}
res["da_claim_confirmed"]=(res["entries_before_confirmation_n96"]>=90 and lower_low_after_entry==0)
(HERE/"xau_15m_n83_confirmation_leak_check_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))
