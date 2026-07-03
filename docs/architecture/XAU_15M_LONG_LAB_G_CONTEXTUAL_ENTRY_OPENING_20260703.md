# LAB G — SISTEMA DE ENTRY CONTEXTUAL DE CAPITULAÇÃO 15M · ABERTURA + AUTO-AUDITORIA (2026-07-03)

**Autorização Cris (verbatim, 2026-07-03):** rodada exaustiva nova até o final; organizada/rastreável/salva em memória; "SE PRECISO CRIE NOVO SISTEMA DE ENTRY COMPLETAMENTE DIFERENTE"; sem relatório intermediário; sem push sem autorização.

## 1. AUTO-AUDITORIA (o que as rodadas anteriores NÃO fizeram — motivo desta)
1. **Indicadores RAW nunca definiram a ENTRADA.** Nos Labs A/F, as features de indicador (bubbles, supply, legpos, clean_sky, downleg physics) entraram só como SKIP-vetoes em micro-configs congeladas (P3/P4) sobre a base mecanizada. Nenhuma rodada construiu a entrada A PARTIR da confluência contexto+indicador.
2. **Regime detector usado só como gate binário (≠BEAR).** Nunca como MAPA de contexto: posição no box do regime, idade do regime, distância do low do regime, transições — apesar de o L2/BPT 4H ter provado que posição-na-estrutura é 1ª classe.
3. **Estruturas aprendidas nas estratégias anteriores (NAS, CHoCH, OB/demand, monforte, bandas de supply do L2, 5ATR/8ATR, bottom-power) não foram cruzadas** em confluência causal com a leitura estrutural — ficaram como colunas dormentes no universo 4502.
4. **Zero indicadores NOVOS criados das séries RAW** (divergência RSI no flush, spike de ATR, profundidade do sweep, velocidade de recuperação, box-position multi-janela) — tudo computável causalmente e nunca tentado.
5. **Cortes de losers não exauridos; corte de winners PEQUENOS em regiões altas nunca testado.**
6. **Viés de processo identificado:** ancorar tudo na base #4 + configs congeladas otimizou auditabilidade às custas de criatividade. Lab F atacou exposição a jusante (cap de trades) em vez da FONTE (seleção de entrada) — confirmatório e caro (~30min de wall-clock, dominado por discovery/DA multi-agente, não pelo cômputo: a execução em si roda em ~1min).

## 2. REFRAME DO OBJETIVO (mandato Cris)
- Buscar as **capitulações constantes do 15M** (distintas das de 4H — mais frequentes), com entradas **extremamente bem contextualizadas**, não mecanizadas.
- **Frequência-alvo: 1-3 trades/semana em RANGE e BULL · 0-1/semana em BEAR** (LONG só com estrutura confirmada de pullback-bull dentro do BEAR).
- **Sem exaustão comparativa com a base** — base #4 entra apenas como referência de sanidade no final.
- WR/streak FundedNext = objetivo de desenho (não pós-filtro).

## 3. DESENHO DA RODADA (rastreabilidade)
- **G1 — Inventário total de lentes** (determinístico): catálogo de TODAS as features do universo 4502 + indicadores NOVOS derivados das séries RAW + estados do regime v5h como mapa (não gate). Script `lab_g_context_inventory.py` → `results/lab_g_inventory.json`.
- **G2 — Discovery multi-agente criativo**: desenhar 2-4 SISTEMAS DE ENTRY completos (capitulação-contextual, regime-condicional, frequência-alvo), cruzando estrutura × indicadores × regime; herdando lições e refutações (0/27 individual, bubbles polaridade contextual, room_above nunca filtro, close-only-causal).
- **G3 — Congelamento das specs** (1 doc por sistema; ledger único; nulls desenhados antes).
- **G4 — Execução**: painéis completos bruto+SB por sistema + frequência semanal por regime + nulls frequency-matched + sub-janelas/jackknife. Status honesto: **EXPLORATORY_CALIBRATION** (thresholds calibrados nos dados = 45-grupos rule; validação = null+convergência+sub-janelas, nunca OOS).
- **G5 — DA independente** · **G6 — docs finais + memória + commit** (`"Build XAU 15M long contextual capitulation entry lab"`), sem push.

## 4. Restrições permanentes herdadas
Research-only · LONG-only · RAW-first/zero SLIM · exit let-run retido (convexidade aprovada) salvo proposta explícita de sistema · detector v5h intocado como DETECTOR (uso como mapa é leitura, não alteração) · subagents nunca commitam · forbidden paths anteriores vigentes (limit/retest pós-sinal, SL pad, filtro de hora, short-mirror, room_above-filtro, indicador individual como gate isolado).
