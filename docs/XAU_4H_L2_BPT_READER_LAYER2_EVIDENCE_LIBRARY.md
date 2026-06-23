# XAU 4H L2/BPT — Camada 2: Biblioteca de Evidências do Reader

> **Inventário amplo da Camada 2 do sistema de leitura viva/contrastiva.**
> Bloco fechado, **read-only** — sem produção, sem Telegram, sem OOS, sem plotagem, sem backtest novo, sem gate, sem score.
> Data: 2026-06-23. Escopo: corpus inteiro de `docs/`, `v1/` scripts, `v1/results/`, memória local do projeto.
> Inventário machine-readable: `v1/results/l2_bpt_reader_layer2_evidence_inventory.csv` (94 lentes).
> Índice de fontes: `v1/results/l2_bpt_reader_layer2_source_index.csv`.

---

## ⚠️ GUARDRAIL — A Camada 2 NÃO deve engessar o Reader

O objetivo deste inventário **não** é transformar a leitura em checklist, score ou fórmula.
O objetivo é dar ao Reader **memória operacional rica para pensar melhor**.

Cada item resgatado deve ser tratado como:
- **lente interpretativa;**
- **precedente histórico;**
- **hipótese contextual;**
- **alerta de erro passado;**
- **evidência condicional.**

Nunca como:
- gate isolado; regra determinística; voto automático; score; substituto da leitura do episódio.

**A biblioteca de evidências NÃO decide. Ela aumenta a profundidade da leitura.**
**O Reader não obedece às evidências; ele dialoga com elas.**

Divisão de papéis (lockada):
- O **DOSSIÊ** organiza o contexto.
- O **READER** interpreta livremente o episódio.
- O **CHALLENGER** testa coerência.
- O **MEDIDOR** só registra e compara *depois*.

A leitura correta responde: (1) que episódio está em andamento? (2) qual o papel deste trade nele? (3) que fatores mudam de significado pelo contexto? (4) que precedentes/sósias ajudam? (5) é continuação, fundo legítimo, trap, rejeição, absorção, markup ou conflito? (6) o que faria a leitura estar errada?

> **Teste de sucesso do inventário:** se ele tornar a leitura mais **rígida**, falhou. Se tornar mais **profunda**, funcionou.
> Se a conclusão puder ser reduzida a uma soma de fatores, a leitura foi mal executada.

---

## DA / Checklist de conformidade do bloco

| Verificação | Status |
|---|---|
| Read-only (nenhum arquivo de produção/pipeline tocado) | ✅ PASS — só criados 3 artefatos novos (este doc + 2 CSVs) |
| Sem produção / receiver / cloudflared / Telegram / chart / MCP | ✅ PASS — nada operacional acionado |
| Sem backtest novo | ✅ PASS — só extração de conclusões já existentes |
| Sem gate | ✅ PASS — nenhuma regra TAKE/SKIP criada |
| Sem score | ✅ PASS — nenhuma pontuação atribuída |
| Sem lift-test novo | ✅ PASS — lifts citados são históricos, das fontes |
| Sem descarte indevido | ✅ PASS — falhas isoladas preservadas como WARNING/CONTEXT, não deletadas |
| Evidências como lentes, não regras | ✅ PASS — cada item catalogado por *como ajuda o Reader a pensar* |
| Conclusões antigas não refeitas | ✅ PASS — extração fiel das fontes; status herdado da memória/docs |

Método: 9 leituras paralelas read-only (uma por família de evidência) **realmente spawnadas via Agent tool**, extraindo conclusões já documentadas; síntese consolidada num único lugar para **não fragmentar**.

---

## Como ler o campo STATUS

| Status | Significado para o Reader |
|---|---|
| **CORE_CONTEXT** | Backbone/contexto que ancora a leitura. Sempre presente no dossiê; condiciona o sentido de tudo. |
| **CONDITIONAL_EVIDENCE** | Vale só sob contexto específico; lean/hipótese, nunca isolada. |
| **CONTRAST_LENS** | Motor de contraste — serve para discriminar ENTRE casos, não dentro de um. |
| **POLARITY_DEPENDS_ON_CONTEXT** | O MESMO sinal inverte de sentido conforme o contexto (topo vs fundo, bull vs bear). |
| **REQUIRES_CASE_READING** | Não há separador limpo; exige leitura caso-a-caso no chart. |
| **WARNING_FAILURE_MODE** | Precedente de erro. Mantido como alerta do que NÃO fazer. |
| **DO_NOT_USE_AS_GATE** | Rico como contexto, fatal como gate automático. |
| **DEAD_AS_AUTHORITY_BUT_KEEP_AS_CONTEXT** | Não reproduz como feature/autoridade, mas o vocabulário/contexto ajuda. |

Objetivos de leitura referenciados (`helps`): recuperar-skip-winners · cortar-take-losers · preservar-monumentais · bear-buy-legítimo-vs-trap · markup-through-supply-vs-supply-rejection · continuação-estrutural · reversão/fundo/capitulação · topo/range/chop.

---

# Camada 1 (eixo condicionante) — relembrada como porta de entrada da Camada 2

A Camada 2 só faz sentido **condicionada** pela Camada 1: `weekly_slope + cascade + dealing-range` + o **D1 leg-state backbone** mudam o significado de cada lente abaixo. O mesmo `dist_supply`, a mesma bubble, o mesmo legpos **invertem de polaridade** conforme a leg macro. Por isso muitas lentes carregam `POLARITY_DEPENDS_ON_CONTEXT`. Ler Camada 2 sem fixar a Camada 1 primeiro = repetir o confound de escala (4H lê pullback local como bear-leg macro).

---

# Família A — MACRO STRUCTURAL READING ENGINE (22 lentes)

Veredito integrado da família: o lado **PRESERVAÇÃO-BULL** está resolvido por `D1 backbone + confluência 9-specialists + leitura-de-conjunto` (anchor 13/14). O lado **SELEÇÃO/RISCO** (separar late-top-em-bull de pullback-em-bull no ponto de entrada) é **auction-irredutível** e tratado como input HUMANO discricionário, não gate automatizável.

