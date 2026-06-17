# XAU 4H — L2/BPT / BOS·CHoCH Pure — Reboot Plan

**Data:** 2026-06-17 · **Tipo:** plano de revalidação estrutural (reconstrução, sem execução) · **NOT_VALIDATION.**
**Decisão de pesquisa:** parar de maturar o BREAKOUT/D1a como motor de entrada; **resgatar e aprofundar a estratégia BOS/CHoCH pura / L2-BPT / Reason Atlas** como mecanismo estrutural de entrada.
**Bloco:** plano — **zero execução** (sem backtest/workflow/agente/plotagem/MCP/RAW-write/Telegram/produção/SLIM/SHORT/Caminho B/OOS). Só este doc.

> **UPDATE 2026-06-17:** o detector do census v1 (Williams 5/5 puro) falhou o recall-gate (0/17 BOM). O **Detector v2.2** (safety pack) foi recuperado e tem **recall 17/17** confirmado — passa a ser o **anchor de recall / candidate generator** desta frente. Ver `XAU_4H_L2_BPT_DETECTOR_V2_2_RECALL_AUDIT.md` + incidente. Próximo trabalho = camadas 2-3 (contexto/gestão/exit) sobre o candidate set do v2.2, com recall-gate permanente.

---

## 1. Executive summary

O BREAKOUT/D1a comprava topos: o gate `close>swing10_high` é uma varredura de liquidez; a entrada imediata é tardia; nem D1a/EMA/ATR/retest-genérico mediam estrutura macro, supply, bear-legs e captura de liquidez. **Pivot:** voltar ao motor estrutural **BOS/CHoCH puro (L2 v2 / SMC Unified Rebuild) + macro-location BPT (at_d1_demand, macro-leg atlas) + Reason Atlas (NAS LONG/SHORT, bubbles, RSI como contexto de exaustão)**, onde o breakout vira **validação**, não entrada.

A família L2/BPT **já tem muito construído** (Ground Truth de 16 BOM, definições SMC canônicas, state-machine pré-registrada, design causal de at_d1_demand, atlas de pernas macro), mas **nunca foi backtestada limpa** (L2 v1 tinha SMC mecânico fraco; o detector v2.2 é só candidate-generator denso). Este plano **reconstrói os gates reais, separa implementação-ruim de conceito-bom, mapeia o teste em RAW e propõe a revalidação faseada** — **sem rodar nada**.

---

## 2. Fontes resgatadas

