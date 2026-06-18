# XAU 4H L2/BPT — Auditoria da rubrica e dos 14 agentes do TAKE engine

**Status:** `AUDIT · ENGINE = AI_REVIEW (reproducible inputs, nondeterministic reasoning) · NOT_VALIDATED` · **Data:** 2026-06-19
Esclarece a lógica efetiva da etapa 13 (reasoning) antes da Opção B. Sem retunar, sem mudar decisões. Foundation: [[XAU_4H_L2_BPT_TAKE_ENGINE_DETERMINISM_POLICY]]. DA: ac4830f5.

## 1. Como os 14 agentes trabalham (inventário)
**FAN-OUT por lote, NÃO ensemble.** Cada um dos 14 subagentes recebeu 1 lote (~20 episódios) e decidiu cada um. **0 episódios têm >1 decisão** → cada trade tem 1 decisão de 1 agente. **Não existe agregador, voto, consenso ou média** — a decisão final É a do agente do lote. Prompts idênticos (varia só o nº do lote); model=claude-opus, temp=default, **sem seed** → não-determinístico. Sem dependência entre agentes. Detalhe: `results/l2_bpt_agent_rubric_inventory.csv`.
- **Input/agente:** packet de **84 fatores causais** (`qual_packets.jsonl`, cego ao outcome) + a rubrica `QUALIFICATION_RUBRIC.md`.
- **Output/agente:** `qual_dec_NN.jsonl` com decision/direction/confidence/setup_type/positive_factors/negative_factors/decisive_reason/closest_known_examples/allow_under_human_review.

## 2. O que os agentes recebem (84 fatores) — `results/l2_bpt_agent_input_84_factor_map.csv`
Todos os 84 fatores são causais e estão no packet (logo no prompt). Respostas às perguntas obrigatórias:
- supply_distance contínua? **SIM** (`dist_4h_supply_low_atr`) + flag binário (`supply_blocks_2/3ATR`) — ambos no packet.
- demand distance? SIM · legpos? SIM (30/60/90) · F_STRICT? SIM · Session VP real? SIM (rel_volume/below_VAL/POC/VA) · NAS/Bubbles/RSI? SIM · capitulação? SIM (drop20/rsi_min8/sweet_spot) · SL demand-anchored? SIM (sl_atr/sl_type).
- macro/regime? PARCIAL — `macro_leg_direction`="REFERENCE_ONLY" (placeholder pouco útil); regime vem de trend_30/90, rsi_1d, price_vs_sma50.
- exemplos conhecidos ou só features? **Features** + as ASSINATURAS (perfil) dos winners/losers na rubrica; a similaridade pré-computada foi REMOVIDA (era outcome-derived).

## 3-4. Metavalidação (com correções do DA — crítico)
**O que o DA RETRATOU dos meus achados iniciais:**
- ❌ **"Agentes usam supply_distance contínua 83%"** = ARTEFATO. O regex media o texto do PACKET dado ao agente, não a cognição. O flag-set é subconjunto estrito do distance-set; 82/227 só aparecem no input, não no `decisive_reason`. **Não dá para afirmar que raciocinam com a distância contínua a partir do texto.**
- ❌ **"setup_type é preditivo (bottom_reversal +0.61, bear_bounce −0.61)"** = CIRCULAR. `setup_type` é ~colinear com a decisão (late_top=77/77 SKIP; bottom_reversal=0 SKIP). O rótulo É a decisão relabelada — o agente corrigindo a própria prova. bear_bounce n=13 (10 stops idênticos −1.1).

**O que se CONFIRMOU:**
- **Confidence NÃO é calibrada** → Spearman(conf,realR)=−0.02, Pearson −0.04. **É ruído; não usar como peso.** (Bucket 45-55 "melhor" é tail-aided.)
- **O reasoning citado NÃO discrimina TAKE-winner de TAKE-loser** (n17 vs n15): demand 100%/100%, macro 100%/100%, top 100%/100%, capit 41%/27% (único gap, <1 SE = ruído). "Sem discriminação detectável a este poder", consistente com winners/losers emaranhados.
- **27 SKIP-winners genuínos** (+2.20R; 19 WIN_HELD/5 BE/3 RUNNER; 14 cruzaram +2R) = continuações bull-beta que os agentes puseram como "topo" e SKIParam. (Base SKIP avgR +0.06, então SKIP não é catastrófico, mas deixa 27 winners limpos na mesa.)

