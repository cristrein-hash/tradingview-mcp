# Deep Dive — Caminho A L1 v1 F4+F5 (XAU 4H LONG continuation)

**Data:** 2026-06-16 · **Tipo:** análise/reconstrução read-only · **NOT_VALIDATION** (não roda backtest novo, não promove, não popula registry, não toca código/runtime/scheduler/Telegram/broker/RAW).

> Escopo deste documento: descrever, de forma neutra e técnica, o que foi a hipótese **Caminho A L1 v1 F4+F5**, como foi construída, quais gates reais tinha, o que sobreviveu de aprendizado, e onde ela se posiciona em relação à **L1 EMA21 CONTINUATION** atualmente operacional (que a absorveu). Toda métrica citada é **in-sample / reconstrução** salvo indicação explícita.

---

## 1. Sumário executivo

**Caminho A L1 v1 F4+F5** é a **semente / precursora** da estratégia hoje operacional **L1 EMA21 CONTINUATION**. Era um setup de **continuação de alta** em XAUUSD 4H: dentro de um uptrend (regime BULL D-1, EMA21>SMA50 com slopes positivos, BOS causal), entrar comprado no **pullback calmo** que toca uma zona de demanda (Custom OB v11) e retoma, filtrando por **volume baixo** (F5: `vol_ratio_med50 ≤ 1.0`).

Três fatos definem o status atual:

1. **F4 era um filtro inerte.** A descoberta canônica de 2026-06-07 (Cris autorizou) é que **F4 (`sell bubbles ≤ 7`) nunca cortou nenhum trade** sob qualquer mapping de bubbles. O resultado "aprovado" vinha **apenas de F5** (volume calmo). A hipótese é, na prática, **EMA21_A + F5**.
2. **A reconciliação numérica nunca fechou.** Existem 3 contagens incompatíveis do mesmo setup: **n=11** (histórico original), **n=16** (re-run 2026-06-07, F5-only), **n=38** (reconstrução rebuild_v3 sob RAW). Tentativas de reconstrução fiel (v1/v2) **falharam**; só a v3 (removendo o `R_CEIL 1.5ATR`) reaproximou a base rule do documentado.
3. **Foi absorvida pela L1.** O master inventory classifica F4+F5 como **`SUPERSEDED_BY_L1 / KEEP_REFERENCE`** — "precursor da L1 (absorvido)". A L1 atual estende a mesma base rule com stack v1 anti-extensão, NAS SHIFT1, RSI exhaustion gate e SL estrutural otimizado.

**Veredito:** F4+F5 é **referência histórica / linhagem**, não candidata viva. Não há nada operável nela que a L1 já não cubra. Seu valor hoje é didático: documenta de onde veio a base rule e quais leads ficaram parqueados.

---

## 2. Fontes lidas (read-only)

| Fonte | Caminho | Papel |
|---|---|---|
| Memória oficial F4+F5 | `memory/project_caminho_a_L1_v1_F4F5_status_candidato_escasso.md` | definição congelada + correção 2026-06-07 + leads |
| Reconstrução v1 | `my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/rebuild_v1/` (README, config.json, summary.json) | tentativa 1 → MISMATCH |
| Reconstrução v2 | `.../rebuild_v2/` (README, config.json, summary.json, candidates_pre_cooldown.jsonl) | tentativa 2 → FAILED_RECONSTRUCTION |
| Reconstrução v3 | `.../rebuild_v3/` (README, summary.json, trades.jsonl) | base rule + SL reconstruídos fielmente (R_CEIL off) |
| Re-derivação regime live | `.../rederive_regime_l1v4/` (README, .json, .py) | 38→63 candidatos sob `regime_l1_v4` |
| L1 aprovada — refinamento | `my-strategy/strategies/.../L1_EMA21_CONTINUATION/APPROVED_REFINEMENT_2026_06_16.md` | config aprovada que absorve F4+F5 |
| L1 aprovada — contrato | `.../L1_EMA21_CONTINUATION/STRATEGY.md` | banner de reclassificação + base rule + gate RSI |
| Inventário mestre | `docs/XAU_4H_STRATEGY_RESCUE_MASTER_INVENTORY.md` | classificação SUPERSEDED_BY_L1 / KEEP_REFERENCE |

