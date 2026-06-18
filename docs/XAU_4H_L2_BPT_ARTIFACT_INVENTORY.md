# XAU 4H L2/BPT — Inventário de Artefatos (auditoria pré-SL estrutural)

**Status:** `AUDIT · NO_BACKTEST · NO_PRODUCTION · NO_DELETE` · **Data:** 2026-06-18
Auditoria de commits, docs, results, scripts e memória antes de iniciar a sessão de **SL estrutural trade-a-trade**. Nada deletado/movido; produção intacta; nenhum backtest novo.

---

## 1. Current canonical state

- **L2/BPT NÃO é estratégia final** — é frente de pesquisa (XAU 4H LONG, reclaim de polaridade pós BOS/CHoCH).
- **Detector v2.2** = candidate generator (recall 17/17 BOM, ~1109/ano). NÃO é estratégia.
- **PRUNED_BASE_V2** = base de pesquisa: 2965 candidatos (recall 17/17 preservado) = **276 episódios** estruturais. Unidade = episódio.
- **Discriminador é posicional-estrutural** (legpos validado: E40 56 vs E39 89), NÃO feature local (supply/demand/bubbles/NAS/RSI/volume isolados ≈ base rate).
- **SL estrutural sem teto (3-4 ATR)** é a fundação; o R_ceiling 1.5ATR era ERRADO.
- **Edge é regime-bound / não-estacionário:** build 2020-22 avgR +0.02 (chato), holdout 2023-26 +0.39 (carrega tudo). É captura de beta long-gold no bull, não edge estacionário.
- Doc canônico vivo: `XAU_4H_L2_BPT_CONSOLIDATED_KNOWLEDGE.md` (atualizado nesta auditoria, §7 e §9 corrigidos).

## 2. Approved decisions

| Decisão | Status | Fonte |
|---|---|---|
| **Exit partial50@2R+6R** (50% sai +2R trava +1R; restante BE→runner +6R; time-stop 60; SL estrutural) | ✅ APROVADO (gestão streak prop-firm; WR48% sumR+63 streak9 vs 13; bootstrap maxDD 17R) | memória `project_l2_bpt_exit_lab_regime_bound` |
| SL estrutural sem teto (Williams pivot −0.1ATR, floor 0.3ATR) | ✅ Fundação validada; precisa **cap operacional ~4ATR** (97/276 >4ATR, máx 15ATR) | CONSOLIDATED §8c, `SL_STRUCTURAL` |
| Recall-gate — **must_preserve = 8 winners** E1/E5/E13/E17/E21/E27/E30/E40 (**E23 reconciliado OUT** = top-exhaustion) | ✅ Regra permanente; lista corrigida 2026-06-18 | `feedback_recall_gate_before_backtest`, `l2_bpt_reconciliation_labels.csv` |
| **User reconciliation (2026-06-18):** E13=valid bad-pivot/entry (winner real); E23=TOP_EXHAUSTION_SHOULD_NOT_LONG (não winner); E1/E17=exit-sensitive big winners (caveat partial50, exit inalterado) | ✅ Confirmado pelo Cris | CONSOLIDATED §8c, `SL_STRUCTURAL §14` |

## 3. Retracted findings (NÃO usar como autoridade)

| Achado | Status | Por quê |
|---|---|---|
| **Volume×1D-bear "breakthrough"** | 🚫 RETRACTED | Artefato de tick-volume; com Session VP real NÃO separa |
| **Bloqueio legbear / bear-leg sequencial** | 🚫 RETRACTED | Circular nos 41 curados; na base 276 bloqueia 5/9 winners, reduz sumR, pior held-out |
| **Gate duro 1D-bear** | 🚫 RETRACTED | Mata E1/E17 (fundo COVID são reversões-de-fundo, não traps) |
| **BE global** e **BE condicional** (em bear-context) | 🚫 REJEITADO | Dá scratch nos monumentais; bear-context é winner-rich (avgR +0.28>base) |
| **"Parede definitiva" (banner intermediário do BEARLEG_WALL)** | 🔄 CORRIGIDO | O corpo (parede estrutural) está CONFIRMADO; só o banner que creditava a confluência retratada foi corrigido |

## 4. Diagnostic-only findings (verdade, mas NÃO são validação/estratégia)

- `FULL_RES_VISUAL_RECONCILIATION` — 11 prints do Cris, 3 erros sistêmicos. Ground-truth visual, NOT_STRATEGY.
- `SWING_STRUCTURE_PRECISION` — swing theory simples REFUTADO, mapa 2×2 de mecanismos. DIAGNOSTIC.
- `LEGPOS_X_INDICATORS_TEST` — legpos validado como eixo; conditioning por exaustão refutado. DIAGNOSTIC.
- `1D_LEG_DECOMPOSITION` — máquina de estado 1D; gate duro bear REFUTADO; caminho realista. DIAGNOSTIC.
- `BEARLEG_FILTER_WALL` — subconjunto não filtrável na entrada (7 abordagens). DIAGNOSTIC, parede CONFIRMADA.
- `REAL_DATA_CONFLUENCE` — retrata o volume breakthrough com Session VP real. DIAGNOSTIC.
- **Exit lab / split temporal / attribution / conditional-BE** (2026-06-18) — em memória + CONSOLIDATED §8b; scripts em `/tmp` (ver §7).

## 5. Current next focus

**SL estrutural trade-a-trade** — afinar o stop estrutural (2-4 ATR sem teto) por episódio, recall-gate primeiro. **NÃO iniciado nesta auditoria.**
Depois (não agora): regime v3 gating · SHORT espelho · operacionalizar flags Telegram legbear/overbought (FUTURE_REQUIREMENT).

