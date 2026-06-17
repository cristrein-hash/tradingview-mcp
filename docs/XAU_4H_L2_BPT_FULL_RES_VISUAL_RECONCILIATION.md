# XAU 4H L2/BPT — Full-Res Visual Reconciliation (leitura trade-a-trade + solução)

**Status:** `VISUAL_GROUND_TRUTH · NOT_STRATEGY · NOT_VALIDATION · NO_OUTCOME_USED` · **Data:** 2026-06-17
**Base: 11 prints full-res ANOTADOS pelo Cris (`REVISÃO 41.zip`), lidos um a um.** Sem outcome/R/PnL · sem backtest · sem filtro final · sem produção/SLIM/Caminho B.

> Desta vez eu **li de fato** os 11 prints (imagens full-res) e transcrevi as **anotações do Cris** por episódio — é ground-truth visual dele, não inferência minha. Onde um episódio não tinha anotação legível, marquei `NO_VISIBLE_ANNOTATION`/`NEEDS_SECOND_REVIEW`.

---

## 1. Prints analisados

11 prints (jan/2020 → jan/2023), cada um cobrindo um cluster de episódios. Todos lidos (`/tmp/rev41/clean/p01–p11.png`). Anotações transcritas em `results/l2_bpt_full_res_visual_episode_review.csv`.

## 2. Leitura trade-a-trade (anotações do Cris, agrupadas)

**A) Setup estrutural correto — winners reais (9):**
- **E1** "MUITO BOM. SL estrutural correto gera BIG WINNER" · **E13** "entrada e SL corretos, vira big winner dos bons" · **E17** "BIG WINNER" · **E27** "entrada real correta do cluster, BIG WINNER" · **E30** "BIG WINNER" · **E40** "BIG WINNER, entrada perfeita, SL curto e eficiente" · **E21/E23/E5** "WINNER OK".
- Padrão: BOS/CHoCH → retest/reclaim → **aceitação** → continuação; SL estrutural faz sentido; supply (quando perto) foi absorvida/rompida.

**B) Setup válido, LOSER por SL curto demais → vira winner com SL estrutural (12):**
- **E38** "loser por SL curto demais; vira winner com SL estrutural" · **E19/E20/E22** "winner, SL a corrigir" · **E3/E4** "SL estrutural é aqui" · **E2/E28/E29/E31/E32** (cluster) "viram todos winners com SL estrutural / com respeito" · **E41** "ponto de entrada correto é mais abaixo; loser que precisa virar BIG WINNER".
- Padrão: a **tese long está certa**, mas o SL mecânico ficou **dentro da respiração normal**, não abaixo da estrutura defendida.

**C) Entradas que NÃO deviam existir — macro bear / topo / exaustão (13):**
- **E15** "não pode existir: topo duplo, entra após barra bear forte" · **E24** "entrada de topo, exaustão clara, MACRO BEAR claro" · **E34** "exaustão; entrar em queda clara de venda não pode" · **E39** "compra sem sentido após perna bear clara; cego para virada bear óbvia" · cluster **E36/E6/E7/E8/E9/E10/E37/E11** (out/2020–mar/2021) "TODAS ENTRADAS EM REGIME BEAR NÃO FUNCIONA".
- Crítica direta do Cris: **falta leitura macro-estrutural madura** — o classificador compra repique dentro de bear leg / topo / distribuição.

**D) Entradas precipitadas — eliminar (3):** **E25/E26/E35** "entradas precipitadas, eliminar; a entrada real correta do cluster é E27 (big winner)".

**E) Gap de detector (1):** **E12** "mesma configuração de E11 — por que o detector NÃO entrou aqui? plotei para verificar/quantificar".

**Resumo:** 18 valid_long (9 ok + ~9 SL-fix) · 13 não-long (macro bear) · 3 precipitadas · resto review.

## 3. Os 3 padrões sistêmicos (o diagnóstico real)

| # | Erro sistêmico | Evidência (Cris) | Natureza |
|---|---|---|---|
| **1** | **Cegueira macro-bear** — compra repique em bear leg/topo/exaustão | E15, E24, E34, E39, cluster out20–mar21 | **falha de leitura macro** (a mais grave) |
| **2** | **SL curto demais** — winner vira loser | E38, E19–E23, E3, E4, E2, E28–E32, E41 | **gestão de SL**, não tese |
| **3** | **Entrada precipitada** — vários sinais na perna, entra no errado | E25/E26/E35 vs E27 | **maturidade de entrada** |

Os 3 são **causais e mensuráveis** — não dependem de "olhar mais screenshot". Os prints **ensinaram a regra**; agora dá pra codificá-la.

## 4. Solução inteligente proposta (3 camadas causais sobre o v2.2)

