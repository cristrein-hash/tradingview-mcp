# TARGET-7 NÃO-SEPARÁVEL — KNOWLEDGE STATE (trava de conhecimento)

**2026-06-22. commit 4c3f0a5.** Diagnóstico nos 62 (ensino). Documentação apenas — sem análise nova.
Preserva o veredicto do bloco profundo de diferenciação do grupo visual do Cris.
Detalhe completo: `docs/XAU_4H_DEEP_TARGET7_DIFFERENTIATION_REPORT.md`.

## Resultado travado
1. **target-7 `{T2,T3,T4,T16,T17,T23,T24}` NÃO é robustamente separável** com as 97 features causais atuais
   (84-stream + categoricais + REFERENCE_ONLY/mortas). Rótulo estrutural (mistura winners T2/T24 e losers) =
   contraste NÃO-circular; ainda assim não há separador.
2. **"clean-sky/vácuo vs romper supply testada com aceitação"** = insight **parcial/contextual** (era-level,
   confirmado por agente cego: target 86% vs same-era winners 30%), **NÃO filtro promovível** — atinge 40% dos
   winners 2024-25.
3. **Confluência exaustiva 1/2/3-way** (todas as features, incl. excluídas) achou 6/7 mas **FALHOU no teste de
   permutação: p=0.167** (20/120 subsets-7 aleatórios igualam) ⇒ **ID-fit/hull, sem sinal real**. Reforçado por
   cluster tightness 1.03 (sem cluster) e ZERO features separando target-7 dos 4 B-excluídos (T18/T20/T30/T40).

## Travas (o que NÃO fazer)
- **NÃO repetir busca cega de confluência sobre o mesmo feature set** — só produz hulls (permutação já provou).
- Permutação é a guarda canônica anti-ID-fit p/ qualquer busca em grupos pequenos.

## Próxima abertura — SÓ com nova informação estrutural
Reabrir esta frente apenas se houver:
- **OHLC contíguo 2020-2022 / geometria de rollover / sequência de swings** (a forma do topo macro, hoje ausente); OU
- **hipótese visual específica do Cris** transformada em **predicado causal** testável (ex.: "2º teste de máxima",
  "sem pullback recente a demanda", "1º pullback após novo ATH").

Comunalidade provável dos 7 = **near-macro-top** (clusters 2020-03 / 2021-11 / 2022-03 que precederam quedas) =
auction-irredutível à entrada — re-confirma o arco do macro engine.
