# XAU 15M BigBeluga + NAS (Leonardo) — Estudo Neutro & Proposta de Workflow

**Data:** 2026-06-16 · **Natureza:** estudo neutro / hypothesis-generation. **NÃO é validação de edge.**
**Fontes:** `~/Desktop/XAU 15M/Analise 15M BB + NAS.pdf` (27 pág, 15 winners) · `~/Desktop/XAU 15M/Analise Losers .pdf` (14 pág, 4 losers selecionados — o doc declara explicitamente ser subconjunto).
**Status no sistema:** estratégia XAU 15M **NÃO aprovada, NÃO ativa, sem Telegram, fora do catalog/scheduler**. Única XAU operacional = L1 4H EMA21 Continuation.

## 1. Executive summary
Os PDFs documentam uma lógica operacional **manual e real** (Leonardo): em XAUUSD M15, entrar em zona BigBeluga (oferta→short / demanda→long) com sinais NAS, stop além da zona, alvo/gestão por zona oposta ou NAS oposto. A amostra mostra winners grandes (até **+19.05R**) e losers instrutivos. **O perigo central é tratar 15 winners curados como prova de edge.** A leitura neutra dos dois docs converge num ponto forte: **o gatilho de entrada (BB+NAS) não é o que separa winner de loser** — os discriminadores recorrentes são **alinhamento com a tendência dominante, comportamento pós-entrada, tempo dentro da zona e tamanho da zona (que define o R via stop)**. Recomendação: **separar reversão vs continuação desde o início**, catalogar as variáveis dos prints, e só então validar em RAW M15. Não automatizar, não complexificar antes de provar necessidade.

## 2. Leitura neutra dos PDFs (o que está OBSERVADO, com referência)
- O próprio doc instrui: *"NÃO se limite ao texto das anotações… extraia dos prints: quantidade de NAS na zona, tipo da região, R, barras, duração, retestes, localização da entrada, dia da semana, amplitude da zona"* (Winners, pág. intro). A **régua azul** nos prints = duração do trade (barras, tempo, deslocamento em pontos).
- Pergunta-mãe declarada: *"por que alguns trades produziram 3R enquanto outros produziram 10R, 15R ou 19R usando exatamente a mesma lógica?"* (Winners, conclusões preliminares).
- Conclusões preliminares dos winners (texto): entrada perto da **extremidade** da zona (não no centro); zona menor → stop menor → R maior; **NAS = qualidade/probabilidade da reação, não magnitude do movimento**; clusters de NAS podem indicar exaustão/absorção/defesa; **duração longa** marca os maiores R (>10R frequentemente >1 dia); dois perfis distintos: **reversão** (preço esticado chega a extremo, NAS contra o fluxo) e **continuação** (pullback à zona, NAS a favor da tendência) — *o doc afirma que os maiores R são majoritariamente continuação* (a verificar; ver §8).
- Conclusões dos losers (texto): falha **não** por ausência de NAS nem erro de execução; falha quando se tenta **reverter tendência dominante intacta**, quando o preço **lateraliza preso na zona sem deslocamento favorável**, e quando há **rompimento legítimo** (não ruído). Dois tipos de loser: **Tipo 1 rompimento imediato** / **Tipo 2 falsa defesa** (lateraliza, parece defender, depois rompe). Retestes múltiplos pré-entrada enfraquecem a zona.

## 3. Lógica operacional presumida (com UNKNOWNs)
- **Ativo/TF:** XAUUSD · M15.
- **Indicadores:** BigBeluga zones (oferta/demanda) + NAS signals (long/short). Contexto de tendência (visual). `UNKNOWN`: timeframe da tendência usada (M15? H1? 4H?).
- **Direção:** long em demanda + NAS long; short em oferta + NAS short.
- **Entrada:** dentro/na extremidade da zona; às vezes 1 sinal, às vezes cluster, às vezes "logo abaixo/acima" da borda. `NEEDS_CONFIRMATION`: regra exata (1º NAS vs cluster; quantos; janela temporal).
- **Stop:** do outro lado da zona BigBeluga (≈ largura da zona = risco).
- **Alvo/saída:** zona oposta · NAS oposto (ex.: Trade 05 saiu em cluster NAS LONG) · permanência longa para capturar perna. `NEEDS_CONFIRMATION`: critério de saída padrão.
- **Gestão:** duração/barras parecem críticas; grandes winners duram mais. `UNKNOWN`: reentrada após stop; filtro de horário (há nota "sinal NAS veio entre 21:45 e 00").