**Não usado:** SLIM features (proibido como validação), RAW reprocessado novo (não rodei backtest), `/tmp` working files (efêmeros, já não confiáveis).

---

## 3. Identidade & hipótese

- **Arquétipo:** continuação de alta (pullback-and-go), **não** reversão de fundo nem breakout decisivo.
- **Ativo/TF/direção:** PEPPERSTONE:XAUUSD · 4H · LONG.
- **Tese mecânica:** num uptrend estabelecido, um **pullback sem volume excessivo** que toca demanda e retoma representa **absorção silenciosa** (retomada institucional), não distribuição/topo. O volume calmo (F5) é o discriminador central.
- **Linhagem:** parte da família **Caminho A** (continuação/natural-bull), irmã das frentes A1 BALANCE e A1' SUPERTREND (estas duas com look-ahead conhecido). É a **camada L1** dos "5 layers + 8 padrões visuais" do Caminho A.
- **Nome ≠ definição:** o nome "F4+F5" é enganoso — **F4 é inerte**; a hipótese real é **EMA21_A + F5**.

---

## 4. Processo de construção

1. **2026-06-06:** backtest L1 v1 roda. DA matemático **refuta** (9/15 PASS no checklist). Cris re-valida por **análise visual** (2 monumentais potenciais em 2024) + investigação de features ortogonais + sub-janela 4/4 anos confirmando direção. Exploração exaustiva de F4+F5 com Bonferroni honesto. **CANDIDATO ESCASSO** aprovado a risco normal (verbatim Cris: aceitar "L1 v1 + F4+F5 puro como CANDIDATO ESCASSO na suite ... SEM RESTRIÇÃO DE 0,25%").
2. **2026-06-07:** re-validação de F4 com mapping correto de bubbles (BUY=plot_0/2/4, SELL=plot_6/8/10). DA spawnado suspeitou de bug; verificações (distribuição global de plots + F5 isolado) confirmaram **não-bug**: F4 simplesmente nunca discriminou. Rebatizado **EMA21_A + F5 only**. Métricas re-validadas: **n=16, WR 43.8%, +31.74R**.
3. **2026-06-14 (rebuild v1):** fonte técnica original perdida (era `/tmp` volátil) → reconstrução a partir do RAW 4H + definição da memória. Resultado **n=3, MISMATCH** vs n=16. DA: `RECONSTRUCTION_UNFAITHFUL_NEEDS_FIX`.
4. **2026-06-14 (rebuild v2):** corrige hipóteses do DA. Mede `candidate_count_pre_cooldown=38`, mas ainda só 3 trades. **Cooldown REFUTADO como causa**; causa real = **`R_CEIL 1.5ATR` abortando 35/38 candidatos** (risco mediano 2.28 ATR). Veredito `FAILED_RECONSTRUCTION — STOP, buscar definição humana`.
5. **2026-06-15 (rebuild v3):** decisão do Cris = **manter stop largo, remover o `R_CEIL`** (esse era o conserto real). KEEP(19) reaproxima o documentado (+32.6R vs +31.74R). Base rule + SL **reconstruídos fielmente**. DA: `NEEDS_CAUSAL_FILTER_BEFORE_ANY_CLAIM` (KEEP é rótulo humano in-sample).
6. **2026-06-16 (re-derivação regime live):** ao unificar o scanner para `regime_l1_v4`, os 38 viram **63 candidatos** (38 preservados, +25 novos). Os números do set de 38 deixam de representar o regime que roda ao vivo.

---