### A1 · D1/weekly leg-state backbone — `CORE_CONTEXT`
- **Fonte:** `leg_state_d1_backbone.py` (e54d87e).
- **Viu:** resolveu o confound de escala (A-set 11 BULL/9 RANGE/1 BEAR); melhor preservação de bull-run de toda a jornada (anchor 13/14, A 20/26).
- **Falhou isolado:** lado RISK fraco (B 3/18); 11 late-tops-em-bull classificados BULL (irredutível); regime D1 às vezes atrasado.
- **DEVE:** espinha dorsal que ancora TODAS as lentes ("em que leg estou"); preserva bull, isola macro-bear-markdown.
- **NÃO:** nunca gate duro de SKIP; nunca deixar regimeB lagging sobrepor uma bull-leg confirmada.
- **Ajuda:** preservar-monumentais · bear-buy-vs-trap · continuação · topo/range/chop.

### A2 · 9 macro specialists (confluência → 12 estados) — `CORE_CONTEXT`
- **Fonte:** `macro_structural_specialists.py` (d0e5566); 558 evidências auditáveis.
- **Viu:** confluência multi-aspecto preserva bull melhor que feature única (anchor 12/14); contexto vive na confluência, não na fatia.
- **Falhou isolado:** no full-276 ENGINE_TAKE WR 24.8% ≈ base 23.6% (null p=0.374); nenhum specialist carrega separação.
- **DEVE:** núcleo de convergência interpretável (factor+value+reason-codes); a leitura BULL emerge da concordância.
- **NÃO:** votação somada/score; gate; esperar que separe winner/loser sozinho.

### A3 · Supply `sup_cat`/`pol_cat` (gestalt categórico) — `POLARITY_DEPENDS_ON_CONTEXT`
- **Fonte:** `demand_supply_quality.py` / censo (9574c22). CLEAN_SKY / SUPPLY_NEAR_BUT_BROKEN(=markup) / SUPPLY_NEAR_AND_REJECTING(=colada).
- **Viu:** já codifica a gestalt que `dist_supply` cru tentou reinventar; distingue no-overhead-bullish de supply-colada-bearish.
- **Falhou isolado:** lift ~0 no 276 (ID-fit nos 62); polaridade depende do regime — near-supply em bull = markup BOM.
- **DEVE:** input de 1ª classe da lente Supply, SEMPRE condicionado à leg (bull→markup; bear→risco).
- **NÃO:** context-free; near-supply como veto; clean-sky como predicado promovível.

### A4 · Volumetry / SVP acceptance (Session VP nativo) — `CONDITIONAL_EVIDENCE`
- **Fonte:** `svp_causality_verification.csv` (7f3c852). Provado as-of-bar causal (sem shift), volume REAL.
- **Falhou isolado:** VP de início de sessão é fino (maturidade baixa); tick-volume da mesma fonte fabricou artefatos (volume×1D-bear RETRATADO).
- **DEVE:** lente de aceitação-acima-de-valor vs distribuição, ponderando maturidade; **sempre Session VP nativo**.
- **NÃO:** tick-volume; tratar maturidade-baixa como look-ahead.

### A5 · Multi-TF alignment (4H+1D+semanal) — `CONDITIONAL_EVIDENCE`
- **Viu:** semanal era riqueza ignorada; distingue bull-run maior de bounce local.
- **Falhou isolado:** weekly-RSI-OB usado errado no late-top v2 (matou S20/S29-S32/S38).
- **NÃO:** weekly-RSI-overbought como sinal isolado de late-top (overbought é natural em bull-run).

### A6 · Macro regime `regime_B_v3` (escalar) — `DO_NOT_USE_AS_GATE`
- **Fonte:** `full276_macro_engine.py` (ab62b1d). Vocabulário rico (cascade/distribution/stall...).
- **Falhou isolado:** MIS-MEDE — over-fire `macro_broken AND combined<0` DENTRO de bull-leg bloqueou 18 winners +27.3R; cego ao bear-junk que pontua bull (T40).
- **DEVE:** evidência condicional de comportamento (não pelo nome), SUBORDINADA ao leg-backbone.
- **NÃO:** deixar regimeB sobrepor a leg D1 (inverte a hierarquia "leg=backbone").

### A7 · Momentum / Exhaustion × legpos — `REQUIRES_CASE_READING`
- **Falhou isolado:** late-top tem momentum STRONG_BULL ANTES de virar; legpos-alto isolado penaliza bull-run.
- **DEVE:** hipótese de exaustão APENAS condicionada a leg+regime; high-legpos saudável é o default em bull-run.

### A8 · Capitulation / Climax (capit+rsi, bubbles_sell) — `REQUIRES_CASE_READING` (CONTEXT_ONLY)
- **Viu:** exemplar-mãe de "fraqueza isolada ≠ inútil"; resgata V-reversals.
- **Falhou isolado:** refutada em OOS bear (regime-bound); bubbles têm polaridade contexto-dependente.
- **DEVE:** input APENAS no regime de fundo/turn; polaridade da bubble sempre context-aware.

### A9 · Fuel / Convexity (room-to-supply / CLEAN_SKY) — `CONTRAST_LENS`
- **Viu:** eixo Auction novo "clean-sky-vácuo vs rompeu-supply-testada".
- **Falhou isolado:** clean-sky falha como eixo (4 B-preservados são 4/4 clean-sky); permutation p=0.167 (hull).
- **DEVE:** flag de confluência, nunca filtro.

### A10 · Risk / Structural-SL specialist (T34) — `CONDITIONAL_EVIDENCE`
- **Viu:** isola "skip-que-deveria-ser-winner por gestão" (12 won + 3 stopped com boa entrada/SL curto); eixo ORTOGONAL.
- **Falhou isolado:** no full-276 dropar o risk-axis AUMENTA big winners 35→42 (corta winners se usado como gate).
- **DEVE:** eixo separado de gestão/exit; rotear entrada-boa-stopada para risk-review, não para SKIP.