- **Memória:** `reference_L2_SMC_definitions_canonicas` (L2 v2 defs), `reference_SMC_Unified_Rebuild_v0_preregistro` (state-machine), `project_caminho_a_padroes_visuais_5_layers` (Padrões #1/#7/#8).
- **Safety pack** `~/Desktop/TRADING/L2_REBOOT_SAFETY_PACK_2026-06-09` (370 arq), lidos:
  - `L2_BOOTSTRAP_STATE.md` — Ground Truth v1 (16 BOM_HIGH ancorados + NAOs com entry/stop/bars), Detector v2.2 (recall 16/16, 1109 cand/ano — só candidate generator), **blockers que matam BOMs** (first_retomada 11/16, BOS_fraco 7/16, overextended 6/16, cluster_BUY_climax/bear_macro/volume_fraco 4/16 — **JAMAIS veto duro**).
  - `L2_BPT_AT_D1_DEMAND_DESIGN_V2.md` — contexto demanda 1D causal (inside/above/below separados; `at_d1_demand = inside OR near_from_above`; **below = "defesa perdida/falling-knife", NÃO at-demand**; ATR_D1 só dailies fechadas; painel tol 0.25/0.5/1.0; saída honesta possível `D1_DEMAND_DOES_NOT_SEPARATE`).
  - `L2_BPT_BLOCKS_1_TO_5_MACRO_LEG_RAW_BREAKDOWN_V2_NAS_LONG_SHORT.md` — Reason Atlas: posição de cada trade na perna macro; **NAS LONG/SHORT via FIRST-APPEARANCE de labels** (nunca TOP/BOTTOM nem `*_SIGNAL` numérico); cluster NAS SHORT + bubbles + RSI = topo/distribuição.
- **Docs:** `XAU_4H_BREAKOUT_D1A_VS_L2_BPT_REASON_ATLAS.md` (comparação), aprendizados BREAKOUT (entry mining, metrics, audit).

---

## 3. Lógica estrutural reconstruída (gates reais — L2 v2 / SMC Unified)

**Convenção:** CLOSE-ONLY-CAUSAL; pivots SHIFT5; tudo de barra fechada.

1. **Pivot** Williams 5/5 SHIFT5: `high[i]>max(high[i±1..5])`; no bar N só pivots `i≤N-5`.
2. **Protected LH** (causal): swing high confirmado imediatamente antes do **LL confirmado mais recente** da fase bearish (não `max`).
3. **CHoCH bullish:** `close > protected_LH + 0.2·ATR` → fixa **polaridade = protected_LH** (não atualiza com BOS).
4. **BOS bullish (obrigatório):** `close > swing_high_anterior + 0.2·ATR` numa sequência HH-HL ativa pós-CHoCH (não `max(high,N)` mecânico).
5. **Retest + reclaim (entry):** `low ≤ polaridade + 0.15·ATR` (retest) → bar verde `close>open`, `body≥0.5`, `close>polaridade + 0.1·ATR` (reclaim/aceitação). Entry = close do reclaim.
6. **SL estrutural:** abaixo do swing low estrutural relevante − 0.1·ATR; **R floor 0.3·ATR / ceiling 1.5·ATR (abort)**.
7. **Invalidação:** close < swing low estrutural pré-CHoCH (ou < HL confirmado pós-CHoCH).
8. **State-machine (SMC Unified S0-S4):** S0 sem-estrutura · S1 CHoCH_fresh (first retest) · S2 BOS_confirmed (retest polaridade/BOS) · S3 uptrend_mature (retest demand-zone/HL) · **S4 topping/block overlay** (NAS SHORT/TOP 5b OR drop>3·ATR — RSI>75 só log).
9. **Macro-location (BPT at_d1_demand v2):** contexto causal de demanda 1D (`d1_record_used` ≤ entry; inside/above/below separados; só inside/near_from_above = suporte). Overlay de contexto, **não trigger**.
10. **Reason Atlas (exaustão/posição na perna):** NAS LONG/SHORT first-appearance, BUY/SELL bubbles, RSI — para distinguir reclaim bom vs armadilha (TOP_OR_DISTRIBUTION / LATE_RECLAIM_BAD_LOCATION / FALLING_KNIFE_INTO_VOID).

---

## 4. Implementação ruim (abandonar) vs conceito bom (reaproveitar)

| Implementação RUIM (abandonar) | Conceito BOM (reaproveitar) |
|---|---|
| L2 v1: BOS = `close>max(high,20)` mecânico | BOS estrutural (HH em sequência HH-HL + 0.2ATR) |
| polaridade = high do swing rompido | polaridade = **protected_LH** (nível defendido, fixo) |
| sem CHoCH como pré-condição | CHoCH (mudança de caráter) obrigatório |
| sem "protected" rigoroso | protected_LH causal (antes do LL recente) |
| Detector v2.2 como estratégia (1109/ano) | v2.2 só como **candidate generator** |
| blockers virando veto duro | blockers como **contexto** (matam BOMs → nunca veto) |
| NAS TOP/BOTTOM ou `*_SIGNAL` numérico | NAS LONG/SHORT **first-appearance** de labels |
| BREAKOUT: entrada imediata no sweep | breakout = **validação**; entrada no retest/reclaim |
| SL `low−0.5ATR` (tight, não-estrutural) | SL estrutural R-bounded (0.3-1.5ATR) |
| swing10 como trigger | swing10 como referência de validação apenas |

---

## 5. Diferenças contra o BREAKOUT/D1a

- **Entrada:** BREAKOUT = imediata no rompimento (compra topo/sweep, tarde). L2/BPT = retest+reclaim a um nível defendido (compra o retorno ao valor após mudança de caráter).
- **Nível:** BREAKOUT = `swing_high_10` (mecânico). L2 = polaridade = `protected_LH` (estrutural, defendido).
- **SL:** BREAKOUT = `low−0.5ATR` (tight). L2 = abaixo da estrutura, R-bounded.
- **Estrutura macro / supply / bear-legs:** BREAKOUT não mede. L2/BPT mede (CHoCH/BOS, at_d1_demand, macro-leg atlas, S4 topping).
- **Aprendizados do BREAKOUT reaproveitados:** evita comprar topos (S4 + Reason Atlas); risco de entrada tardia (entry no retest, não no sweep); **D1a → contexto macro auxiliar (at_d1_demand)**; **EMA/ATR → tags, não gatilhos**.

---

## 6. Como testar BOS/CHoCH puro em RAW (mapeamento)

- **Fonte:** RAW 4H `.gz` via extractor auditado in-memory (zero slim) — mesma cadeia já validada nesta sessão. SMC labels/boxes, NAS labels, Custom OB boxes, RSI vêm do RAW (`pine_labels`/`pine_boxes`/`study_values`).
- **Detectores próprios (causais):** pivots 5/5 SHIFT5 → protected_LH → CHoCH → BOS → polaridade → retest/reclaim. (Não confiar em `smc_*` repintáveis do extractor como gate sem SHIFT — usar detector próprio + cross-check com SMC nativo.)
- **Macro 1D:** `d1_record_used` causal (≤ entry) para at_d1_demand + ATR_D1 (dailies fechadas). Reusar EMA1D já gerado se aplicável.
- **NAS:** first-appearance de labels (≤ entry−1).
- **Causalidade:** guarda 1D↔4H, SHIFT5 pivots, close-only, no-overlap, sem `x` como tempo.

---

## 7. Plano de revalidação estrutural (faseado — NÃO executar; cada fase exige autorização)

- **Fase A — Detectores causais (read-only):** implementar pivots 5/5 SHIFT5, protected_LH, CHoCH, BOS, polaridade em `/tmp` ou research; **audit de causalidade** (`pivot.idx+5 ≤ bar`) + cross-check vs SMC nativo (±5 bars). Sem backtest.
- **Fase B — State-machine S0-S4 + entry/SL:** mecanizar triggers por estado + SL estrutural R-bounded; **gate manifest** + sanity examples (1 pass/1 fail/1 borderline). Sem backtest.
- **Fase C — Overlays:** at_d1_demand v2 (contexto, painel tol sem vencedor) + Reason Atlas (NAS/bubbles/RSI exaustão) + S4 topping. Como **contexto/diagnóstico**, não filtros prematuros.
- **Fase D — Backtest pré-registrado (só com autorização):** por estado S1/S2/S3, no-overlap, TRAIN/HOLDOUT, **gross + custos**, Bonferroni (α/3), bootstrap vs avgR=0, MFE/MAE por estado, no-topN/jackknife. Saída honesta possível: `STATE_X_NO_EDGE` / `D1_DEMAND_DOES_NOT_SEPARATE`.
- **Fase E — Visual review** dos trades por estado (Auction Theory) antes de qualquer veredito.
- **Disciplina:** medir antes de filtrar; blockers nunca viram veto duro; calibração ≠ validação; janela virgem exige set independente.

---

## 8. O que será reaproveitado · o que será abandonado

**Reaproveitado:** definições SMC canônicas (L2 v2) · state-machine SMC Unified v0 (pré-registro pronto) · at_d1_demand v2 causal · NAS LONG/SHORT first-appearance · Custom OB v11 demand zones · Ground Truth de 16 BOM (referência de acerto) · análise de blockers (o que NÃO vetar) · infra causal (extractor RAW in-memory, EMA1D, no-overlap, TRAIN/HOLDOUT, DA framework) · buffers canônicos (0.2/0.1/0.15 ATR, R 0.3-1.5) · aprendizados do BREAKOUT (D1a→contexto, EMA/ATR→tags, evitar topo, entrada tardia).

**Abandonado:** BREAKOUT como motor de entrada imediata · swing10 como trigger · SL tight 0.5ATR · L2 v1 (SMC mecânico) · detector v2.2 como estratégia · NAS TOP/BOTTOM e `*_SIGNAL` numérico · blockers como veto duro · geometria +4R-sobre-stop-minúsculo como "resposta".

---

## 9. Devil's Advocate (auto-checklist)

- ✅ Nenhum backtest/execução. ✅ Nenhuma plotagem/MCP/Telegram/broker/produção. ✅ Sem SLIM (plano aponta RAW-only). ✅ L2/BPT reconstruído de fontes reais (memória + safety pack), não inventado. ✅ BREAKOUT tratado como aprendizado, não descartado como "sem valor". ✅ Conceito-bom separado de implementação-ruim. ✅ Não chamou nada de validado (tudo pré-registro/plano). ✅ SHORT não aberto · Caminho B não recomendado · OOS não rodado. ✅ L1 intacta · catalog/strategy_rules intactos.

**DA: PASS (plano de reconstrução; nada executado).**

---

*Read-only. Reconstrução a partir de memória + safety pack (`~/Desktop/TRADING/L2_REBOOT_SAFETY_PACK_2026-06-09`) + docs. Nenhum backtest, plotagem, RAW-write, produção. Próximo passo aguarda decisão do usuário.*
