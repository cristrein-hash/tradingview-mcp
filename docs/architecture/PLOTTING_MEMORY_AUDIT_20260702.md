# PLOTTING MEMORY AUDIT — 4H + 15M (2026-07-02)

**Modo:** read-only / audit-first. Zero chart/TradingView/MCP-chart tocado · zero script alterado · zero produção/runtime/RAW tocado · Supabase consultado só via MCP read-only.
**Fontes:** Supabase memory (queries por plot/canonical/visual/long_position) · memory cards locais (lidos integralmente: feedback_canonical_trade_plotting, reference_trade_plotting_canonical, reference_long_position_overrides_ticks_bug) · MEMORY.md hot · MEMORY_ARCHIVE · docs/project_authority · docs/architecture · docs/ raiz · **32+ scripts de plotagem** (alert-bridge, my-strategy, research/xau_15m_bb_nas_leonardo, regime_turnstate_engine) via 2 subagents Explore reais · status master.

## 1. Executive verdict

**PLOTTING_CANON_PARTIALLY_CLEAR**

Existe uma fonte única de verdade **forte e explícita** — `docs/CANONICAL_TRADE_PLOTTING.md` (status CANÔNICO, 2026-06-18, com regra absoluta do Cris "NUNCA plotar sem ler este doc") + helper vivo + teste dry-run. O núcleo do canon (long_position+label, ticks, cores, #id, verificação) está claro e consistente. **Porém**: (a) o doc é 4H-cêntrico e **não incorpora o refinamento 15M de 2026-06-26** ("20 barras é demais p/ 15M"); (b) coexistem **duas gramáticas de cor** legítimas mas não reconciliadas no doc (outcome vs direção); (c) o **próprio script de referência está dessincronizado** do doc; (d) drift de largura entre scripts (6/8/10/12/20). Nenhum risco ativo de bug (o único script com o bug de preço absoluto está DEPRECATED com banner), mas o canon precisa de consolidação 4H+15M num master antes de virar agente.

## 2. Timeline of plotting changes

| Data | Mudança | Fonte | Conflito criado |
|---|---|---|---|
| 2026-06-02 | 3 tentativas falhas inventando overrides → regra "copiar formato EXATO de `draw_xau_4h_trades.py`" | reference_trade_plotting_canonical | — |
| 2026-06-06 | Label = **R-value** colorido; posição do label iterada V1→V3 (`entry+0.5R` vence) | idem | superseded depois (label) |
| 2026-06-09 | **Nunca verificar por screenshot** — `draw_list` + success | idem | — |
| 2026-06-11 | **BUG TICKS descoberto**: stopLevel/profitLevel = OFFSETS EM TICKS (mintick 0.01), não preço absoluto; 26 targets arrastados à mão | ticks_bug card · doc §0 | invalidou todos os exemplos com preço absoluto |
| 2026-06-13 | Cris "reagiu forte": text-only labels = **ERRADO**; canonical = long_position+label | MEMORY_ARCHIVE:72 | baniu prática v1 |
| 2026-06-14 | Label muda de R-value para **`#<id cronológico>`** (Cris) | feedback_canonical_trade_plotting | scripts antigos c/ R-label viram legacy |
| 2026-06-16 | `docs/CANONICAL_TRADE_PLOTTING.md` **criado** como fonte única + teste; política SL estrutural −0.1×ATR / target +3R p/ candidatos sem exit; azul p/ sem-outcome; **2ª reincidência** text-only registrada | doc + card | — |
| 2026-06-18 | **REGRA ABSOLUTA** (3ª reincidência): "NÃO AUTORIZO NUNCA NENHUMA PLOTAGEM QUE NÃO SEJA CANÔNICA"; **largura padrão = 20 barras**; HORIZON_BARS=10 SUPERSEDED | doc §2/§7 + card | largura <20 nos scripts vira drift |
| 2026-06-26 | Cris: **"20 é demais p/ 15M"** → 15M relaxado p/ ~8–12 (10 típico); canon de visualização de reversões (F#/T#, verde LONG/vermelho SHORT); exceção text-only autorizada 1× (`plot_candidates_labels.py`); screenshots autorizados p/ 1 engine (`plot_v2_visual.py`) | docstrings 15M | **refinamento nunca escrito no doc canônico** |
| 2026-06-27 | Plotters 15M de estratégia aprovados (5atr_a2, chosen, etc.) | docstrings | — |

## 3. Current known canon candidates

1. **`docs/CANONICAL_TRADE_PLOTTING.md`** — fonte: doc canônico auto-declarado · TF: 4H (aspira a "toda plotagem") · script ref: `alert-bridge/draw_xau_4h_trades.py` · data/outcome source: agnóstico (close_R) · label: `#<id>` · cores: verde `#1a8917` win / vermelho `#cc0000` loss / azul `#1565c0` sem-outcome · marker: long_position point2@target, largura 20 barras, label `entry+0.5R` · **status: CANÔNICO VIGENTE** · risco: não cobre 15M nem gramática por-direção.
2. **`plot_capit_rsi_trades.py`** (4H) — mais aderente ao doc (WIDTH 20, #id, ticks, outcome-color) · status: compliant · risco: nenhum.
3. **`plot_candidates_canonical.py` + `plot_strategy_canonical.py`** (15M) — canon 15M de fato: WIDTH 10 ("Cris 2026-06-26: 20 é demais p/ 15M"), #N, verde LONG/vermelho SHORT · status: aprovado por docstring, **não codificado em doc** · risco: gramática de cor invertível se auditor assumir outcome-semantics.
4. **`draw_xau_4h_trades.py`** — referência viva **como provedor do helper** (`price_to_ticks_offset`, MCPClient) · corpo (R-label, HORIZON 10) = **legacy declarado** pelo doc §7 · risco: copiar o corpo em vez do doc.
5. **Legacy/deprecated:** `candidates/xau_4h_reversal_v1_4g_rws_a6/plot_script.py` (bug preço absoluto, banner DO-NOT-RUN, citado no doc §9) · fase-plotters do regime engine (width 12, R-labels — pré-canon).

## 4. 4H plotting audit

- **Scripts:** `draw_xau_4h_trades.py` (helper canônico; corpo legacy R-label/width10) · `l2_plot_4h.py` (WIDTH **6** ⚠️, #id, ticks, outcome-color; fontsize 9) · `plot_capit_rsi_trades.py` (WIDTH **20** ✅) · `plot_t8_canonical.py` (ticks inline, #id, `entry+0.5R`, hard-stops ✅) · `plot_new_only.py`/`plot_poc_cut8.py` (BOX 20, azul sem-outcome ✅, label `target+0.4ATR` ≠ doc) · `plot_script.py` (DEPRECATED bug) · regime_turnstate `phase*_plot_*.py` (geradores de JSON p/ MCP; width 12, R-labels — legacy pré-canon).
- **Inputs/RAW:** todos partem de RAW-derivados (jsonl de replay, qual_packets, CSVs de outcomes) — RAW-first respeitado.
- **long_position:** universal nos vigentes; ticks corretos via helper compartilhado em todos os atuais.
- **Outcome field:** `close_R`/`realR`/R era-selected conforme fonte; cor sempre no label, nunca no widget.
- **Label:** #id nos atuais; R-value nos legacy; variantes documentadas (`#cut dp=…`, `F_STRICT #eid`).
- **Known issues:** width drift (6 vs 20) · corpo do script-referência stale · fase-plotters legacy sem banner.
- **Canonical candidate 4H:** doc atual §0–§9 + WIDTH 20 + #id + outcome-color — **praticamente pronto**; falta só marcar legacy e alinhar `l2_plot_4h.py`/`draw_xau_4h_trades.py`.

## 5. 15M plotting audit

- **Scripts (research/xau_15m_bb_nas_leonardo/):** estratégia (`plot_strategy_canonical`, `plot_chosen_canonical`, `plot_5atr_a2*`, `plot_5atr_regime170`) · visualização (`plot_reversals_canonical` F#/T#) · candidatos (`plot_candidates_canonical` WIDTH 10) · features (substrate4/sweptsempre/deeprange/cleansky/nas_cut — **clusters quase-duplicados**, alguns com `draw_clear` ⚠️) · exceções autorizadas (`plot_candidates_labels.py` text-only 1×; `plot_v2_visual.py` screenshots 1 engine).
- **Inputs/RAW:** `strategy_*_trades.csv` derivados do RAW 15M; BAR_S=900; ticks mintick 0.01 corretos em todos.
- **Outcome/label/cores:** #N cronológico universal; **duas gramáticas**: verde/vermelho por **outcome** (chosen/5atr — trades resolvidos) e por **direção LONG/SHORT** (strategy/candidates/reversals — a pedido do Cris); adds `#N·2u` laranja/azul; features em azul.
- **Referências de estratégia:** swept-runner/substrate #4/8ATR/regime detector aparecem como janelas plotadas — plotagem sempre pós-fato sobre CSV, sem acoplamento ao detector.
- **Known issues:** largura 8–12 (padrão de fato ~10) **não codificada em doc** · `draw_clear` em 4 scripts de feature vs regra "nunca apagar sem autorização" · duplicação alta (variantes iterativas de junho).
- **Canonical candidate 15M:** long/short_position WIDTH 10 + `#N` + gramática de cor **declarada por plot** (outcome OU direção) + SL/exit da fonte (A-flush −0.1ATR etc.) — vigente na prática, falta oficializar.

## 6. Conflict table

| # | Issue | Versão A | Versão B | TF | Consequência | Resolução proposta | Aprovação Cris? |
|---|---|---|---|---|---|---|---|
| 1 | Largura 4H | doc: 20 barras | `l2_plot_4h.py`: 6 (sliver!) | 4H | plots quase invisíveis em zoom | 20 = padrão 4H; alinhar script | Não (já decidido 06-18); só autorizar edição futura |
| 2 | Largura 15M | doc: 20 incondicional | Cris 06-26: "20 é demais p/ 15M" → 8–12 | 15M | doc contradiz instrução mais recente | **Codificar 15M = 10 barras** (default) no master | **Sim** (confirmar 10) |
| 3 | Label | doc: `#id` | `draw_xau_4h_trades.py` corpo + phase-plotters: R-value | 4H | copiar script = label errado | `#id` default; R só a pedido; marcar legacy nos scripts | Não (já decidido 06-14); edição futura sim |
| 4 | Gramática de cor | verde/vermelho = win/loss (doc §3) | verde/vermelho = LONG/SHORT (15M, a pedido Cris 06-26) | ambos | mesma cor, 2 semânticas — leitura ambígua de chart | Master define **2 modos nomeados** (outcome-mode default p/ trades resolvidos; direction-mode p/ sets mistos/sem outcome) + declarar modo em todo plot report | **Sim** |
| 5 | `draw_clear` | regra: nunca apagar sem autorização | 4 scripts de feature 15M limpam chart | 15M | risco de apagar desenhos do Cris | draw_clear só com flag explícita de autorização; marcar scripts | **Sim** |
| 6 | Screenshot | ban geral (06-09) | `plot_v2_visual.py` autorizado 1 engine | 15M | exceção não escrita no doc | Master codifica: screenshot só sob autorização explícita por-engine | Não (registrar como está) |
| 7 | Exit defaults | helper: stop −1.0ATR/target 2.7ATR | política candidatos: SL estrutural −0.1ATR/+3R; fontes com exit próprio (V_stair, let-run) | ambos | qual usar quando fonte omite? | Precedência no master: exit da fonte > política estrutural > default legacy (sempre DECLARAR) | **Sim** |
| 8 | Variantes de label | doc: só `#id` | F#/T#, `#N·2u`, azul candidato, `#cut dp=` | ambos | variantes vivem só em docstrings | Master lista variantes sancionadas | **Sim** (ratificar lista) |
| 9 | MEMORY_ARCHIVE:217 | "preços absolutos" (stale, pré-bug) | tudo mais: TICKS | ambos | leitura do archive pode reintroduzir bug | Archive é snapshot congelado — não editar; master reafirma ticks e aponta o stale | Não |
| 10 | Script bug vivo | `plot_script.py` DEPRECATED (preço absoluto) | — | 4H | rodar por engano | mantido banner-guarded; master lista em "what not to do" | Não |

## 7. Non-negotiable plotting rules (confirmadas pelas fontes)

1. **TODA plotagem = `long_position` (ou `short_position`) + `text` label — NUNCA lines/vertical_line/text-only** (regra ABSOLUTA Cris 2026-06-18, após 3 reincidências).
2. **`stopLevel`/`profitLevel` = OFFSETS EM TICKS** do entry; **XAUUSD mintick = 0.01** (confirmado; bug 2026-06-11). `point2` no TARGET (não no entry).
3. **Cores:** verde `#1a8917` / vermelho `#cc0000` / azul `#1565c0` (sem-outcome) — **só no label**, nunca no widget.
4. **Label default = `#<id cronológico>`** estável entre janelas/replots (Cris 2026-06-14); R/métricas só a pedido explícito.
5. **Full population para visual review de estratégia** ("Plota TODOS" nos plotters de estratégia 4H e 15M); amostras curadas existem (45 grupos, README 15M) mas são **calibração, nunca base rate/validação** — declarar quando for amostra.
6. **Nunca SLIM/proxy como fonte** — inputs de plot vêm de RAW/derivados com source_ref (RAW-first).
7. **Nunca screenshot** para conferir plotagem — verificação = `success` + `draw_list` (count/entity_ids); screenshot só a pedido explícito.
8. **Nunca apagar desenhos sem autorização**; chart vazio = limpeza manual do Cris (esperado).
9. **Production safety antes de tocar chart:** confirmar símbolo/TF com o Cris, pausar daemon **E** cron, pause flag quando aplicável, restaurar só com autorização.
10. **NUNCA plotar sem ler `docs/CANONICAL_TRADE_PLOTTING.md` antes** (regra absoluta do próprio doc).

## 8. What is not yet safe

- **Largura 15M**: sem doc — só docstring; risco de replots 15M com 20 barras.
- **Gramática de cor dupla** não reconciliada — chart de direção lido como chart de outcome inverte a interpretação.
- **Corpo do script-referência** stale (R-label, HORIZON 10): copiar o script sem ler o doc reproduz canon velho — exatamente o modo de falha das 3 reincidências.
- **Clusters duplicados 15M** (substrate4/sweptsempre/deeprange ×3-4 variantes) — qual é o vigente de cada família não está declarado.
- **4 scripts com `draw_clear`** sem gate de autorização.
- **Fase-plotters do regime engine** (width 12, R-label) sem banner legacy.
- **MEMORY_ARCHIVE:217** stale ("preços absolutos").

## 9. Recommendation

- **Canon 4H final (proposto):** exatamente o `docs/CANONICAL_TRADE_PLOTTING.md` vigente (ticks 0.01 · 2 shapes · point2@target · **largura 20** · label `#id` `entry+0.5R` bold 12 · verde/vermelho por outcome · azul sem-outcome · SL estrutural −0.1ATR/+3R p/ candidatos sem exit · precedência de exit da fonte · draw_list-only · sem delete/screenshot) + marcação legacy nos scripts dessincronizados.
- **Canon 15M final (proposto):** herda TUDO do 4H **exceto largura = 10 barras** (BAR_S=900) e admite **direction-mode** de cor (verde LONG/vermelho SHORT) para sets mistos/sem outcome — modo SEMPRE declarado no report do plot; variantes sancionadas: `F#/T#` (reversões), `#N·2u` (adds), azul features/candidatos.
- **Precisa de aprovação do Cris:** conflitos #2 (largura 15M=10), #4 (2 modos de cor nomeados), #5 (gate p/ draw_clear), #7 (precedência de exit), #8 (lista de variantes) — o resto já está decidido por ele e só precisa consolidação.

## 10. Next step

1. Cris aprova este audit (+ decisões #2/#4/#5/#7/#8) → criar **`docs/project_authority/PLOTTING_CANON_MASTER.md`** (canon 4H + 15M unificado, contratos de input/output, gramáticas, safety, templates, what-not-to-do).
2. Depois do master aprovado: ajustar scripts, se autorizado (alinhar `draw_xau_4h_trades.py` corpo, `l2_plot_4h.py` width, banners legacy, gate draw_clear).
3. Depois: criar **PLOTTING_CANON_AGENT** (workflow/skill versionado que lê o master, confirma TF/estratégia/fonte/output, nunca sampleia visual review, nunca SLIM, nunca toca produção, registra command+inputs+output+checksum, reporta conflito em vez de improvisar).

---
*Nenhum script editado · nenhum chart tocado · nenhuma produção alterada · Supabase só leitura. Fan-out executado com 2 subagents Explore reais (scripts + docs). Correção a um achado de subagent: os memory cards originais CONTINUAM no disco (verificado por leitura direta nesta sessão); o Supabase é espelho.*
