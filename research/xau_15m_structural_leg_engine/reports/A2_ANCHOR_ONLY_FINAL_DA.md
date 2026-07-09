# DA FINAL — A2-ANCHOR-ONLY (2026-07-09)

> Devil's Advocate real (Agent tool, read-only + 2 sondas declaradas: mining-null passo-1 e
> base-rate de cobertura) atacando implementação, gate e narrativa do bloco A2.

## VERDICT: `BLOCKED_A2_GT_GATE` — mantido; núcleo epistemológico LIMPO (não é FAIL_A2_LOOKAHEAD)

## As 9 perguntas do Cris (respostas verificadas no código/results)
1. **Epistemologia respeitada?** SIM — known_at=fecho da confirmação; barra de confirmação nunca
   reteste; eventos versionados; macro causal; GT só na avaliação. Ressalva: `no_entry_on_confirmation`
   é invariante estrutural (tautologia), não check falível — declarado; a proteção real = ausência
   de camada de entry + exclusão da barra de confirmação (testadas no guard).
2. **Só regiões para o futuro?** SIM — truncation VERDADEIRO 60/60 (Data reconstruído) + checks
   full-stream nas 2.584 regiões (monotonicidade, first_retest>known_at, determinismo sha256).
3. **Evitou comprar o fundo confirmado?** SIM — zero código de entry; geometria: no flip o close
   está ≥4 ATR acima do low, fora da banda.
4. **Melhorou o F1.5 de forma real?** SIM com nuance — r=4: 8/10+7/11 vs 6/10+4/11; mining-null
   P=0,000 (obs 15 vs null med 1, q95 3); MAS parte do salto é densidade (+24% candidatos;
   per-candidato 0,135→0,163); **r=6 = 0,250 de precisão com 40% menos candidatos** (o caso limpo).
5. **Ainda é detector infantil?** Mecanicamente é reversor por threshold; a diferença TODA vs o
   zigzag banido é o CONTRATO DE USO (só-futuro, provado por truncation) + decisão explícita do Cris
   no manifest. ALERTA: abrir r<4 "porque a tendência melhora" = rampa de fit-ao-GT — só com GT
   declarado queimado.
6. **FP/dia aceitável?** 0,89/dia FP; 6,4 fundos/sem vs GT 0,7/sem (~9×); precision_gt 0,023;
   agravante: sem teto de idade, regiões de 200+ dias contam cobertura (2/10 cobertas) — estratificar
   por idade em qualquer v2 (D1 do Cris ficou mais urgente).
7. **Chance de losers ≤10?** A ponte 30-70× está declarada. (a) retested→invalidated 92-98% é teto
   de MEDO, não taxa de perda medida (invalidação pode vir após reteste que pagaria 3R — não medido,
   e NÃO se mede nesta fase sem autorização de backtest); (b) a "esperança por família" (7/7, 3/3)
   era TAUTOLOGIA de construção — corrigida no report; o otimismo F2 fica sem essa base.
8. **Pronta para F2?** NÃO como está: gate falhou; r não congelou; INVALIDO não rejeitados nesta
   camada (arquiteturalmente correto — rejeição = estado da perna em F2 — mas os 4 já foram lidos
   2×: a futura rejeição deles será in-sample storytelling, não validação); GT queimado.
9. **Descartar ou redesenhar?** NENHUM dos dois é forçado: a camada é sólida (causalidade provada,
   determinística, parametrizável); a decisão é do Cris entre (a) aceitar 8/10·7/11 como fasquia
   revista com GT queimado declarado, ou (b) abrir r={2,3} como looks novos SOBRE GT queimado.

## Ataques extra confirmados → corrigidos antes do commit
- "BULL_PULLBACK 7/7 / RANGE_BOTTOM 3/3" = tautologia → reescrito como composição das 11 cobertas.
- "Achado central entry-serviceable 29/42=69%" = métrica PÓS-HOC não pré-registada, constantes LATE
  improvisadas, reteste 10-38h NÃO verificado → rotulado EXPLORATORY_POSTHOC/NOT_FOR_DECISION +
  linhas no ledger. A favor: lift ~6× sobre base-rate (11,4% análogo vs 69%; null não extreme-matched).
- Passo 3 com r escolhido a olhar o GT → consequência escrita: **42+50+4 = GT QUEIMADO,
  NOT_FOR_DECISION para seleção futura** (ledger A2_BURN_GT).
- Latência "16-36 barras" = global, não das 18 LATE → corrigido no report.
- Mining-null ausente do passo 1 (regressão vs F1.5) → sonda citada + ledgered (A2_NULL_S1).

## Ataques refutados
Lookahead: nenhum · entry escondida: nenhuma · GT no builder: nenhum · truncation fake: não —
reconstrução verdadeira · "melhora = só densidade": não (P=0,000; r=6 melhora precisão com menos
candidatos) · "achado central = maquiagem do BLOCKED": não — o report mantém BLOCKED, precision
0,023 e INVALIDO 1/4 visíveis; é hipótese exploratória, agora rotulada como tal.

## Números do report vs results: TODOS verificados (12 conferências, 1 deslize de latência corrigido).
