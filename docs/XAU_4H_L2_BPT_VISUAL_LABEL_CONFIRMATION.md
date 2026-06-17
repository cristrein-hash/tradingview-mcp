# XAU 4H L2/BPT — Visual Label Confirmation (revisão visual assistida)

**Status:** `ASSISTED_REVIEW · DOSSIER_READY · VISUAL_CONFIRM=AWAITING_USER · NOT_STRATEGY` · **Data:** 2026-06-17
**Sem outcome/R/winner-loser · sem backtest/cruzamento-com-outcome · sem filtro/SLIM/Caminho B/produção.**

---

## 0. Escopo honesto (o que eu posso e o que não posso)

A confirmação visual (`CONFIRMED/CORRECTED/UNCLEAR`) é **tua** — eu não tenho os olhos no gráfico. Eu **não** preenchi nenhum `CONFIRMED/CORRECTED`; fazer isso seria fabricar leitura visual. O que entrego: para cada um dos 41 episódios, o **dossiê estrutural pré-outcome** (a estrutura que o gráfico desenha, RAW, sem outcome) + uma leitura mecânica auto-consistente — para você navegar ao timestamp e confirmar rápido.

- **Revisados por mim (visualmente): 0.** Dossiês preparados: **41.**
- `visual_confirm = AWAITING_USER` em todos (colunas `visual_label_final`, `why_visual`, etc. em branco no CSV para você preencher).
- A coluna `mechanical_corroboration` deu **SUPPORTS em 41/41** — mas isso é **auto-consistente** (meu `claude_structural_read` usa as mesmas features da primeira-passada), **não é confirmação independente**. Só o teu olho valida.

## 1. Como usar (passo a passo)

1. Abra `results/l2_bpt_visual_episode_labels.csv`.
2. Para cada `EN`, vá ao `navigate_to` (timestamp) no XAUUSD 4H.
3. Olhe a estrutura (o dossiê abaixo já resume os fatos objetivos). Decida a categoria real.
4. Preencha `visual_label_final` + `visual_confirm` (CONFIRMED/CORRECTED/UNCLEAR) + `why_visual` + as colunas de pergunta.

## 2. Dossiê pré-outcome por episódio (sem outcome)

`reclaim` = candle de entrada · `dist` em ATR · `brk/rej` = supply broken/rejected · `aceitação` = held 2-4c acima da polaridade OU HH/HL · `bear` = contexto de perna bear (proxy).

