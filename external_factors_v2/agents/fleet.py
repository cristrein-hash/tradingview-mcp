#!/usr/bin/env python3
"""FASE 3 — FROTA External Factors (Tier-2 LLM via `claude -p` headless = DENTRO do plano Max, NÃO API key).
Synthesizer LABELS ONLY (fronteira de determinismo: NUNCA emite número; números vêm do Tier-1, só ecoa).
OPÇÃO B (Cris 2026-06-29): usa o login Max do Claude Code (subscription), sem cobrança separada de API.
⚠️ Remove ANTHROPIC_API_KEY do ambiente do subprocesso -> força auth da assinatura (com a key, o CLI cobraria API).
Sem `claude` CLI ou erro -> fallback keyless (Tier-1+calendar). Saída: snapshots/external_context.json (external_*).
human-in-loop, NUNCA auto-gate. Tier-2 = contexto/flag, nunca edge."""
import os,json,subprocess,shutil
from pathlib import Path
H=Path(__file__).parent.parent
SK=H/"agents/skills"
MODEL=os.environ.get("EF_TIER2_MODEL","claude-haiku-4-5-20251001")  # leve na cota do Max; labels só
def tier1_context():
    p=H/"snapshots/latest.json"
    if p.exists():
        s=json.loads(p.read_text())
        return {"tier1":s.get("tier1_macro_recorded_context",{}),"events":s.get("layer_A_imminent_le96h",[]),
                "layerB":s.get("layer_B_slow_macro",{}),"news_fed":s.get("layer_text_news_recent",[]),
                "news_market":s.get("layer_market_news_recent",[]),"gold":s.get("layer_gold_canonical",{}),
                "fed_path":s.get("layer_fed_path",{})}
    return {"tier1":{},"events":[],"layerB":{},"news_fed":[],"news_market":[],"gold":{},"fed_path":{}}
SYS="""Você é o External Context Synthesizer (XAU/ouro) do módulo External Factors v2. Skills de referência (12):
economic-calendar-reader, event-severity, fed-tone-interpreter, gold-driver-analyzer, macro-regime-builder,
usd-regime-analyzer, yield-curve-reader, news-validation, news-deduplication, risk-classification,
geopolitical-impact, source-reliability.
REGRAS DURAS (fronteira de determinismo):
- NUNCA emita número novo (yield/%/preço/probabilidade). Só ECOE os números do grounding Tier-1 e produza LABELS.
- Saída = contexto/flag para HUMANO decidir. NUNCA é gate automático nem recomendação de trade. external_trade_validation SEMPRE "neutral" (passive-logging).
- Camada A = reação imediata (NFP/CPI/FOMC; NFP valida ~2,6x reação no ouro). Camada B = macro lento (real-yield/USD/curva).
- REGRA DE DIREÇÃO NFP (canônica, não invente): surpresa = actual − consenso. surpresa>0 (jobs FORTES) -> USD↑ -> ouro BEARISH. surpresa<0 (jobs fracos) -> USD↓ -> ouro BULLISH. A direção autoritativa é a determinística (capture_nfp_actual); você só ecoa esta regra.
- NÍVEL macro estático NÃO provou edge (Fase 1 null) -> confidence baixo, é contexto.
- Sem evidência clara -> neutral/unknown. Honestidade > narrativa."""
INSTR="""Produza EXCLUSIVAMENTE um objeto JSON (nada antes/depois) com as chaves:
{"external_bias":"long|short|neutral|unknown","external_risk_level":"normal|event_window|elevated",
 "external_trade_validation":"neutral","external_confidence":0-100,
 "external_main_reasons":[...],"external_directional_notes":[...],
 "echoed_tier1":{...só os números relevantes copiados do grounding...}}"""
def keyless_fallback(ctx,why):
    ev=ctx["events"]
    return {"_mode":"keyless_fallback","tier2":"unavailable","reason":why,
            "external_factors":{"external_bias":"unknown","external_risk_level":"event_window" if ev else "normal",
              "external_trade_validation":"neutral","external_confidence":0,
              "external_main_reasons":[f"{e['event']} em {e.get('hours_until')}h"+(f" (consenso {e.get('consensus_k')}K->{e.get('direction',{}).get('bias')})" if e.get('consensus_k') else "") for e in ev],
              "external_us10y_real":ctx["tier1"].get("us10y_real",{}).get("value"),
              "external_vix":ctx["tier1"].get("vix",{}).get("value")}}
def extract_json(txt):
    i=txt.find("{"); j=txt.rfind("}")
    if i<0 or j<0 or j<i: return None
    try: return json.loads(txt[i:j+1])
    except Exception: return None
def run_claude_p(ctx):
    """Tier-2 via `claude -p` (subscription/Max). Remove ANTHROPIC_API_KEY -> não cair em billing de API."""
    exe=shutil.which("claude") or str(Path.home()/".local/bin/claude")
    if not Path(exe).exists(): return None,"claude CLI ausente"
    prompt=("GROUNDING Tier-1 (determinístico — ecoe números, gere só labels):\n"
            f"{json.dumps(ctx,ensure_ascii=False)}\n\n{INSTR}")
    env=dict(os.environ); env.pop("ANTHROPIC_API_KEY",None)  # força auth da assinatura (Opção B)
    try:
        r=subprocess.run([exe,"-p",prompt,"--append-system-prompt",SYS,"--output-format","json","--model",MODEL],
                         capture_output=True,text=True,timeout=180,env=env)
    except subprocess.TimeoutExpired: return None,"timeout claude -p"
    if r.returncode!=0: return None,f"claude rc={r.returncode}: {(r.stderr or r.stdout)[:200]}"
    try: env_out=json.loads(r.stdout)  # envelope --output-format json
    except Exception: env_out={"result":r.stdout}
    body=env_out.get("result") if isinstance(env_out,dict) else r.stdout
    parsed=extract_json(body or "")
    if not parsed: return None,"resposta sem JSON parseável"
    parsed["external_trade_validation"]="neutral"  # trava dura: passive-logging
    return {"_mode":"claude_p_subscription","tier2":"active","model":MODEL,"external_factors":parsed},None
def main():
    ctx=tier1_context()
    skills=[d.name for d in SK.iterdir() if (d/"SKILL.md").exists()] if SK.exists() else []
    print(f"skills ref: {skills} | modelo Tier-2: {MODEL}")
    res,err=run_claude_p(ctx)
    if res is None:
        res=keyless_fallback(ctx,err or "indisponível")
        print(f"Tier-2 via claude -p indisponível ({err}) -> fallback keyless.")
    else:
        print("Tier-2 ATIVO via claude -p (subscription/Max, sem billing de API).")
    p=H/"snapshots/external_context.json"; p.write_text(json.dumps(res,indent=1,ensure_ascii=False))
    print(json.dumps(res,indent=1,ensure_ascii=False)[:1400])
    print(f"\n-> {p}")
if __name__=="__main__": main()
