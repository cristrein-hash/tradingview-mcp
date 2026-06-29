# RTSE_PHASE_PLAN_V0 — Plano em Fases & Gates

**Status:** PLANNING. Documentação only. Sequência de construção com gate make-or-break por fase e critério de FALHA explícito. **Nunca começar como gate live.**

---

## Arquitetura-alvo (6 camadas + caminho live)
```
L0 Source & Provenance  →  L1 Causal Feature Factory  →  L2 State Reader (multi-eixo)
   →  L3 Confidence×Latency (EF modula aqui)  →  L4 Profile Router (terminal, por-profile)  →  Strategy Consumers

Live: Recorded Context First → Passive Runtime → Shadow Comparison → Regression Lock → User Sign-off → Live Advisory Only → (Possível gate futuro)
```

## Fases (cada uma só avança se o GATE passar)

| Fase | Entrega | GATE make-or-break | Critério de FALHA |
|---|---|---|---|
| **0 — Harness + ground-truth (BARATO, primeiro)** | `true_reversals_loader`, `latency_fp_frontier`, `redteam_lookahead`, baselines triviais. Mede **v5 atual + baselines vs M8**. | Harness reproduz 414/205/209; produz a 1ª curva latência/FP; red-team passa no detector trivial. **v5 mostra sinal de bater o lagged-MA.** | Nem v5 bate o trivial → **premissa frágil, re-escopar antes de construir camadas.** |
| **1 — L0+L1 (provenance + feature factory)** | Gate de inputs (selos RAW), as-of/SHIFT1/D-1, feature factory das features provadas. | Todo input com selo; red-team byte-idêntico sob barra-futura injetada. | Qualquer feature UNKNOWN/REJECTED entrando em validação → bloqueia. |
| **2 — L2 regime sub-layer (subsume v5) + FRONTIER vs baselines** | `structural_regime` generalizado do v5 + 4H fallback. Curva completa vs todos baselines. | **RTSE Pareto-bate v5-puro E MA-cross E swing E RSI E null**, sob null+jackknife-episódio+por-ano, Bonferroni-aware. | Só empata v5 → entregar como **consolidação, não edge** (declarar). Colapsa em jackknife/ano → beta, matar claim. |
| **3 — L2 turn-state + counter-pullback** | `turn_state` (early→confirmed), `counter_pullback`, `strength`. | swept/h1_pos/bottom-power reproduzem null p=0 / p=0,018 / beats-null; counter-pullback separa dip-em-bull de regime-break acima de null. | Não passa null por valor → fica RESEARCH_ONLY (nascimento faseado §schema). |
| **4 — L3 Confidence×Latency** | confidence (não-fitada §schema §5), componentes, latency buckets, FP budgets. | Agregado é não-tunado OU forward-calibrado; multi-M (M6/8/10/12) não quebra. | Confidence vira soma de pesos a dedo → rejeitada. Edge some ao trocar M → frágil. |
| **5 — L4 Profile Router + API + regression-lock** | `state_at(asset,tf,ts,profile)`, `profile_routes`, wire L1/L2/15M via API. | As 3 estratégias aprovadas **reproduzem métricas locked via API** (15M N435/+291,5R; L1 +45R) → desacoplamento provado por números idênticos. | Números divergem → acoplamento/bug, não promove. |
| **6 — EF Bridge + Skills + recorded_context** | ponte EF (modula confiança only), skills label-only, `rtse_service` passivo, snapshots. | Determinism boundary aplicado (validator rejeita número emitido por LLM); EF não muda estado determinístico; snapshots replayáveis por SHA. | LLM emite número / EF altera regime → viola boundary. |
| **7 — Phase live (SÓ com sign-off)** | daemon, shadow comparison, advisory live. | **Sign-off explícito do Cris** + N ciclos passivos batendo backtest (shadow). | Sem sign-off → fica recorded_context. Default-deny. |

## Skills/Agents (espírito External Factors — análise/validação, NÃO decisão de trade)
RTSE Plan · Source Map · Feature Provenance · **Lookahead Red-Team** (PASS/FAIL/SUSPECT/NEEDS_RAW_PROOF) · Label Auditor · Baseline · **Frontier** (curva latência×FP + Pareto vs baselines) · Profile Router · **External Bridge** (compara hipótese técnica vs USD/yields/Fed/COT/news; só ALIGNED/CONTRADICTS/NEUTRAL) · Production Safety. Cada um pequeno, label-only.

## Sequência de documentação (FEITA antes de qualquer código — esta etapa)
`RTSE_CANON_V0` ✅ · `RTSE_SOURCE_MAP_V0` ✅ · `RTSE_SCHEMA_V0` ✅ · `RTSE_VALIDATION_PROTOCOL_V0` ✅ · `RTSE_EXTERNAL_FACTORS_BRIDGE_V0` ✅ · `RTSE_PHASE_PLAN_V0` ✅ → **revisão do Cris → só então aprovar Fase 0.**

## Maior risco (não-técnico): virar oracle
A importância do módulo tenta puxá-lo a "resolver tudo" / explicar todo loser pós-fato. **Se virar oracle, morreu.** Trava no `RTSE_CANON_V0` §3. Função = leitura/padronização/velocidade/desduplicação/tolerância-por-estratégia. Não = achar fundo, provar entrada, substituir estratégia, bloquear tudo, oráculo.