### A11 · Leitura-de-conjunto condicional (D1-backbone) — `CORE_CONTEXT`
- **Viu:** melhor preservação (13/14); prova ao mais alto nível de que late-top-em-bull ≡ pullback-em-bull no ponto de entrada (auction-irreducibility).
- **Falhou isolado:** B-RISK 3/18; "leitor não separa" ≠ prova de irredutibilidade (só T32 genuíno; T17/T20 feature-missing).
- **NÃO:** tratar "não separou" como irredutibilidade; overfittar contra o disfarce de liquidez.

### A12 · Visual-anchored regime (13 estados) — `DEAD_AS_AUTHORITY_BUT_KEEP_AS_CONTEXT`
- **Viu:** conserta o gargalo nos 3 eixos (concordância 6→16/18, big winners TAKE 8→27, runners 1→5/5).
- **Falhou isolado:** NÃO reproduzível por features causais em 20/62 (32%) = calibração HUMANA; concordância parcialmente tautológica; timeline carrega hindsight.
- **DEVE:** input HUMANO discricionário de regime, sobre o qual o engine faz auction/risco/exit.

### A13 · Entry-quality specialist (localização) — `WARNING_FAILURE_MODE`
- **Falhou:** REFUTADA — features quase idênticas A vs B; bad-entries estruturalmente idênticos aos good (ambos pullback-a-demanda-defendida-perto-de-valor).
- **Lição:** o separador NÃO é onde se entra, mas em QUE leg.

### A14 · `macro_phase` D1 (BULL_RUN/PULLBACK/RANGE/BEAR) — `CONDITIONAL_EVIDENCE`
- **Falhou isolado:** DATE-PROXY do melt-up 2023-25 (WR 43.5% no bull 2020 real); thresholds in-sample; feature lagging marca BULL_RUN NO topo.
- **NÃO:** policy TAKE=BULL_RUN; confundir beta-2023-25 com edge.

### A15 · Indicator confluence cross × engine — `WARNING_FAILURE_MODE`
- **Falhou:** v1 bug de polaridade; v2 nenhum bucket TAKE separa (p=0.332); polaridade DERIVADA do engine = camada REDUNDANTE.
- **Lição:** indicadores precisam ser ORTOGONAIS ao engine para somar.

### A16 · Bear-Leg Block v3 — `CONDITIONAL_EVIDENCE`
- **Viu:** drop20_atr robusto [0.5,1.5]; captura 13/16 runners.
- **Falhou isolado:** no full-276 bear-markdown é O CUSTO (over-fire em bull-leg, bloqueia 12-18 winners).
- **DEVE:** FLAG de review humano; bear-markdown só FORA de bull-leg.

### A17 · Microstructure liquidity (micro-top/sweep) — `WARNING_FAILURE_MODE`
- **Falhou:** o filtro INVERTERIA (marca 5 winners como BAD, lê os bad como GOOD); OHLC contíguo indisponível.
- **Lição:** perseguir detector micro-top é overfit; aceitar resíduo T17/T24/T32.

### A18 · Confluence v2 (override + late-top) — `DO_NOT_USE_AS_GATE`
- **Viu:** revelou que o gap NÃO é macro, é entrada-ruim-dentro-de-bull-correto (10/13 falsos-BULL sem macro_broken).
- **Falhou:** PIOROU (12/14→6/14); late-top-via-legpos matou S20/S29-S32/S38.

### A19 · Feature census (122 features) — `CONDITIONAL_EVIDENCE`
- **Viu:** 63 não-testadas; identificou sup_cat/pol_cat como achado central; classificou MORTAS/FORBIDDEN.
- **DEVE:** roster que estrutura a busca; fonte de proveniência/causalidade por feature. **NÃO:** fit cego de 122.

### A20 · SMC BOS/CHoCH + pivots (causalidade verificada) — `CONDITIONAL_EVIDENCE`
- **Viu:** verificados causais (smc por appearance-time; pivots lookforward capado).
- **Falhou isolado:** SMC esparso ~41%; SHIFT1 obrigatório.

### A21 · Deep Target-7 + permutation guard — `WARNING_FAILURE_MODE`
- **Viu:** estabeleceu PERMUTAÇÃO como guarda canônica anti-ID-fit.
- **Falhou:** cluster tightness 1.03 (pior que aleatório); zero features separam os 7; comunalidade = near-macro-top (irredutível).

### A22 · 4H fractal leg-state — `WARNING_FAILURE_MODE`
- **Falhou:** confound de escala (12/14 A-winners marcados RISK são MACRO-BULL no D1). Macro-leg vive no D1/weekly, não em fractais 4H. Útil só para sweep LOCAL.

---

# Família B — DSPA · Dynamic Structural Path Aggregator (11 lentes)

Engine de 2ª ordem que lê a **trajetória** que produziu o estado (não snapshot). O **par-núcleo** `demand_defended + acceptance` carrega o sinal; o eixo isolado mais forte é **SVP-acceptance-above-value (F6)**.

### B1 · SVP acceptance-above-value (F6) — `CONDITIONAL_EVIDENCE` ⭐ lead mais forte
- **Viu:** UNGATED n=132 **lift 1.28 p=0.0064**, captura **18/30 monumentais**, P1 28%/P2 38% estável; sinal INDEPENDENTE (svp sem plain-accept lift 1.31 p=0.047); vive FORA do bear (lift 1.41 p=0.028).
- **Falhou isolado:** foi over-gateado atrás de `bear` na regra A4 e colapsou (lift 0.99); ainda falha multiple-testing honesto (alpha 0.00089) e Bonferroni-18.
- **DEVE:** eixo primário UNGATED de aceitação-de-valor; modular com structure (svp_acc & st_up). **NÃO:** gatear atrás de bear-context (mata o eixo); colapsar com plain-acceptance.

### B2 · Multi-bar acceptance (F3) — `CORE_CONTEXT`
- **Viu:** `acceptance_above` é 92% dos LBB; junto com demand_defended carrega o sinal inteiro.
- **Falhou isolado:** plain-accept SEM svp = RUÍDO (lift 0.78). **NÃO:** colapsar plain-accept com SVP-accept.

### B3 · Swing structure (F4) — `CONDITIONAL_EVIDENCE`
- **Viu:** `svp_acc & st_up` n=41 lift 1.50 p=0.035 — structure_up adiciona ao eixo svp. Modulador, não gate.

