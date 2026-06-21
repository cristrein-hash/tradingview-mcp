# BLOCO HAS_OVERHEAD-AWARE CONTEXT FEATURE — SPEC (fechado)

**2026-06-21.** Escopo: XAU_4H_L2_BPT_BOS_CHOCH. **Diagnóstico apenas.** Sucessor do REGIME/CONTEXT/FUEL v1
(cf7dafa), que concluiu: `dist_4h_supply` separa A/B no agregado mas FALHA âncoras (preserve 9/18, aceita
S40) porque **conflaciona dois mercados** — supply-overhead-real-bearish vs no-overhead/ATH-bullish. Este
bloco desenha a **feature composta causal has_overhead-aware** que desconflaciona. **Resultado = hipótese
calibrada, não feature validada/promovida.**

## Travas (invioláveis)
Diagnóstico apenas · não rodar AGG_v2 · não promover regra/gate/feature · não alterar engine/decisions_merged/
registry/library/produção/Telegram/chart-MCP/SLIM/runtime/monitor/receiver/strategy_rules/catalog ·
**nenhum predicado usa outcome/realR/exit_type/MFE/futuro** · **não usar IDs específicos para fit** ·
não commitar execução — agora SÓ spec.

---

## 1. Feature design
**Inputs causais (todos conhecíveis no close do bar i; externas só com shift D-1):**
| input | papel |
|---|---|
| `has_4h_supply_overhead` (0/1) | **gate primário**: existe supply acima? |
| `dist_4h_supply_low_atr` | distância à supply 4H (só interpretável SE has_overhead=1) |
| `supply_broken_before` / `supply_rejected_before` (0/1) | supply já rompida (bullish) vs rejeitou antes (resistência viva) |
| `supply_blocks_2/3ATR` | densidade de overhead próximo |
| `demand_touched_on_retest`, `demand_age_bars`, `dist_4h_demand_low_atr` | suporte abaixo (qualidade demanda) |
| `dist_d1_supply_atr`, `dist_d1_demand_atr`, `has_d1_supply/demand` | posição no frame D1 (markup vs bounce) |
| `trend_30_atr`, `slope20_atr`, `rsi_1d`, `rsi` | momentum/trend (condiciona legpos) |
| `legpos90/60/30` | **só condicionado a trend/momentum**, nunca monótono |
| ATH/no-overhead proxy = (`has_4h_supply_overhead==0`) | proxy bullish ATH |

**Tratamento de `dist_supply = None` (o erro do v1):**
- `None` **NÃO** é "não-bull". Decompor a causa:
  - `has_4h_supply_overhead==0` → **NO_OVERHEAD** (não há supply acima) → ATH/markup → contexto **bullish** (é sinal, não dado faltante).
  - `has_4h_supply_overhead==1` mas dist ausente → **missing data real** → estado UNKNOWN.
- **Distinção None-bullish vs missing:** sempre cruzar `dist_supply` com `has_4h_supply_overhead`. None+overhead=0 = bullish; None+overhead=1 = missing → UNKNOWN.

## 2. Estados da feature (saída categórica + score contínuo de fuel)
| estado | condição (causal, na entrada) | leitura |
|---|---|---|
| **NO_OVERHEAD_BULLISH** | has_overhead=0 (dist=None por ausência de supply) + momentum não-negativo | ATH/sem teto → bull-run/markup |
| **MARKUP_BREAKING_SUPPLY** | has_overhead=1 + dist baixa + supply_broken_before=1 + trend forte | rompendo supply próxima em markup |
| **VALID_OVERHEAD_SUPPLY_RISK** | has_overhead=1 + dist baixa + supply_rejected_before=1 / não rompida | supply viva colada acima = risco |
| **SUPPLY_COLADA_BEARISH** | has_overhead=1 + dist muito baixa + momentum fraco + sob overhead | trap: bounce sob teto |
| **LATE_TOP_UNDER_SUPPLY** | has_overhead=1 + legpos90 alto + momentum a enfraquecer + rsi alto | exaustão de topo |
| **UNKNOWN_INSUFFICIENT_DATA** | dist None com has_overhead=1, ou inputs-chave faltando | sem leitura → fora do fit |

Nota: NO_OVERHEAD_BULLISH e MARKUP_BREAKING_SUPPLY = família bull (preservar); VALID_OVERHEAD/SUPPLY_COLADA/
LATE_TOP = família risco (bloquear/revisar). **fuel** = score contínuo (room-to-overhead OU "sem teto") — tier
diagnóstico, **sem position sizing**.

## 3. Causalidade
- Timestamp: cada input no close do bar i (4H). Externas (D1 regime) só com **shift D-1** (validado no v1: 0 join_issues, shift≥1).
- **Sem futuro.** Proibido: supply "rompida DEPOIS", candle posterior, outcome.
- **Anti "supply rompida depois":** `supply_broken_before` tem que ser computada **só com bars ≤ i** (rompimento ANTES da entrada). Verificar a proveniência do campo (Layer-1 style) antes de usar; se a flag embute futuro, descartar e derivar versão causal.

## 4. Teste diagnóstico (quando autorizado)
- Reaplicar em **A=26, B=18, C=18** (mesmos sets do v1; C continua FORA do fit).
- **Anchor check (critério, não fit):** preservar T34/T35/T37/T41, S29-S32, T39, S20, S24-S27, S35-S38; bloquear T40/S40-like. **Foco no que o dist_supply puro FALHOU:** os None-bullish (S29-32/T39) e os overhead-moderado-bull (T34/35/37/41) têm que cair em família bull; S40 em família risco.
- **Comparar contra `dist_4h_supply` puro** (baseline v1): quantos anchors recupera, quantos perde.
- Reportar onde melhora e onde ainda falha.

## 5. Robustez
- Split temporal (2020-23 / 2024-26) + reverso/sensibilidade SE viável; shuffle-null se aplicável.
- **Declarar n pequeno** (A=26/B=18; held-out B-late n=3 — provável frágil). Calibração, não validação.

## 6. Market interpretation (obrigatória, não "estado X separa")
- Por que cada estado = contexto real de mercado.
- **no_overhead_bullish vs supply_colada_bearish:** ausência de teto (ATH/markup) é combustível; teto vivo colado é risco — a mesma "supply próxima" lida ao contrário conforme has_overhead/broken.
- **bull-run high-legpos vs late-top exhaustion:** legpos alto COM momentum forte + sem teto = continuação; legpos alto COM momentum a enfraquecer + sob overhead + rsi alto = exaustão.
- Veredicto: confluência contextual real ou estado frágil?

## 7. Outputs (quando autorizado — NÃO agora)
`results/l2_bpt_overhead_feature_{values,comparison_vs_distsupply,anchor_check,da}.csv` + relatório curto.
Commit isolado SÓ após autorização + preflight. Sem tocar engine/produção/decisions/registry.

**PRÓXIMO:** aguardar autorização explícita para EXECUTAR. Este bloco entrega só o spec.
