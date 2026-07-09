# XAU 15M N83 — SL + EXIT REVIEW · FINAL Devil's Advocate

**2026-07-09.** DA real (Agent tool) + verificação independente minha (`xau_15m_n83_confirmation_leak_check.py`). **Verdict: `FAIL_LEAK_OR_NOT_REPRODUCIBLE`** — com atribuição precisa: o leak vive na **base N96 aprovada**, não na maquinaria SL/exit deste bloco.

## 1-2. Source / RAW mapping / Reprodução — OK
Lib reproduz o pipeline **byte-match 96/96** (t/ent/sl/tgt/out vs master JSON); zz/legwalk/build_entry idênticos linha-a-linha; N83=83, cut=13 losers. Primitives nativos, sem SLIM/proxy.

## 3. Universo — OK (congelado)
N96=96 → N83=83; 0 timeouts; 0 both-touch-same-bar; regimes BULL38/BEAR24/RANGE21.

## 4. SL causality — PARCIAL (preço causal; certificação corrigida)
O **preço** do SL (demand_low−0,1ATR) é conhecível no entry. MAS a minha certificação original (`known_before_trade: SIM — pivô confirmado ci<j`) estava **FALSA**: o teste usado (`i<j`) era o errado. O certo é `conf_i<=j` — e **94/96 entries disparam ANTES de conf_i**.

## 5. Exit causality — OK ao nível do trade
FIXED_3R first-touch SL-first; sem MFE-trigger; timestop fecha a mercado; executável — **condicional à população**.

## 6. Métricas — válidas SÓ condicional-à-população
Baseline N83 62,7%/+125R/DD−4/stk4; SL atual **domina** as 4 alternativas; 3R vs 2R/4R/timestop = trade-off WR/streak vs sumR. Estes achados **transferem** para uma base reparada.

## 7. Robustez — OK nos testes, com 2 correções de leitura
- Slippage (0,05/0,10 ATR): −5R apenas; delay-1-bar: inalterado; 0 gap-through (medido, com opens; **sample-limited** — 114 gaps ≥24h na série, nenhum trade calhou de atravessar um até ao stop; risco de cauda residual, não "resolvido").
- **Exposure-null p=0,0 do timestop = MECÂNICO** (F é o membro de exposição-máxima da própria família do null; R é monótono na exposição: cap 48→89,6 … 288→211,6). O null na verdade **suporta** a história de beta: random-hold médio (+144) > baseline 3R (+125) → o excesso do 4R/timestop é beta de tendência da amostra (eco da lição L1 4H).
- **Boundary do filtro ±0,5 = ROBUSTEZ-POR-VAZIO** (0 trades BEAR com px_vs_ema em (−0,5,+0,5); vizinhos −0,56/+0,62) — o sweep é não-informativo, não robustez.
- Janela real = **~11 meses** (ago-2025→jul-2026), não "2 anos"; per-quarter = 4 trimestres cheios; WR CI95 [52,2, 73,1].
- **21/83 trades sobrepõem-se** (máx 3 posições concorrentes) — +125R assume todos tomados; sob sizing FN = até 3R de exposição simultânea, não-divulgado antes.

## 8. Execution realism — OK exceto o ponto 9
Fills target sem exigência de penetração (leve otimismo, imaterial); spread stress adequado p/ XAU.

## 9. 🚨 ACHADO CENTRAL (FAIL): EVENT-SELECTION LOOKAHEAD NA BASE N96
- O zz(r=6) só emite o pivô L (demanda) quando um **rally FUTURO de 6 ATR** o confirma (`conf_i`). `build_entry` dispara do bar i+1 **sem esperar conf_i**.
- **Medido (2×, DA + eu): 94/96 (N83: 82/83) entries ANTES da confirmação; mediana 20 barras cedo; máx 109; 22/96 antes até do H-pivot anterior confirmar.**
- **Assinatura de survivorship: 0/94 eventos mantidos imprimem lower-low entre entry e confirmação** — a população foi filtrada pelo próprio movimento que faz o trade ganhar.
- **Análogo live-fireable do DA** (low candidato + reclaim EMA21, sem esperar confirmação): **N173 entries, WR 28,3%, +23R** (vs backtest N96 54,2% +112R); os 98 extra silenciosamente excluídos vão 8W/90L = −66R. (Uma operacionalização; números ±, direção robusta.)
- **Consequência: 62,7%/+125R/stk4/DD−4 NÃO são reproduzíveis por um executor causal.** É a MESMA classe de leak que matou o r=12 em 2026-07-07 ("a confirmação do pivô usa movimento futuro") — a lição estava registada mas **não foi aplicada ao próprio r=6 base**.

## 10. Production readiness — NÃO
`FAIL_LEAK_OR_NOT_REPRODUCIBLE` no nível da certificação. A maquinaria SL/exit deste bloco não introduziu leak (reprodução PASS; alternativas causais); o defeito é **herdado da base aprovada** `entry_engine_master_20260707.py`.

## Salvage path (não é redesign, é re-run)
1. **Reparar a base:** entries gated em `conf_i` (só dispara após confirmação do pivô) **OU** aceitar o universo honesto live-fireable (~173 entries) — decisão do Cris.
2. Re-correr universo → filtro capitulation → SL/exit stack sobre a base reparada (os achados SL-dominância e exit-trade-off devem transferir).
3. Re-flag do status N96/N83 na autoridade (provenance discipline).

**PRODUÇÃO: NOT_AUTHORIZED. Base N96/N83 = requer re-verificação causal antes de qualquer preproduction.**