### B4 · regime_B trajectory (F7) — `CORE_CONTEXT`
- **DEVE:** condicionador lento que muda o SIGNIFICADO das evidências (bear_ctx/bull_ctx). **NÃO:** usar como gate (over-gatear svp atrás de bear foi o erro).

### B5 · LBB — Legitimate-Bear-Buy signal — `CONDITIONAL_EVIDENCE` ⭐ 1ª separação real do resíduo bear
- **Viu:** LBB n=37 38% runner lift 1.45, 6 monumentais vs BPT n=23 13% 0 monumentais; Fisher p≈0.045; SOBREVIVE P1/P2.
- **Falhou isolado:** o sinal É o PAR demand+accept em bear context (par p=0.135); convergência completa NÃO agrega; n=37 fino.
- **DEVE:** lean estrutural (demand-defendida aceitando em bear = preserve runner-risk); BPT é runner-poor (evitar).

### B6 · Liquidity sweep / reclaim (F1) — `CONDITIONAL_EVIDENCE`
- **Viu:** carrier interno do LBB (`swept_low_reclaimed`) = assinatura de reversão real.
- **Falhou isolado:** n=4 (drop-1 = ruído). Cor qualitativa em convergência, nunca isolada.

### B7 · Flush geometry V vs grind (F2) — `CONDITIONAL_EVIDENCE`
- **Viu:** FLUSH_V (capitulação) vs GRIND_DOWN (distributivo).
- **Falhou isolado:** carrier n=12; `f2_velocity` é CIRCULAR com FLUSH_V. **NÃO:** construir numéricos derivados (MT noise).

### B8 · Capitulation/Reversal lens (sub-leitor) — `CONTRAST_LENS`
- **Viu:** estados STRONG_BEAR_CONFIRM/CORRECTIVE_BEAR_LEG runner-lift 1.25-1.36 — os monstros vêm de reversão e os engines liam ao contrário.
- **DEVE:** lente que INVERTE a leitura ingênua (contexto bearish pode esconder runner).

### B9 · Dealing-range premium/discount (F5) — `DEAD_AS_AUTHORITY_BUT_KEEP_AS_CONTEXT`
- Localização (discount favorece buy, premium favorece risco-topo) só como contexto; nenhum teste isolado passou.

### B10 · Intermediate states (9 estados) — `DEAD_AS_AUTHORITY_BUT_KEEP_AS_CONTEXT`
- **Viu:** UNKNOWN_CONFLICT corretamente low-edge (lift 0.29 = sinal honesto de baixa-edge).
- **Falhou:** MARKUP_THROUGH_SUPPLY e SUPPLY_REJECTION_TRAP FRACOS; over-specified. Vocabulário de trajetória, não policy.

### B11 · Cross-confluence (18 regras / loser-cut) — `WARNING_FAILURE_MODE`
- **Viu:** A2/A5 leads sub-significativos; revelou o miss de svp_acc.
- **Falhou:** NENHUMA das 18 passa Bonferroni; **loser-cut = 0/86 cortáveis limpos** (ABSÊNCIA real). **NÃO:** construir regra de loser-cut (irredutível).

---

# Família C — BEAR-LEG (5 lentes)

### C1 · Bear-leg REFINED loser-cut — `CONDITIONAL_EVIDENCE` ✅ aprovado como loser-cut condicional
- **Escopo:** `macro_reader_leg == MACRO_BEAR_LEG` ONLY (n=29/276).
- **Viu:** dentro do bear-leg cortou 8/19 losers (100% `supply_reject + fuel_low`), preservou 5/5 runners + 2/2 monumentais. Edge na CONJUNÇÃO bear × supply-reject × low-fuel.
- **Falhou isolado:** fora do bear-leg = ruído (lift 1.01); preserve-5/5 parcialmente tautológica; 11 leaked irredutíveis.
- **NÃO:** gate global; fora do bear-leg; regra de produção sem walk-forward.

### C2 · Bear-state 1D — `CORE_CONTEXT`
- **Viu:** constrói leg 1D/weekly limpa; vê que E1/E17 são bottom-reclaims do COVID bear.
- **Falhou isolado:** máquina 1D não separa capitulation-bottom de weak-mid-bounce (bloqueia E1/E17 junto com traps); bottom-signal (NAS/bubble) aponta o lado errado.
- **DEVE:** backbone macro-leg que as outras lentes condicionam. **NÃO:** entry filter para o subset reversal-from-bottom.

### C3 · Leaked-vs-blocked residue — `REQUIRES_CASE_READING`
- **Achado:** os 11 leaked losers são estruturalmente IDÊNTICOS aos 5 runners no ponto de entrada — a diferença é OUTCOME. Porta sub-4H permanentemente fechada.
- **DEVE:** aceitar como understood-losers; ler caso-a-caso; gerir via SL estrutural + BE. **NÃO:** construir filtro separador.

### C4 · Retracted block gate (v1/v2/v3) — `WARNING_FAILURE_MODE`
- **Precedente de erro:** forte no curado-62 (que CONTINHA seus próprios target-winners = circular); no full-276 FALHOU (drop sumR 84.2→75.3, bloqueia 12 winners incl. 3 monumentais). **Lição:** gate calibrado E avaliado no set que o contém é circular; com SL estrutural não há regime para bloquear.

### C5 · Overbought-in-bear (exhaustion polarity) — `POLARITY_DEPENDS_ON_CONTEXT`
- Oversold+reclaim+demand@fundo = capitulation-buy; overbought+legpos>90@topo = extreme-top soft-veto (classe E24 = único filtro limpo concedido). Isolado mislabel (v2 preservou T17 errado).

---

# Família D — MICROSTRUTURA / LIQUIDEZ / SWING ANATOMY (12 lentes) · Camada 0

Helpers de **percepção da forma viva do preço**. Conclusão repetida: nenhum escalar único separa limpo; a separação é mecanismo-específica e parcialmente irredutível.

### D1 · V-flush vs grind (capitulation_base) — `CORE_CONTEXT`
- Seleciona a base de capitulação (swing defendido); reconhece V_REVERSAL_RECLAIM (E27/E30/E40). Não distingue V-bom de V-em-bear sozinho (precisa do 1D-trend).