> Princípio: o screenshot foi o professor; a regra aprendida é mecanizável a partir do RAW que já temos (1D/4H SMC, swing lows, bear displacement, aceitação). Validar por **recall-gate contra os 9 winners confirmados** antes de qualquer métrica.

**LAYER M — MACRO REGIME GATE (resolve o erro #1, o que mais move o ponteiro):**
Bloquear/review LONG quando o macro está em bear-displacement. Sinais causais (todos já extraíveis):
- **1D estrutura:** sequência LH/LL + close < EMA/SMA 1D + CHoCH/BOS 1D bearish (SMC no 1D).
- **4H bear displacement** imediatamente antes do reclaim (candle bear range ≥ ~1.5 ATR mergulhando na entrada).
- **Confirmação:** cluster NAS TOP / distribuição + RSI bearish-divergence cluster.
- Regra: macro bear dominante → `MACRO_BEAR_NO_LONG` (bloqueia) ou review-only. Mata E15/E24/E34/E39 + todo o cluster out20–mar21.
- **Recall-gate:** NÃO pode bloquear os 9 winners (E1,E13,E17,E27,E30,E40,E21,E23,E5).

**LAYER S — SL ESTRUTURAL FLEXÍVEL (resolve o erro #2):**
Trocar o SL fixo (min-6-bars) por SL escolhido pela estrutura: abaixo do **swing low estrutural defendido** (pivot Williams da base/retest) / base da demand / invalidação por close abaixo da polaridade. R-bounded, mas permitindo a distância estrutural real.
- Modelos: `SL_RETEST_LOW` · `SL_STRUCTURE_LOW` · `SL_DEMAND_BASE` · `SL_POLARITY_CLOSE_INVALIDATION`.
- Converte os 12 `VALID_SETUP_BAD_SL` em winners (medir com o outcome real por episódio depois).

**LAYER E — MATURIDADE/DEDUP-PARA-A-ENTRADA-REAL (resolve o erro #3):**
Entre sinais seriais numa perna, escolher o **reclaim estruturalmente correto** (aceitação + defende polaridade), não o precipitado. (E25/E26/E35 → E27.)

**+ ACCEPTANCE GATE** (já definido): held acima da polaridade + sem LH/LL imediato + supply rompida/aceita.

## 5. Plano de validação (próximo bloco, se autorizado)

1. Codificar LAYER M (macro bear gate) causal a partir de 1D/4H RAW.
2. **Recall-gate:** confirmar que M preserva os 9 winners e bloqueia os 13 macro-bear. Se cortar winner → reespecificar (não promover).
3. Aplicar LAYER S (SL estrutural) e medir outcome real por episódio (stop estrutural + R, lift vs base rate, **por episódio**) — só DEPOIS do recall-gate.
4. Investigar E12 (gap de recall do detector — por que pulou config igual a E11).
5. Resíduo `NEEDS_SECOND_REVIEW` (E12,E14,E16,E18,E33) → revisão visual.

## 6. O que ainda precisa do teu olho

Os 5 `NEEDS_SECOND_REVIEW` + a calibração do limiar "bear displacement dominante" (quão forte/recente a perna bear precisa ser para bloquear) — isso é julgamento que só tu fecha; eu trago os candidatos medidos.

## 7. DA appendix

- Todos os 11 prints lidos? ✅ (full-res, um a um).
- Anotações do Cris registradas? ✅ (`..._episode_review.csv`, com `image_file`).
- Não fabricou leitura? ✅ — onde não há anotação legível, `NO_VISIBLE_ANNOTATION`/`NEEDS_SECOND_REVIEW`.
- Não usou outcome/PnL? ✅ (só estrutura + anotações; outcome fica para a validação).
- Separou SL ruim de setup ruim? ✅ (12 SL_issue vs 13 macro_bear vs 9 ok).
- Separou macro bear de pullback bull? ✅ (é o núcleo da LAYER M).
- Não criou filtro final / não rodou backtest? ✅ (solução é proposta; validação é próximo bloco).
- Produção intacta? ✅.

**DA verdict: PASS — 11 prints lidos e anotações do Cris consolidadas como ground-truth; 3 erros sistêmicos isolados (macro-bear blindness, SL curto, entrada precipitada); solução = 3 camadas causais (Macro Gate + SL estrutural + maturidade) validáveis por recall-gate contra os 9 winners; nada executado/promovido.**

---

*Read-only. Outputs: este doc + `results/l2_bpt_full_res_visual_episode_review.csv` (41 episódios: image_file, user_annotation, corrected_visual_label, valid_long, issue_type, suggested_SL_model, ...). Prints em `/tmp/rev41/clean/` (efêmero). Sem outcome, sem produção.*