| ep | navegar | first-pass | reclaim | demand(dist) | supply(dist) | brk/rej | aceitação | bear | NASsh | RSI |
|---|---|---|---|---|---|---|---|---|--:|--:|
| E1 | 2020-03-23 22:00 | DEMAND_SUP_RECLAIM | verde 60% | SUPPORTING(3.51) | FRESH_DANG(0.68) | 0/0 | ACEITOU | SIM | 7 | 62 |
| E2 | 2020-05-04 06:00 | SUPPLY_REJECTION | verde 83% | SUPPORTING(2.26) | NEAR_REJ(0.41) | 0/1 | NÃO | não | 8 | 50 |
| E3 | 2020-06-10 18:00 | TOP_SWEEP_REJ | verde 75% | SUPPORTING(3.29) | FRESH_DANG(0.73) | 0/0 | NÃO | não | 7 | 54 |
| E4 | 2020-07-02 14:00 | POLARITY_DEFENDED | verde 47% | PRESENT(0.75) | NEAR_REJ(0.66) | 0/1 | ACEITOU | não | 11 | 53 |
| E5 | 2020-07-30 22:00 | DEMAND_SUP_RECLAIM | verde 82% | SUPPORTING(0.9) | NEAR_REJ(0.36) | 0/1 | ACEITOU | não | 9 | 61 |
| E6 | 2020-10-08 22:00 | DEMAND_SUP_RECLAIM | verde 99% | SUPPORTING(2.43) | FRESH_DANG(0.47) | 0/0 | ACEITOU | SIM | 5 | 50 |
| E7 | 2020-10-14 10:00 | BEAR_LEG_TRAP | verde 77% | SUPPORTING(1.61) | NEAR_REJ(0.84) | 0/1 | NÃO | SIM | 6 | 44 |
| E8 | 2020-11-05 07:00 | ACCEPTED_SUP_BREAK | verde 77% | SUPPORTING(1.95) | NEAR_BROKEN(0.15) | 1/0 | ACEITOU | não | 5 | 64 |
| E9 | 2020-11-08 23:00 | BEAR_LEG_TRAP | verde 31% | ABSENT(5.73) | FRESH_DANG(0.39) | 0/0 | NÃO | SIM | 2 | 69 |
| E10 | 2020-12-17 19:00 | DEMAND_SUP_RECLAIM | verde 26% | SUPPORTING(2.74) | NEAR_REJ(0.07) | 0/1 | ACEITOU | SIM | 0 | 68 |
| E11 | 2021-02-24 15:00 | POLARITY_DEFENDED | verde 57% | PRESENT(2.36) | NEAR_REJ(0.64) | 0/1 | ACEITOU | SIM | 8 | 40 |
| E12 | 2021-03-25 14:00 | POLARITY_DEFENDED | vermelho 58% | PRESENT(2.03) | NEAR_REJ(0.46) | 0/1 | ACEITOU | SIM | 5 | 55 |
| E13 | 2020-01-20 03:00 | DEMAND_SUP_RECLAIM | verde 72% | SUPPORTING(1.48) | CLEAN_SKY(8.89) | 0/0 | ACEITOU | SIM | 8 | 56 |
| E14 | 2020-02-20 15:00 | POLARITY_DEFENDED | verde 17% | ABSENT(5.05) | CLEAN_SKY | 0/0 | ACEITOU | não | 5 | 76 |
| E15 | 2020-03-09 06:00 | DEMAND_SUP_RECLAIM | verde 8% | SUPPORTING(0.74) | CLEAN_SKY | 0/0 | ACEITOU | não | 1 | 53 |
| E16 | 2020-03-31 06:00 | TOP_SWEEP_REJ | vermelho 45% | ABSENT(8.43) | CLEAN_SKY(4.11) | 0/0 | NÃO | não | 7 | 54 |
| E17 | 2020-04-01 14:00 | DEMAND_SUP_RECLAIM | verde 11% | SUPPORTING(0.03) | CLEAN_SKY(5.15) | 0/0 | ACEITOU | SIM | 7 | 41 |
| E18 | 2020-05-18 14:00 | POLARITY_DEFENDED | vermelho 21% | ABSENT(4.32) | CLEAN_SKY | 0/0 | ACEITOU | não | 11 | 53 |
| E19 | 2020-06-30 06:00 | DEMAND_SUP_RECLAIM | vermelho 6% | SUPPORTING(1.51) | CLEAN_SKY | 0/0 | ACEITOU | não | 11 | 57 |
| E20 | 2020-07-15 14:00 | TOP_SWEEP_REJ | verde 75% | SUPPORTING(1.42) | CLEAN_SKY | 0/0 | NÃO | não | 7 | 51 |
| E21 | 2020-07-17 14:00 | TOP_SWEEP_REJ | verde 57% | SUPPORTING(2.29) | CLEAN_SKY | 0/0 | NÃO | não | 7 | 55 |
| E22 | 2020-07-23 02:00 | POLARITY_DEFENDED | verde 39% | ABSENT(6.31) | CLEAN_SKY | 0/0 | ACEITOU | não | 9 | 77 |
| E23 | 2020-08-04 22:00 | DEMAND_SUP_RECLAIM | vermelho 12% | SUPPORTING(3.82) | CLEAN_SKY | 0/0 | ACEITOU | não | 9 | 78 |
| E24 | 2020-08-07 10:00 | TOP_SWEEP_REJ | vermelho 55% | ABSENT(4.17) | CLEAN_SKY | 0/0 | NÃO | não | 6 | 69 |
| E25 | 2020-01-30 23:00 | DEMAND_SUP_RECLAIM | vermelho 28% | SUPPORTING(0.67) | BLOCKS_TGT(1.54) | 0/1 | ACEITOU | SIM | 7 | 50 |
| E26 | 2020-02-05 03:00 | BEAR_LEG_TRAP | verde 78% | SUPPORTING(0.96) | FAR(3.66) | 0/0 | NÃO | SIM | 7 | 34 |
| E27 | 2020-02-06 19:00 | DEMAND_SUP_RECLAIM | verde 24% | SUPPORTING(1.31) | FAR(3.17) | 0/0 | ACEITOU | SIM | 7 | 51 |
| E28 | 2020-05-07 18:00 | DEMAND_SUP_RECLAIM | vermelho 46% | SUPPORTING(2.04) | BLOCKS_TGT(1.11) | 0/0 | ACEITOU | não | 8 | 64 |
| E29 | 2020-05-28 18:00 | DEMAND_SUP_RECLAIM | verde 56% | SUPPORTING(1.26) | BLOCKS_TGT(1.34) | 0/0 | ACEITOU | SIM | 11 | 44 |
| E30 | 2020-01-14 07:00 | POLARITY_DEFENDED | verde 77% | TOO_DEEP(3.58) | BLOCKS_TGT(1.99) | 0/1 | ACEITOU | SIM | 8 | 37 |
| E31 | 2020-04-17 18:00 | POLARITY_DEFENDED | vermelho 62% | ABSENT(4.07) | FAR(2.86) | 0/1 | ACEITOU | SIM | 9 | 41 |
| E32 | 2020-04-27 14:00 | TOP_SWEEP_REJ | vermelho 35% | TOO_DEEP(3.6) | BLOCKS_TGT(1.54) | 0/1 | NÃO | não | 9 | 51 |
| E33 | 2020-08-17 10:00 | ACCEPTED_SUP_BREAK | verde 91% | ABSENT(6.02) | CLEAN_SKY(4.01) | 1/0 | ACEITOU | não | 6 | 49 |
| E34 | 2020-02-25 23:00 | POLARITY_DEFENDED | verde 42% | PRESENT(0.06) | FAR(2.33) | 0/1 | ACEITOU | não | 3 | 49 |
| E35 | 2020-02-03 15:00 | POLARITY_DEFENDED | verde 63% | PRESENT(0.06) | BLOCKS_TGT(1.34) | 0/1 | ACEITOU | SIM | 7 | 43 |
| E36 | 2020-10-12 18:00 | BEAR_LEG_TRAP | vermelho 24% | SUPPORTING(3.0) | FAR(2.61) | 0/0 | NÃO | SIM | 6 | 63 |
| E37 | 2021-02-22 07:00 | ACCEPTED_SUP_BREAK | verde 51% | SUPPORTING(2.25) | FAR(2.18) | 1/0 | ACEITOU | SIM | 8 | 51 |
| E38 | 2021-05-12 18:00 | BEAR_LEG_TRAP | vermelho 73% | TOO_DEEP(3.72) | BLOCKS_TGT(1.78) | 0/1 | NÃO | SIM | 9 | 48 |
| E39 | 2021-06-07 06:00 | DEMAND_SUP_RECLAIM | verde 15% | SUPPORTING(1.83) | NEAR_REJ(0.37) | 0/1 | ACEITOU | SIM | 2 | 46 |
| E40 | 2021-05-02 22:00 | DEMAND_SUP_RECLAIM | verde 60% | SUPPORTING(0.68) | BLOCKS_TGT(1.31) | 0/1 | ACEITOU | SIM | 8 | 45 |
| E41 | 2022-12-15 03:00 | BEAR_LEG_TRAP | verde 23% | SUPPORTING(1.3) | BLOCKS_TGT(1.89) | 0/1 | NÃO | SIM | 0 | 47 |

