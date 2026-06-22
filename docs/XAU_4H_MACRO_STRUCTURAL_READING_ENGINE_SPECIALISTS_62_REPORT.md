# MACRO STRUCTURAL READING ENGINE — 9 SPECIALISTS / 62 TEACHING SET — RELATÓRIO

**2026-06-22.** Diagnóstico/calibração. Os 62 = ENSINO, não validação. Sem outcome como predicado.
Engine/decisions/produção intocados. Script `macro_structural_specialists.py`.

## Processado
62 trades (A26 bull-cortado · B18 bear-aceito · C18 ambíguo) × 9 especialistas = 558 evidências auditáveis.
Especialistas (determinísticos, causais): Supply(sup_cat/pol_cat) · Demand(demand_cat) · Volumetry(SVP as-of-bar) ·
Multi-TF(4H+1D+W) · Macro Regime(regime_B_v3 completo, D-1) · Momentum/Exhaustion · Capitulation · Fuel · Risk/SL.

## Estados finais (7 de 12 usados)
NO_OVERHEAD_MARKUP 15 · MACRO_BULL_RUN_CONTINUATION 13 · CORRECTIVE_BEAR_LEG 12 · BULL_PULLBACK_CONTINUATION 8 ·
RANGE_MACRO_BULL_RECLAIM 7 · BEAR_BOUNCE_RISK 6 · CAPITULATION_RECLAIM_VALID 1. Família: 44 BULL / 18 RISK.

## Família por set
- **A (bull-cortado, deve BULL): 20/26 BULL = 0.77** — melhor que dist_supply puro (0.73) e composite (0.35).
- **B (bear-aceito, deve RISK): 5/18 RISK = 0.28** — FRACO (pior que dist_supply 0.89).
- C (ambíguo): 11 BULL / 7 RISK.

## Anchor check
- **preserve (BULL): 12/14** — falha só S26, S27. **Melhor preservação de big winners de qualquer abordagem até hoje.**
- **block (RISK): 0/1** — T40 falhou (NO_OVERHEAD_MARKUP).

## Onde o engine ACERTA (o ganho real)
A confluência multi-aspecto **preserva bull-run/continuação muito melhor que qualquer feature única** (12/14 anchors).
Confirma o diagnóstico do Cris: contexto bull vive na confluência (CLEAN_SKY + demanda defendida + multi-TF bull +
momentum), não numa fatia. O lado de PRESERVAÇÃO está resolvido em nível conceitual.

## Onde o engine AINDA FALHA (honesto)
Lado RISK/block fraco (B 5/18). Diagnóstico das falhas:
1. **Macro override:** T40, T18 têm `regime=MACRO_BROKEN_DISTRIBUTION` MAS foram classificados BULL porque a regra
   de confluência deixou o sinal LOCAL (CLEAN_SKY + momentum forte) sobrepor o MACRO (macro_broken). **Bug de
   prioridade:** macro_broken/distribution deveria ser FATAL CONFLICT que bloqueia estados BULL, independente do local.
2. **Late-top com momentum forte:** T2/T3/T4/T16 são topos de bull (Cris: late/top exhaustion) mas o Momentum
   specialist deu STRONG_BULL/HEALTHY_HIGH_LEGPOS — porque tops têm momentum forte ANTES de virar. Detector de
   exaustão (bear_div/rise20/distribution) insuficiente. **A distinção healthy-high-legpos vs late-top-com-momentum
   é o problema mais difícil — features atuais não bastam.**
3. **Range/winner-curto (T25/T26):** zona cinzenta "aceitável perder" — genuinamente ambíguo.

## Conclusão: SUCESSO PARCIAL — direção confirmada, lado RISK incompleto
- ✅ Confluência multi-aspecto é o caminho certo: **preserva bull-run melhor que tudo (12/14)**.
- ❌ Bloqueio de bear/corrective/late-top fraco. Dois fixes PRINCIPADOS (não ID-fit) p/ próximo bloco:
  (a) **macro_broken/distribution como FATAL CONFLICT** que veta BULL (macro sobrepõe local);
  (b) **detector de late-top mais forte** (a exaustão com momentum-ainda-forte precisa de feature nova — talvez
      distribution_flag D1 + dist_d1_supply + posição na perna semanal).
- NÃO re-tunei aos IDs (proibido). Calibração, não validação.

## Próximos passos
1. v2 da confluência com macro-override (fatal conflict). 2. Late-top detector (features adicionais). 3. SÓ DEPOIS:
aplicar aos 276 + OOS (validar o princípio). 4. SHORT futuro = espelho do lado RISK.
