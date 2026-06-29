#!/usr/bin/env python3
"""FORWARD-SCORING das TEORIAS (scaffold honesto).
META (Cris): agregar teorias do núcleo credível e deixar a REALIDADE dar nota progressivamente ao longo da
produção -> ML/validação REAL (não opinião-como-feature). Método: cada teoria do ledger recebe (1) um CLAIM
falsificável + direção prevista p/ ouro + horizonte (extração = passo LLM Tier-2, fleet), depois (2) o scorer
compara a direção prevista com o RETORNO REAL do ouro no horizonte -> hit/miss -> atualiza credibility-weight
por FONTE (hit-rate + Brier). Forward genuíno no tempo (NÃO OOS histórico fitado = permitido pelo cânone).
⚠️ HOJE: claims ainda não extraídos e outcomes ainda não venceram horizonte -> reporta 'acumulando'. Honesto:
só fica significativo após semanas/meses de produção. Determinístico, py3.9. Lê snapshots/theory_ledger.jsonl."""
import json,datetime as dt
from pathlib import Path
H=Path(__file__).parent.parent; SNAP=H/"snapshots"
LEDGER=SNAP/"theory_ledger.jsonl"; NOWT=int(dt.datetime.now(dt.timezone.utc).timestamp())
def load():
    if not LEDGER.exists(): return []
    out=[]
    for ln in LEDGER.read_text().splitlines():
        try: out.append(json.loads(ln))
        except Exception: pass
    return out
def main():
    led=load()
    by_src={}
    for e in led: by_src.setdefault(e["source_id"],{"total":0,"with_claim":0,"scored":0,"hits":0,"briers":[]})
    for e in led:
        s=by_src[e["source_id"]]; s["total"]+=1
        if e.get("claim"): s["with_claim"]+=1
        if e.get("scored"):
            s["scored"]+=1
            if e.get("outcome")=="hit": s["hits"]+=1
            if isinstance(e.get("brier"),(int,float)): s["briers"].append(e["brier"])
    board=[]
    for sid,s in by_src.items():
        hit_rate=round(s["hits"]/s["scored"],3) if s["scored"] else None
        brier=round(sum(s["briers"])/len(s["briers"]),3) if s["briers"] else None
        # credibility weight = começa 0.5 (neutro), move com hit-rate quando houver amostra (>=10 scored)
        weight=0.5 if not s["scored"] or s["scored"]<10 else round(hit_rate,3)
        board.append({"source_id":sid,"theories_total":s["total"],"with_claim":s["with_claim"],
                      "scored":s["scored"],"hit_rate":hit_rate,"brier":brier,"credibility_weight":weight,
                      "status":"acumulando" if s["scored"]<10 else "ativo"})
    board.sort(key=lambda x:(x["scored"],x["theories_total"]),reverse=True)
    state={"_meta":{"built_ts":NOWT,"method":"forward hit-rate + Brier por fonte; weight ativa em scored>=10",
            "honest_note":"claims ainda não extraídos (passo LLM) e horizontes não vencidos -> fase ACUMULANDO; significativo só após semanas/meses de produção"},
           "scoreboard":board,"ledger_total":len(led),
           "scored_total":sum(s["scored"] for s in by_src.values()),
           "with_claim_total":sum(s["with_claim"] for s in by_src.values())}
    (SNAP/"theory_scoreboard.json").write_text(json.dumps(state,indent=1,ensure_ascii=False))
    print(f"THEORY FORWARD-SCORING (scaffold): ledger {len(led)} | claims {state['with_claim_total']} | scored {state['scored_total']}")
    for b in board: print(f"  {b['source_id']:14} teorias={b['theories_total']:3} claims={b['with_claim']:3} scored={b['scored']:3} hit={b['hit_rate']} weight={b['credibility_weight']} [{b['status']}]")
    print("  -> fase ACUMULANDO (precisa claims+horizontes vencidos); honesto. " )
    print(f"-> {SNAP/'theory_scoreboard.json'}")
if __name__=="__main__": main()