(SMC CHoCH/BOS recente + price por episódio estão no CSV `recent_smc_struct` — **mas o campo de preço do smc_recent parece não-confiável** (números fora do range real); use o texto/bars-ago, confirme o nível no chart.)

## 3. Relatório

- **Total revisado por mim (visual):** 0 (não tenho o gráfico). **Dossiês preparados:** 41.
- **CONFIRMED / CORRECTED / UNCLEAR:** 0 / 0 / 0 — **aguardando tua revisão** (não fabriquei).
- **Principais correções:** nenhuma feita por mim; a fila de prioridade pra teu olho são os de **divergência potencial** entre first-pass e os fatos: os `DEMAND_SUP_RECLAIM` marcados `bear=SIM` (E1, E6, E10, E13, E17, E25, E27, E29, E39, E40) — pode ser "demanda apoia em bull" OU "repique em bear leg"; só tu decides.
- **Categorias que parecem confiáveis (pelos fatos objetivos):** o eixo **aceitação** é limpo — os `NÃO_aceitou` (E2,E3,E7,E9,E16,E20,E21,E24,E26,E32,E36,E38,E41) caem todos em REJECTION/TRAP; os `ACEITOU` em DEFENDED/RECLAIM. `ACCEPTED_SUP_BREAK` (E8,E33,E37) tem supply broken=1 + aceitação — coerente.
- **Categorias frágeis (precisam do teu olho):** `bear_leg` (proxy cru — dispara em E1/E6/E13/E17 que são 2020-bull, podem ser pullback e não bear leg); `DEMAND_SUP_RECLAIM` com candle de corpo minúsculo (E15 8%, E19 6%, E23 12%, E10 26%) — reclaim pode ser fraco demais; `clean_sky` com dist vazia (sem supply acima) precisa confirmar se é continuação ou esticado.
- **Nenhum outcome / PnL usado.** Produção intacta.

## 4. DA appendix

- Não mostrou R/winner-loser/target-stop? ✅. Não cruzou com outcome? ✅. Não fabricou leitura visual? ✅ (visual_confirm=AWAITING_USER, 0 preenchidos por mim).
- Não inventou o que não está visível? ✅ (flag no campo SMC price não-confiável). Não virou regra? ✅.
- SLIM/Caminho B/produção? ❌ nenhum.

**DA verdict: PASS — dossiê pré-outcome dos 41 entregue para revisão assistida; confirmação visual deixada explicitamente para o Cris (0 fabricados); eixo aceitação coerente nos fatos; frágeis sinalizados (bear_leg proxy, reclaim fraco, SMC price não-confiável).**

---

*Read-only. RAW-only. Sem outcome. Outputs: este doc + `results/l2_bpt_visual_episode_labels.csv` (dossiê + colunas `visual_confirm=AWAITING_USER` para preencher). Script: `visual_review_assist.py`.*
