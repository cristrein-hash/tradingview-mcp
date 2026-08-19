# L2 ENTRY REFINEMENT — MANIFEST + PREREG (selado 2026-08-19, aprovado Cris "PODE FAZER TODO ESTUDO")

## Motivação (documentada, fora do score)
4 trades forward live (21/07-04/08) 0W-4L −2,3R, todos REGIME_FLIP hold=1; leitura discricionária do Cris
(esperar FVG/demanda inferior) ≈3W-1L. Estes 4 trades NÃO pontuam nas hipóteses (geraram-nas).

## Fontes (verificadas no P0 antes de ler)
- Base in-sample: régua estrutural 245 trades `XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv`
  (bar_idx, entry, sl) + motor VIVO `l2_engine.py` (paridade V-1..V-4; gates SELECT-17 sumR≈105.3/DD-4.1/stk3
  e FULL≈399.2 do parity_trend_exit.py — o estudo RE-CORRE os gates antes de medir; FAIL ⇒ HARD_STOP).
- RAW 4H: `research/revalidation/raw_4h_ohlc.jsonl` (canónico, dono bar_store). RAW 1H:
  `research/revalidation/raw_1h_ohlc.jsonl` — CAVEAT: cobre 2024-05-24→hoje ⇒ H1 só é mensurável nos trades
  com entry ≥ 2024-05-24 + janela 1H completa. Trades fora = OUT_OF_1H_COVERAGE (contados, não pontuados).
  NÃO se resampleia 4H→1H (proibição RAW-first).
- Detetor FVG: REUSO da lógica do AMD (`amd_lab/amd_v2.py::entry_fvg_ob`, viva em produção via amd ping2) —
  FVG long: gap_top=win[k].l, gap_bot=win[k-2].h, existe se gap_top>gap_bot. ZERO implementação paralela.
- "Demanda 15M/1H" como alternativa: CORTADA do estudo (boxes OB históricas 1H não disponíveis para a base;
  reconstruir seria inventar zonas — regra do Cris).

## H1 — ENTRADA ADIADA NO FVG-1H (regras seladas)
Por trade da base (bi, entry, sl; risk=entry−sl):
- Janela: barras 1H em [T4[bi], T4[exit_bar_mech]] (exit mecânico do próprio trade, regime_flip_detail).
- FVG elegível: primeiro FVG-1H (lógica AMD) FORMADO na janela com gap_top < entry e (entry−gap_top) ≤ 1×risk.
- Fill: primeira barra 1H posterior com low ≤ gap_top → entry2=gap_top. Sem fill até ao exit ⇒ NO-FILL
  (resultado registado; na métrica combinada NO-FILL = 0R/0pts — o trade não aconteceu).
- Outcome do adiado: mesmo SL; SL-first nas barras 1H de fill→exit (low ≤ sl ⇒ LOSS em sl); senão sai no
  MESMO exit (close 4H do exit_bar mecânico). Mesma COST 0.35R do motor.
- MÉTRICA DUPLA (anti-inflação de R): (a) PONTOS capturados (exit−entry vs exit−entry2; SL em pontos);
  (b) R-do-próprio-trade. Painel completo (N·WR·sumR·avgR·maxDD·retDD·streak·por-ano) + no-fill rate +
  comparação PAREADA por episódio. Scopes: SELECT-17∩cobertura-1H e FULL∩cobertura-1H.
- NULL (desconto-igual): 500 réplicas; por trade, desconto d amostrado (com reposição) da distribuição
  REAL dos descontos FVG observados; entry_null=entry−d; mesmas regras de fill/SL/exit. Estatística:
  rank do delta-pontos FVG vs distribuição null (separa "FVG discrimina" de "comprar mais baixo").
- Sub-janelas: painel por ano; jackknife leave-one-year-out no delta-pontos.

## H2 — FLIP CONFIRMADO 2 BARRAS (exit research; gerada pelos 4 forwards ⇒ só pontua na base)
Variante do regime_flip_detail: sai no fecho da 2ª barra BEAR CONSECUTIVA (1ª BEAR isolada não sai;
SL-first mantém-se sempre). Painel completo vs baseline nos mesmos scopes. Sem outros valores de N
(sem varrimento de knobs — N=2 é a única variante, multiplicidade=1, declarada).

## Vereditos possíveis (selados)
H1 SUPORTADA se: delta-pontos pareado >0 nos 2 scopes E rank null ≥95% E sobrevive jackknife E no-fill
não destrói o total (sumR-pontos combinado ≥ baseline). H2 idem (sem null — é exit determinística).
Qualquer resultado ≠ isto = NÃO SUPORTADA. Resultado NÃO altera a L2 live; se suportada → proposta de
prereg forward L2.1 para aprovação do Cris. Claims só via claims_ledger.jsonl deste diretório.
