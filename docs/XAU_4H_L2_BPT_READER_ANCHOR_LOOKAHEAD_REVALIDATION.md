# XAU 4H L2/BPT — ANCHOR LOOK-AHEAD INCIDENT + POST-FIX REVALIDATION — 2026-06-23

## O bug
O `l2_bpt_raw_backbone_builder.py` (commit a72b012) ancorava cada episódio ao RAW por **close-match** (a barra
RAW cujo close fosse mais próximo do close frozen) SEM trava causal, e usava `bar_open()` de **grade 4H fixa**
em UTC. Dois defeitos somados:
1. **close-match sem causalidade:** em **13/19** episódios a barra ancorada caía 1-2 barras DEPOIS da entry
   (ep 1661 caiu na sessão errada, −15 barras, sem warning). A janela que o reader cego viu e o supply/demand
   foram computados em barra **futura** = look-ahead.
2. **grade fixa errada no DST:** a grade do feed desloca com o DST de NY (ex.: mar/2023 abre 03/07/11/15/19/23;
   ago/2023 abre 02/06/10/14/18/22). O `bar_open` de offset fixo errava o bar; o close-match mascarava isso à
   custa de causalidade.

## A correção (commit 1267c8d)
Anchor = **as-of join pelo timestamp REAL da última barra fechada** (sem assumir grade): o snapshot ancorado é
aquele cuja última barra fechada == entry (`ENTRY[b]`); fallback as-of (≤1 barra antes); **nunca barra futura**.
Resultado verificado (`results/_DA_lookahead_window_check.py` + DA independente):
- **19/19 causal** (zero barra futura), **19/19 entry exata**.
- 3/19 (1661, 4401, 1775) com `anchor_close_fidelity=False` = feed RAW PEPPERSTONE ~$13 ≠ frozen (diferença de
  **feed**, anchor exato por timestamp; flagado por episódio, NÃO look-ahead).
- Volume SVP também passou a juntar por tempo real.

## Impacto / status dos artefatos
A leitura cega dos Clusters 1/2, o supply/demand do backbone e os audits **anteriores ao fix** rodaram sobre
janelas com 1-2 barras futuras + grade DST errada. Exemplo concreto: `dist_supply` do 5627 era **0.84 ATR**
(contaminado, "supply colado") e causalmente é **1.87 ATR** (SUPPLY_BLOCKS) — muda a leitura do caso.

| Artefato | Status |
|---|---|
| `results/raw_rebuild_cluster{1,2}/reading_packet_RAW_CLEAN.md` (pré-fix) | **PRE_FIX_HISTORICAL_REFERENCE_ONLY** |
| `results/raw_rebuild_cluster{1,2}/reader_dossier_RAW_FROZEN.md` (pré-fix) | **PRE_FIX_HISTORICAL_REFERENCE_ONLY** |
| `results/raw_rebuild_cluster{1,2}/phase3_audit_RAW_FROZEN_vs_outcome.md` (pré-fix) | **PRE_FIX_HISTORICAL_REFERENCE_ONLY** |
| Leituras/lentes derivadas do bloco pré-fix (97998e3) | **POST_FIX_REVALIDATION_REQUIRED** |

**Não apagar o histórico.** Os artefatos pré-fix ficam no repo como referência; a base FINAL passa a ser a
revalidação pós-fix (`results/raw_rebuild_cluster{1,2}_postfix/*`). As lentes só contam como confirmadas se
sobreviverem ao backbone causal corrigido (sem o espiar de 1-2 barras).

## Revalidação pós-fix (este bloco)
Pacotes RAW-clean pós-fix regenerados sobre o backbone causal; Reader cego fresco por cluster; freeze antes do
outcome; audit pós-outcome fresco; visual post-audit; comparação pré-fix vs pós-fix; Operating Manual
RAW-confirmed atualizado. Resultado em `docs/XAU_4H_L2_BPT_CLUSTER{1,2}_PREFIX_VS_POSTFIX_REVALIDATION.md`.
