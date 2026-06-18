# XAU 4H L2/BPT — Defended Swing Selection

**Status:** `RESEARCH · DIAGNOSTIC · GATE_NOT_PASSED · NOT_PROMOTED · NO_PRODUCTION · NO_SLIM` · **Data:** 2026-06-18
Tenta uma regra causal para escolher o low estrutural que a entrada defende (corrigir E13 raso e E1/E17 fundo). Exit FIXO partial50@2R+6R. Hard-stop em casos-chave. 7º DA. **Conclusão: não funcionou como regra; hard-stop honrado; nada promovido.**

---

## 1. Executive summary

**A ideia NÃO funcionou como regra causal.** Nenhuma regra única resolve os 4 casos-chave: **V1_HYBRID** (type-based) recupera E13 (+1.11) e corta E23 (NO_TRADE) mas **falha E17** (classificado NORMAL → pivô 8.4ATR); **V2_NEAREST_VALID** recupera E17 (+3.90) mas **falha E13** (−1.10, varrido) e não corta E23. As duas falhas são **opostas** (E17 quer SL tight, E13 quer SL fundo) e o classificador causal não as separa sem overfit. Pior: o filtro TOP_EXHAUSTION do V1 **corta 2/15 monumentais BOM** na base (falha recall), e o V2 é "**tight SL rebatizado**" (slATRmed 1.84≈baseline 1.97; sumR +80.1≈baseline tight +78.8 — o ganho é o efeito R-múltiplo do SL apertado, não inteligência de swing-defendido). **Per hard-stop (gate não passou): NÃO promovido.** O único efeito mecanicamente-real (não conceitual) é o nearest-valid-pivot **capar a distância do SL (>4ATR 97→6)** — mas isso é disciplina de pivô-tight já conhecida, falha os bad_SL (E13) e é choppy (maxDD 27). O separador real (distância-à-demanda E17 0.03 vs E13 8.89ATR) é **hipótese n=2 não resolvida**. Nada em produção.

## 2. Why defended swing selection matters

A heurística "pivô 5/5 mais recente" falha nos dois sentidos (E13 raso varrido; E1/E17 fundo = crash low comprime R). A alavanca seria escolher o low que a entrada *realmente defende* — não automaticamente o mais recente, nem o mais fundo, nem min-N, nem cap fixo.

## 3. Failure modes: E13 vs E1/E17 (opostos)

- **E13 (SHALLOW):** pivô recente 1548 (2.87ATR) varrido por wick (1546) antes do run; precisa de low **mais fundo** (~5.3ATR) para sobreviver. Entrada **longe da demanda** (8.89ATR).
- **E1/E17 (DEEP):** pivô = crash COVID (5.3/8.36ATR); a base defendida real é **tight** (~0.5-1ATR, post-capitulação); precisa de low **mais tight**. Entrada **na demanda** (E17 0.03ATR).
- **A oposição é o problema:** um quer tight, o outro quer fundo. Separá-los na entrada exige um sinal causal — candidato = distância-à-demanda — mas é **n=2** (2 pontos de sinal oposto = textbook overfit).

## 4. Structural types (tipologia causal)

`TOP_EXHAUSTION_NO_LONG` (legpos>85 & ext>4ATR) · `V_REVERSAL_RECLAIM` (capitulação >3ATR recente + reclaim) · `SHALLOW_PIVOT_SWEEP` (pivô recente <1.8ATR) · `NORMAL_BPT` (default) · `STRUCTURE_TOO_WIDE_REVIEW` (SL>4ATR sem base defendida). **Classificador frágil:** E17 caiu em NORMAL (capitulação COVID >40 bars atrás, fora da janela) — o que prova que não generaliza.

## 5. Candidate SL definitions (`results/l2_bpt_defended_swing_candidates.csv`)

recent_pivot (PL5 j≤i-5) · nearest_pl3 (PL3 j≤i-3) · retest_low (min 2b) · microbase_low (min 4b) · cap_base_low (menor low após capitulação em [i-40,i-5]) · min_10b/20b/30b. Todos causais. Campos: preço, dist_atr, in_band_0.5-4ATR, too_shallow/too_deep, demand_dist.

## 6. Policy definitions

V1_HYBRID (type→base) · V2_NEAREST_VALID (low válido mais próximo na banda 0.5-4ATR) · V3_DEEPER_IF_SWEEP · V4_REVIEW_ONLY (tag TOO_SHALLOW/DEEP/OK/NO_TRADE). Máx 4 regras, sem grid. **Nenhuma usa outcome** (mecanicamente causais) — mas o rótulo "defended" é retrofit (sabe-se qual low era defendido porque o outcome confirmou).

## 7. Key case results (`results/l2_bpt_defended_swing_key_cases.csv`)

