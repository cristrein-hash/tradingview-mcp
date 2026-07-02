# PLOTTING CANON MASTER — 4H + 15M (fonte única de verdade)

**Criado:** 2026-07-02 · **Base:** `docs/architecture/PLOTTING_MEMORY_AUDIT_20260702.md` (aprovado) + decisões Cris 2026-07-02.

## 1. Executive status

**DRAFT_PENDING_USER_REVIEW** — conteúdo reflete as 5 decisões aprovadas pelo Cris em 2026-07-02 + canon vigente consolidado; vira APPROVED quando o Cris revisar este documento inteiro.

## 2. Authority

- Este master é a **fonte única de verdade** para plotagem canônica **4H + 15M**. Substitui docs dispersos e docstrings conflitantes.
- **Antes de QUALQUER plot canônico: ler este master.** (Herda a regra absoluta Cris 2026-06-18: "NÃO AUTORIZO NUNCA NENHUMA PLOTAGEM QUE NÃO SEJA CANÔNICA NESTE PROJETO".)
- `docs/CANONICAL_TRADE_PLOTTING.md` fica **incorporado/compatibilizado** (continua válido para mecânica 4H de shapes/ticks; onde divergir deste master — 15M width, modos de cor, exit precedence — **este master prevalece**). Não ignorá-lo: ele contém o detalhe operacional §0–§9.
- Em conflito com memória/docstring/script antigo: **este master > CANONICAL_TRADE_PLOTTING.md > tudo o mais**.

## 3. Global rules

1. RAW/source-first — todo input de plot deriva de RAW/fonte de autoridade com source_ref.
2. **Nunca SLIM/proxy** como fonte/validação.
3. **Nunca samplear visual review** de estratégia — plotar a população completa; amostra curada só como calibração e **declarada**.
4. Nunca tocar chart/TradingView/MCP sem autorização explícita + production safety (§11).
5. **Nunca limpar chart** (draw_clear/delete) sem autorização explícita — default **NO_CLEAR**.
6. Nunca alterar produção/runtime/daemons/Telegram/RAW num bloco de plotagem.
7. Todo plot registra: input, output, command, mode, counts, checksum quando houver ficheiro (§12).
8. Verificação = `success` por shape + `draw_list` (count/entity_ids). **Nunca screenshot** salvo pedido explícito por-engine.

## 4. Canon 4H

- **Shapes:** 2 por trade — `long_position` (`point`=entry; **`point2` = (entry_time + 20×14400, target_price)**) + `text` label. `short_position` quando aplicável (§9).
- **Width = 20 barras** (Cris 2026-06-18). `bar_seconds = 14400`.
- **Ticks:** `stopLevel`/`profitLevel` = offsets em ticks — `round(|nível − entry| / 0.01)`; **XAUUSD mintick = 0.01**. NUNCA preço absoluto (bug 2026-06-11).
- **Label padrão:** `#<chronological_id>` (estável entre janelas/replots; `#1` = mais antigo), posição `entry + 0.5×R_dollars`, bold, fontsize 12.
- **Cor default = outcome-mode** para trades resolvidos (§6).
- **Outcome source:** `close_R`/`realR`/R da fonte — declarado no report. Exit precedence: §8.
- **Usos aceitos:** visual review de estratégias/backtests/candidatos 4H sobre CSV/JSONL RAW-derivado, população completa.
- **Proibidos:** vertical_line/text-only como substituto · overrides inventados (`transparency`, `linewidth`…) · `point2` no entry · cor no widget · copiar o corpo de `draw_xau_4h_trades.py` sem ler este master (corpo stale — §13).

## 5. Canon 15M

- Herda TUDO do canon 4H, exceto:
- **Width = 10 barras** (Cris 2026-06-26/2026-07-02: "20 é demais p/ 15M"). `bar_seconds = 900` → `point2.time = entry_time + 10×900`.
- **Label padrão:** `#<chronological_id>`, salvo variante aprovada (§7).
- **Cor:** default outcome-mode para trades resolvidos; **direction-mode permitido** para features/candidatos/sets mistos/sem outcome (§6).
- **Tick:** XAUUSD 0.01 (idem).
- **Outcome/exit:** precedence §8 (ex.: SL A-flush −0.1ATR + exit let-run real quando a fonte define).
- **Regime/swept-runner/substrate #4/8ATR:** entram como **contexto declarado pela fonte** (coluna/campo do CSV), nunca como regra visual inferida automaticamente pelo plotter.

