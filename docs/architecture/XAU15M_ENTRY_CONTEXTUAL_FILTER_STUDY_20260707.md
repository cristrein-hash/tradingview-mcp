# XAU 15M LONG — Estudo de Filtragem Contextual dos Losers (visual + bateria de features)

**Data:** 2026-07-07 · **Estado:** leitura visual VALIDADA pelo Cris; filtragem contextual = MURO (poisoning) com features atuais.

## 1. Leitura visual (22 prints, #1-#96) — VALIDADA pelo Cris
**WINNERS** = pullback-à-demanda dentro de perna de markup impulsiva JOVEM/MÉDIA (tendência com combustível, estende a 3R): #1R, #11-14, #28-30, #44-45, #71-75, #82R, #95-96. Assinatura: higher-low genuíno + BOS/CHoCH-up + VELA DE FUNDO + reclaim rápido (R) + perna ainda não esticada ao topo macro.

**LOSERS** = 3 modos macro-contextuais (= as 3 marcas de inválido do Cris):
1. **Exaustão de topo macro** (última puxada de perna esticada → range/reverte): #21,#23,#31,#55,#65,#83,#85,#46R → "POLARIDADE TOPO".
2. **Range/chop** (sem tendência p/ 3R): #56-60, #5-8R.
3. **Perna bear macro ativa** (comprar contra estrutura descendente): #66,#69,#93,#94,#89R → "FUNDO NÃO VALIDO POIS PERNA BEAR CLARA ANTECEDE"; #49,#50R → "FUNDOS NÃO VALIDOS DE PEQUENA ACUMULAÇÃO".

Nota: #64R,#77R,#80R,#87R,#89R,#93R são R (reclaim rápido) e MESMO ASSIM vermelhos → reclaim-R só qualifica dentro de markup jovem; em topo/range/bear falha. **markup/correção = MASTER; R = seletor dentro dele.**

## 2. Correção honesta dos proxies anteriores
O estudo de caso numérico anterior disse "exaustão não separa" e "bear-leg refutado" — ERRADO por medir na escala errada (leg_pos micro-15M; EMA diária lenta). A leitura visual macro prova que exaustão-de-topo e perna-bear SÃO os grandes viveiros de losers. Mesma miopia macro→micro.

## 3. Alinhamento ground-truth
Os 96 entries recomputados = as trades #1-#96 do Cris, **32/32 outcomes alinhados** (winners/losers conhecidos). Base sólida para reverse-engineering.

