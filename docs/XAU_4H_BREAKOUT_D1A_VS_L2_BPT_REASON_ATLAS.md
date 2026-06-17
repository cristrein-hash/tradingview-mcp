# XAU 4H — BREAKOUT/D1a × L2 / BPT / Reason Atlas — Comparação Profunda de Conceitos

**Data:** 2026-06-17 · **Tipo:** reconstrução comparativa conceitual · **NOT_VALIDATION — hypotheses-only.**
**Escopo:** XAUUSD_4H_BREAKOUT_CONTINUATION / D1a vs família L2 / BPT / Reason Atlas.
**Bloco:** **zero execução** — nenhum backtest/workflow/agente/mineração/plotagem/MCP/RAW/script novo. Só este doc. Não misturar as duas como estratégia; só entender se uma complementa a outra.

---

## 1. Executive summary

A hipótese do Cris — **BREAKOUT/D1a = validação macro/momentum ("há deslocamento e contexto para compra?"); L2/BPT = mecanismo de entrada estrutural ("onde e quando entrar depois do deslocamento?")** — é **conceitualmente forte e já tem precedente registrado no próprio acervo**: o **Padrão #1 do Cris** (anotação 2026-06-06): *"ROMPIMENTO / RETORNO A POLARIDADE DE TOPO ANTERIOR — MESMA ALTURA DE CHoCH/BOS + SL ABAIXO DO FUNDO ESTRUTURAL"*. Isso é, literalmente, breakout-como-validação + L2-como-entrada.

