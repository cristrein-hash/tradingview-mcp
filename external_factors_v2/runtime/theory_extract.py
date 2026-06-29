#!/usr/bin/env python3
"""EXTRAÇÃO DE CLAIMS (skill theory-extractor via `claude -p`, dentro do Max — sem API key).
Para cada item do theory_ledger ainda não extraído, gera afirmação FALSIFICÁVEL (direção+horizonte+claim),
labels-only, e grava de volta no ledger. Cap por ciclo (poupa cota Max). Sem `claude` -> no-op honesto.
Determinístico no I/O; py3.9. Roda no run_cycle entre theory_sources e theory_score."""
import json,os,subprocess,shutil
from pathlib import Path
H=Path(__file__).parent.parent; SNAP=H/"snapshots"; LEDGER=SNAP/"theory_ledger.jsonl"
import datetime as dt
NOWT=int(dt.datetime.now(dt.timezone.utc).timestamp())
CAP=int(os.environ.get("EF_EXTRACT_CAP","8"))          # itens por ciclo
MODEL=os.environ.get("EF_TIER2_MODEL","claude-haiku-4-5-20251001")
SYS=("Você é o Theory Extractor (ouro/XAU). Recebe título+resumo+fonte de uma análise e devolve EXCLUSIVAMENTE "
     "um JSON: {\"gold_relevant\":bool,\"predicted_gold_dir\":\"bullish|bearish|neutral|na\",\"horizon_days\":int|null,"
     "\"claim\":\"frase falsificável curta\",\"conditional_on\":\"driver ou null\",\"confidence_label\":\"low|med|high\"}. "
     "Se não houver previsão testável sobre o ouro -> gold_relevant=false, dir=na, horizon=null. Só LABELS + tempo; "
     "NUNCA invente preço/%/probabilidade. Não exagere viés de fonte perma-bull (sem tese nova -> confidence=low).")
def load():
    if not LEDGER.exists(): return []
    out=[]
    for ln in LEDGER.read_text().splitlines():
        try: out.append(json.loads(ln))
        except Exception: pass
    return out
def save(rows):
    with open(LEDGER,"w") as fh:
        for r in rows: fh.write(json.dumps(r,ensure_ascii=False)+"\n")
def extract_json(t):
    i=t.find("{"); j=t.rfind("}")
    if i<0 or j<0: return None
    try: return json.loads(t[i:j+1])
    except Exception: return None
def call_claude(item):
    exe=shutil.which("claude") or str(Path.home()/".local/bin/claude")
    if not Path(exe).exists(): return None
    prompt=(f"FONTE: {item.get('source_name')} (viés: {item.get('bias')})\nTÍTULO: {item.get('title')}\n"
            f"RESUMO: {(item.get('summary') or '')[:600]}\n\nExtraia o JSON da hipótese falsificável sobre o ouro.")
    env=dict(os.environ); env.pop("ANTHROPIC_API_KEY",None)  # força assinatura Max
    try:
        r=subprocess.run([exe,"-p",prompt,"--append-system-prompt",SYS,"--output-format","json","--model",MODEL],
                         capture_output=True,text=True,timeout=120,env=env)
    except subprocess.TimeoutExpired: return None
    if r.returncode!=0: return None
    try: body=json.loads(r.stdout).get("result","")
    except Exception: body=r.stdout
    return extract_json(body or "")
def main():
    rows=load()
    pend=[r for r in rows if not r.get("extracted")]
    if not pend: print("theory_extract: nada pendente (todos extraídos)."); return
    exe=shutil.which("claude") or str(Path.home()/".local/bin/claude")
    if not Path(exe).exists(): print("theory_extract: claude CLI ausente -> no-op (claims ficam pendentes)."); return
    done=0
    for r in pend[:CAP]:
        c=call_claude(r)
        if c is None:
            continue
        r["extracted"]=True; r["extracted_ts"]=NOWT
        r["gold_relevant"]=bool(c.get("gold_relevant"))
        r["predicted_gold_dir"]=c.get("predicted_gold_dir","na")
        r["horizon_days"]=c.get("horizon_days")
        if r["gold_relevant"] and not isinstance(r["horizon_days"],(int,float)): r["horizon_days"]=90
        r["claim"]=(c.get("claim") or "")[:240]
        r["conditional_on"]=c.get("conditional_on")
        r["confidence_label"]=c.get("confidence_label")
        done+=1
    save(rows)
    rel=sum(1 for r in rows if r.get("gold_relevant"))
    print(f"theory_extract: extraídos {done} (cap {CAP}) | total extraídos {sum(1 for r in rows if r.get('extracted'))}/{len(rows)} | gold-relevant {rel}")
    for r in rows:
        if r.get("extracted_ts")==NOWT and r.get("gold_relevant"):
            print(f"  [{r['source_id']}] {r['predicted_gold_dir']}/{r['horizon_days']}d :: {r['claim'][:60]}")
if __name__=="__main__": main()