### D2 · Defended swing — `CORE_CONTEXT`
- Seleciona o low estrutural por mecanismo; SL swing-origin recupera bad_SL 5→10/12. Não é onde mora a edge; cap ~4ATR.

### D3 · Flush shape (drop20/rise20) — `CONDITIONAL_EVIDENCE`
- drop20≥0.8 alimenta a assinatura FAILED_BREAKOUT (T20); magnitude isolada é compartilhada good/bad.

### D4 · Reclaim (body + dist) — `CONDITIONAL_EVIDENCE`
- reclaim<0 below-VAL = falha; reclaim>0 compartilhado por acceptance-good E trap-bad. Combinar com va_state.

### D5 · Acceptance / rejection (va_state) — `CONTRAST_LENS`
- below-VAL+reclaim<0 = flag de rejeição; ABOVE_VAH+reclaim>0 precede tanto good quanto trap (T17). Não usar acceptance como gate de qualidade (inverte).

### D6 · Leg maturity (legpos 60/90d) — `POLARITY_DEPENDS_ON_CONTEXT`
- Resolve E40(56,cedo)×E39(89,tarde); mas legpos no AGREGADO INVERTE (WIN 85 > TRAP 51) — só com 1D-trend + mecanismo.

### D7 · Exhaustion (RSI-div / sell-climax) — `WARNING_FAILURE_MODE`
- Sinaliza topo SÓ no high-legpos+bear, com volume SVP (não tick-vol). Isolado não separa os 4 traps dos 6 winners high-legpos.

### D8 · Blowoff (F_TOP_OB_RSI) — `WARNING_FAILURE_MODE`
- Flag de topo exausto extremo (E24/E34); em open-sky blowoff-top e breakout-acceptance são mecanicamente IDÊNTICOS.

### D9 · Absorption (OB/demand zone) — `DEAD_AS_AUTHORITY_BUT_KEEP_AS_CONTEXT`
- Contexto conceitual de liquidez institucional pendente; medir por distância+qualidade. Presença binária é nula (lift 0.99).

### D10 · Micro liquidity sweep — `REQUIRES_CASE_READING`
- Conceito sweep+reclaim em reversão; sweep 4H não separa; intrabar verdadeiro = FEATURE_UNAVAILABLE (sem OHLC contíguo).

### D11 · Swing-high origin precision — `REQUIRES_CASE_READING`
- Localiza origem do swing/SL; a tese "HL-após-sweep = winner" NÃO aparece nas sequências (refutada). Discriminação é multi-dimensional.

### D12 · OB micro-vs-macro — `DO_NOT_USE_AS_GATE`
- Detectores OB algorítmicos são MICRO ($15-25); Cris opera zona MACRO ($150-200 manual). Sinalizar REGIÃO, deixar entrada visual; `dist_supply` mata breakout-through-supply (S15/S24).

---

# Família E — INDICATOR CONFLUENCE (8 lentes)

**Limite transversal honrado:** indicadores identificam **TOPO MACRO** (distribuição/exaustão), **não comparam trades par-a-par**. No par decisivo E39/E40 os indicadores são idênticos; só `legpos` separou.

### E1 · NAS LONG/SHORT clustering — `CONDITIONAL_EVIDENCE`
- Cluster de 4 NAS SHORT confirmou topo jul-ago 2023. SEMPRE LONG/SHORT por first-appearance ≤entry−1. **NUNCA** TOP/BOTTOM, NAS_*_SIGNAL numérico (decouplado=0), índice `x`, nem gate isolado.

### E2 · Bubble polarity (context-dependent) — `POLARITY_DEPENDS_ON_CONTEXT`
- BOTTOM→sell=clímax-bullish; PULLBACK→buy=acumulação (WR 61.5% vs 34.8% se invertido); TOP→buy=absorção-vendedora/short. Classificar contexto PRIMEIRO. Validar plot_id mapping antes.

### E3 · SMC BOS/CHoCH — `CONTRAST_LENS`
- BOS=continuação, CHoCH=reversão; CHoCH em fundo = gatilho bullish. Pivot 4H é local demais para separar WIN×TRAP.

### E4 · SVP acceptance / value-area — `DEAD_AS_AUTHORITY_BUT_KEEP_AS_CONTEXT`
- `dist_above_VAL` lean fraco; inside_VA / above_VAH não separam com dados reais. Contexto de aceitação, nunca gate.

### E5 · Session VP native volume (climax) — `WARNING_FAILURE_MODE`
- Volume REAL corrigiu a leitura do tick-volume (E1 COVID = capitulação 4.88, não 0.78). O "breakthrough" volume×1D-bear era artefato de tick-volume (RETRATADO). **NUNCA** tick-volume do frozen.

### E6 · Demand/supply distance + quality — `REQUIRES_CASE_READING`
- Melhor separador estrutural small-n: `supply_dist_from_polarity` BOM 2.48 vs NÃO 1.08 (não compra contra o teto). Fragile BOM q=0 com supply perigoso VENCE → qualidade-de-supply não prediz outcome. **NUNCA** presença binária / threshold ATR apertado (fabrica falso-nulo).

### E7 · Overhead-supply awareness — `CONDITIONAL_EVIDENCE`
- `has_4h_supply_overhead` é gate NECESSÁRIO (resolve no-overhead/ATH-bullish vs overhead-bearish); composite isolado pior (shuffle-null P=0.070 ns). None+overhead=0 = bullish, não missing.

### E8 · plot_id mapping correctness — `DO_NOT_USE_AS_GATE` (gate de integridade obrigatório)
- Mapping CORRETO: BUY=plot_0/2/4, SELL=plot_6/8/10 (plot_8=MEDIUM, plot_10=LARGE), POC=plot_12. Validar (Counter) ANTES de qualquer feature bubble. Mapping invertido 2026-06-05 custou 5 dias.

---

# Família F — REGIME / CONTEXT-FUEL (8 lentes)

Regime = **conditioning do significado** (como a Camada 1), não gate. Achado-chave: a alavanca real é **regime, não exit**; e o **BEAR-state carrega os monumentais**.