## 6. Color grammar — 2 modos oficiais (PLOTTING_COLOR_MODES_APPROVED)

- **outcome-mode (DEFAULT para trades resolvidos):** verde `#1a8917` = winner (`close_R > 0`) · vermelho `#cc0000` = loser (`close_R <= 0`). **Só usar quando outcome/close_R (ou equivalente confiável) estiver definido.**
- **direction-mode:** verde = LONG · vermelho = SHORT. Para candidatos, features, sets mistos, sem outcome, ou quando a direção é o objeto visual.
- **Obrigatório:** todo plot report declara `color_mode = outcome-mode | direction-mode`.
- **Não fazer:** misturar os dois modos num mesmo chart sem separação declarada · usar outcome-mode com exit assumido/legacy como se fosse validado · cor no widget long_position (cor é SÓ do label; exceção: borda win/loss em geradores JSON legacy — não replicar em plots novos).
- Azul `#1565c0` = sem-outcome/candidato/feature (neutro), em qualquer modo.

## 7. Label grammar (PLOTTING_LABEL_VARIANTS_APPROVED)

- **Padrão principal:** `#<chronological_id>`.
- **Variantes sancionadas:** `F#`/`T#` (fundos/topos em plots de reversão) · `#N·2u` (adds/segunda unidade) · **azul** para candidatos/features (com declaração).
- **Regra:** qualquer variante não-padrão (inclusive R/métricas no texto, `#cut dp=`, sufixos) **precisa ser declarada no report** — e R/métricas só a pedido explícito do Cris.
- Posição: `entry + 0.5×R_dollars` (default); alternativas (ex. `target+0.4ATR` em candidatos azuis) = declarar.

## 8. Exit/outcome contract (PLOTTING_EXIT_PRECEDENCE_APPROVED_WITH_LEGACY_WARNING)

Precedência: **1) exit da fonte explícita** (V_stair, let-run real, SL/TP do CSV) → **2) política estrutural documentada** (SL estrutural = low da zona/swing −0.1×ATR14; TARGET = +3R — Cris 2026-06-16) → **3) default legacy declarado** (stop −1.0ATR / target +2.7ATR do helper).

- 🚨 **Regra crítica (Cris 2026-07-02):** se cair no nível 3, o report marca **`EXIT_ASSUMED_LEGACY`** — obrigatório e destacado. **Default legacy NUNCA é tratado como outcome validado**; nesse caso outcome-mode é PROIBIDO (usar azul/direction-mode), porque não há outcome real.
- **outcome-mode só com outcome confiável** (campo de R realizado vindo da fonte). Se o "outcome" foi fabricado por exit assumido → não é outcome.
- Sempre declarar `exit_policy` no report (§12).

## 9. Marker placement / long_position

- **Uso oficial:** `long_position` para trades LONG; `short_position` para trades SHORT. A direção vem do **campo de direção da fonte** (ou gate real documentado) — **nunca inferida do nome do script/variante** sem checar os gates reais.
- `point` = (entry_time, entry_price) · `point2` = (entry_time + width×bar_seconds, target_price) — point2 **no target** (caixa cheia).
- Overrides: SÓ `stopLevel`/`profitLevel` em ticks. Validações hard-stop (herdadas do helper): entry>stop (long), target>entry (long), ticks>0, campos completos — violação = não plota.
- 1 label `text` por trade, canal do id/cor (§6–7).

## 10. Width policy

- **4H = 20 barras** (14400s/bar) · **15M = 10 barras** (900s/bar) — `PLOTTING_15M_WIDTH_CANON = 10_BARS`.
- Qualquer outra largura = **justificativa + declaração no report**. Largura <~6 barras = sliver invisível (proibida). `createShape` de 1 ponto (sem point2) = largura default errada (proibido).
- Outros TFs (futuro): definir width explicitamente antes de plotar; não extrapolar sem aprovação.

## 11. Safety rules

