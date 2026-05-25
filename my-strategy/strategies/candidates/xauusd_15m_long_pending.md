# XAU 15M LONG — Candidate Packet (draft pendente)

**Status:** RESEARCH (pre-CANDIDATE — falta hipótese e critérios objetivos)
**Criado:** 2026-05-25 (draft preparado por Claude pra preenchimento por Cris)

---

## Cabeçalho pré-preenchido

```yaml
strategy_id: xauusd_15m_long_<short_name>
display_name: <preencher>
asset: PEPPERSTONE:XAUUSD
base_symbol: XAUUSD
timeframe: 15
direction: LONG
status: RESEARCH
created_at: 2026-05-25
author: Cris+Claude

approved_by: pending
approved_at: null
last_promotion_at: null
last_promotion_to: null
exception_to_pipeline: none
```

---

## ⚡ Slots obrigatórios pra preencher (mínimo pra promover RESEARCH → CANDIDATE)

### 1. Hipótese operacional
*(preencher: 2-3 frases — o que captura e por que deve funcionar)*

### 2. Critérios objetivos
**Entrada:**
- *(trigger 1)*
- *(trigger 2)*

**Filtros:**
- *(filtro 1 — provavelmente regime macro alinhado, ver memory scan abaixo)*

**Invalidação:**
- *(condição)*

**Stop técnico:** *(regra única)*

**Target / saída:** *(regra única)*

**Quando NÃO operar:** *(regimes/contextos a evitar)*

### 3. Backtest
*(janela mínima 6 meses ou n=30 trades; expectancy >0R obrigatório)*

```yaml
window: { start: ..., end: ... }
n_trades: ?
win_rate_pct: ?
expectancy_R: ?
profit_factor: ?
max_drawdown_R: ?
```

---

## 📚 Memory scan — contexto e referências (preparado 2026-05-25)

### Por que XAU 15M LONG é candidato natural agora

1. **TF 15M LONG já liberado operacionalmente** (`[[project_tf_15m_long_liberated]]`, 2026-05-15): peso igual a TF 4H quando ativo whitelist + direção LONG. Não há rigor extra pra promoção a CANDIDATO_FORTE.

2. **D2R Phase 2 valida edge geral em TF 15M LONG** (n=18 outcomes cross-asset):
   - Win 72%, expectancy +1.50R, PF 6.38 ⭐
   - Comparável a TF 4H LONG (75% win, +1.43R, PF 9.61)

3. **MAS XAU 15M LONG NÃO está na amostra D2R Phase 2.** Edge é em US500 (n=11, PF 5.19) e XPTUSD (n=19, PF 2.50). Premissa: **assumir transferência de edge pra XAU é hipótese, não evidência.** Backtest específico XAU 15M obrigatório antes de promover.

4. **Não há audit XAU 15M específico em `research/backtests/`** (só `xauusd_audit_20260512` que é 4H e `xauusd_1h_audit_20260512` que é 1H). Backtest novo precisa ser feito.

5. **Bubble gate relaxado por TF** (`[[project_bubble_gate_relaxed_by_tf]]`): LTF mantém gate, HTF cluster opcional. Aplicável se a estratégia usar Bubbles como filtro.

### Padrões perdedores XAU já documentados (evitar repetir)

`[[project_xau_losing_patterns]]` — 7 trades XAU perdedores. Padrões recorrentes:
- **Sweep traps** (rompimento de range que reverte)
- **SHORT contra-trend** (não aplicável pra LONG mas instrutivo)

### Infraestrutura já pronta

- **Custom OB v12** (`12_custom_ob_detector_v12.pine`) — disponível em XAU 15M, já dispara DEMAND zones detectadas
- **NAS TopBottom** — disponível em XAU 15M
- **Bubbles** — disponíveis em XAU 15M (large/medium/small × buy/sell, 6 alertas)
- **RSI** — bear/bull div + cross 30/50/70 disponíveis em XAU 15M

### Possíveis ângulos de hipótese (pra Cris escolher/refinar)

1. **DEMAND_BREAKOUT_INTRADAY** — análogo ao XAU 4H DEMAND_BREAKOUT mas em 15M. Trigger: Custom_OB DEMAND tocado + breakout swing high pequeno.
2. **PULLBACK_EMA50_15M** — análogo ao ETH 1H PULLBACK_EMA50 mas em XAU 15M. Trigger: pullback EMA50 + reclaim + bullish body.
3. **BUBBLE_LARGE_BUY_REGIME** — Bubble Large_Buy em XAU 15M filtrado por regime 1H alinhado (HTF1H bullish).
4. **NAS_LONG_INTRADAY** — NAS TopBottom Bottom em XAU 15M filtrado por regime 4H bullish.

---

## Próximo passo

Cris define hipótese (ou escolhe um dos 4 ângulos acima ou outro), preenche seções 1-2-3 do template padrão (`my-strategy/research/STRATEGY_CANDIDATE_TEMPLATE.md`), aprova → status passa a CANDIDATE.