## 4. Bateria de features (deixar os dados escolherem) — resultado
12 features macro/estruturais causais, ranking por AUC (winner vs loser, N96 52W/44L):
- `slope_emaD` AUC 0,393 (mais forte): losers com slope 20d-EMA MUITO íngreme (+38 vs +14) = exaustão. **MAS filtrar slope>30 corta 23 losers matando 22 winners** (#13,#14,#44,#45,#71… markup forte tem slope íngreme) = ENVENENA.
- `supply_above` AUC 0,584 (0,619 dentro de R): winners com room à supply acima; losers encaixotados. Mecânico (3R precisa espaço).
- `demand_near`/`pos_in_20d`/`ret_20d`: ~0,5 = não separam. **Range-demand-no-fundo REFUTADO p/ 3R** (pos_in_20d 0-0,33 = 14% hit-3R; bounce de fundo de range só vai ~1R até o topo do range).

## 5. Filtragem = MURO de poisoning (achado central)
~~Melhor filtro = room: R & supply_above≥0,35 = 72% hit-3R N25.~~ **🚨 CORREÇÃO (2026-07-07, Cris perguntou "isso era lookahead também?"): SIM, PARCIALMENTE. `verify_supply_causal_20260707.py`: 92% das zonas SUPPLY têm last_t>born_t (estendem no tempo); o supply_above original filtrava por last_t>=entry−3d = usa toque FUTURO para decidir quais resistências contam. Sob causalidade ESTRITA (zona completada antes do entry): 72%→66,7% N9 (s_born N6 66,7%); 22/44 entries mudam de lado. O 72% era lookahead-contaminado; o resíduo causal = fraco, N minúsculo, in-sample.** Mesmo o filtro de room cortava ~9 winners para ~10 losers = ~1:1 poisoning. **NENHUMA feature corta losers sem matar winners na mesma proporção.** Winners e losers COEXISTEM no espaço de features — os winners de markup forte têm a MESMA assinatura macro (slope, supply, bear) que os losers, porque são os que ROMPERAM. A distinção visual do Cris ("esta perna tem momentum p/ romper?") não está nas features atuais. **Mesmo muro do PLT/DM: leitura visual > features disponíveis.**

## 6. Estado honesto / dial
- **Engine limpo:** markup master 54,2% → reclaim-R 61,4% (ambos anos+, Cris-validado). Não-envenenado.
- **Room = dial opcional de risco** (não filtro grátis): exigir room-à-supply sobe hit-3R (72%) trocando por menos winners; decisão do Cris sobre o trade-off. É a exaustão ex-ante defensável (não sabes ex-ante quem rompe).
- **Diferenciação fina** (bull-genuíno-em-bear, range-demand, exaustão-sem-poison) = precisa do read visual do Cris OU features que não temos (momentum de rutura da perna). Não mecanizável limpo com o set atual.

## 6b. Tentativa "vencer o muro como no PLT/DM" (mudança de representação) = LOOKAHEAD apanhado
Cris: "como venceste o PLT/DM? faz o mesmo." Lição PLT/DM = trocar snapshot-feature por PROCESSO sequencial (caminhada de pernas). Apliquei aqui: estado sequencial da escada + **subir a ESCALA do master walk**. Resultado espetacular e robusto por-ano: r=6 54% → r=8 61% → r=9 68% → r=10 76% → **r=12 80% (N30, 2025:88%/2026:71%)**. **MAS = LOOKAHEAD:** a caminhada só rotula um low como "demanda r=12" depois de a subida de 12-ATR o confirmar — e essa subida É o movimento vencedor. Selecionar demandas r=12 = selecionar winners por construção. **Teste causal (`causal_priorleg_test_20260707.py`): a perna ANTERIOR causal (momentum passado, conhecido ANTES do entry) NÃO separa — WIN med 12,59 vs LOSE med 12,77; filtrar dá ≤58%.** Portanto o ganho de escala era artefato de lookahead, apanhado.

**Natureza do muro (≠ PLT/DM):** PLT/DM era DETETAR estrutura que existe causalmente (venci mudando representação). Aqui a distinção winner/loser depende de a perna ROMPER no FUTURO — o "estado sequencial" que separaria é o próprio resultado, não está na estrutura pré-entry. **"Qual perna rompe" não é causalmente previsível pela estrutura anterior nestes dados.** reclaim-R (61%, causal, validado) = o que é causalmente conhecível.

## 6c. Motor multi-agente exaustivo (workflow wf_2cbffa42, 2026-07-07) — verificado
8 hipóteses causais estruturais (kit `agent_ctx_kit.py`, scoring anti-poison), cada uma auditada adversarialmente para lookahead + null + poison + por-ano. **7 FALHARAM causal-clean:** HTF-structure BOS/CHoCH (causal, null 0,041, poison ok, MAS 2026=47%<base = instável entre anos); RANGE-demanda causal (causal MAS null_p=0,128 winner-curse + 2026=50%<base); higher-high-seq (poison≥1); room-to-prior-high [substituto causal do supply que era lookahead] = REFUTADO sem separação; leg-maturity (57%, fraco); bull-in-bear-CHoCH (poison 0,89, +1,5pp negligível); RSI/EMA-regime (poison 0,97). **→ O router macro-contextual estrutural (a)+(b)+(c) desenhado pelo Cris é um MURO causal-clean: nenhuma feature que o implementa sobrevive.**

**1 SOBREVIVENTE (todos os 4 gates, confirmado por mim no kit):** `impulse_efficiency_prior_leg` = **Kaufman ER da PERNA ANTERIOR (causal, barras≤j, ER≥0,26)** — a perna que precede o pullback foi impulsiva/limpa (eficiência direcional) vs choppy. É a tese "momentum para romper" do Cris na forma CAUSAL (medida do passado, não do futuro). Métricas: **N52 · hit-3R 63,5% (+9,3pp) · poison 0,76 (corta 25 losers vs 19 winners) · 2025 63,6% / 2026 63,3% (estável) · null_p 0,038(perm)/0,042(rot) · lookahead-audit CLEAN (reproduzido byte-a-byte).** Corta 9 losers conhecidos (#21,#23,#55,#83 topo · #89,#93,#94 bear · #49,#50 falso-fundo) ao custo de 5 winners (#11,#29,#44,#45,#82). Plateau de threshold [0,24-0,26]. **CAVEATS HONESTOS (auditor+síntese): null_p 0,038 é MARGINAL e não-corrigido p/ multiplicidade cross-feature (~7 looks → sob Bonferroni cruza 0,1); separação subjacente modesta (ER mediana winners 0,289 vs losers 0,247, Δ~0,04); NÃO é o router estrutural desenhado, é um proxy de qualidade-de-impulso. VEREDITO = PROMISSOR-NÃO-VALIDADO; árbitro limpo = forward/dados virgens; NÃO promover como edge isolado.** Scripts `wf_cand_*/wf_verify_*/wf_synth_final.py`.

## 7. Artefatos
`entry_macro_context` / `entry_struct_state` / `feature_battery_20260707.py` + results/*.json (commit desta sessão). Bateria: `results/feature_battery_20260707.json` (96 × 12 features + outcome).
