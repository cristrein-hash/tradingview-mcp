# XAU 15M LONG — MARKUP-DEMAND + FILTER N83 · PRÉ-REGISTRO / MANIFEST

**Versão:** 1.0 · **Data:** 2026-07-09 · **Protocolo:** `XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1 = ACTIVE`

## 1. Status
**`BLOCKED_BASE_EVENT_SELECTION_LOOKAHEAD`** (SL/exit review 2026-07-09; era `PASS_READY_FOR_TEST_AUTHORIZATION` pós-recovery).
**🚨 SL/EXIT REVIEW (FINAL DA = FAIL_LEAK_OR_NOT_REPRODUCIBLE):** a base N96 tem **event-selection lookahead** — 94/96 entries disparam ANTES da confirmação do pivô de demanda (zz r=6 confirma com rally FUTURO de 6 ATR; mediana 20 barras cedo; 0 lower-lows entre entry e confirmação = survivorship). Análogo live-fireable ≈ **N173 · WR 28,3% · +23R** vs backtest 54,2%/+112R. Os headline numbers (62,7%/+125R) **não são reproduzíveis por executor causal**. Achados condicionais que transferem p/ base reparada: SL V1 domina alternativas; 3R fixo = perfil FN; 4R/timestop = beta. Docs: `XAU_15M_N83_SL_EXIT_{FINAL_DA,STATUS_UPDATE}.md` + `xau_15m_n83_confirmation_leak_check_result.json`. **Pré-condição de qualquer teste futuro: reparar a base (entries gated em conf_i OU universo live-fireable ~173) — decisão do Cris.**
**RECOVERY:** o Cris corrigiu o diagnóstico — o PDF do Desktop (`Sistema_Agentico_Trading_XAU_LONG_PT.pdf`, 2026-07-08, tabela "A SUITE APROVADA") reporta **Markup-Demanda + Filtro Capitulação · 15M · 96 → 83 · 62,7% · +125R**. Usando o PDF **só como ponte de proveniência** (não validação), a fonte real foi recuperada e verificada mecanicamente do repo (`reports/n83_source_recovery_verify.py` → `SOURCE_RECOVERED`): **"Filter N83" = INTRA-BEAR CAPITULATION FILTER sobre o N96** (96−13 cortados=83 · 52W/31L=62,65%≈62,7% · 52×3−31×1=+125R — match exato nas 3 métricas). Nenhum backtest novo corrido.

## 2. Objetivo
Preparar o estudo **XAU 15M LONG — Markup-Demand + Filter N83** sob o protocolo 15M V1, sem produção.

## 3. Não-objetivos
Não produção · não Telegram · não broker · não SHORT · não tratar swept-runner como oficial · não otimização · não transformar pesquisa em validação · não rodar backtest neste bloco.

## 4. Unidade de análise
**Episódio markup-demand → entrada causal por reclaim** (unidade do engine N96). 1 registro = 1 evento de demanda de perna (leg-walk MASTER) com entrada causal = reclaim EMA21 pós-demanda. **CONGELADA** para a base. ⚠️ Se "Filter N83" alterar a população (ex.: filtro que reduz N96→~83), a unidade permanece a mesma (episódio), muda só o subconjunto — **não trocar unidade no processo**.

## 5. Filter N83 — **RECUPERADO: INTRA-BEAR CAPITULATION FILTER**
> Histórico: a busca literal por `N83`/`filter_n83` = 0 matches levou ao verdict inicial `BLOCKED_MISSING_N83` (erro: grep-por-nome não bastava). O Cris corrigiu apontando o PDF como prova de que a fonte existia. Recovery via ponte de proveniência (2026-07-09).