## 4. Winners — padrões observados (sem causalidade)
Ver tabela no Apêndice A (15 trades extraídos das anotações). Observações **da amostra** (curada, sem negativos → não é base rate):
- **NAS count NÃO escala com R:** 6 NAS → +2.81R (T09) e +4.60R (T14); 5 NAS → +5.45R (T15); **3 NAS → +19.05R (T10)**; 1 NAS → +3.5R (T08); 4 NAS → +12.62R (T07). **Confirma a própria hipótese do doc: NAS ≠ magnitude.**
- **R é dominado pelo tamanho do risco (largura da zona):** menores riscos (5.76 T07, 11.14 T10, 11.23 T11) estão entre os maiores R (12.62, 19.05, 15.3). Mega-R = **zona estreita + perna direcional sustentada**, não "mais sinal".
- **Skew de direção:** 11/15 SHORT, 4/15 LONG → amostra enviesada (limitação, não feature).
- Entrada perto da borda com stop além da zona aparece em quase todos (consistente com a tese de localização).

## 5. Losers — padrões observados
Ver Apêndice B (4 losers selecionados). Padrões:
- **NAS não salva:** L04 (2 NAS) e L05 (6 NAS) ambos falharam → count irrelevante para evitar perda.
- **Contra-tendência dominante** é o modo de falha recorrente (L03, L04, L05 contra tendência forte; L02 até a favor mas rompeu após múltiplos testes).
- **Dois tipos:** L04 = Tipo 1 (rompimento imediato, chegada muito impulsiva); L05 = Tipo 2 (6 NAS, lateralizou preso, depois rompeu a favor da tendência).
- **Tempo na zona sem deslocamento favorável** = bandeira vermelha (L03/L05 "permaneceu horas"). Hipótese do doc: lateralização ≠ absorção.
- **Rompimento legítimo** (continuação após stop, sem retorno à zona) distingue falha estrutural de stop por ruído.

## 6. Variáveis obrigatórias a catalogar
Dicionário completo (identidade, BigBeluga, NAS, contexto, pós-entrada, gestão) conforme o pedido — **resumo** dos eixos críticos; lista exaustiva mantida como spec da Fase 1:
- **Identidade:** trade_id, source_pdf, page, symbol, tf, datetime, day_of_week, direction, winner/loser, R, points, entry, stop, risk_points.
- **BigBeluga:** zone_type, zone_high/low, **zone_width_points**, **entry_location_in_zone** (upper/lower extreme/middle/outside), entry_distance_to_edge/center, stop_distance_beyond_zone, **retests_pre/post**, **time_inside_zone_before/after_entry**.
- **NAS:** count_total/before/after, direction, **cluster_density**, time_first/last_NAS→entry, price_dispersion, zone_alignment, opposite_NAS_exit_present.
- **Contexto:** trend_M15/H1/4H, **with/counter_trend**, **impulse_distance/speed_before_zone**, volatility, distance_to_opposite_BB, session, weekday.
- **Pós-entrada (provável núcleo do edge):** **MFE_R_before_adverse_break**, bars_to_1R/2R/5R, bars_to_exit, total_duration, **did_price_leave_zone_quickly / lateralize / break_cleanly / return_after_break**, **failure_type** {immediate_break, false_defense, slow_bleed, wick_stop, no_followthrough, trend_continuation_against}.
- **Gestão:** exit_reason, target_type, opposite_zone/NAS_exit, time_exit, discretionary_exit, mechanical_exit_possible.

## 7. Hipóteses testáveis (H1–H15)
H1 entrada na extremidade ↑R (via risco menor). H2 zona menor ↑R potencial mas ↓tolerância a ruído. H3 NAS count ↑probabilidade de reação, **não** magnitude. H4 cluster > sinal isolado **só com expansão pós-entrada**. H5 continuação a favor da tendência > reversão em R. H6 grandes winners dependem de **duração longa**. H7 lateralização prolongada sem deslocamento ↑falha. H8 muitos retestes pré-entrada ↓qualidade da zona. H9 NAS pós-entrada não confirmam se o preço não desloca. H10 velocidade/agressividade de chegada é filtro crítico. H11 contra-tendência exige confirmação extra / gestão mais rápida. H12 **comportamento nos primeiros N candles pós-entrada > gatilho de entrada como preditor**. H13 NAS oposto como saída/gestão (testar). H14 a melhor versão pode ser simples: BB zone + NAS + tendência + filtro de expansão pós-entrada. H15 confluências adicionais podem ↑winrate mas ↓N e ↑overfitting.

