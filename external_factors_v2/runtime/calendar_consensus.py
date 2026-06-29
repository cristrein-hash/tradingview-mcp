#!/usr/bin/env python3
"""CONSENSO DE CALENDÁRIO -> DIREÇÃO. Registra o próximo evento de alto impacto com consenso (fonte canônica de
calendário, ex. TradingEconomics) e aplica a REGRA DE DIREÇÃO: surpresa = actual - consenso. NFP: surpresa>0
(jobs fortes) -> USD↑ -> ouro BEARISH; surpresa<0 -> ouro BULLISH. Pré-release: actual=None -> bias=pending.
⚠️ Datas/consenso vêm da FONTE REAL (não do gerador determinístico — que erra em shift de feriado, ex. NFP qui 02-jul).
Backtest da direção via proxy = sinal fraco mas correto-sinalizado (4H corr−0,24, 56%). Consenso real afia."""
import json,datetime as dt
from pathlib import Path
H=Path(__file__).parent.parent; SNAP=H/"snapshots"; SNAP.mkdir(exist_ok=True)
# fonte: TradingEconomics (WebFetch 2026-06-29). Em produção: refresh via calendar agent/MCP.
UPCOMING=[{
  "event":"Nonfarm Payrolls (NFP)","release_date":"2026-07-02","release_time_utc":"12:30",
  "release_ts":int(dt.datetime(2026,7,2,12,30,tzinfo=dt.timezone.utc).timestamp()),
  "consensus_k":110,"previous_k":172,"last_actual_k":172,"actual_k":None,
  "impact":"HIGH","layer":"A","driver":"USD->GOLD","source":"TradingEconomics (live fetch 2026-06-29)",
  "note":"feriado 04/jul antecipou p/ QUINTA 02-jul (gerador 1ª-sexta erraria p/ 03-jul) — usar fonte real"
}]
def direction(ev):
    a=ev.get("actual_k"); c=ev.get("consensus_k")
    if a is None or c is None: return {"bias":"pending","rule":"surpresa=actual-consenso; >0=ouro bearish, <0=bullish","awaiting":"actual no release"}
    surp=a-c
    return {"bias":"bearish" if surp>0 else ("bullish" if surp<0 else "neutral"),"surprise_k":surp,
            "rule":"NFP forte(actual>consenso)->USD↑->ouro↓","confidence_backtest":"fraco-correto (proxy 4H corr−0,24/56%); consenso real afia"}
out=[]
for ev in UPCOMING:
    ev2=dict(ev); ev2["direction"]=direction(ev); out.append(ev2)
state={"_meta":{"built":"2026-06-29","purpose":"consenso->direção (Camada A)"},"upcoming_high_impact":out}
(SNAP/"calendar_consensus.json").write_text(json.dumps(state,indent=1,ensure_ascii=False))
print(json.dumps(state,indent=1,ensure_ascii=False))
print(f"\n-> {SNAP/'calendar_consensus.json'}")
