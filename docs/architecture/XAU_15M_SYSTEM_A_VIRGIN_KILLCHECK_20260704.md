# SISTEMA A "EMA-SHAKEOUT" — KILL-CHECK VIRGEM (2026-07-04)

## Veredito: **VIRGIN_INCONCLUSIVE_N_LT_20 (N=0)** — não aprova nem mata (critério congelado).

**Janela virgem:** 2026-05-25 00:00 → 2026-07-03 16:30 UTC (9º bloco RAW, 2714 barras, 240 candidatos flush-low novos). **Spec congelada** do Lab G aplicada linha-a-linha (DA verificou identidade com o frozen; zero reotimização; critérios pré-registrados: WR<50% OU avgR<+0,15 em N≥20 = KILL; N<20 = inconclusivo).

## O fato central
**Os 240 candidatos da janela são 100% BEAR pelo detector v5h** (recomputado independentemente pelo DA: 240/240, zero mismatch; causalidade re-auditada — 1H fechado + D-1). O mercado caiu ~4565→4166 com low 3942 (~−12%). O Sistema A é **BULL-only por construção** → **0 picks em todos os painéis** (spec congelada E bounds htf:=0/htf:=1 — a staleness do HTF ficou irrelevante com N=0).

## Leitura operacional (dado, não validação)
Numa queda de ~12%, o Sistema A teria ficado **100% de fora** — o stand-aside por regime funcionou exatamente como desenhado (zero LONGs, zero perdas). O mesmo vale para a base #4 (gate ≠BEAR: 0 elegíveis) e para a lane BEAR-pullback congelada (0 casos — o pullback-bull confirmado dentro do BEAR não ocorreu). Diagnóstico rotulado (NÃO kill-check): sem o gate de regime, A teria feito 1 trade, loser (−0,25 NET) — evidência anedótica A FAVOR do gate.

## Consequência para o status do Sistema A
Permanece **EXPLORATORY_CALIBRATION / POSITIVO_FRÁGIL** com as MESMAS pendências (a janela virgem não adicionou N): (i) próxima janela virgem útil = quando v5h sair de BEAR (a extensão precisa continuar em blocos futuros); (ii) reconciliação visual do Cris nos 21 trades fora-da-base; (iii) N fora de 2025. Kill-criteria de RAW-estendido seguem armados para a próxima janela com N≥20.

Outputs: `results/system_a_virgin_killcheck_20260704.csv` (0 linhas de picks) · `results/system_a_virgin_killcheck_summary.json` · script congelado `system_a_virgin_killcheck_20260704.py` · DA scripts `_DA_ext_*.py`.
