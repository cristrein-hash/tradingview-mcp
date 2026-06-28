# ENGINE 3 — Qualificação multi-TF de fundos MON+FORTE (PLANO + auto-auditoria)
*2026-06-28. Objetivo: capturar TODOS MONSTER + TODOS FORTE com MÍNIMO de trades. Qualidade, não quantidade. Sem largura de features que maquia preguiça. Executar com seriedade; sem trazer resultado/opinião prematuros.*

## A. AUTO-AUDITORIA do Engine 2 (por que foi raso e errado)
- **6,4× over-fire:** 369 trades p/ 58 fundos MON+FORTE (27 capturados, 37 MED/FRACO, **305 NONE**). Largura, não leitura.
- **Alvo errado:** otimizou PRECISÃO-DE-LABEL num universo agulha-no-palheiro (1,3%), via busca greedy de **3 features** → superficial por construção.
- **Ignorou conhecimento do Eng1:** o fingerprint (atr_regime baixo, rsi_min8 alto, pullback raso) e o eixo macro NÃO entraram como QUALIFICAÇÃO. Resultado: 18% da seleção = faca-caindo; das 332 facas do universo, 60 MED/FRACO vs 14 MON+FORTE (facas são majoritariamente lixo) e o engine não as gateou.
- **Sem multi-TF de verdade:** só resample 15M. Faltou OB/NAS/RSI/SVP NATIVOS de 4H/1D, transição de regime, confluência cruzada de indicadores.
- **Lição:** seleção-de-entrada por maximização-de-label sobre fluxo ruidoso = preguiça. O caminho é **QUALIFICAÇÃO-PRIMEIRO multi-TF convergente** que estreita o universo a poucos candidatos de alta qualidade.

## B. Objetivo (nítido, mensurável)
- **Recall máximo de MONSTER (20) + FORTE (39)** = os 59 alvos. Meta: capturar ~todos.
- **Mínimo de trades totais** (alvo: dezenas, não centenas). Excesso = falha.
- **~Zero faca-caindo** e mínimo MED/FRACO/NONE. Falling-knife é o 1º a eliminar.
- Métrica: `recall_monforte` + `n_total` (penaliza excesso) + `knife_rate≈0` + contaminação. NÃO precisão-de-label solta.

## C. Proveniência (RAW nativo disponível — usar)
- 4H nativo: `XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz` (OB/NAS/SMC/RSI/bubbles/SVP por barra) + `XAUUSD_240m_replay_2023-01-03_to_2026-05-25`.
- 1D nativo: `XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz`.
- Cobrem a janela 15M (2024-05→2026-05). Extrair primitivas causais 4H/1D (como build_causal_primitives, SHIFT1/as-of).

## D. NOVO mapa de features (confluência multi-TF cruzada — lentes novas)
Reusar features já achadas (Eng1 fingerprint + Eng2 reação) **em contexto**, e ADICIONAR:
1. **HTF OB-confluence (NOVA):** o fundo 15M cai DENTRO de zona DEMAND nativa do 4H E/OU 1D (Custom OB), born antes, virgem/fresca, largura/idade. = "fundo validado por demanda de TF maior" (o que Cris pediu).
2. **Regime-transition onset (NOVA):** detecção de INÍCIO de virada/transição via 4H+1D — sequência de CHoCH/BOS bullish no 4H após perna de baixa; cruzamento estrutura 1D; saída de BEAR→TRANSITION. Não só "macro=BULL" (snapshot) e sim "virada começando".
3. **Macro leg-state 4H/1D (NOVA):** MACRO_BULL_LEG / CORRECTIVE_PULLBACK / BEAR_LEG / TRANSITION (fractais 1D HH/HL) — fundo em pullback-corretivo de leg de alta = forte; em bear-leg sem exaustão = faca.
4. **Indicator confluence cruzada (NOVA):** contagem de confluência num só score-vetor (NÃO soma cega): NAS-LONG(15M+4H) + bubble SELL-absorvida no fundo + RSI(15M+4H+1D) não-exausto + Volume climax-com-reclaim + OB demand(15M+4H+1D). Confluência ≥k de vozes ORTOGONAIS.
5. **Falling-knife detector explícito (NOVA, gate):** bear-leg 1D/4H + sobrevendido profundo + perna acelerando + sem demanda HTF + oferta acima + abaixo do valor = FACA → excluir primeiro.
6. **Reusar (contexto):** Eng1 (legpos/h1_pos/rsi_min8/atr_regime/atr_compression/dist_demand) + Eng2 reação (reclaim/pullback_depth/sweep/micro_hl) — como qualificadores, não como buscador greedy.

## E. Lógica do engine (QUALIFICAÇÃO-PRIMEIRO, managed agents sério)
- **Fase 0:** extrair primitivas nativas 4H + 1D (causal) p/ a janela.
- **Fase 1 (GATE anti-faca + qualificação macro):** remover faca-caindo e não-qualificados via confluência multi-TF (regime-onset + HTF-demand + não-exausto). Estreita o universo de 4502 → poucas centenas qualificadas, preservando recall MON+FORTE.
- **Fase 2 (especialistas managed-agents, 1 por lente/TF):** cada um lê os candidatos qualificados e devolve voz/score ortogonal (HTF-OB, regime-onset, indicator-confluence, reação, fingerprint).
- **Fase 3 (assembler de confluência):** combina vozes em leitura convergente; seleção TIGHT por confluência-≥k que maximiza recall MON+FORTE com n mínimo (frontier recall×n).
- **Fase 4 (DA adversarial):** null/permutation, per-ano, leave-block, look-ahead, e o teste-chave: a seleção tight é R-positiva E enxuta? captura os 59?
- **Fase 5:** síntese (dados, sem opinião) + plot canônico p/ revisão visual.

## F. Travas
RAW-causal as-of (SHIFT1 repintáveis; 4H/1D só barras fechadas t_end≤tc; born_t/known_at≤tc). Sem OOS (cânon). Tier = label forward (nunca feature). Reuso de features anteriores como evidência condicional. Auto-auditar cada scoring de unidade. Sem trazer resultado/opinião até validado.
