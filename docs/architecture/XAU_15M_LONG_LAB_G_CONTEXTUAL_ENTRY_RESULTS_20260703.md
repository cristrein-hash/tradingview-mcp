# LAB G — ENTRY CONTEXTUAL DE CAPITULAÇÃO 15M · REGISTRO DE RESULTADOS (2026-07-03)

**Status da rodada: EXPLORATORY_CALIBRATION** (thresholds calibrados nestes dados; percentis individuais NÃO sobrevivem ao desconto de multiplicidade familiar — ~18 olhadas de outcome na família, declaradas). Rastreabilidade: abertura+auto-auditoria em `..._LAB_G_CONTEXTUAL_ENTRY_OPENING_20260703.md`; discovery = workflow `wf_15184946-f29` (3 designers com filosofias distintas + DA-pré + síntese; 341k tokens); scripts `lab_g_*.py` + `_DA_lab_g_*.py` no repo; universo `results/lab_g_candidates.jsonl` (7,3MB, REGENERÁVEL por `lab_g_context_inventory.py` — não versionado).

## 1. O que esta rodada fez de NOVO (resposta à auto-auditoria)
Universo pré-gate 4499 flush-lows × 74 campos causais: 61 do builder + **13 indicadores novos derivados das séries RAW** (g_rsi_div, g_atr_spike, g_sweep_depth, g_box96/480, g_rec_speed, g_downrun, g_ema21_dist/50, g_flush_wick, g_cj_body, g_regime_flip5d, g_bear_pullback_ok) + regime v5h como MAPA. Entradas definidas POR confluência contexto×indicador×regime (não pela pilha de gates da base). Frequência-alvo do mandato embutida no desenho. Negativos valiosos registrados: depth-first (−23,1R, pct 4,3 = anti-seleção) · floor-raid RANGE 15M (2× refutado — veto permanente) · VEXA-R resposta-standalone · segundo-mergulho.

## 2. Sistemas congelados e medidos (ledger: 2 tentativas + 1 amputação pré-autorizada)

### Sistema A — "EMA-SHAKEOUT" (BULL-only) → **POSITIVO_FRÁGIL (DA)** · gate FN PASS na estimativa pontual
Predicado: BULL(v5h) + estrutura H1 intacta (h1_trend=1, h1_pos≥0,33) + flush na EMA21 (abaixo ou reclaim ≤3 barras) + violência (atr_spike≥1,27 OU downrun≥3) + demanda (in_demand OU htf_demand) + resposta consumada (rec_speed≥0,69 OU reclaim≥2,0) + sem faca. Entry close cj · SL flush−0,1ATR · let-run.
**Painel: N53 · WR_liq 60,4% · NET +25,9 (bruto +29,8) · DD −3,2 · stk −3 · anos 4,1/22,9/−1,1 · 0,9/semana-BULL (0,5/sem geral).** P(streak≤−7): 3% permutação / 3,9% block-bootstrap / 6,6% bayes-WR. Robusto a custo SC$1,50 (+22,4) e a −32pp de WR até NET≤0. Nulls: freq-matched 94,8 · **context-pool 91,0 (kill ≥90 PASSA, estável 10 seeds: 90,2-92,1)** · time-matched 79,8 · pools endurecidos 69-85.
**Achado central (DA): 21/53 trades estão FORA da base435 (15 = flushes NÃO-swept) e carregam 70% do NET com WR 76** — substrato novo real, não base fantasiada.
**Fragilidades (DA, obrigatórias):** P(max de 18 olhadas ≥ pct 91 | H0) = 82% → evidência estatística ≈ nula após desconto; binomial vs próprio pool p=0,063; IC95 do WR [49,76]; 88% do NET em 2025; 2026 N=3; branch BULL extraído post-hoc (admitido no ledger).

### Sistema B — "PoT-Map v2.1" (+ B' amputado) → **CONFIRMA_NEGATIVO**
1ª medição da config congelada: N182 · WR 45,1 · NET +33,9 · stk −7 · P7=78% → FAIL FN. Célula RANGE N55 net −2,9 → amputação pré-autorizada: B' BULL-only N127 · WR 49,6 · +36,8 · P7=38% → FAIL FN. Implementação verificada por re-implementação independente; sem caminho dentro do ledger.

## 3. Bugs de builder anotados pelo DA (família B futura; A não usa esses campos)
(a) `h1n_choch_up_rec` não filtra direção do CHoCH (`build_engine3_features.py:41`); (b) eventos SMC/NAS de HTF filtrados por `t<=cj_t` sem ajuste de fechamento do bar HTF (vazamento intra-bar plausível na lente-2 de B). Corrigir antes de qualquer rodada futura que use esses campos.

## 4. Pendências BLOQUEANTES antes de qualquer upgrade de status do Sistema A (Passo 9 do protocolo)
1. **Re-medição no RAW estendido mar→jun-2026** (janela virgem; spec byte-idêntica; kill: WR_liq<50 OU avgR<+0,15 OU streak>6 em N≥20).
2. **Reconciliação visual pelo Cris** (via skill plotting-canon) — prioridade nos **21 trades fora-da-base** (coração do sistema, nunca vistos em chart).
3. N adicional fora de 2025.

## 5. Decisões em aberto (Cris)
Plotar os 53 trades de A (ou os 21 novos) para leitura visual · abrir coleta do RAW estendido (5 aprovações do plano) · rodada futura da lane registrada "capitulação LOCALIZA + displacement P1 ENTRA" · correção dos 2 bugs de builder.