- **DRAW_CLEAR_REQUIRES_EXPLICIT_APPROVAL:** default NO_CLEAR. Qualquer script/execução que limpe chart/labels/drawings/overlays deve declarar isso, pedir autorização explícita, e nunca limpar chart vivo automaticamente. Chart vazio antes de plotar = limpeza manual do Cris (esperado); nunca apagar desenhos dele.
- **Chart interaction safety (antes de plotar):** confirmar com o Cris símbolo (PEPPERSTONE:XAUUSD) e timeframe · pausar daemon **E** cron que tocam o chart · criar pause flag quando aplicável (`/tmp/claude_recheck.paused`) · plotar · validar via `draw_list` · **restaurar só com autorização**.
- Produção/runtime/daemons/Telegram/receiver/RAW intocados em qualquer operação de plot.
- Nenhuma interação TradingView/MCP sem autorização explícita do Cris para aquele plot.
- Nunca screenshot como verificação (exceção por-engine só com autorização explícita registrada).

## 12. Report contract — todo plot reporta

`symbol` · `timeframe` · `strategy/family` · `source_file` (+ checksum se aplicável) · `outcome_source` · `color_mode` (outcome|direction) · `width` (barras) · `label_mode` (padrão ou variante declarada) · `exit_policy` (fonte|estrutural|**EXIT_ASSUMED_LEGACY**) · `script_used` · `output_path` (se houver) · `counts` (trades plotados / shapes criados / draw_list total) · `warnings` (conflitos, campos faltantes, trades pulados) · `checksum` de ficheiro de output quando existir.

## 13. Script reconciliation list (detectado no audit — **NÃO alterar neste bloco**)

- `alert-bridge/draw_xau_4h_trades.py` — **corpo stale** (label R-value, HORIZON 10); válido SÓ como provedor de `price_to_ticks_offset`/`MCPClient`. Revisão futura: alinhar corpo ao master ou banner "helper-only".
- `my-strategy/research/revalidation/l2_plot_4h.py` — width **6** (viola §10; sliver). Revisão futura: 20.
- 15M widths 8/12 (`plot_substrate4` 8, `plot_chosen_canonical` 12) — normalizar para 10 ou declarar.
- **4 scripts 15M com `draw_clear`** (`plot_substrate4/flow_tagged/cleansky/nas_cut` + `plot_choch`) — adicionar gate de autorização (§11).
- `candidates/xau_4h_reversal_v1_4g_rws_a6/plot_script.py` — **DEPRECATED (bug preço absoluto)**, banner-guarded; nunca executar.
- `regime_turnstate_engine/validation/phase*_plot_*.py` — legacy pré-canon (width 12, R-labels); banner legacy futuro.
- Clusters duplicados 15M (substrate4/sweptsempre/deeprange ×3-4) — declarar vigente por família em revisão futura.
- `MEMORY_ARCHIVE.md:217` — wording stale ("preços absolutos"); snapshot congelado, não editar; TICKS prevalece (§4).
- `docs/CANONICAL_TRADE_PLOTTING.md` — atualizar em revisão futura com ponteiro para este master (15M width + color modes).

## 14. Approval section

**Decisões aprovadas pelo Cris (2026-07-02):**
- PLOTTING_15M_WIDTH_CANON = 10_BARS
- PLOTTING_COLOR_MODES_APPROVED (outcome-mode default p/ resolvidos · direction-mode p/ candidatos/features/mistos/sem-outcome · declaração obrigatória)
- DRAW_CLEAR_REQUIRES_EXPLICIT_APPROVAL (default NO_CLEAR)
- PLOTTING_EXIT_PRECEDENCE_APPROVED_WITH_LEGACY_WARNING (fonte > estrutural > legacy declarado; **EXIT_ASSUMED_LEGACY obrigatório**; legacy nunca vira outcome validado)
- PLOTTING_LABEL_VARIANTS_APPROVED (`#id` padrão · F#/T# · #N·2u · azul candidatos/features · variantes declaradas)
- (Herdadas, já decididas antes: width 4H=20 · label #id · ticks 0.01 · long_position+label sempre · sem screenshot · sem delete · full population.)

**Pendências (não-blockers):** revisão futura dos scripts listados em §13 (só após aprovação deste master) · atualização de `CANONICAL_TRADE_PLOTTING.md` com ponteiro · criação do PLOTTING_CANON_AGENT (workflow/skill) após aprovação.

**Status final: DRAFT_PENDING_USER_REVIEW** — aguardando revisão integral do Cris para virar `PLOTTING_CANON_MASTER_APPROVED`.