**Achado de reconciliação importante:** a minha mecanização ingênua "retrace à demanda" (refutada em expectância) usava a **demanda profunda do impulso** (= Padrão #8, ~4 ATR de risco → destruía o `avgR`). O L2/BPT madura usa a **polaridade do topo rompido** (= Padrão #1, nível do CHoCH/BOS, raso, com **R-ceiling 1.5 ATR**). Ou seja: **o problema de entrada que vi nos prints já tem uma mecanização madura desenhada — o L2 v2 / SMC Unified Rebuild — e ela ataca exatamente o "tarde demais" + "SL curto/errado" de uma vez.**

**Mas:** L2/BPT **nunca foi validado** (L2 v1 refutado por SMC fraco; L2 v2 = definições canônicas; SMC Unified Rebuild v0 = **pré-registro LOCKED, não implementado**). E BREAKOUT/D1a é hypotheses-only/gross. **Combinar duas hipóteses não-validadas é a principal armadilha.** Conceitualmente são complementares e ortogonais; empiricamente, nenhuma está provada. Este doc organiza a relação — não decide nem mistura.

---

## 2. Fontes lidas (read-only)

- `docs/XAU_LEGACY_KNOWLEDGE_INDEX.md` (linha L2/BPT/Reason Atlas), `XAU_4H_STRATEGY_RESCUE_MASTER_INVENTORY.md`, `XAU_STRATEGY_REEVALUATION_PLAN.md` (F9), `FUTURE_CORE_BOUNDARY.md`, `my-strategy/strategies/xau_legacy_preservation_audit.md`.
- Memória: `reference_L2_SMC_definitions_canonicas` (L2 v2), `reference_SMC_Unified_Rebuild_v0_preregistro` (state-machine), `project_caminho_a_padroes_visuais_5_layers` (Padrões #1/#7/#8; Layers L1-L5).
- Safety pack (listado, não aberto a fundo): `~/Desktop/TRADING/L2_REBOOT_SAFETY_PACK_2026-06-09` (~370 arq: `L2_BPT_AT_D1_DEMAND_*`, `L2_BPT_ATLAS_FIELD_DEPENDENCY_AUDIT`, `L2_BPT_BLOCKS_1_TO_5_MACRO_LEG_RAW_BREAKDOWN`, `L2_BPT_D1_HTF_DEMAND_RAW_SOURCE_MAPPING`, `L2_BLOCK_PROTECT_TRANSFORM_MATRIX`, `L2_BPT_EPISODE_GATE_COMPOSITE_PREREG`, `VIRGIN_VERDICTS`, `TRANSFORM_REENTRY`).
- BREAKOUT/D1a: docs desta sessão (deep dive, edge decomp, feature mapping, D1/EMA1D shift audits, entry mining, current-state synthesis).

> ⚠️ **Cobertura honesta:** o safety pack BPT tem detalhe RAW-traced profundo (macro-leg atlas, at-D1-demand, block/protect/transform) que **não abri arquivo-a-arquivo** neste bloco de organização. A reconstrução abaixo usa o nível conceitual preservado nas memórias/inventários + os nomes do pack.

---

## 3. Reconstrução L2 / BPT / Reason Atlas

**Identidade:** família **RESEARCH_CORE / KEEP_REFERENCE / FUTURE_CORE_CANDIDATE** (P2). LONG, continuation/pullback estrutural em bull. Preservada em safety pack. **Nunca promovida; sem produção.**

**Linha do tempo / versões:**
- **L2 v1 (Breakout polaridade) — REFUTADA.** Leitura SMC mecânica fraca: BOS = `close>max(high,20)`, polaridade = high do swing rompido, **sem CHoCH pré-condição**, sem "protected" rigoroso. ~109-143 trades.
- **L2 v2 (definições SMC canônicas, 2026-06-06) — referência viva.** Pivot Williams 5/5 SHIFT5; **Protected LH causal** (swing high antes do LL recente, não max); **CHoCH** = `close > protected_LH + 0.2·ATR`; **polaridade fixa no nível CHoCH** (não atualiza com BOS → evita entrada tardia); **BOS obrigatório**; **retest+reclaim** (bar verde body≥0.5, buffer 0.1·ATR) como trigger; invalidação por close < swing low estrutural. CLOSE-ONLY-CAUSAL.
- **SMC Unified Rebuild v0 (2026-06-07) — pré-registro LOCKED, NÃO implementado.** Substitui "L2/L2.5/L3 separados" por **1 state-machine SMC** com 5 estados: S0 no-structure, S1 CHoCH_fresh, S2 BOS_confirmed, S3 uptrend_mature, S4 topping/block (overlay). Trigger por estado (retest polaridade CHoCH / BOS / demand zone HTF). **SL estrutural R-bounded (floor 0.3·ATR, ceiling 1.5·ATR → abort)**. Bonferroni S1/S2/S3, bootstrap, métricas por estado. Aguarda autorização.
- **BPT / Reason Atlas.** Linha RAW-traced (safety pack): **macro-leg atlas** (breakdown dos blocos macro 1-55), **at_D1_demand** (entrada na zona de demanda HTF D1), **NAS ordering**, **acceptance**, **block/protect/transform matrix**, episode gate composite. "Atlas" = atlas das pernas/razões macro. Conhecimento-chave preservado: *"o que separa good/bad é gestão/exit, não filtro de entrada; zona REVIEW irredutível no miolo BULL_EXPANSION."*

**O que funcionava (conhecimento preservado):** leitura SMC institucional correta (CHoCH→BOS→retest→reclaim); polaridade como nível de defesa institucional; macro-location D1; SL estrutural R-bounded. **O que falhou:** L2 v1 (SMC mecânico); separar em muitas layers (fragmenta); a parte "miolo de BULL_EXPANSION" é irredutível por filtro de entrada (precisa gestão). **Status:** KEEP_REFERENCE / P2 / pré-registro aguardando autorização.

---

## 4. Reconstrução BREAKOUT/D1a (relevante à comparação)

- **Identidade:** breakout decisivo (`close>swing10_high[i-1]` + bullish + body≥0.5 + RSI>MA) + regime (R1-R5) + D1a (macro 1D causal). LONG.
- **Natureza (provada nos prints + mineração):** o breakout é **evento de varredura de liquidez / deslocamento** — não uma entrada de valor. A entrada imediata é **frequentemente tardia** (no sweep das máximas). 61% nunca recuam à demanda profunda; a edge residual é **seleção de regime** (H3: close>EMA200 & atr_expanding); o stop curto +4R/1R é R-eficiente; e o **problema de entrada/exit permanece não resolvido**.
- **O que falta:** a "entrada de valor" — que os prints mostram ser o **retorno à polaridade/BOS/demanda**, com SL estrutural. **É exatamente o que L2/BPT mecaniza.**

---

## 5. Comparação

| Eixo | BREAKOUT/D1a | L2 / BPT |
|---|---|---|
| Papel | **validação macro/momentum** ("há deslocamento + contexto bull?") | **mecanismo de entrada estrutural** ("onde/quando entrar no retorno?") |
| Evento-gatilho | sweep de swing10 (rompimento de máximas) | CHoCH→BOS estrutural (mudança de caráter + confirmação) |
| Entrada | **imediata** no rompimento (tardia) | **retest + reclaim** à polaridade (de valor) |
| Nível de referência | máxima de 10 barras (mecânico) | polaridade CHoCH / BOS (estrutural, defendido) |
| SL | `low−0.5ATR` (curto) ou demanda profunda (4 ATR, estourou) | abaixo do HL/swing estrutural, **R-bounded 0.3–1.5 ATR** |
| Contexto macro | D1a (close_1D>EMA200 & EMA50>EMA200) + regime 4H | macro-location D1 (at_D1_demand), NAS ordering, acceptance |
| Filosofia | momentum/displacement | SMC institucional / Auction (polaridade, aceitação) |
| Status | hypotheses-only, gross, in-sample | RESEARCH_CORE, nunca validado, pré-registro lockado |

**Onde se sobrepõem:** ambos LONG continuation bull; o **swing10 breakout ≈ um BOS cru** (rompimento de máxima anterior). Ambos querem **aceitação** acima do nível.
**Onde são ortogonais:** breakout = *momentum/permissão* coarse; L2 = *timing/localização estrutural* da entrada. Eixos diferentes (deslocamento vs estrutura).
**Onde se complementam (a tese):** breakout/D1a responde *"vale a pena olhar esta perna?"*; L2/BPT responde *"o ponto de entrada de valor é o retorno à polaridade X, SL abaixo do fundo Y"*. = **Padrão #1 do Cris.**

---

## 6. Pontos de conexão (mapeamento)

| Conceito | BREAKOUT/D1a | L2/BPT |
|---|---|---|
| breakout swing10 | gatilho de validação | ≈ BOS cru (L2 usa BOS estrutural rigoroso) |
| BOS/CHoCH | não usa (só swing10) | núcleo: CHoCH (caráter) + BOS (confirmação) |
| nível de polaridade | ausente | nível CHoCH fixo = entrada de valor (Padrão #1) |
| demanda abaixo | tentei a profunda (Padrão #8 → 4 ATR, estourou) | at_D1_demand / demand zone HTF (S3); polaridade rasa (S1/S2) |
| reclaim candle | ausente (entra no rompimento) | bar verde body≥0.5 + buffer 0.1 ATR (trigger) |
| aceitação vs rejeição | só RSI>MA (cru) | acceptance explícita (reclaim válido vs falha) |
| sweep de topo | é o que o breakout faz (e falha em topo) | S4 topping/block; NAS short/top como hard block |
| short inversion | insight visual paralelo (parado) | block/protect/transform matrix lida com falha/reversão |

---

## 7. Respostas às perguntas do bloco

- **L2/BPT já resolve a entrada tardia do BREAKOUT?** **Conceitualmente, sim** — o retest+reclaim à polaridade é a "entrada de valor" que substitui a entrada no sweep. **Mas L2 não está validado** (pré-registrado, nunca implementado). É a mecanização madura *candidata* do que o breakout precisa.
- **BREAKOUT/D1a pode filtrar melhor os episódios L2?** **Hipótese plausível** — D1a (contexto macro 1D causal) + deslocamento como *permissão* poderiam pré-selecionar quais estruturas SMC operar (só pernas com deslocamento + contexto bull). Não testado.
- **D1a melhora BPT?** **Sobreposição parcial** — BPT já usa macro-location D1 (at_D1_demand). D1a é um gate D1 mais simples/causal (EMA-stack 1D) que pode reforçar ou ser redundante com o at_D1_demand. A distinguir.
- **BPT melhora o ponto de entrada do BREAKOUT?** **Sim — é a tese central.** Retest polaridade/BOS + reclaim + SL estrutural R-bounded ataca o "tarde demais" **e** o "SL curto/errado" simultaneamente. E corrige meu erro: usar a **polaridade rasa** (1.5 ATR), não a demanda profunda (4 ATR).
- **Há conflito entre as lógicas?** **Risco de redundância:** o BOS estrutural de L2 ≈ o swing10 breakout. Se o breakout for *só* um BOS cru, **L2 o supersede** (não é camada separada — é a versão madura). A pergunta aberta: o breakout/D1a agrega *permissão de momentum/regime* além do que o BOS de L2 já carrega, ou é redundante?
- **Devem virar uma estratégia ou duas camadas?** **Não decidir agora** (não misturar sem prova). Conceitualmente são 2 papéis (validação macro + entrada estrutural), mas **ambos são hipóteses não-validadas**. Observação: a **SMC Unified S2/S3 já É a fusão conceitual** ("BOS confirmado → retest → reclaim"); nesse caso o papel do breakout/D1a seria **gate de permissão/regime** sobre a state-machine, não uma estratégia paralela.

---

## 8. Mapa conceitual (validação → entrada → gestão)

| Etapa | Mecanismo (síntese das duas famílias) |
|---|---|
| **validação** | breakout swing10 (deslocamento) **+** D1a/regime (contexto macro bull) — "vale olhar esta perna?" |
| **espera** | **não** entrar no sweep; aguardar retorno (a chave que faltava no breakout) |
| **retorno** | retest à **polaridade do topo rompido** (Padrão #1, raso) ou à **demanda do impulso** (Padrão #8, profundo) |
| **reclaim** | bar verde forte (body≥0.5) + buffer 0.1·ATR acima da polaridade (aceitação) |
| **entrada** | close do reclaim |
| **SL** | abaixo do HL/fundo estrutural, **R-bounded 0.3–1.5 ATR** (não low−0.5ATR, não demanda de 4 ATR) |
| **target** | dimensionado ao risco estrutural (a lição: não +4R sobre risco grande) |
| **invalidação** | close < swing low estrutural / HL confirmado |

---

## 9. Pontos de sinergia · 10. Riscos · 11. Hipóteses preservadas

**Sinergia:** breakout/D1a dá *permissão macro/momentum*; L2/BPT dá *entrada estrutural de valor*; juntos = Padrão #1 do Cris, que ataca o problema real dos prints. A polaridade rasa de L2 resolve o erro de risco do meu retrace profundo.

**Riscos:** (a) combinar **duas hipóteses não-validadas**; (b) **redundância** BOS-estrutural vs swing10-breakout (talvez L2 já contenha o breakout); (c) L2 **nunca implementado** (pré-registro lockado); (d) BPT é **pesado** (coleta, macro-leg atlas) — pode não caber em janelas curtas; (e) **overfit** ao juntar; (f) não promover BREAKOUT por gross; **não chamar L2 de "resolvido"** (é referência, não edge); (g) não descartar L2 pelas falhas do v1 (eram de implementação).

**Hipóteses preservadas:** (1) arquitetura em 2 papéis (validação macro + entrada estrutural); (2) **Padrão #1** (retest à polaridade) como entrada madura; (3) **SMC Unified Rebuild v0** como a mecanização pré-registrada que poderia *ser* a camada de entrada; (4) BREAKOUT/D1a como gate de permissão/regime sobre a state-machine SMC; (5) short-inversion ligada ao S4/block-protect-transform.

---

## 12. Próximos testes POSSÍVEIS (listados, NÃO executados, NÃO recomendados)

Apenas para registro do espaço de teste (decisão do usuário, sem prioridade atribuída):
- Sobreposição temporal: quantos eventos de breakout/D1a caem dentro de uma estrutura L2 (S1/S2/S3) — medir redundância vs complementaridade.
- Reconciliar `swing10 breakout` vs `BOS estrutural` (são o mesmo nível? quão frequente o breakout é um BOS cru?).
- Medir se a entrada Padrão #1 (retest polaridade rasa, R-bounded 1.5 ATR) sobre os eventos breakout/D1a melhora `avgR` vs a entrada-no-rompimento (corrige o erro do retrace profundo).
- (Tudo exigiria implementação + pré-registro + RAW + DA — nada feito aqui.)

---

## 13. Devil's Advocate (auto-checklist)

- ✅ Não chamou hipótese de validação (L2 e BREAKOUT marcados hypotheses-only/não-validados).
- ✅ Não misturou estratégias sem prova (explicitamente "não decidir/não fundir agora").
- ✅ Não descartou L2 por falhas antigas (v1 = falha de implementação; v2/Unified preservados).
- ✅ Não promoveu BREAKOUT por métricas gross.
- ✅ Não abriu nova frente fora deste conceito (comparação L2 × BREAKOUT só).
- ✅ Não recomendou Caminho B / SHORT / OOS / cross-asset como próximo.
- ✅ Nenhuma execução; produção intacta.

---

## 14. Decisão pendente do usuário

Nome correto da família confirmado: **L2 / BPT / Reason Atlas** (RESEARCH_CORE, safety pack `L2_REBOOT_SAFETY_PACK_2026-06-09`). Complementaridade conceitual = forte (Padrão #1). Conflito potencial = redundância BOS vs swing10. Vale teste futuro = sim, em tese — mas ambas não-validadas.

**Próximo passo aguarda decisão do usuário.**

---

*Read-only. Nenhuma execução, plotagem, MCP, RAW ou slim tocado. Reconstrução conceitual a partir de docs/memórias/inventário + listagem do safety pack (não aberto arquivo-a-arquivo). Ambas as famílias permanecem hypotheses-only.*