## 8. O que NÃO sabemos / NÃO concluir
- **Não há edge provado.** Amostra = winners curados + 4 losers selecionados; **sem contagem total de sinais nem de negativos** → winrate/expectancy **desconhecidos**.
- A afirmação "maiores R são continuação" **não está limpa nos próprios exemplos** (T10 +19.05R e T01 +11.26R são descritos como reversão/contra-tendência). **Não assumir; medir.**
- NAS count alto ≠ qualidade. 5–6 NAS não validam (aparecem em winners medianos E em losers).
- Reversão e continuação **não são a mesma estratégia** — não misturar.
- Losers podem não ser erro humano — verificar.
- PDFs **não** são amostra completa (declarado no doc dos losers).

## 9. Perguntas para Leonardo (Fase 0)
Condição exata de entrada? 1º NAS ou cluster? O que define BigBeluga válida? Reversão e continuação operadas igual? Como define tendência (e em que TF)? Quando NÃO entra? Como posiciona stop? Como decide alvo? Como segura trades longos? Quando sai antes? Reentra após stop? O que é NAS válido? Filtro de horário (a nota 21:45–00 é regra)? Usa H1/4H/diário visual? O que faria diferente nos losers?

## 10. Workflow proposto (fases)
- **Fase 0 — Operacional com Leonardo:** confirmar a regra real (perguntas §9). Bloqueia interpretação errada.
- **Fase 1 — Dataset manual estruturado:** transformar PDFs em tabela (seed no Apêndice A/B). Saída futura: `research/xau_15m_bb_nas_leonardo/manual_trade_table.csv`. **Não usar para backtest ainda.**
- **Fase 2 — Taxonomia:** buckets {continuation_with_trend, reversal_countertrend, extreme_exhaustion, pullback_to_zone, immediate_break_loser, false_defense_loser, no_followthrough, long_duration_runner, quick_reaction_winner, median_winner}.
- **Fase 3 — Candidate variables:** classificar cada variável em mechanical / semi-mechanical / human-review-only / unavailable.
- **Fase 4 — Feasibility com o sistema atual:** checar disponibilidade no event store/RAW — BigBeluga M15? NAS M15? Bubbles/RSI? tendência H1/4H? zone_width? NAS-in-zone? time-in-zone? retests? post-entry behavior? (provável: muitas variáveis exigem zona geométrica e comportamento, não só sinal pontual).
- **Fase 5 — Gate manifest futuro (estrutura, não criar agora):** Setup A continuação · Setup B reversão · Setup C exhaustion · Setup D no-trade/failure filters.
- **Fase 6 — Backtest RAW:** XAU 15M RAW/source; predicados exatos; stop/target; R-real; **separar continuation vs reversal**; TRAIN/VAL/TEST; não otimizar em TEST.
- **Fase 7 — Forward shadow:** se hipótese forte, rodar como shadow candidate **sem Telegram de trade**, capturar signal_hash, comparar live vs RAW via Forward Outcome Layer.

## 11. Possíveis filtros/confluências a testar (neutro, sem recomendar ainda)
Tendência H1/4H · velocidade de chegada · tempo-na-zona (sair/reduzir se não desloca em N candles) · retestes pré-entrada · deslocamento inicial mínimo (MFE≥X em N candles — **cuidado: vira gestão, não entrada**) · separar continuação/reversão · gestão por duração (NAS oposto / zona oposta / trailing / parcial) · filtro de zona (width, edge efficiency) · filtro de NAS (densidade/timing/dispersão, **não count isolado**) · confluências (RSI div? Bubbles? HTF BigBeluga? volume só se RAW confiável; regime_L1_v4 provavelmente não direto no M15).

## 12. Riscos de overfitting
Amostra curada (15W) sem negativos → qualquer filtro "explica" os winners por construção (in-sample). Muitas variáveis (≈40) vs N pequeno → fácil achar correlação espúria. Calibração ≠ validação. Mitigar: derivar filtros da **lógica** (auction/estrutura), não do fit; validar em RAW independente; TRAIN/VAL/TEST; preferir poucos filtros robustos; medir N total e base rate, não só winners.

