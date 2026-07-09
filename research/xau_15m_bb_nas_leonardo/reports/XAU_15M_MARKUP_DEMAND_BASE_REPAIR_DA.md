# XAU 15M MARKUP-DEMAND — BASE REPAIR (Opção B) · Devil's Advocate FINAL

**2026-07-09.** DA real (Agent tool; re-implementou o walk independentemente e reproduziu o CSV 166/166). **Verdict: `PARTIAL_EDGE_WEAK_BUT_RESEARCHABLE`** (4 emendas obrigatórias, aplicadas).

## 1. Erro da base original
Event-selection lookahead (zz r=6 confirma pivô com rally FUTURO de 6 ATR; 94/96 entries pré-confirmação; survivorship 0/94). Base N96/N83 contaminada — 62,7%/+125R irrecuperáveis.

## 2. Live-fireable removeu o lookahead? — SIM (OK)
Walk online: pivôs só existem a partir da confirmação; estado no bar k computável com dados ≤ k (verificado pelo DA em TODOS os 166, 0 violações; outcome recompute 0 mismatches). **47,6% dos candidatos imprimem lower-low pós-entry** (vs 0% na base contaminada) = assinatura de survivorship QUEBRADA.
**Deviation divulgada (conservadora, não-leak):** no caminho da janela residual pós-confirmação, `prevL` é sobrescrito antes do check MARKUP → 3 trades omitidos (2 SL/1 TGT, net +1R se incluídos). Explica parte do N=166 vs ~173 do prior (resto = folga de operacionalização de um prior explicitamente aproximado).

## 3. Source guard — PASS
Seleção usa só zz-state online/running-low/reclaim/janela/higher-low-confirmado; sem outcome/membership; features causais (1D último bar fechado — **sanity diff 0.000 vs cut CSV original**, normalização ATR_15M[j] idêntica ao original; regime v5 hour-causal verbatim, auditado antes).

## 4. Filtro capitulation na base causal — **A DESCOBERTA POSITIVA DO REPAIR (OK, sobrevive a todos os ataques)**
- Corta **22 trades = 22 losers / 0 winners** na base CAUSAL.
- **Null exato (hipergeométrico): P=0,0016** (o 0,0005 simulado era otimista — emendado). **Null episódico (10 episódios, 3-day gap): P=0,0047.**
- **Replicação out-of-population genuína:** dos 22 cortados, só 8 são da cut-13 original; **14 são trades NOVOS que nunca existiram na base contaminada — todos losers.** Filtro congelado 2026-07-08, antes deste universo existir. Não é re-mineração.
- Sem canal mecânico de artefato identificado (SL 15M sem ligação à EMA 1D); leitura estrutural coerente (corta longs contra-tendência em rally de bear). Condicional à definição do regime v5.

## 5-6. SL/exit transfer + métricas — OK, mas MARGINAIS (emenda 4 aplicada)
KEPT n=144: WR 31,9% · +40R · PF 1,41 · DD −15 · streak 15 · 1 trimestre negativo. **Estatística honesta:**
- Base 166 @ 27,7% vs breakeven 25%: **p=0,235** (indistinguível de breakeven).
- Kept 144 @ 31,9%: binomial **p=0,036**; com breakeven ajustado a slippage **p=0,049**.
- **Independência violada: 45/166 entries com trade anterior aberto** (máx 3 concorrentes); bootstrap semanal (44 semanas): **P(sumR≤0)=0,061** → **+40R NÃO é robustamente >0.**
- Concentração/decay: sem o melhor mês (dez-25 +15) → +25R; 2026 últimos 3 meses cheios −1/−5/−5.
- Delay-1-bar: 2 flips que se compensam ("net-unchanged", não "unchanged"). Slippage −1,8/−3,6R.

## 7. Robustez — mista
Filtro: fortíssimo (nulls acima). Agregado: marginal (acima). BULL bucket 44,4%/PF 2,4/n45 = lead de pesquisa declarado (structural-first, sem tuning); RANGE negativo; US session flat.

## 8. B vs base contaminada
Contaminada 96→83: 62,7%/+125/DD−4/stk4. Causal 166→144: 31,9%/+40(marginal)/DD−15/stk15. **O edifício antigo não volta.**

## 9. Opção A necessária?
Não executada (B deu resposta suficiente: PARTIAL). Prereg da A criado (`XAU_15M_MARKUP_DEMAND_BASE_REPAIR_OPTION_A_PREREG.md`) para decisão futura do Cris — entries só após `conf_i` (timing mais tardio, N menor, potencialmente WR maior).

## 10. Verdict: `PARTIAL_EDGE_WEAK_BUT_RESEARCHABLE`
NÃO é FAIL: os ativos validados são reais — (i) **filtro capitulation = causal loser-cutter replicado out-of-population** (P 0,0016/0,0047; 14/14 losers novos); (ii) **BULL bucket** como lead. NÃO é PASS: o agregado +40R é marginal (p 0,049-0,061), streak 15/DD −15 inoperáveis, sem viabilidade FN/produção. **Qualquer citação de "+40R/PF 1,41" TEM de carregar o qualificador p≈0,05-0,06.**
