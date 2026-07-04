# MTF SIGNATURE GATE TEST · PRÉ-REGISTRO (2026-07-04, ANTES da execução)

**Bloco:** XAU_15M_LONG_MTF_SIGNATURE_GATE_TEST · research-only / prereg-first / LONG-only · sem produção/Telegram/runtime/chart/plot/RAW-write. Pergunta única: a assinatura MTF do discovery (`XAU_15M_LONG_MTF_SIGNATURE_DISCOVERY_20260704.md`) melhora a ESTRATÉGIA (painel de outcomes) ou era só separação visual/hindsight?

## 1. Scope
XAU 15M LONG only · base #4 (N435) · detector v5 mantido · SB $0,80 obrigatório · sem SHORT · sem produção.

## 2. Assinatura CONGELADA (zero variação; 3 ATR / 1 ATR imutáveis pós-resultado)
- `supply_far_3atr_15M(t0,price)`: NÃO existe zona SUPPLY Custom OB 15M ativa em t0 (born_t ≤ t0 ≤ last_t) com low ≥ price e (low−price)/ATR15_asof < 3,0.
- `demand_near_1atr_1H(t0,price)`: existe zona DEMAND Custom OB 1H ativa em t0 com price dentro dela, OU com high ≤ price e (price−high)/ATR1H_asof ≤ 1,0.
- **GATE = supply_far_3atr_15M AND demand_near_1atr_1H**, avaliado no cj de cada candidato (price = close@cj). Sem exclusão manual, sem visual override, sem thresholds novos, sem filtro adicional, sem alterar exit/SL/detector. Implementação = EXATAMENTE a do mapeamento (`map_cris_trades_indicators_20260704.py`, lentes verbatim; ativação de zona por lifecycle first-appearance — causalidade provada contra RAW pelo DA do discovery).

## 3. Source/data mapping
Universo SELADO `results/lab_g_candidates.jsonl` (sha verificado no preâmbulo) · zonas 15M = primitives oficiais (9 blocos, cobertura total) · **zonas 1H = sandbox builder-canônico-re-alvo (3 blocos: 2024-05-25→2026-05-25)** — os 240 candidatos da extensão (>2026-05-25, todos BEAR) ficam SEM cobertura 1H → excluídos e contados (não afeta a base, que é ≠BEAR ≤2026-05-25) · ATR = barra asof do próprio TF (como no mapeamento) · exit/R = `g_R` (let-run do engine real) · custo SB por trade = 0,8/g_risk · episódio = cluster gap≤96 barras · limitação declarada: zonas não cruzam fronteiras de bloco (mesma dos históricos) · zero SLIM; source guard PASS vigente.

## 4. Baseline reproduction (fail-loud)
N435 · +291,5 bruto · +233,6 NET · WR_liq 46,0 · DD −14,2 · r/DD 16,4 · stk −8 · runners 53. Não bater → PARAR.

## 5. Hipótese
O gate deve: aumentar WR · reduzir clusters ruins · preservar runners · melhorar/preservar r/DD líquido · reduzir exposição sem suporte/sem espaço.

## 6. Avaliações pré-declaradas (DUAS, congeladas — sem best-of pós-hoc)
- **E1 BASE∩GATE**: gate como filtro sobre os 435 → painel completo vs baseline.
- **E2 UNIVERSE∩GATE (standalone)**: gate puro sobre o universo (sem outros filtros) → painel + células por regime (todas reportadas; nada escondido) + frequência/semana. Responde "novo substrato" — inclui verificação: dos candidatos casados aos 21 fora-da-base do Cris, quantos passam o gate.

## 7. Metrics
N · WR · bruto · NET-SB · avgR · DD · r/DD · streak · por-ano · pior mês/semana · runners kept/lost · losers cut · retention % · frequência/semana · FN-proxy · jackknife-episódio (concentração ≤15%) · concentração 2025 · cobertura dos 35-alvo e dos 21 fora-da-base.

## 8. Nulls (obrigatórios)
random-gate mesmo-N (500) · year-aware (mesmo N por ano, 500) · episode-aware (500) · runner-preservation reportado · **multiplicidade do discovery declarada** (assinatura = melhor par de ~57 lentes+15 pares sobre o TARGET SET; o null de rotulagem do discovery deu máx 2,18× em 200 reps — mas ESTE teste mede outcomes, dimensão nova; ainda assim 1 tentativa no ledger) · DA adversarial antes do report.

## 9. Acceptance (congelado)
SIGNATURE_GATE_STRONG (melhora WR/streak/DD/r-DD E retém ≥75% SB-net/runners) · SIGNATURE_GATE_REVIEW_LAYER (melhora contexto/risco mas corta lucro demais p/ gate) · SIGNATURE_GATE_FAIL · SIGNATURE_GATE_BLOCKED_BY_MAPPING.

## 10. Forbidden interpretations
Não concluir edge por lift no hindsight-target · não aprovar produção · não concluir SHORT · não virar regra operacional sem painel completo · não esconder runner-kill · não vender risk-control como edge · não re-tunar 3ATR/1ATR.

## 11. Outputs
`mtf_signature_gate_test.py` · `results/mtf_signature_gate_results.csv` + `_summary.json` · DA doc · report doc · commit `"Evaluate XAU 15M MTF structural signature gate"` — sem push sem autorização.
