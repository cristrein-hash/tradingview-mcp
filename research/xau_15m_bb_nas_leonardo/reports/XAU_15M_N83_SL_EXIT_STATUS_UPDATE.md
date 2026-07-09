# XAU 15M N83 — SL/EXIT REVIEW · STATUS UPDATE

**2026-07-09.** Bloco SL+EXIT review executado por completo (universo→audits→baseline→reviews→robustez→DA). **Verdict final: `FAIL_LEAK_OR_NOT_REPRODUCIBLE`** (DA + verificação independente).

## O que o bloco encontrou (2 camadas)

### Camada 1 — dentro da população congelada (válido condicional)
- **Modelo de execução é real ao nível do trade:** SL/target = preços reais; 0 timeouts; 0 both-touch; 0 gap-through; **+125R = +3/−1 = modelo executável first-touch** (não simplificação).
- **SL atual (demand_low−0,1ATR V1) DOMINA** as 4 alternativas pré-registradas em todas as métricas → `KEEP_CURRENT_SL` (condicional).
- **Exit 3R atual = perfil FN** (WR 62,7, stk 4, DD −4, 0 trimestres negativos, robusto a slippage/delay). 4R (+162R) e timestop-288 (+211,6R) = **beta de exposição** (random-hold médio +144 > 125; excesso = tendência da amostra), EXPLORATORY, não adotar.
- Estes achados **transferem para uma base reparada**.

### Camada 2 — 🚨 a base N96 tem EVENT-SELECTION LOOKAHEAD (o achado que manda)
- **94/96 entries disparam ANTES da confirmação do pivô de demanda** (zz r=6 confirma com rally futuro de 6 ATR; mediana 20 barras cedo). 0/94 lower-lows entre entry e confirmação = survivorship pura.
- Análogo live-fireable: **N173 · WR 28,3% · +23R** (vs N96 54,2% +112R). Os headline numbers **não são reproduzíveis por executor causal**.
- Defeito **herdado da base aprovada** (`entry_engine_master_20260707.py`); a maquinaria deste bloco reproduz byte-match e não introduziu leak.
- As minhas certificações F3/F4 (`known_before_trade: SIM`) usavam o teste errado (`i<j` em vez de `conf_i<=j`) — **corrigidas por este update**; os JSONs de audit ficam como artifact histórico com esta correção por cima.

## Decisão do bloco
`BLOCKED_EXECUTION_MODEL` no nível da estratégia (via `FAIL_LEAK` da certificação): **não há preproduction possível sobre a base atual.**
- SL selecionado (condicional): **manter V1**. Exit selecionado (condicional): **manter 3R fixo**.
- **+125R era executável DENTRO da população; a população em si não era causalmente alcançável.**

## Próximo gate necessário (decisão do Cris)
1. **Reparar a base** — opção A: entries só após `conf_i` (confirmação do pivô); opção B: universo live-fireable completo (~173) e re-filtrar dali.
2. Re-correr filtro capitulation + SL/exit sobre a base reparada.
3. Re-flag N96/N83 no STRATEGY_STATUS_MASTER (de `USER_APPROVED_NOT_PRODUCTION` para `NEEDS_CAUSAL_REBASE`) — **requer decisão do Cris** (não alterado por mim).

## Confirmação negativa
Sem produção/Telegram/broker/runtime/strategy_rules/monitor · sem chart/plot/screenshot · sem sinal · prereg/manifest atualizados. **PRODUÇÃO: NOT_AUTHORIZED.**