**Definição real (fonte: `docs/architecture/XAU_15M_N96_INTRA_BEAR_CAPITULATION_FILTER_20260708.md`):**
- **Predicado:** `SKIP se macro_regime == BEAR (v5 hour-causal) E 1D_px_vs_ema >= 0` (preço de entrada no/acima da EMA 1D, último bar 1D **fechado**, ATR-normalizado = repique raso, não-capitulação). KEEP se bem abaixo (capitulação funda). **BULL/RANGE: sem filtro** (lógica bear-específica por construção, prior estrutural RTSE).
- **Efeito:** corta **13 trades = 13 losers / 0 winners** (ids: 24,25,55,56,57,58,59,66,67,79,83,84,85) → **N96→N83** · 52W/31L · WR 62,7% · +125R@3R (verificado mecanicamente: `n83_source_recovery_verify_result.json` = `SOURCE_RECOVERED`, match 3/3 com o PDF).
- **Causalidade:** PASS (DA original: `1D_px_vs_ema` recomputado do RAW = último bar 1D fechado; regime hour-causal; 0 winners cortados robusto em todas as variantes de detector).
- **Nulls (do bloco original):** feature-search P=0.005 · within-bear P=0.001 · joint 3-regime P=0.007.
- **Descoberta:** in-sample sobre os losers do N96 (multiplicidade paga pelo feature-search null; a feature escolhida foi a teórica, não a de máx-separação).
- **Proveniência completa:** script `n96_fase1_fase2_maps.py` (gera `cut_trades.csv` + family map; contém o predicado `CUT=[... if REG=="BEAR" and px>=0]` com assert fail-loud anti-winner) → `results/n96_intra_bear_cut_trades.csv`; `n96_intra_bear_cut_list.json` commitado em `a32b25a` sem gerador nomeado (atribuição imprecisa — conteúdo reproduz exatamente do predicado, verificado cego) → doc 20260708 → commit **`a32b25a`** (2026-07-08 01:08, ANTERIOR ao PDF 11:36 — direção da cadeia correta) → PDF do Desktop (ponte).
- **Verificação endurecida (DA):** `n83_source_recovery_verify.py` agora (i) checa os 13 ids contra `out` da BASE, (ii) aplica o predicado **cego aos 96** (winners incluídos) → seleciona exatamente os 13, zero winners (todos os 16 BEAR-winners têm `1D_px_vs_ema` < 0). Edge-case latente documentado: gerador usa `or -99` → `1D_px_vs_ema==0.0` seria KEEP (falsy); 0 ocorrências no dataset.
- **Status:** `USER_APPROVED_NOT_PRODUCTION` (parte da aprovação N96, Cris 2026-07-08) · `PROFITABLE_BUT_FRAGILE` — **magnitude +4…+13R conforme detector (nunca citar +13 solto)**; N pequeno; 11/13 cortes num único bear (2026); HTF congela 2026-05-24.

**Classificação N83: `CANDIDATE_FILTER` (causal, mapeado, aprovado-não-produção).**

## 6. Universo (base markup-demand — mapeado)
- **Símbolo:** PEPPERSTONE:XAUUSD · **Timeframe:** 15M · **Período:** ago-2025 → 2026-07-03 (janela do master).
- **Fonte RAW:** `research/xau_15m_bb_nas_leonardo/` (RAW 15M + primitives + htf_primitives nativos). Lineage via blocker `scripts/safety/check_xau_15m_raw_lineage.py`.
- **Base:** engine N96 (`entry_engine_master_20260707.py` → `results/entry_engine_master_20260707.json`, list N=164, subconjunto `kind='markup'` = 96 sinais / 52W). Status: swept-runner = `RESEARCH_BASE_NOT_OFFICIAL`; N96 = `USER_APPROVED_NOT_PRODUCTION`.

## 7. Campos obrigatórios — RAW/source mapping
| campo | fonte | causal? | estado |
|---|---|---|---|
| `macro_regime` (v5 causal) | `results/n96_causal_regime.json` · regime v5 4H-native | sim (D-1/causal) | ✅ mapeado |
| `leg_state` / `position_in_leg` | leg-walk MASTER (`leg_walk_reader_20260707.py`, zigzag r=6) | sim | ✅ mapeado |
| `family_label` | `results/n96_loser_family_map_corrected.csv` (famílias de loser: topo/bear/range/D) | pós-hoc (rótulo) | ⚠️ **PARCIAL — loser-only (44/96; winners SEM rótulo de família)**; cobertura completa de family_label p/ os 96 = pendência antes do teste |
| markup-demand primitives (demand zone, reclaim, drop, sweep, box96) | `entry_engine_master_20260707.json` keys (`d,ent,sl,tgt,reclaim_lag,drop,sweep,box96,ema_dist,cascade,choch_since_lo,bos_since_lo`) | sim (forward-only outcome `out`) | ✅ mapeado |
| entry/SL/target | `ent`/`sl`/`tgt` (reclaim EMA21; SL=demand−0,1ATR V1; 3R) | sim | ✅ mapeado |
| **Filter N83 predicates** | `macro_regime` = v5 hour-causal (`n96_causal_regime.json`) · `1D_px_vs_ema` = RAW 1D último bar fechado, ATR-norm (`n96_intra_bear_cut_trades.csv` col `1D_px_vs_ema`) | sim (ambos conhecidos no fecho da barra de entrada) | ✅ **RECUPERADO/mapeado** |

## 8. Predicados exatos
- **Markup-demand (base):** evento de demanda de perna (higher-low, tendência intacta) da caminhada MASTER; entrada = 1ª barra de reclaim EMA21 pós-demanda; SL = zona_demanda − 0,1ATR; target = +3R; outcome = forward-only (`out`). **[DEFINIDO]**
- **Filter N83 (recuperado):** `SKIP se macro_regime==BEAR (v5 hour-causal) E 1D_px_vs_ema >= 0`; KEEP capitulação funda; BULL/RANGE sem filtro. **[DEFINIDO]**
- **Exits/SL:** os da base (SL=demand−0,1ATR V1; +3R fixo) — inalterados pelo filtro.