## 13. Como validar com RAW no futuro
RAW/source XAU 15M é fonte de verdade (datasets replay 15M existem — ver skill replay-backtest-manager / dataset registry). BigBeluga/NAS são indicadores Pine → extrair zonas (boxes) e sinais (labels) close-only-causal/SHIFT1 (repaint!). Predicados exatos no gate manifest. Live signals (event store) servem para forward/hipótese, **não** para provar edge.

## 14. Recomendação inicial
- **Manter simples?** Sim por ora — não complexificar antes de medir. A hipótese H14 (BB zone + NAS + tendência + expansão pós-entrada) é a baseline a bater.
- **Dividir reversal/continuation?** **SIM, desde já** — são perfis diferentes de risco/duração; misturar contamina a métrica.
- **Priorizar quais filtros?** Os 3 de maior sinal em ambos os docs: **(1) alinhamento com tendência dominante**, **(2) comportamento pós-entrada / tempo-na-zona (deslocamento favorável rápido)**, **(3) tamanho da zona (R via stop)**. NAS count fica como qualidade, não gate isolado.
- **Próximo bloco:** **Fase 0 (perguntas ao Leonardo) + Fase 1 (CSV manual estruturado a partir dos PDFs)**. Sem backtest, sem código de estratégia.

---
## Apêndice A — Winners (extraídos das anotações; pontos→R conferidos)
| # | Dir | Entry | Stop | Risk(pts) | +pts | R | NAS (na zona) | Perfil declarado |
|---|---|---|---|---|---|---|---|---|
|01|Short|4590.58|4606.21|15.63|+176|**+11.26**|~5 SHORT cluster|reversão (chegada esticada alta→oferta)|
|02|Short|4545.24|4572.48|27.24|+89.46|+3.3|2 SHORT|reversão (rejeição oferta)|
|03|Long|4586.91|4566.92|19.99|+223.87|**+11.2**|2 LONG|demanda após queda forte|
|04|Short|4839.29|4859.77|20.48|+106.80|+5.21|~7 SHORT (2 zonas)|reversão multi-zona|
|05|Short|4789.92|4807.75|17.83|+130.25|+7.31|2 SHORT|continuação (pullback em downtrend); saída em NAS LONG|
|06|Short|4887.07|4900.36|13.29|+137.76|**+10.37**|3 SHORT|reversão (impulso→oferta)|
|07|Long|4750.51|4744.75|**5.76**|+72.69|**+12.62**|4 LONG|demanda (risco minúsculo→R alto)|
|08|Short|4741.15|4754.79|13.64|+47.80|+3.5|**1 SHORT**|reversão (1 sinal, timing crítico)|
|09|Long|4677.30|4665.63|11.67|+29.58|+2.81|**6 LONG**|maior cluster, **menor R**|
|10|Short|4764.03|4775.17|11.14|+60.81|**+19.05**|3 SHORT|mega-winner (zona estreita)|
|11|Short|4720.37|4731.60|11.23|+171.78|**+15.3**|5 SHORT|continuação (downtrend)|
|12|Short|4578.50|4590.25|11.75|+90.37|+7.69|4 SHORT|reversão/pullback oferta|
|13|Short|4577.11|4590.47|13.36|+155.63|**+11.65**|4 SHORT|continuação (estrutura de baixa)|
|14|Long|4395.50|4370.14|25.36|+116.57|+4.60|**6 LONG**|cluster grande, R modesto|
|15|Short|4535.03|4546.55|11.52|+62.83|+5.45|5 SHORT|cluster forte, R mediano|

_Direção: 11 SHORT / 4 LONG (amostra enviesada). NAS count não ordena R (ver §4)._

## Apêndice B — Losers selecionados (4; subconjunto declarado)
| # | Dir | NAS | Tendência | Tipo de falha | Nota |
|---|---|---|---|---|---|
|L02|Short|2 SHORT|a favor (downtrend macro)|rompimento real após múltiplos testes|falhou **mesmo a favor**: zona consumida por retestes|
|L03|Long|5 NAS LONG|contra (downtrend forte)|rompimento legítimo da demanda|"horas" preso na zona antes de romper|
|L04|Long|2 NAS LONG|contra (queda acelerada)|Tipo 1 rompimento imediato|chegada muito impulsiva, sem desaceleração|
|L05|Short|**6 NAS SHORT**|contra (uptrend intacto)|Tipo 2 falsa defesa (lateraliza→rompe a favor)|maior cluster **e** loser → NAS count não salva|

---
_Estudo neutro. Nenhum backtest rodado, nenhum código de estratégia, produção não tocada. poppler instalado (dev tool) para render/extração dos PDFs._
