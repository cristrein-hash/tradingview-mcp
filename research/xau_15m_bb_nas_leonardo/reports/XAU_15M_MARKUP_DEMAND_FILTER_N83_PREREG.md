# XAU 15M LONG — MARKUP-DEMAND + FILTER N83 · PRÉ-REGISTRO / MANIFEST

**Versão:** 1.0 · **Data:** 2026-07-09 · **Protocolo:** `XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1 = ACTIVE`

## 1. Status
**`PREREG_ONLY_NOT_TESTED`** · **`BLOCKED_MISSING_N83`** (ver §5/§14). Bootstrap + localização de fontes + mapeamento feitos; **nenhum backtest corrido**. A base markup-demand está mapeada; **"Filter N83" NÃO foi localizado como filtro definido** → o lab não pode ser autorizado até o Cris desambiguar o que "N83" significa.

## 2. Objetivo
Preparar o estudo **XAU 15M LONG — Markup-Demand + Filter N83** sob o protocolo 15M V1, sem produção.

## 3. Não-objetivos
Não produção · não Telegram · não broker · não SHORT · não tratar swept-runner como oficial · não otimização · não transformar pesquisa em validação · não rodar backtest neste bloco.

## 4. Unidade de análise
**Episódio markup-demand → entrada causal por reclaim** (unidade do engine N96). 1 registro = 1 evento de demanda de perna (leg-walk MASTER) com entrada causal = reclaim EMA21 pós-demanda. **CONGELADA** para a base. ⚠️ Se "Filter N83" alterar a população (ex.: filtro que reduz N96→~83), a unidade permanece a mesma (episódio), muda só o subconjunto — **não trocar unidade no processo**.

## 5. Filter N83 — **NÃO LOCALIZADO (BLOCKED)**
Busca exaustiva no repo: `N83` / `filter_n83` / `FILTER_N83` = **0 matches literais**. O token `#83` que existe é **um ÍNDICE DE TRADE loser** (topo/exaustão): `XAU15M_TOTAL_STRUCTURAL_READING` "#82R winner vs **#83**,#84,#85 losers"; Kaufman-ER "corta losers topo #21/23/55/**83**". **Não há predicado/threshold/artifact chamado "N83".**

**Candidatos plausíveis ao que "N83" pode designar (Cris deve escolher — NÃO adivinhar):**
| candidato | o que é | N | fonte |
|---|---|---|---|
| `n96_range_distribution_filter` | corte RANGE-distribution sobre N96 ("cortar RANGE 54,2%→57,3%, mantém **N82**") | ~82 | `results/n96_range_distribution_filter_{summary.json,results.csv}` |
| `n96_d_bear_active_filter` | corte intra-BEAR D-active (13L family D) | — | `results/n96_d_bear_active_filter_*` · doc `XAU_15M_N96_D_BEAR_ACTIVE_FILTER_*` |
| `impulse_efficiency_prior_leg` (Kaufman-ER) | ER da perna anterior ≥0,26 | N52 | card swept-runner · `mtf_feat_*` |
| N96 base inteiro | markup-demand engine sem filtro extra | N96 (96) | `entry_engine_master_20260707.json` |
| trade **#83** literal | um loser específico (topo) | 1 | docs 15M |

**Classificação N83: `BLOCKED` (N83 não localizado).**

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
| **Filter N83 predicates** | — | — | **❌ BLOCKED (indefinido)** |

## 8. Predicados exatos
- **Markup-demand (base):** evento de demanda de perna (higher-low, tendência intacta) da caminhada MASTER; entrada = 1ª barra de reclaim EMA21 pós-demanda; SL = zona_demanda − 0,1ATR; target = +3R; outcome = forward-only (`out`). **[DEFINIDO]**
- **Filter N83:** **TBD / BLOCKED** — sem definição localizada.
- **Filtros estruturais / exits / SL adicionais:** **TBD** (dependem do que N83 for).

## 9. Baldes structural-first (canónicos do protocolo)
`BULL_impulse · BULL_pullback · BULL_excess_top · RANGE_neutral · RANGE_distribution_top_bear · RANGE_accumulation_bottom · BEAR_active · BEAR_shallow_bounce · BEAR_deep_capitulation · countertrend_bounce_in_bear · management_do_not_filter`. Regra-mãe: **indicador só vira evidência DENTRO de balde** (macro_regime + leg_state + family_label). Blocker: `check_xau_15m_structural_first.py`.

## 10. Claims ledger inicial
| claim | source | status | evidence | allowed? |
|---|---|---|---|---|
| markup-demand base = N96, 96 sinais/52W | `entry_engine_master_20260707.json` | VERIFIED_DERIVED (linhagem RAW→primitives) | list N=164, kind=markup 96 | sim (base research) |
| "Filter N83" existe como filtro definido | busca no repo | **REFUTED** (0 matches) | grep N83/filter_n83 = vazio | **não** |
| #83 = trade loser topo/exaustão | docs 15M + card | VERIFIED | "#82R vs #83…#85 losers" | contexto apenas |
| campos macro_regime/leg_state/family_label existem | ficheiros results | VERIFIED_DERIVED | n96_causal_regime/loser_family_map | sim |

## 11. Sanity checks obrigatórios antes de teste (quando N83 desbloquear)
timestamp alignment · no future leak (outcome forward-only já é) · no outcome fields como feature · no proxy/SLIM · coverage · missingness · family_label availability · consistência macro/leg · **source guard `check_xau_15m_raw_lineage.py` = RAW_LINEAGE_PASS** · **structural-first `check_xau_15m_structural_first.py`** · **claims ledger `check_xau_15m_claims_ledger.py`** · gate `run_xau_15m_lab_gate.py` = `XAU_15M_LAB_GATE_PASS`.

## 12. DA obrigatório para o próximo bloco
source DA · causality DA · mapping DA · metric DA · overfit/selection DA — **via Agent tool real** (Stage 7 do protocolo).

## 13. Critérios de PASS para autorizar teste futuro
Todos os campos mapeados RAW/source ✅ (base) · **N83 definido por predicado real ❌** · unidade congelada ✅ · manifest completo (parcial — falta N83) · nenhum outcome leak ✅ · nenhum proxy ✅ · sanity ready (pendente N83). → **NÃO cumprido (falta N83).**

## 14. Critérios de BLOCKED (qual se aplica)
- ✅ **N83 não localizado** → `BLOCKED_MISSING_N83`.
- (não aplicável) macro_regime/leg_state/family_label ausentes → **presentes**.
- (não aplicável) RAW mapping incompleto (base) → **base mapeada**.
- (não aplicável) dependência de swept-runner oficial → swept-runner é base research, não oficial.

## Estado / próximo passo
`PREREG_ONLY_NOT_TESTED` · `BLOCKED_MISSING_N83` · **NÃO rodar teste.** **Requer decisão do Cris:** *qual filtro "N83" designa?* (candidatos em §5). Assim que N83 for definido por predicado real + mapeado, completar §7/§8/§11 e re-submeter o manifest ao gate `run_xau_15m_lab_gate.py`. PRODUÇÃO/Telegram/broker/runtime = intocados.