**Veredito DA (o ponto central):** A **DECISÃO carrega sinal real** — TAKE +0.91R/53%WR vs SKIP +0.06R/21%WR é gradiente monotônico genuíno (o *gestalt* funciona). MAS o **aparato CITADO não se sustenta**: confidence ρ≈0, setup_type=relabel, fatores indistinguíveis win/lose. **Os agentes escolhem trades razoáveis, mas a racionalização escrita é narrativa post-hoc sobre dados estruturalmente emaranhados, não uma cadeia causal verificável.**

## 5. Concordância/discordância — `results/l2_bpt_agent_agreement_disagreement.csv`
**HARD-STOP PARCIAL:** como é fan-out (não ensemble), **não há respostas multi-agente por trade** → agreement/entropy/voto por trade = N/A. Só dá para medir consistência inter-lote (TAKE-rate por lote varia 1-4, dispersão Poisson-plausível, sem agente "redundante" pois cada um cobre trades distintos). Conclusão: **não dá para isolar "quais agentes acertam mais" nem testar subset menor — a estrutura fan-out impede.**

## 6. Reasoning vs outcome — `results/l2_bpt_agent_reasoning_vs_outcome.csv`
Os fatores citados são quase idênticos entre win e lose dentro de cada bucket de decisão → o erro de raciocínio recorrente é **narrativa-plausível-igual para resultados opostos** (não há "tell" textual). Erros de dados: nenhum grosseiro (os agentes citam valores do packet corretamente). Omissão central: nada no texto separa o winner do loser.

## 7. Deterministic Rubric v0 — PROPOSTA (NÃO implementar)
**Dá para converter em score determinístico?** Parcialmente, mas com ressalva forte: o valor do engine é o **gestalt** (decisão integrada), e os DAs anteriores mostraram que um filtro determinístico de 2-3 linhas (`legpos30≤35 & dist_dem≤2 & sl≤2`) **empata o avgR per-trade mas perde 2/3 da cobertura e não filtra os losers da regra**. Logo um score v0 determinístico provavelmente **subperforma o gestalt**.
- **Componentes obrigatórios (causais, não-circulares):** legpos (30/60/90), demand-distance contínua, **supply-distance contínua** (não o flag — único lever técnico vivo das auditorias visuais), capitulação (drop20+rsi_min8), F_STRICT (anti-topo).
- **Positivos:** demand-backed colado + capitulação + reclaim bullish + below-VAL.
- **Veto (candidato):** F_STRICT (legpos90≥85 & rsi≥70) — mas auditoria anterior mostrou que não é auto-block limpo → review-flag, não veto duro.
- **Review-only:** demanda longe / supply capando target / sinais conflitantes.
- **Pesos justificáveis:** monótonos em legpos/demand-dist/supply-dist. **Pesos overfit a evitar:** qualquer peso ajustado aos 276 (drift in-sample).
- **O que DEVE continuar AI-review:** a integração gestalt (o que bate a regra). NÃO usar confidence (ruído) nem setup_type (relabel) como features do score.

## 8. Decisão metodológica (classificação do engine)
**Estado = (3) AI_REVIEW_REPRODUCIBLE_INPUTS_NONDETERMINISTIC_REASONING.**
- Inputs (84 fatores, builders, frozen, /tmp) = reproduzíveis e auditáveis. Reasoning = não-determinístico mas agora AUDITADO: o gestalt funciona, a racionalização é post-hoc.
- NÃO é (1) DETERMINISTIC_READY (não há regra reproduzível que capture o gestalt). É também (2) FROZEN_AI_REVIEW_ARTIFACT para 2020-2026 (decisões congeladas, não reexecutáveis idênticas).
- Para Opção B, a questão (4) NEEDS_DETERMINISTIC_RUBRIC_BEFORE_OPTION_B depende do Cris: validar com agentes LLM soltos (AI_REVIEW declarado) é aceitável SE rotulado como AI-review e não como backtest determinístico.

## 9. Recomendação
1. **Opção B como AI_REVIEW** (re-rodar os subagentes em 2013-2017, declarado não-determinístico, comparado vs baselines) — viável e honesto, **DESDE QUE** rotulado AI-review, não "engine determinístico".
2. **OU** construir Deterministic Rubric v0 (§7) num bloco separado e comparar contra o gestalt — provavelmente subperforma, mas dá um baseline reproduzível.
**Não usar confidence como peso. Não usar setup_type como preditor independente.** O sinal está na decisão integrada, não no texto citado.

---
*Auditoria. Sem retune/validação Opção B/mudança de decisões/SLIM/chart/plot/produção. CSVs: `results/l2_bpt_agent_*.csv`. Script: `pipeline/qualification/audit_agents.py`. DA ac4830f5 (retratou supply_distance% + setup_type-predictiveness; confirmou confidence-noise + 27-missed-winners + gestalt-works-rationale-posthoc).*