### F1 · Regime Classifier B v3 — `CORE_CONTEXT`
- 3-state BULL/TRANSITION/BEAR; validado visualmente. BEAR-state carrega MAIOR avgR LONG (+1.32R) porque mean-reversion vive lá. Nenhum gate de regime bateu LONG puro. **DEVE:** mapa de significado + ativação SHORT em BEAR+MACRO_BROKEN.

### F2 · Context-Fuel v1 (7 eixos) — `REQUIRES_CASE_READING`
- `dist_4h_supply` ba=0.946 (mas é UM termo condicional a `has_overhead`). Falha critério de âncoras (corta ATH no-overhead). **DEVE:** tratar None=bullish-ATH; caso-a-caso.

### F3 · Supply-Fuel Global (sup_reject AND fuel_low) — `CONDITIONAL_EVIDENCE`
- Soft-warning combinado dentro do bear_leg onde nasceu; supply-rejection é flat no full-276. Não é veto global.

### F4 · BOM Tiering supply-risk — `CONDITIONAL_EVIDENCE`
- supply≤0.5 ATR corta UNK com CUSTO ZERO de BOM; A-tier intacto. O killer-axis = PROFUNDIDADE do veto (>1.0 ATR mata B-tier frágil). Borda TIGHT como soft_warning.

### F5 · F-strict × Regime — `WARNING_FAILURE_MODE`
- F_STRICT é discriminador de topo útil, MAS a tese "regime separa" é FALSA (near-breakeven em todo regime, W/L interleaved). **DEVE:** F_STRICT como flag de human-review/Telegram; conditioner = estrutura per-trade, não regime.

### F6 · CAPITULATION carrier — `POLARITY_DEPENDS_ON_CONTEXT`
- Bear-context (143/276) avgR +0.28 ACIMA da base, contém 9/15 monumentais. **DEVE:** reconhecer que bear/capitulação GERA monumentais → NÃO proteger/BE-armar lá; ler a assinatura de V.

### F7 · Learned-Context vs Convexity — `CONTRAST_LENS`
- markup-vs-rejeição que o engine aprendeu é FLAT; inversão coerente n≥30 (runners em STRONG_BEAR/SELL_DISTRIBUTION/CORRECTIVE_BEAR, morrem em BULL_PULLBACK 0.57). **DEVE:** re-polarizar a leitura para reversão.

### F8 · Edge non-stationary / regime-bound — `WARNING_FAILURE_MODE`
- Build 2020-22 avgR +0.02 vs holdout 2023-26 +0.39 (carrega tudo); 13/15 monumentais no build → "preservar monumentais" é beta long-gold, não edge estacionária. **NÃO:** concluir WR/avgR de um único período.

---

# Família G — RISK / SL / EXIT / CONVEXITY (8 lentes)

Canon: realR-capado = **CALIBRAÇÃO não árbitro**; o eixo risco/exit tem **eixo próprio**; SL **não é onde mora a edge**.

### G1 · SL estrutural swing-origin (M5) — `CORE_CONTEXT`
- = o SL que as anotações visuais do Cris apontam. Recupera bad_SL 5→10/12; torna 2020-22 positivo. 97/276 SL>4ATR (máx 15ATR) = FATAL prop-firm sem cap. **DEVE:** leitura da estrutura defendida; **NÃO:** SL mecânico operável (largo demais).

### G2 · SL contextual (demanda 4H) — `CORE_CONTEXT`
- Resolve a largura (E17 8.4→1.03ATR vira WIN +3.90); repaint-audit PASS. Bootstrap vs mecânico = WASH (expectancy-neutral). **DEVE:** SL risk-shaped causal; **NÃO:** tratar como edge.

### G3 · SL cap ~4ATR — `WARNING_FAILURE_MODE`
- REJECT corta E1+E17 (V-reversals); CLAMP cria stop fictício mid-structure (FATAL). **DEVE:** flag de viabilidade (SL>4ATR = entrada-tarde) para review humano, não teto automático.

### G4 · Exit decomposition (uncapped) — `CONDITIONAL_EVIDENCE`
- realR capado +3.9R apaga 45-65% da edge; let-run +241R vs capped +84R; 72 runners, 30 monstros até +30.7R; engine é ANTI-seletivo. **DEVE:** régua econômica (convexity-capture uncapped por episódio + P1/P2).

### G5 · Convexity target function — `CORE_CONTEXT`
- Harvester de convexidade (WR baixo é feature; cortar 1 monstro destrói mais que muitos losers). Convexidade é BETA (random-long context-matched capta o mesmo runner_freq). **DEVE:** proteger runners; DD/streak = restrição, não objetivo.

### G6 · BE rejected — `WARNING_FAILURE_MODE`
- BE/scratch é anti-correlacionado com a assinatura de V-reversal; premissa "bear=loser-prone" é FALSA. **NÃO:** proteger preventivamente os trades que mais pagam.

### G7 · partial50@2R+6R — `CONDITIONAL_EVIDENCE`
- Lisa a curva (streak 9 vs 13), aprovado por Cris para streak prop-firm; custo ~2R nos monumentais. Exit fixo de gestão, não maximizador / árbitro de entrada.

### G8 · Exit = noise / edge regime-bound — `DEAD_AS_AUTHORITY_BUT_KEEP_AS_CONTEXT`
- Nenhuma das 9 políticas bate baseline +3R fora do ruído; a alavanca é regime, não exit. Exit baseline como default.

---

# Família H — READING ENGINE / EPISODE CANON / SÓSIA / CONTINUAÇÃO / QUALIFICAÇÃO (11 lentes)

A própria maquinaria do Reader. Cataloga-se aqui **como cada peça aprofunda (não engessa) a leitura**.

### H1 · Episódio = unidade de análise (canon) — `CORE_CONTEXT` 🔑 lei-mãe
- Colapsar convergência multifatorial-dinâmica em aritmética mata o conditioning; `bear leg` muda de sentido conforme weekly+cascade. **DEVE:** segurar o episódio inteiro, condicionar TODO fator pelo timeframe superior, saída = narrativa graduada com gatilhos de invalidação. **NUNCA:** colapsar em score/voto/threshold; medidor nunca arbitra.