## 5. Gates reais (definição congelada)

Base rule **EMA21_A** (todos causais, SHIFT1 onde repinta):

- Regime D-1 == **BULL** (na época via `regime_B_v3`; hoje a L1 usa `regime_l1_v4`).
- `close[i-1] > EMA21[i-1]` **e** `close[i-1] > SMA50[i-1]`.
- `EMA21[i-1] > EMA21[i-4]` (slope intraday +) **e** `SMA50[i-1] > SMA50[i-7]` (slope macro +).
- **BOS causal:** `highest_high(20)[i-1] > max(close[i-21..i-2])`.
- `ATR14` ratio em **[0.004, 0.030]** (ASSUMPTION: memória dizia "[0.4,3.0] USD", interpretado como ratio).
- **Zona de demanda Custom OB v11** elegível (box abaixo do preço) OU fallback EMA21_proxy. ASSUMPTION: RAW não traz label DEMAND/SUPPLY → "demand" = box geométrico abaixo do preço; SHIFT1 nas zonas.
- Toque: `low[i]` OU `low[i-1]` entrou na zona (tol. 0.1% OB / 0.2% MA).
- `close[i] > zona_high`; `body_pct[i] ≥ 0.35`; `close[i] > close[i-1]`; `ret_5bars > -4%` (anti-falso-fundo).
- **Cooldown** no-overlap (máx 1 trade L1 ativo).

Filtros adicionais:

- **F5 (ATIVO, único real):** `vol_ratio_med50 ≤ 1.0` (volume[i] / mediana(volume[i-50..i-1]) ≤ 1.0). Corta 29→16 trades, sobe WR 31%→43.8%, **preserva o monumental**.
- **F4 (INERTE, descartado):** `sell bubbles ≤ 7` nos 5 bars anteriores. Sob mapping antigo max=3; sob mapping correto **max=0** → ≤7 sempre trivialmente verdadeiro. Descartado **por inércia, não por mérito**.

Stop/exit congelados na memória (note a inconsistência do §7):

- **SL estrutural:** `min(low[i], low[i-1..i-4], zona_low) − 0.1·ATR14`; R floor 0.3·ATR, **R ceiling 1.5·ATR (abort)** ← este leg é o que quebrou as reconstruções.
- **Exit V_stair_A:** BE@+2R → +5R lock+1R → +8R lock+3R → +12R lock+6R → +16R lock+10R; target +20R; time_stop 60 bars.
- Slippage 0.1R determinístico.

---

## 6. Indicadores / features usados

| Feature | Fonte | Causalidade |
|---|---|---|
| EMA21 / SMA50 / slopes | closes RAW | causal (SHIFT1) |
| ATR14 | closes RAW | causal |
| BOS | highest_high(20) reconstruído | causal |
| Zona demanda | Custom OB v11 (`pine_boxes`) | SHIFT1 (repinta) |
| Volume (F5) | volume RAW | causal |
| Regime D-1 | `regime_B_v3` (época) / `regime_l1_v4` (hoje) | SHIFT1 (D-1) |
| Sell bubbles (F4) | Market Order Bubbles | SHIFT1 — **mas inerte** |

Leads não usados como gate (parqueados): `buy_bubbles_10b` (score direcional), `body_pct_prev` negativo (pullback forte → reclaim), concentração hora 18 UTC.

---

## 7. Estudos / backtests & métricas

Todas as métricas abaixo são **in-sample / reconstrução**. As três contagens nunca reconciliaram:

