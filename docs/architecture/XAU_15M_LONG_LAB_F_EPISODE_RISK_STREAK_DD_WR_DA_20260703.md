# LAB F — DA ADVERSARIAL (2026-07-03)

Dois DAs reais: (i) **DA-pré** (workflow de discovery `wf_7e18ae96-186`, 7 agentes) — impôs as 17 exigências D1-D17 ANTES da execução, incluindo a solução causal central (estado sequencial só atualiza no EXIT realizado; trade aberto = outcome invisível); (ii) **DA pós-resultado independente** (subagent real; scripts `_DA_lab_f_attack{1,2,3}*.py`, salvos, **não commitados** — git log verificado).

## Bug material encontrado (corrigido e re-executado)
**F3 breaker — término da pausa divergia do prereg:** o código só liberava o trade que INICIA o cluster novo; os seguintes ficavam bloqueados até um win realizado (a janela de 48b entre exits não expira com o tempo). Regra do prereg ("pausa termina quando novo cluster começa") implementada e republicada: BASE br2 N322→336, NET 174,5→**180,0**, DD −20,0→**−16,9** (o headline "br2 piora DD para −20" era parcialmente artefato do bug); P1 br2 N→332, NET 199,3, DD **−13,4** (≈ baseline −13,5), stk −6 (lente exit-order: −7). Entre os extra-bloqueados havia winners grandes (+3,36; +3,48). **Nulls recomputados: p 0,46-0,75 → continua no-claim; veredito da família não muda (negativo).**

## Desvios de prereg encontrados (corrigidos)
1. **F5 sem o null calendar-shuffle** (obrigatório no §6): adicionado (cascata com rótulos permutados) — daily3 p=0,478/0,482 · wk5 p=**0,958/0,984** (o weekly-stop é PIOR que rótulos embaralhados: corta semanas pós-loss que revertem). No-claim em tudo.
2. **F5 sem os bounds entry-time (D12):** adicionados. Daily3: Δ exit-attr −2,9/−2,7 (causal) · entry-attr +1,6/+0,6 (bound simples; a variante cascata do DA dá −5,2) — leitura: efeito ~0±5R, cosmético. Weekly: −35,4/−40,6 exit · −27,9 entry — negativo em qualquer atribuição. Nota: o bound "daily +1,6" do discovery não era reproduzível com cascata; o report usa os pares recomputados.

## Ataques dissolvidos (verificados com código)
- **Determinismo:** re-runs byte-idênticos (stdout+CSV; hash do CSV do repo confere).
- **F1 (D3/D5):** replicação independente do zero → kept sets idênticos nos 6 painéis; cascata real (variante hindsight diverge em 10-26 trades).
- **F4 chain_pos causal (D4):** 0 violações em 870; pos 362/59/14 consistente com o discovery (hindsight 352/65/18; 73/66 pares demovidos por prev-aberto).
- **F8 (D7):** 0 mismatches vs letrun do engine; SL prevalece; w→l/l→w recontados idênticos; sem look-ahead no nível (só k>cj); null corrigido para vivos-na-barra-8 (p 0,73-0,85) — continua no-claim.
- **Painéis:** F4_sz BASE, F5_daily3 BASE, F2_max1c P1 recomputados com painel escrito do zero — batem o CSV dígito a dígito.
- **Concorrência (D11):** máx 4 posições / 108-100 overlaps confirmados por full-scan.

## Leituras obrigatórias (o relatório carrega)
1. **F2_max1c (linha P1) é a ÚNICA config das 26 que atinge os dois eixos FN (WR 50,0 · stk −5) — e é FAIL pelo §8:** retention 33,8%, mata 39/56 runners (70%), 7 do top-10, 2026 negativo, no-claim nos nulls. Atinge os eixos destruindo a estratégia. Não vender.
2. **F8 piora os DOIS eixos FN** (WR −3,0/−3,5pp · streak −8→−13, converte 13-17 winners em pequenas losses) e o claim "runners intocados por construção" era FALSO (5 runner-kills; ex. R+6,87→−0,04). Kill-criterion do P2 transferido para exit NÃO paga.
3. **F4:** ganho real mas modesto e distribucionalmente pequeno (DD obs −12-18%, DD q95 bootstrap 21,4→20,7 / 19,9→18,5; streak invariante POR CONSTRUÇÃO; "run 51/52" é threshold ponderado, não runner morto). Nunca edge (D15).
4. **Lente de conta (exit-order, D11):** P1 br2 stk −6→−7; F5_daily3 stk −7→−8; max2day DD piora ~1,4R — eixos FN citados devem considerar a lente exit.
5. **F2_max2day FN1/6:** o corte de 2024 (+13,6→−4,2) vem de UM dia (2024-07-31, corta +10,76/+7,3/+6,12) — o guard amputa a cauda gorda intradiária (fail-then-fire).
6. F5_daily3 (ret 99%) = cosmético; enquadrar como sem-efeito, não "quase-PASS".
7. Multiplicidade: 26 painéis + nulls; NADA com p<0,05 (muito menos α=0,004); pior mês/semana atribuídos por entry-time (declarado).

## Veredito DA por família (pós-correção)
**F1** CONFIRMA_NEGATIVO · **F2** CONFIRMA_NEGATIVO (max1c FAIL §8 apesar da ótica WR/streak) · **F3** BUG_CORRIGIR→CONFIRMA_NEGATIVO · **F4** CONFIRMA_POSITIVO **só como risk-control de DD, nunca edge** · **F5** CONFIRMA_NEGATIVO (+2 desvios de prereg corrigidos) · **F8** CONFIRMA_NEGATIVO.

## Veredito global sugerido pelo DA
**NO_STREAK_DD_WR_SOLUTION** — nenhuma das 26 variantes bate os nulls; nenhum PASS_STRONG; a única que toca WR/streak é FAIL por runner-kill desproporcional; F4 registrado como suavizador marginal de DD via sizing.