### H2 · Sósia surface clustering (3a) — `CONTRAST_LENS`
- Match na superfície (flush+clean_sky+demand+acceptance), discriminadores (weekly/cascade/forma) FORA do match. O cluster 4918 reproduziu o par manual 4918↔1661. **DEVE:** discriminar ENTRE casos (puxar sósias, ler o que varia fora do match).

### H3 · Continuação estrutural (3b) — `CONDITIONAL_EVIDENCE`
- "Mesmo movimento" = entradas que partem do MESMO swing-high de origem (pivô causal K=4, prom≥1.2 ATR). Liga 4926 (continuação +18R) ao topo pré-flush de 4918. **DEVE:** não cortar o 2º evento da mesma perna só pela superfície local. **NÃO:** gate de TAKE (mesmo movimento ≠ runner garantido).

### H4 · Reading-consistency audit — `CORE_CONTEXT`
- Guarda anti-superfície: confere se a narrativa de fato condiciona pelo weekly/cascade (critério-semente: legit = weekly≥0 ou cascade raso). **NÃO:** converter o critério-semente em regra dura.

### H5 · Dynamic reader v1 (7 sub-leitores) — `DEAD_AS_AUTHORITY_BUT_KEEP_AS_CONTEXT`
- Codifica markup-vs-rejeição como TRAJETÓRIA; 7 skip-winners recuperados (lift 1.21). Convergência = voto somado (proibido como árbitro). **DEVE:** os 7 sub-estados como VOCABULÁRIO de trajetória.

### H6 · Dynamic reader v2 (staged) — `DO_NOT_USE_AS_GATE`
- S2 (prior engines) melhor in-sample (lift 1.30); empilhar fontes em thr baixo DILUI (lift 1.04). **DEVE:** tabela de evidência por FONTE; ler forte-convergência, não soma frouxa.

### H7 · Dynamic reader v3 (sub-window validation) — `WARNING_FAILURE_MODE`
- Expôs honestamente que a lift 1.30 de v2 era PARCIALMENTE in-sample: out-of-slice lift 1.16/1.21 (null_p 0.30/0.28, não-significante). **Prova permanente** de que vote-convergence sobre os 276 é in-sample → reforça por que a leitura tem de ser holística, não somada.

### H8 · Visual discrimination taxonomy — `REQUIRES_CASE_READING`
- 9 categorias por MECANISMO; métrica `acceptance_after_reclaim`. O discriminador é COMO o preço interage com supply/demand DEPOIS do reclaim (não presença). Primeira-passada mecânica PENDING (não inspeção real).

### H9 · Trade Qualification Engine (84 fatores) — `CONDITIONAL_EVIDENCE`
- TAKE WR 53%/+0.91R, monotônico, bate 3 baselines P≥0.99, held-out +0.73, 2.3× cobertura. Edge real mas FINO (~2/3 re-deriva legpos+demanda, n=32, 73% sumR em 2023-26, 0 SHORT TAKE; OOS bear refuta). **NÃO PROMOVIDO.** Gradiente de qualidade no escopo LONG bull/dip/reversão-de-fundo.

### H10 · Multi-specialist reader/challenger (design) — `CONDITIONAL_EVIDENCE`
- Mesa por trade: Stage A (re-deriva setup_type cego, MI 0.913, não-circular) → ~20 especialistas (evidência estruturada disjunta) → DA → aggregator que constrói TESE (não soma votos). `nas` DECISIVE, `capit+rsi` única confluência genuína in-sample (REFUTADA OOS). Infra de auditoria viva; **nenhuma regra promovida**; aggregator não-autorizável (overfit).

### H11 · (referência) Episode reading 276 library — `CORE_CONTEXT`
- Biblioteca de leituras vivas: leitura FORTE em evitar (trap/skip lift 0.52/0.75), FRACA em capturar (legit-buy ≈ base); 25/30 monumentais preservados. Substrato do canon H1.

---

# Família I — FUNDAÇÕES / GUARD-RAILS METODOLÓGICOS (9 lentes)

O frame dentro do qual o Reader opera. Maioria `CORE_CONTEXT` (verdades de substrato) ou `WARNING_FAILURE_MODE` (armadilhas a respeitar).

### I1 · Entry/BOS-CHoCH sem edge isolado — `CORE_CONTEXT`
- BOS reclaim não bate random-long matched-by-legpos (~80% do retorno é drift). O bar do BOS é proxy ruidoso (às vezes bottom-reversal, às vezes high-leg/top). **NÃO:** refinar o trigger; medir entrada vs zero.

### I2 · Losers auction-irredutíveis no entry — `CORE_CONTEXT`
- target-7 não separável com 97 features; mesmo vetor precede good-breakout E micro-top-loser. Irredutibilidade é CONDICIONAL ao feature-set frozen-4H (falta sub-4H OHLC contíguo). **DEVE:** flag de baixa-confiança, não corte limpo.

### I3 · legpos = eixo causal validado — `CORE_CONTEXT`
- Primeira/única feature a separar par inseparável (E40 win 56 vs E39 trap 89). NÃO separa no agregado (inverte) — dois mecanismos (Trap A exaustão-topo high-legpos vs Trap B downtrend reclaim baixo/mid). **DEVE:** lente posicional backbone (mapa 2×2 com leg-direction).

### I4 · Indicadores = MACRO TOP, não comparação per-trade — `POLARITY_DEPENDS_ON_CONTEXT`
- Identificam topo-macro-bear-legítimo vs pullback-em-bull-leg-mid; near/under-supply em bull = markup BOM. Equal-veto per-trade afunda winners (16/16 cortes errados tinham Auction≠TAKE).

### I5 · 9 known winners (recall anchor) — `CONDITIONAL_EVIDENCE`
- Set must-preserve: Win1 reversal E27/E30/E40, Win2 pullback E1/E5/E13/E17/E21. **E23 reconciliado OUT (2026-06-18)** como blow-off-top → lista agora 8. **NÃO:** usar para provar edge ou ratificar selector (circular); ainda contar E23.

