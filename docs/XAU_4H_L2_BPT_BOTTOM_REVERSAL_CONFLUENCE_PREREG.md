# XAU 4H L2/BPT — Bottom/Reversal Confluence entry: PRÉ-REGISTRO

**Status:** `PRE-REGISTERED · NOT_STARTED · AWAITING_APPROVAL` · **Data:** 2026-06-18
Reconstruir a ENTRADA do L2/BPT como **reversão-de-fundo-com-confluência** (o edge comum a Caminho B / Capitulation / V1.4g), usando **BOS/CHoCH só como confirmação secundária**. Pré-registrado ANTES de medir. Sem plotagem. Foundation: [[XAU_4H_L2_BPT_ENTRY_DEEP_REFLECTION]].

---

## 0. Fixo (não mexer neste bloco)
- **SL = demand-anchored** (causal, repaint-auditado). **Exit = partial50@2R+6R.**
- **BOS/CHoCH = confirmação secundária**, NÃO o gatilho. Não refinar BOS.
- Classificação por **TIPO DE SAÍDA** (target/partial/runner/stop/time), nunca R-sign.

## 1. REGRA DURA (a que evita o erro anterior)
> **Baseline = RANDOM LONG NO MESMO ESTADO de capitulação/convergência** — NÃO random-geral nem só legpos-matched.
Comparar contra drift geral fabrica falso edge. A pergunta certa é dupla:
- **Teste A (o estado tem edge?):** long-no-estado-de-convergência vs legpos-random-geral. (Esperado SIM, por Caminho B/Capitulation.)
- **Teste B (o reclaim BOS adiciona sobre o estado?):** L2/BPT-reclaim-no-estado vs **random-long-no-mesmo-estado**. (Se ~zero ⇒ edge é o ESTADO, BOS é incidental — também é resultado válido e coerente com a tese.)
Bootstrap + Bonferroni. Delta dentro do ruído = rejeitado.

## 2. Definição de ESTADO de convergência (causal, a auditar em RAW — Parte 0)
Importado do Bottom Catcher (Caminho B) que comprovadamente funciona. Estado = ≥K dos sinais causais (≤ entry):
- **Capitulação:** `drop_20_atr ≥ 4` (queda recente em ATR).
- **Oversold:** `rsi_min em N barras ≤ 30`.
- **Absorção SELL (auction):** `≥2 bubble_SELL em 8 barras` (mapping BUY=plot0/2/4, SELL=plot6/8/10 — auditar causal).
- **Demand-backed:** `dist_4h_demand_low_atr ≤ θ` (a demanda que ancora o SL).
- **NAS LONG** recente (bottom signal, confluência não gate isolado).
- **legpos baixo/médio** (não alto-na-perna).
RAW audit obrigatório de cada campo (causalidade, mapping, cobertura). Hard stop se não-causal/ausente/retratado.

## 3. As 3 hipóteses (ordem fixa do Cris)

### H-CONV (PRIMEIRO)
O reclaim L2/BPT só vale se coincide com o ESTADO de convergência de fundo. Subset = reclaims-em-estado. **Teste B (vs random-long-no-mesmo-estado)** + Teste A (estado vs legpos-random). Hipótese: o estado carrega o edge (igual Caminho B); o reclaim é confirmação.

### H-RETRACE (DEPOIS)
BOS/CHoCH = VALIDAÇÃO de que a estrutura virou; a entrada de VALOR é o **RETRACE à zona de demanda** após o BOS, não o bar do reclaim (lição Breakout D1a). Definição causal: após BOS confirmado, entrar quando o preço retesta a demanda (sem look-ahead). Comparar vs entrar-no-reclaim e vs random-no-estado.

### H-NODIV (POR ÚLTIMO, filtro de topo)
Importar o **A7 do V1.4g**: rejeitar se `≥2 RSI-bear-div em 20 barras` (mons têm ZERO; cortou só losers-topo no V1.4g). Camada de remoção de blow-off/topo complementar ao F_STRICT. Medir o lift da remoção sobre o subset H-CONV/H-RETRACE.

## 4. Metodologia (obrigatória)
- Baseline state-matched (Teste B é o gate primário; Teste A é o foundation).
- SL demand-anchored + partial50 fixos · classificação por tipo de saída · recall-gate (must-preserve 8) · bootstrap 5000 (delta CI 5/50/95, P) · **Bonferroni** sobre as hipóteses da rodada · split temporal 2020-22/2023-26 · RAW audit (Parte 0) · **sem look-ahead** (toda feature ≤ entry; H-RETRACE com def causal) · **sem plotagem** · sem SLIM/retratado.

## 5. Não fazer
Não refinar BOS · não baseline-drift-geral (só state-matched) · não declarar edge sem bater random-no-estado + bootstrap + Bonferroni · não mexer SL/exit · não look-ahead · não plotar · não produção · não promover.

## 6. Outputs previstos (quando autorizado)
`results/l2_bpt_botrev_{raw_audit,state_def,Hconv,Hretrace,Hnodiv,bootstrap}.csv` + doc `XAU_4H_L2_BPT_BOTTOM_REVERSAL_CONFLUENCE_RESEARCH.md` + DA obrigatório.

---

*Pré-registro. NÃO medir/plotar sem autorização explícita. Importa o edge comprovado (reversão+convergência) de [[project_xau_4h_caminho_b_long]] · [[project_xau_4h_reversal_capitulation_long]] · [[project_xau_4h_reversal_v1_4g_rws_a6_a7]] para a entrada do L2/BPT.*
