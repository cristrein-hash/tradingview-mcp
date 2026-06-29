#!/usr/bin/env python3
"""FORWARD-SCORING das TEORIAS (scorer REAL).
A realidade dá nota a cada claim: ancora no published_ts (data em que o analista falou — as-of, sem look-ahead),
mede o retorno REAL do ouro (gold_price_history GCUSD) no horizonte e marca hit/miss + Brier. Atualiza
credibility-weight por FONTE (weight = hit_rate quando scored>=10; senão 0.5 neutro). Calcula um CONSENSO
ponderado (contexto, NUNCA gate — Fase 4). Forward genuíno no tempo (NÃO OOS fitado: a previsão precede o preço).
Determinístico, py3.9. Lê theory_ledger.jsonl + gold_price_history.jsonl -> theory_scoreboard.json."""
import json,datetime as dt
from pathlib import Path
H=Path(__file__).parent.parent; SNAP=H/"snapshots"
LEDGER=SNAP/"theory_ledger.jsonl"; HIST=SNAP/"gold_price_history.jsonl"
NOWT=int(dt.datetime.now(dt.timezone.utc).timestamp()); BAND=0.005  # ±0.5% banda do neutral
def load_jsonl(p):
    if not p.exists(): return []
    out=[]
    for ln in p.read_text().splitlines():
        try: out.append(json.loads(ln))
        except Exception: pass
    return out
def price_at(hist,ts,tol=8*86400):
    """preço mais próximo no tempo (EOD diário); None se nada dentro de tol."""
    best=None;bd=None
    for h in hist:
        d=abs(h["ts"]-ts)
        if bd is None or d<bd: bd=d;best=h
    return best["price"] if (best and bd is not None and bd<=tol) else None
def main():
    rows=load_jsonl(LEDGER); hist=load_jsonl(HIST); changed=0
    for r in rows:
        if r.get("scored") or not r.get("gold_relevant"): continue
        d=r.get("predicted_gold_dir")
        if d not in ("bullish","bearish","neutral"): continue
        hz=r.get("horizon_days")
        if not isinstance(hz,(int,float)) or hz<=0: hz=90; r["horizon_days"]=90   # default quando vago/null (persiste p/ auditoria)
        anchor=r.get("published_ts") or r.get("collected_ts")
        if not anchor: continue
        end=int(anchor+hz*86400)
        if end>NOWT: continue                      # horizonte não venceu -> pendente
        p0=price_at(hist,anchor); p1=price_at(hist,end)
        if p0 is None or p1 is None: continue       # sem preço cobrindo -> não pontua
        ret=(p1-p0)/p0; up=ret>0
        hit = (d=="bullish" and ret>BAND) or (d=="bearish" and ret<-BAND) or (d=="neutral" and abs(ret)<=BAND)
        prob_up=1.0 if d=="bullish" else (0.0 if d=="bearish" else 0.5)
        r["scored"]=True; r["outcome"]="hit" if hit else "miss"; r["ret"]=round(ret,4)
        r["brier"]=round((prob_up-(1.0 if up else 0.0))**2,3); r["outcome_ts"]=NOWT
        r["p_anchor"]=p0; r["p_horizon"]=p1; changed+=1
    if changed:
        with open(LEDGER,"w") as fh:
            for r in rows: fh.write(json.dumps(r,ensure_ascii=False)+"\n")
    # scoreboard por fonte
    by={}
    for r in rows:
        s=by.setdefault(r["source_id"],{"total":0,"extracted":0,"claims":0,"scored":0,"hits":0,"briers":[]})
        s["total"]+=1
        if r.get("extracted"): s["extracted"]+=1
        if r.get("gold_relevant"): s["claims"]+=1
        if r.get("scored"):
            s["scored"]+=1
            if r.get("outcome")=="hit": s["hits"]+=1
            if isinstance(r.get("brier"),(int,float)): s["briers"].append(r["brier"])
    board=[]
    for sid,s in by.items():
        hr=round(s["hits"]/s["scored"],3) if s["scored"] else None
        br=round(sum(s["briers"])/len(s["briers"]),3) if s["briers"] else None
        weight=round(hr,3) if (s["scored"]>=10 and hr is not None) else 0.5
        board.append({"source_id":sid,"theories":s["total"],"claims":s["claims"],"scored":s["scored"],
                      "hit_rate":hr,"brier":br,"credibility_weight":weight,
                      "status":"ativo" if s["scored"]>=10 else "acumulando"})
    board.sort(key=lambda x:(x["scored"],x["claims"]),reverse=True)
    wmap={b["source_id"]:b["credibility_weight"] for b in board}
    # CONSENSO ponderado (contexto, NUNCA gate) — claims atuais bull/bear publicados ≤60d
    num=den=0;n=0
    for r in rows:
        if not r.get("gold_relevant"): continue
        d=r.get("predicted_gold_dir")
        if d not in ("bullish","bearish"): continue
        if (NOWT-(r.get("published_ts") or r.get("collected_ts") or NOWT))>60*86400: continue
        w=wmap.get(r["source_id"],0.5); num+=w*(1 if d=="bullish" else -1); den+=w; n+=1
    net=round(num/den,3) if den else 0.0
    consensus="bullish-lean" if net>0.2 else ("bearish-lean" if net<-0.2 else "mixed/neutral")
    state={"_meta":{"built_ts":NOWT,"method":"hit-rate+Brier por fonte (ancora published_ts, preço GCUSD real no horizonte); weight ativa scored>=10",
            "gate":"CONTEXTO/flag — consenso NUNCA dispara trade (Fase 4: sign-off+default-deny)"},
           "scoreboard":board,"ledger_total":len(rows),
           "scored_total":sum(b["scored"] for b in board),"claims_total":sum(b["claims"] for b in board),
           "price_history_days":len(hist),
           "theory_consensus":{"net_weighted":net,"label":consensus,"n_claims":n,"note":"ponderado por credibility_weight; contexto, não-gate"}}
    (SNAP/"theory_scoreboard.json").write_text(json.dumps(state,indent=1,ensure_ascii=False))
    print(f"THEORY SCORING: ledger {len(rows)} | claims {state['claims_total']} | scored {state['scored_total']} (+{changed} agora) | hist {len(hist)}d")
    for b in board: print(f"  {b['source_id']:14} claims={b['claims']:3} scored={b['scored']:3} hit={b['hit_rate']} brier={b['brier']} weight={b['credibility_weight']} [{b['status']}]")
    print(f"  CONSENSO ponderado: {consensus} (net {net}, n={n}) — CONTEXTO, nunca gate")
    print(f"-> {SNAP/'theory_scoreboard.json'}")
if __name__=="__main__": main()