| Caso | tipo | V1 | V2 | gate |
|---|---|---|---|---|
| E1 | V_REVERSAL | 4.2ATR +0.82 | 4.0ATR +0.88 | parcial |
| **E17** | NORMAL(!) | 8.4ATR +0.91 ❌ | 1.0ATR **+3.90** ✅ | V1 falha |
| **E13** | V_REVERSAL | 3.3ATR **+1.11** ✅ | 1.6ATR −1.10 ❌ | V2 falha |
| **E23** | TOP_EXH | **NO_TRADE** ✅ | 4.2ATR −1.10 ❌ | V2 falha |
| E5/E21/E27/E30/E40 | — | preservados + | preservados + (E40 V2 mutado) | ok |

**Hard-stop: nenhuma regra resolve E1+E17+E13+E23 juntos → NÃO aplicar à base como validação.**

## 8. Full-base results (DIAGNOSTIC — gate não passou, NÃO promovido)

| Política | n | no_trade | WR | avgR | sumR | PF | maxDD | streak | SL máx | >4ATR |
|---|---|---|---|---|---|---|---|---|---|---|
| V1_HYBRID | 224 | 52 | 50.4 | +0.325 | +72.7 | **1.67** | **14.5** | 9 | 15.04 | 45 |
| V2_NEAREST_VALID | 276 | 0 | 43.5 | +0.29 | **+80.1** | 1.48 | 27.0 | 9 | **5.3** | **6** |
| *ref* STRUCT_PURE | 276 | 0 | 48.2 | +0.226 | +62.5 | 1.44 | 24.3 | 9 | 15.04 | 97 |
| *ref* baseline tight | 276 | 0 | 42.8 | +0.286 | +78.8 | 1.46 | 30.4 | 12 | 5.3 | 9 |

**Leitura (DA):** V2 ≈ baseline tight (slATRmed 1.84≈1.97, sumR +80≈+78.8) = tight-SL rebatizado, sem edge de swing-defendido. V1 melhor maxDD/PF mas corta 52 e mantém 45 >4ATR.

## 9. Recall-gate

Must_preserve (8) nos casos-chave: V1 preserva E1/E5/E13/E21/E27/E30/E40 (E17 mutado), V2 preserva E17/E1/E5/E21/E27/E30 (E13 perdido, E40 mutado). **Na base completa, o filtro TOP_EXHAUSTION do V1 corta 2/15 monumentais BOM** (+50 UNKNOWN) — **falha recall**, o filtro não é limpo. should-cut E23 ✅ (V1). E15/E24/E34: não auditados individualmente, mas legpos>85 sweep cortaria parte (e os 2 BOM cortados mostram que over-corta).

## 10. Operational risk

V2 resolve o >4ATR (97→6, máx 15→5.3ATR) — mas é o perfil tight-SL (maxDD 27, choppy, falha bad_SL E13). V1 mantém 45 >4ATR (máx 15) — não resolve operacional. **Nenhuma regra entrega "SL operável + preserva cauda + recall limpo" simultaneamente.**

## 11. DA appendix

7º DA. Verdict (síntese): "**Defended swing selection é calibração n=9 disfarçada de regra.** V2 = tight-SL rebatizado (sem edge conceitual). V1 = classificador frágil (E17 falha) e threshold-tunado; TOP_EXHAUSTION corta 2/15 BOM. O separador E17-vs-E13 (distância-à-demanda) é hipótese n=2, não finding. Honrar o hard-stop: não promover." Checklist: **causal?** sim (pivôs j≤i-5, cap_base [i-40,i-5]); **outcome p/ escolher swing?** não mecanicamente, mas rótulo "defended" é retrofit; **E1/E17 n=2 overfit?** sim, o separador é; **E13 caso pontual?** sim (n=1); **E23 cortado por regra real ou label?** regra (legpos>85&ext>4) MAS over-corta 2 BOM; **melhora a base ou só os 9?** V2 melhora agregado mas = tight-SL conhecido; **SL operável?** só V2, ao custo de falhar E13; **futuro?** não; **exit alterado?** não; **produção?** intacta; **SLIM?** não.

## 12. Recommendation (research-only)

**Não promover nenhuma regra de defended-swing (hard-stop honrado).** A ideia é correta em princípio mas **não é operacionalizável por regra causal simples** — as falhas são opostas (tight vs fundo) e o classificador over-corta monumentais. Opções honestas:
1. **Tratar a seleção de swing defendido como julgamento discricionário/REVIEW humano** (olhar o chart por trade) — não automação; conecta ao tema de flags/review humano já registrado.
2. **Aceitar o operating point atual:** SL estrutural com o trade-off conhecido (STRUCT_PURE) OU tight-SL (V2/baseline) — escolha por objetivo, sem fingir que "defended swing" adiciona inteligência.
3. **O separador distância-à-demanda** fica como **lead não-validado (n=2)** para teste futuro com amostra independente, NUNCA como regra agora.
4. Meta-conclusão (4 blocos): SL/exit/cap/defended-swing **não são a alavanca**. A próxima frente real é **entrada/exhaustion** — mas com a ressalva de que mesmo lá o DA tem sido cético; validar com amostra, não com os 9 casos.

---

*Outputs: `results/l2_bpt_defended_swing_{key_cases,candidates,policy_results,recall_gate}.csv`. Script: `l2_bpt_defended_swing.py`. Sem produção, sem SLIM, sem chart, exit inalterado, nada promovido.*