### I6 · Outcome-proxy = lift-vs-base-rate por episódio — `WARNING_FAILURE_MODE`
- MFE/MAE forward mediu o drift bull, não edge (66% vs 67.3% base = lift 0.99×); 2965 candidatos = 276 episódios. **DEVE:** sempre lift, agregar por EPISÓDIO (dedup serial), N real ~276.

### I7 · 45 grupos = calibração não validação — `WARNING_FAILURE_MODE`
- Grupos rotulados com hindsight servem para descobrir predicados e eliminar features, NÃO para provar edge/lockar thresholds. Todo "sucesso" foi no 62 e colapsa no 276. Concordância-com-Cris ≠ skill preditivo.

### I8 · Trava no-OOS / no-cross-asset — `WARNING_FAILURE_MODE`
- Cross-asset/bear-2013-16 NUNCA refutam XAU sozinhos (XAU-specific by design). Validação mora DENTRO dos 276 (convergência causal + sub-janelas + null/jackknife + lift por episódio). **NUNCA** escrever "needs OOS/held-out/cross-asset".

### I9 · Recall-gate antes de backtest — `WARNING_FAILURE_MODE`
- Se há Ground Truth de winners, validar recall ANTES do censo. v1 recapturou 2/17 → censo NULO. Recall preserva winners mas não confere edge (v2.2 recall 17/17 = âncora, não prova).

---

# Síntese (relatório final)

**Arquivos criados (3):**
- `docs/XAU_4H_L2_BPT_READER_LAYER2_EVIDENCE_LIBRARY.md` (este)
- `my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_reader_layer2_evidence_inventory.csv` (94 lentes, machine-readable)
- `.../v1/results/l2_bpt_reader_layer2_source_index.csv` (índice de fontes: docs + scripts + memória)

**Número de evidências catalogadas:** 94 lentes em 9 famílias (Macro 22 · DSPA 11 · Bear-leg 5 · Microstrutura 12 · Indicator 8 · Regime 8 · Risk/Exit 8 · Reading 11 · Fundações 9).

**Principais famílias encontradas:** (1) eixo condicionante macro/D1; (2) trajetória de 2ª ordem (DSPA/path); (3) bear-leg legitimacy; (4) forma viva do preço (microstrutura); (5) confluência de indicadores; (6) regime/fuel; (7) risco/exit/convexidade; (8) maquinaria de leitura (episódio/sósia/continuação/qualificação); (9) guard-rails de substrato/metodologia.

**CORE_CONTEXT (backbone que o dossiê sempre carrega — 14):** D1/weekly leg-state · 9 specialists · leitura-de-conjunto D1 · bear-state 1D · V-flush/capitulation-base · defended-swing · multi-bar acceptance (F3) · regime_B trajectory (F7) · regime classifier v3 · SL estrutural · SL contextual · convexity target function · episódio-canon · reading-consistency audit · entry-BOS-sem-edge · losers-irredutíveis · legpos · (episode-276-library). *(legpos/entry-BOS/losers-irredutíveis catalogados em Fundações.)*

**CONDITIONAL (vale só sob contexto — núcleo operacional do Reader):** SVP-acceptance F6 (lead mais forte) · LBB signal · bear-leg refined loser-cut · continuação estrutural 3b · trade qualification engine · multi-specialist design · macro_phase · overhead-awareness · partial50 · supply-fuel global · BOM tiering · context-fuel 7-axis · 9-winners recall · feature census · SMC pivots · sweep/flush F1/F2 · swing F4.

**WARNING / FAILURE_MODE (precedentes de erro — manter como alerta, nunca repetir):** retracted block gate (circular) · entry-quality refutada · indicator-confluence-redundante · confluence-v2-override · microstructure-inverte · deep-target7 (hull) · 4H-fractal-leg (confound) · cross-confluence loser-cut (0/86) · F-strict×regime · edge-non-stationary · BE-rejected · SL-cap4(reject/clamp) · exhaustion-isolada · blowoff-isolado · Session-VP-volume-breakthrough (retratado) · dynamic-reader-v3 (in-sample) · outcome-proxy-absoluto · 45-grupos-calibração · trava-no-OOS · recall-gate.

**NÃO devem virar gate (`DO_NOT_USE_AS_GATE`):** regime_B_v3 escalar · confluence-v2-override-late-top · OB-micro-vs-macro · dynamic-reader-v2-net-vote · plot_id-mapping (é gate de integridade, não de mercado).

**POLARITY_DEPENDS_ON_CONTEXT (o sentido inverte — exigem a Camada 1 fixada antes):** sup_cat/pol_cat · bubble polarity · overbought-in-bear · leg-maturity · CAPITULATION-carrier · indicadores-macro-top.

**Lacunas ainda existentes (não fabricar conclusão, são limites reais):**
1. **Sub-4H OHLC contíguo 2020-2023** — feature ausente que poderia desambiguar markup-vs-rejection/sweep; porta empiricamente fechada (bear-leg residue, microstructure). É a fronteira da irredutibilidade.
2. **Resíduo auction-irredutível** (11 leaked bear-leg + ~97 losers idênticos aos winners no entry) — sem separador atual; só leitura caso-a-caso + SL estrutural.
3. **Lado SHORT** — 0 SHORT TAKE no qualification engine; toda a biblioteca é LONG-cêntrica (espelho SHORT é bônus futuro).
4. **Não-estacionariedade** — 13/15 monumentais no build 2020-22; "preservar monumentais" é beta-long-gold, não testável dentro da trava no-OOS — exige convergência causal, não outro dataset.
5. **Eixo "aceitação-ao-longo-do-tempo" (acceptance_after_reclaim)** — vocabulário definido (H8) mas leitura ainda PENDING de inspeção visual real caso-a-caso.
6. **Maturidade do VP de início-de-sessão** — fino nas primeiras barras; lente A4/E4 deve ponderar isso, não tratar como look-ahead.

**Como o Reader usa esta biblioteca (fecho):** fixe a Camada 1 (weekly+cascade+leg-state) → puxe os CORE_CONTEXT como dossiê → consulte CONDITIONAL/CONTRAST/POLARITY como hipóteses e precedentes → respeite os WARNING como erros já cometidos → leia o episódio livremente e responda às 6 perguntas. **A biblioteca não decide; ela aprofunda.**