| Versão | n | WR | sumR | avgR | big15W | Status |
|---|---|---|---|---|---|---|
| Histórico original (memória, prosa) | 11 | 55% | +35.2R | — | 1 | não reproduzível hoje |
| Re-run 2026-06-07 (F5-only) | 16 | 43.8% | +31.74R | +1.98R | 1 (#2024-03-26 +18.19R) | métrica oficial da memória |
| rebuild_v1 | 3 | 33.3% | −0.3R | −0.1 | 0 | **MISMATCH** |
| rebuild_v2 | 3 (38 candidatos) | 33.3% | −0.3R | — | 0 | **FAILED_RECONSTRUCTION** |
| rebuild_v3 FULL-38 | 38 | 31.6% | +14.9R | +0.39 | — | base mecanizável honesta (fraca) |
| rebuild_v3 KEEP-19 (rótulo humano) | 19 | 57.9% | +32.6R | +1.72 | — | **ARTEFATO IN-SAMPLE** |
| rebuild_v3 BLOCK_TOP-17 | 17 | 5.9% | −15.6R | −0.92 | — | losers reais (split visual correto) |

**Causa-raiz do colapso 38→3 (decisiva):** não era cooldown (v2 refutou empiricamente — dedup local dropou 0). Era o **`R_CEIL 1.5ATR` abort**: 35/38 candidatos têm stop estrutural > 1.5 ATR (risco mediano 2.28, max 4.05). A config documentada é **auto-inconsistente** — aborta 35 dos seus próprios 38 candidatos. Remover o R_CEIL (rebuild_v3) foi o conserto que reaproximou o documentado.

**Monumental 2024-03-26:** rejeitado **pelos gates** em todos os 6 bars do dia (close_prev≤EMA21, ema21_slope3≤0, body<0.35, zone_not_touched) na reconstrução — `ENTRY_GAP_UNRESOLVED`. O trigger exato do original se perdeu.

---

## 8. Trades / candidatos relevantes

7 winners (re-run n=16, por final_R): **2024-03-26 +18.19R** (único big15W), 2024-09-10 +7.94R, 2025-09-25 +7.91R, 2022-02-16 +2.90R, 2022-03-03 +0.90R, 2020-08-03 +0.90R, 2024-05-14 +0.90R.

- O resultado depende **fortemente** do monumental 2024-03-26: sem ele, sumR cai de +31.74R para ~+13.5R.
- "Monumental" tem nomenclatura ambígua (Cris menciona 3; big15W matemático conta 1). Há candidatos ≥7R (2024-09-10, 2025-09-25) que o Cris pode considerar monumentais visualmente. **Reconciliação pendente** — não decidir aqui.
- No rebuild_v3, o split KEEP/BLOCK foi rotulado **vendo o chart com o resultado visível** (hindsight) → o colapso de DD 7.9R→1.3R é o tell de seleção por outcome.

---

## 9. Comparação vs L1 EMA21 CONTINUATION (aprovada 2026-06-16)

| Dimensão | F4+F5 (precursora) | L1 EMA21 CONTINUATION (atual) |
|---|---|---|
| Base rule | EMA21>SMA50 + slopes + BOS + OB + body≥0.35 + F5 | **mesma base rule** |
| Regime | `regime_B_v3` (morto p/ live) | **`regime_l1_v4`** (unificado scanner=runtime) |
| Filtros extras | F5 only (F4 inerte) | F5 + **stack v1** (ret5≤1.42%, ext_ema≤2.95ATR, zone_w≥0.6ATR, dist_zone≤1.81ATR) + **NAS SHIFT1≥1.31** + **RSI gate `rsi_vs_ma≤−9.35`** |
| Stop | estrutural `min(low i..i-4, zona_low)−0.1ATR` **+ R_CEIL 1.5ATR abort** (inconsistente) | **`max(zona_OB_low, swing6_low)−0.1ATR`** (R_CEIL removido) |
| Exit | V_stair_A (target +20R, TS 60) | **target +3R fixo** (neste refinamento) |
| n / métrica | 16 / +31.74R (in-sample, não reconciliado) | 31 ops / 17 TARGET / **+40.0R / PF 4.08** / 5/5 monumentais (in-sample full-scan) |
| Governance | CANDIDATO ESCASSO (risco normal) | **USER_APPROVED_FINAL · HUMAN_DISCRETIONARY** |
| Evidence | in-sample, escasso | in-sample, **NOT_VALIDATED_OOS** (risco assumido) |

**Conclusão da comparação:** a L1 é uma **superset estrita** da F4+F5 na base rule, com 3 camadas de seletividade novas e um SL melhor especificado (sem o R_CEIL que quebrava a precursora). Tudo que F4+F5 oferecia (continuação calma em uptrend + F5) está dentro da L1. **A F4+F5 não tem nenhum gate ou trade que a L1 não cubra.**

---

## 10. Riscos & contaminação

- **Reconciliação nunca fechou (11/16/38).** Indica que a config original tinha variação de trigger/stop **não documentada e perdida**. Qualquer número de F4+F5 carrega essa incerteza.
- **`regime_B_v3` (regime da época):** bias residual ~10.68% (`NEEDS_SHIFT1_AUDIT`), **não forward-computável** (gerador v1 perdido). Por isso a L1 migrou para `regime_l1_v4`. Não reabrir B_v3 live.
- **KEEP-19 é artefato in-sample** (rótulo humano com hindsight). Não é prova de edge. `mechanizable_now=false`.
- **Dependência de 1 monumental** (2024-03-26) para a expectância positiva — frágil a slippage e à definição exata de trigger (que se perdeu).
- **ASSUMPTIONs herdadas:** ATR band como ratio, OB demand = box geométrico (sem label), K_bars de dedup. Nenhuma introduz look-ahead novo, mas todas afetam contagem.
- **Causalidade:** sem leak temporal novo nas reconstruções (NAS first-appearance, swing 5/5, regime D-1, R por forward bars — OK). Risco é **seleção/hindsight + n pequeno**, não look-ahead.

---

## 11. Aprendizados reutilizáveis

1. **F5 (volume calmo) é o discriminador que sobreviveu** — "pullback sem volume excessivo = absorção silenciosa" virou parte permanente da base rule da L1.
2. **`R_CEIL` agressivo pode matar a própria estratégia silenciosamente** — abortou 35/38 candidatos sem alarme. Lição: stop largo = respiro/RxR para winners; um ceiling de risco precisa ser auditado contra a distribuição real de risco dos candidatos.
3. **Nome ≠ definição** — F4 parecia um gate ativo e era inerte. Reforça `[[feedback_name_vs_definition_mismatch]]`: comparar lista de componentes vs definição interna antes de concluir.
4. **Cooldown não-overlap pode (ou não) serializar** — aqui foi refutado como causa; medir antes de assumir.
5. **Reconstrução exige fonte fiel** — perder a fonte `/tmp` custou 3 rebuilds. Lição operacional: artefatos de pesquisa relevantes não vivem em `/tmp`.
6. **45 grupos / rótulo visual = calibração, não validação** (`[[feedback_calibration_vs_validation_45_groups]]`) — o KEEP-19 ilustra exatamente o artefato in-sample que esse princípio previne.

---

## 12. Melhorias potenciais (parqueadas, NÃO promover agora)

- **Lead #1 — `buy_bubbles_10b ≥ 10` como score** (winners 24.2 vs losers 12.6, Δ+11.6). Cuidado: F4+F6 puro perde o monumental (buy_10b=0 nele). Re-investigar com sample agregado da suite.
- **Lead #2 — `body_pct_prev` negativo em winners** (pullback forte → reclaim). Não testado como filtro; salvar p/ L2+.
- **Lead #3 — concentração hora 18 UTC** (London-NY close); inconsistente entre anos.
- **Hipótese F4 ≤ 2 stricter + F5** (in-sample n=13, +35.04R) — **parqueada** por decisão Cris; número derivado vendo os trades = in-sample puro. Exige pré-registro + set independente.
- Todas essas melhorias hoje pertencem mais à **L1 / camadas futuras (L2-L5)** do que a reabrir F4+F5.

---

## 13. Veredito

**Caminho A L1 v1 F4+F5 = `SUPERSEDED_BY_L1 / KEEP_REFERENCE`.**

- É a **linhagem/semente** confirmada da L1 EMA21 CONTINUATION. Foi **absorvida**: a L1 contém sua base rule inteira mais 3 camadas de seletividade e um SL melhor.
- **Não há nada operável nela que a L1 não cubra.** Não é candidata viva; não deve ser reaberta como estratégia independente.
- Seu valor é **didático/referência**: documenta a origem da base rule, a descoberta de que F4 era inerte, e a lição do R_CEIL.
- Seus números (11/16/38, +31.74R) são **in-sample e não-reconciliados** — não usar como prova de edge em nenhum contexto.

---

## 14. Próximo bloco recomendado

Coerente com o master inventory (Caminho B é **P0** para próxima reanálise profunda):

1. **Não reabrir F4+F5.** Arquivar como referência (este doc já cumpre isso).
2. **Foco da L1:** o gargalo real da L1 é **validação OOS** (`NEEDS_RAW_BACKTEST`) — gate manifest + RAW OOS (holdout forward ou cross-asset EUR/USOUSD) com thresholds congelados, ≥8-10 losers novos bloqueados / 0 winners novos.
3. **Próxima reanálise estrutural:** Caminho B gate manifest (P0 no inventário), separado deste continuation thread.
4. Qualquer lead de F4+F5 (buy_10b, body_prev) só entra como hipótese **de uma camada nova (L2+)**, com pré-registro + set independente — nunca como reabertura da F4+F5.

---

## 15. Apêndice — Devil's Advocate

Pontos céticos levantados ao longo das reconstruções (preservados como contraponto permanente):

- **"F4+F5 funcionava?"** — Indeterminado. As 3 contagens (11/16/38) nunca reconciliaram; rebuild_v1/v2 falharam; só v3 (com R_CEIL removido) reaproximou. A config documentada é auto-inconsistente. Nenhum número de F4+F5 é confiável como medida de edge.
- **"KEEP-19 +32.6R não prova edge?"** — Correto, não prova. Foi rotulado com hindsight (DD 7.9→1.3R é o tell). `NEEDS_CAUSAL_FILTER_BEFORE_ANY_CLAIM`, `mechanizable_now=false`. O composto objetivo (nas_short20≥2 AND ext≥3) **não** reproduz o BLOCK_TOP visual (pega 8/17, erra 6 KEEP winners) → o julgamento visual codifica info que as features não capturam.
- **"A base mecanizável honesta?"** — FULL-38 +14.9R / WR 31.6% / avgR +0.39 — fraca e frágil a slippage. É o que uma regra puramente causal entrega hoje.
- **"Há look-ahead?"** — Não-novo. O único resíduo é o `regime_B_v3` (~10.68% bias, herdado) que inflaria, não suprimiria — e já foi abandonado para live (`regime_l1_v4`).
- **"A L1 herda os mesmos problemas?"** — A L1 também é **in-sample / NOT_VALIDATED_OOS** com n pequeno (31-34). A diferença é governança (USER_APPROVED_FINAL, risco assumido pelo Cris) e regime live correto — **não** validação estatística independente. O ceticismo sobre edge se aplica igualmente; o que a L1 ganhou foi seletividade causal e SL coerente, não prova de edge.
- **"Por que arquivar e não reabrir?"** — Porque reabrir F4+F5 seria re-trabalhar uma config perdida/inconsistente cujo melhor caso já está absorvido na L1. O ROI está em validar a L1 OOS, não em reconstruir a precursora.

---

*Documento read-only. Nenhum backtest novo rodado, nenhum código/runtime/scheduler/catalog/registry/Telegram/broker/RAW tocado. Métricas citadas são in-sample/reconstrução conforme as fontes do §2.*