## 9. Baldes structural-first (canónicos do protocolo)
`BULL_impulse · BULL_pullback · BULL_excess_top · RANGE_neutral · RANGE_distribution_top_bear · RANGE_accumulation_bottom · BEAR_active · BEAR_shallow_bounce · BEAR_deep_capitulation · countertrend_bounce_in_bear · management_do_not_filter`. Regra-mãe: **indicador só vira evidência DENTRO de balde** (macro_regime + leg_state + family_label). Blocker: `check_xau_15m_structural_first.py`.

## 10. Claims ledger inicial
| claim | source | status | evidence | allowed? |
|---|---|---|---|---|
| Existe comparação N96→N83 | PDF Desktop 2026-07-08 (ponte) + repo | VERIFIED | tabela "96 → 83 · 62,7% · +125" | sim (proveniência) |
| PDF = ponte de proveniência, não validação | este prereg | RULE | — | — |
| Fonte real recuperada | `n83_source_recovery_verify.py` → `_result.json` | **VERIFIED (SOURCE_RECOVERED)** | match 3/3: N 96→83 · WR 62,7 · +125R derivados do repo | sim |
| Predicado real = intra-BEAR capitulation (BEAR-v5 & 1D_px_vs_ema≥0) | doc 20260708 + cut_list/cut_trades | VERIFIED | 13 ids, 13L/0W | sim |
| Filtro é causal | DA original (doc 20260708) | VERIFIED (causalidade PASS) | 1D bar fechado; regime hour-causal | sim |
| Filtro NÃO depende de outcome como input | doc + CSV campos | VERIFIED (descoberto in-sample; multiplicidade paga P=0.005) | features causais; outcome só como label | sim, c/ caveat FRAGILE |
| Filtro tem RAW mapping | §7 | VERIFIED | macro_regime v5 + 1D_px_vs_ema | sim |
| Estratégia aprovada? | STATUS_MASTER §4.6 | `USER_APPROVED_NOT_PRODUCTION` | Cris 2026-07-08 | não é produção |
| Próximo teste autorizado? | — | **NÃO** (aguarda autorização explícita do Cris) | — | — |
| "Filter N83" como nome literal no repo | busca | REFUTED (0 matches) — o nome é do PDF; o filtro real chama-se intra-BEAR capitulation | grep vazio | contexto |

## 11. Sanity checks obrigatórios antes de teste (quando N83 desbloquear)
timestamp alignment · no future leak (outcome forward-only já é) · no outcome fields como feature · no proxy/SLIM · coverage · missingness · family_label availability · consistência macro/leg · **source guard `check_xau_15m_raw_lineage.py` = RAW_LINEAGE_PASS** · **structural-first `check_xau_15m_structural_first.py`** · **claims ledger `check_xau_15m_claims_ledger.py`** · gate `run_xau_15m_lab_gate.py` = `XAU_15M_LAB_GATE_PASS`.

## 12. DA obrigatório para o próximo bloco
source DA · causality DA · mapping DA · metric DA · overfit/selection DA — **via Agent tool real** (Stage 7 do protocolo).

## 13. Critérios de PASS para autorizar teste futuro
Todos os campos mapeados RAW/source ✅ · **N83 definido por predicado real ✅ (recuperado)** · unidade congelada ✅ · manifest completo ✅ · nenhum outcome leak como input ✅ · nenhum proxy ✅ · sanity ready ✅ (pendência leve: family_label 96/96 se algum estudo futuro a usar como gate). → **CUMPRIDO: `PASS_READY_FOR_TEST_AUTHORIZATION`.**

## 14. Critérios de BLOCKED (histórico)
- ~~`BLOCKED_MISSING_N83`~~ → **resolvido por recovery 2026-07-09** (PDF como ponte → fonte real no repo).
- Restante: nenhum. Caveats herdados do filtro: `PROFITABLE_BUT_FRAGILE` (+4…+13R), N pequeno, concentração 2026, HTF congela 2026-05-24.

## Estado / próximo passo
`PREREG_ONLY_NOT_TESTED` · **`PASS_READY_FOR_TEST_AUTHORIZATION`** · **NÃO rodar teste sem autorização explícita do Cris.** A base (N96) e o filtro (intra-BEAR capitulation → N83) estão definidos, causais e mapeados; qualquer estudo novo sobre esta combinação passa primeiro pelos blockers do gate 15M (`run_xau_15m_lab_gate.py`). PRODUÇÃO/Telegram/broker/runtime = intocados.
