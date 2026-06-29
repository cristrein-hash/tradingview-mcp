#!/usr/bin/env python3
"""FASE 3 — FROTA External Factors (Anthropic Agent SDK). Master Synthesizer + subagentes (Calendar, News, Fed-tone,
Gold-driver) — Tier-2 LLM, LABELS ONLY (fronteira de determinismo: agente NUNCA emite número; números vêm do Tier-1).
Roda no venv .venv-agents (claude-agent-sdk). Se ANTHROPIC_API_KEY ausente -> degrada p/ Tier-1+calendar keyless
(monitor) e marca tier2=unavailable. Saída: snapshots/latest.json (schema external_*). human-in-loop, NUNCA auto-gate."""
import os,json,sys,asyncio
from pathlib import Path
H=Path(__file__).parent.parent
SK=H/"agents/skills"
def tier1_context():
    """grounding numérico determinístico (passado AOS agentes; eles ecoam, nunca geram)."""
    p=H/"snapshots/latest.json"
    if p.exists():
        s=json.loads(p.read_text())
        return {"tier1":s.get("tier1_macro_recorded_context",{}),"events":s.get("layer_A_imminent_le96h",[]),"layerB":s.get("layer_B_slow_macro",{})}
    return {"tier1":{},"events":[],"layerB":{}}
SYNTH_PROMPT = """Você é o External Context Synthesizer (XAU). Recebe GROUNDING numérico Tier-1 (já calculado, determinístico)
e leituras de subagentes (Calendar, News, Fed-tone, Gold-driver). Produza um JSON de CONTEXTO para o trading system.
REGRAS DURAS:
- Você NUNCA emite número novo (yield, %, preço, probabilidade). Só ECOA os números do grounding e produz LABELS.
- Saída = contexto/flag para HUMANO decidir. NUNCA é gate automático nem recomendação de trade.
- Camada A (reação imediata: NFP/CPI/FOMC) e Camada B (macro lento). NFP valida ~2-2,6x reação no ouro (event-window).
Campos de saída (schema external_*): external_bias(long/short/neutral/unknown), external_risk_level(normal/event_window/elevated),
external_trade_validation(neutral SEMPRE em passive-logging), external_main_reasons[list], external_directional_notes[list].
Se não houver evidência clara -> neutral/unknown. Honestidade > narrativa."""
def keyless_fallback(ctx):
    ev=ctx["events"]
    return {"_mode":"keyless_fallback_tier1_only","tier2":"unavailable_no_api_key",
            "external_factors":{"external_bias":"unknown","external_risk_level":"event_window" if ev else "normal",
              "external_trade_validation":"neutral","external_confidence":0,
              "external_main_reasons":[f"{e['event']} em {e.get('hours_until')}h (NFP~2.6x reação validada)" for e in ev],
              "external_us10y_real":ctx["tier1"].get("us10y_real",{}).get("value"),
              "external_vix":ctx["tier1"].get("vix",{}).get("value")}}
async def run_fleet(ctx):
    """orquestra via claude-agent-sdk (precisa ANTHROPIC_API_KEY). Subagentes = skills em agents/skills/."""
    from claude_agent_sdk import query, ClaudeAgentOptions  # import tardio (só com key)
    opts=ClaudeAgentOptions(system_prompt=SYNTH_PROMPT, allowed_tools=[], max_turns=2)
    grounding=json.dumps(ctx)
    prompt=f"GROUNDING Tier-1 (determinístico, ecoe números, gere só labels):\n{grounding}\n\nProduza o JSON de contexto external_* (labels only)."
    out=[]
    async for msg in query(prompt=prompt,options=opts):
        out.append(str(getattr(msg,'content',msg)))
    return {"_mode":"sdk_fleet","tier2":"active","raw":"".join(out)[:4000]}
def main():
    ctx=tier1_context()
    skills=[d.name for d in SK.iterdir() if (d/"SKILL.md").exists()] if SK.exists() else []
    print(f"skills disponíveis: {skills}")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        res=keyless_fallback(ctx)
        print("ANTHROPIC_API_KEY ausente -> fallback keyless (Tier-1+calendar). Tier-2 LLM inativo.")
    else:
        try: res=asyncio.run(run_fleet(ctx))
        except Exception as e: res={"_mode":"error","err":str(e)[:200], **keyless_fallback(ctx)}
    p=H/"snapshots/external_context.json"; p.write_text(json.dumps(res,indent=1,ensure_ascii=False))
    print(json.dumps(res,indent=1,ensure_ascii=False)[:1200])
    print(f"\n-> {p}")
if __name__=="__main__": main()
