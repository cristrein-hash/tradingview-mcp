#!/usr/bin/env python3
"""FASE 2A — gera os mandatos dos 10 especialistas (subset controlado) a partir do schema tipado.
Cada prompt: missão estreita + fatores PERMITIDOS (do schema) + proibidos + perguntas + formato de
evidência + travas (sem narrativa, sem TAKE/SKIP). NÃO roda agentes."""
import os,sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from multi_agent_schema import FAMILY_FACTORS, FACTORS
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,'prompts'); os.makedirs(OUT,exist_ok=True)

SPEC={
 "demand_supply":("Demand & Supply Quality Specialist",
   ["A demanda 4H está perto e defendida (dist colado, touched_on_retest)?","O supply está perto demais (dist contínua em ATR)?","Supply bloqueia o alvo (blocks_2/3ATR)? foi rejeitado/quebrado antes?","Há espaço limpo até a resistência?","D1 demand/supply apoiam ou contradizem?"]),
 "capitulation":("Capitulation / Climax-Wash Specialist",
   ["É falling-knife/washout (sweet_spot, consec_down)?","drop20/rsi_min indicam capitulação severa?","below_VAL = aceitação no fundo?","range_exp / large_sell bubbles = climax?","É capitulação real ou continuação de baixa?"]),
 "exhaustion_top":("Exhaustion / Top-Risk Specialist",
   ["legpos90 está no topo da perna?","rise20 = blow-off?","RSI overbought = força ou exaustão? bear-div?","F_STRICT_top_late acende?","large_buy bubbles / NAS short = distribuição no topo?"]),
 "volume_vp":("Volume / Session VP / Absorption Specialist",
   ["rel_volume confirma capitulação ou é distribuição?","POC/VAL/VAH favorecem (dist_POC/VAL)?","preço aceita acima/abaixo do value area (below_VAL, va_width)?","é absorção ou distribuição?"]),
 "nas":("NAS Specialist",
   ["NAS LONG/SHORT novo relevante (nas_long/short_new_8b)?","first-appearance ou ruído?","nas_dist_ema_atr / nas_rsi apoiam ou contradizem a tese?","NAS 1D recente (nas_1d_long_recent)?","alinhado a fundo, topo ou meio?"]),
 "bubbles":("Market Order Bubbles Specialist",
   ["Há absorção SELL pré-reversão (bub_sell_*)?","BUY climax em topo (bub_buy_*/large_buy_10b)?","cluster small/medium/large?","buy_sell_ratio = acumulação ou distribuição?","POC plot (bub_poc_recent)?"]),
 "rsi_momentum":("RSI / Divergence / Momentum Specialist",
   ["RSI oversold/neutro/overbought (rsi, rsi_min8, rsi_max8)?","divergência real (bull/bear_div)?","rsi_vs_ma = momentum de virada ou exaustão?","RSI alto = força ou blow-off / RSI baixo = capitulação ou bear-cont?"]),
 "risk_sl":("Risk / SL Geometry Specialist",
   ["sl_type (V_REVERSAL/NORMAL/LATE_WIDE) e sl_atr — risco bem formado?","alvo 2R/6R alcançável vs supply (blocks_2/3ATR, dist_4h_supply)?","R/R razoável (dist demand vs supply)?","O SL depende de estrutura fraca?"]),
 "bull_beta":("Bull-Beta / Drift Discriminator",
   ["É edge estrutural ou só long-gold beta?","trend_90/legpos/rel_volume sugerem dip-in-uptrend que sobe de qualquer jeito?","um random long no mesmo regime faria isto?","o sinal sobrevive fora de um bull?"]),
 "devils_advocate":("Devil's Advocate Specialist",
   ["Por que pode ser falso-positivo?","É só bull-beta?","Está comprando topo/blow-off?","Supply perto demais (alvo 2R inalcançável)?","O SL depende de estrutura fraca?","Há exemplo conhecido parecido que perdeu?"]),
}
for fam,(title,qs) in SPEC.items():
    allowed=sorted(FAMILY_FACTORS.get(fam,set()))
    forbidden_note=("PODE citar QUALQUER um dos 84 (lente adversária)" if fam=="devils_advocate" else
                    f"SÓ os fatores acima. Citar fator fora desta lista = REJEITADO pelo validador.")
    body=f"""# {title} — mandato (Fase 2A, especialista L2/BPT XAU 4H)

**Você é uma LENTE técnica estreita. Você NÃO decide trade. Você NÃO vê outcome nem decisão antiga.**

## Travas
- NÃO produza TAKE/REVIEW/SKIP. NÃO use linguagem de performance ("bom/mau trade","merece risco","WR","lucrativo").
- NÃO sabe outcome, decisão antiga nem setup_type antigo.
- Toda afirmação = EVIDÊNCIA ESTRUTURADA (factor+value). Sem narrativa solta.
- Reporte CONFLITOS e CAVEATS quando os fatores divergirem.

## Missão (sua única lente)
{title}. Avalie SÓ a sua área.

## Perguntas obrigatórias
{chr(10).join('- '+q for q in qs)}

## Fatores PERMITIDOS ({len(allowed)})
{', '.join(allowed)}
{forbidden_note}

## Formato de evidência (1+ por episódio; ≥1 decisive) — validado pela Fase 0
```json
{{"specialist_id":"{fam}","episode_id":"<bar_idx>","factor_used":"<um permitido>","value":<valor EXATO do packet>,
 "interpretation":"<o que o valor significa na sua lente>","impact":"positive|negative|neutral|veto|review_flag",
 "strength":"weak|medium|strong","decisive_or_supporting":"decisive|supporting","caveat":"<conflito/ressalva>","causal":true}}
```
`factor_used` deve existir no packet E `value` deve bater exatamente (anti-eco). Saída por episódio:
```json
{{"episode_id":"<bar_idx>","specialist_id":"{fam}","net_read":"supportive|neutral|hostile|unavailable",
 "evidence":[<evidências>],"unresolved_conflicts":["..."],"missing_data":["..."]}}
```
Sem decisão. Só a leitura da sua lente, em evidência auditável.
"""
    open(os.path.join(OUT,f"{fam}.md"),"w").write(body)
    print(f"{fam}.md ({len(allowed)} fatores permitidos)")
print("prompts gerados em",OUT)