## 6. Files required for SL structural phase

**Results (base + labels + SL):**
- `results/l2_bpt_v2_2_pruned_base_v2.csv` (a base de 276 episódios) — **CURRENT, necessário**
- `results/l2_bpt_v2_2_candidate_matrix.csv` (label BOM/NAO/UNK por candidato) — **CURRENT, necessário**
- `results/l2_bpt_full_res_visual_episode_review.csv` + `results/l2_bpt_visual_episode_labels.csv` (rótulos visuais / GT 41) — **CURRENT, necessário (recall-gate)**
- `results/l2_bpt_real_outcome_per_episode.csv` + `results/l2_bpt_real_outcome_sl_validation.csv` (outcome real com SL estrutural; validação 3-4 ATR vs stop_cris) — **CURRENT, necessário**
- `results/l2_bpt_swing_anatomy.csv` (anatomia de swing — base pro SL estrutural) — **CURRENT, relevante**

**Scripts (in-repo, reutilizáveis):**
- `real_outcome.py` (outcome real com SL estrutural — função `risk_of` canônica) — **CURRENT, necessário**
- `swing_anatomy.py`, `leg_maturity.py`, `build_1d_ohlc.py`, `extract_svp.py` — **CURRENT, suporte**

**Datasets (ephemeral em `/tmp`, regeneráveis — necessários):**
- `/tmp/raw_features_2020_2026.jsonl` (frozen 4H — volume é tick-volume NÃO-CONFIÁVEL)
- `/tmp/svp_bars.jsonl` (volume REAL + Session VP POC/VAH/VAL + RSI por bar 4H)
- `/tmp/XAU_1D_ohlc.jsonl` (1D OHLC)

## 7. Files NOT to use as authority

- `XAU_4H_L2_BPT_VOLUME_CONFLUENCE_BREAKTHROUGH.md` — 🚫 RETRACTED (banner no topo).
- Memória `project_l2_bpt_volume_1dbear_confluence.md` — 🚫 RETRACTED.
- Memória `project_l2_bpt_legbear_block.md` — 🚫 RETRACTED.
- `results/l2_bpt_deep_confluence.csv` — saída do volume breakthrough retratado; **não usar como filtro**.
- Banner intermediário antigo do `BEARLEG_FILTER_WALL` (já corrigido) — não citar a confluência como válida.
- Qualquer resultado de outcome **proxy MFE/MAE** (`l2_bpt_outcome_proxy_failure_audit.csv`, `l2_bpt_pruned_base_v2_outcome_anatomy*`) — media DRIFT, NÃO edge (lift 0.99×). DIAGNOSTIC do erro, não autoridade.
- Scripts de exit lab estão **só em `/tmp`** (`exit_lab.py`, `exit_decisive.py`, `exit_cond.py`, `attribution.py`, `rebuild.py`) — efêmeros, não versionados; conclusões já em memória + CONSOLIDATED §8b.

## 8. Memory status

| Arquivo | Status |
|---|---|
| `project_l2_bpt_consolidated_knowledge.md` | ✅ Corrigido nesta auditoria (bloqueio→RETRATADO, next→SL estrutural) |
| `project_l2_bpt_exit_lab_regime_bound.md` | ✅ OK (partial50 aprovado, BE rejeitado, edge regime-bound) |
| `project_l2_bpt_legbear_block.md` | ✅ OK (RETRATADO) |
| `project_l2_bpt_volume_1dbear_confluence.md` | ✅ OK (RETRATADO) |
| `project_l2_bpt_telegram_bear_flags_FUTURE.md` | ✅ OK (FUTURE_REQUIREMENT) |
| `project_regime_classifier_v3_official.md` | ✅ OK (referência; regime fica para depois, não executado) |
| `MEMORY.md` índice | ✅ Entradas L2/BPT atualizadas; ⚠️ arquivo 37.5KB (> limite 24.4KB) — recomendação de enxugar (§10) |

## 9. Risks before continuing

1. **Scripts de exit lab só em `/tmp`** — se `/tmp` for limpo, perde-se o código (não as conclusões). Recomendar promover (§10).
2. **Datasets `/tmp` efêmeros** (`raw_features`, `svp_bars`, `XAU_1D_ohlc`) — necessários pro SL; regeneráveis mas não versionados.
3. **MEMORY.md acima do limite** (37.5KB) — risco de só carregar parte do índice.
4. **Volume do frozen = tick-volume** — risco de re-cometer o erro do breakthrough; sempre Session VP quando volume importar.
5. **Edge regime-bound** — qualquer número de SL deve ser lido com o split temporal em mente (build 2020-22 é chato); não concluir de janela única.
6. **n=15 monumentais** — objetivo "preservar monumentais" é anedótico OOS (13/15 no build); não promover SL por BOMsumR isolado.

## 10. Cleanup recommendations (NÃO executar agora)

- **Promover** `/tmp/exit_lab.py`, `/tmp/exit_decisive.py`, `/tmp/exit_cond.py` para `v1/` (versionar o código do exit lab). [requer autorização]
- **Enxugar MEMORY.md** — encurtar entradas longas, mover detalhe pros arquivos-tópico (índice > limite). [requer autorização]
- **Considerar arquivar** results retratados/proxy (`l2_bpt_deep_confluence.csv`, `l2_bpt_outcome_proxy_*`) numa subpasta `_retracted/` para não confundir. [requer autorização — não deletar]
- Nenhuma deleção recomendada. Nenhum arquivo movido sem autorização.

---

*Auditoria read-only + correção de docs/memória obsoletos. Sem backtest, sem produção, sem deleção, sem MCP/chart, sem SLIM.*
