# ASSINATURA DE DISTRIBUIÇÃO (topo-a-formar) — MANIFEST + PREREG (selado 2026-08-28, ordem Cris)

## Problema (medido, não inventado)
Semana 24-28/08: −6R em 8 sinais A1/A2; 5 losers subiram +0.9R a +3R antes de reverter = compra de pullback
DENTRO de distribuição. Nenhum guard atual cobre a fase-1 do topo (choch=fase-2 confirmada; sweep-reject=
vela 4H pontual). Na segunda 24/08 o mapa de liquidez JÁ mostrava BSL varrida sem progresso — hipótese: essa
assinatura é detetável CEDO e mecanicamente.

## Hipótese selada — assinatura DISTRIB ativa na barra i se, na janela K:
  d1. ≥2 CAPTURAS de BSL falhadas: high de swing anterior rompido E fecho de volta abaixo em ≤8 barras
      E sem aceitação (nenhum fecho ≥ high_varrido + 0.5×ATR depois da captura)
  d2. progresso líquido dos highs na janela < 1.0×ATR ("varre sem avançar")
Duas variantes (multiplicidade=2 declarada, zero sweeps de knobs):
  V15: swings/capturas no 15M, K=96 barras (24h) · V1H: swings/capturas no 1H, K=24 barras (24h)
Params fixados ANTES de correr: falha=8 barras · aceitação=0.5×ATR · capturas mín=2 · progresso=1.0×ATR.

## Teste (aprende TODAS as lições da série anterior)
- Base: censo A1/A2 do DETETOR REAL sobre RAW 15M canónico 2 anos (harness já validado: 816 A1 + 73 A2,
  identidade byte-exata). Unidade = episódio (gap 8 barras).
- Para cada sinal do censo: assinatura ON/OFF no momento da entrada (causal). Split e painel completo
  (N·WR·sumR·avgR·DD·retDD·streak·por-semestre) por grupo, custos 0/0.2/0.35R.
- NULL: 300 réplicas com flag aleatória da MESMA frequência-ON (a assinatura tem de bater flag aleatória
  na separação de WR entre grupos).
- A semana 24-28/08 que motivou = DESCRITIVA, não pontua (mesma regra dos 4 forwards no estudo L2).

## Gates de veredito (selados)
SUPORTADA se, em pelo menos uma variante: WR(ON) ≤ WR(OFF) − 12pp E sumR(ON) < 0 a custo 0.2 E
grupo OFF retém ≥70% do lucro total E bate o null E nenhum semestre inverte o sinal (jackknife).
SUPORTADA ⇒ proposta "distrib_guard" (família choch/sweep, mesmo wiring de envio LONG) + shadow forward
≥2 semanas ANTES de reter qualquer sinal — nunca produção direta. NÃO SUPORTADA ⇒ morre documentada.
DA adversarial obrigatório antes do relatório. Claims só via claims_ledger.jsonl.

## ADENDA (Cris 28/08, antes de correr): os gates acima ficam como REFERÊNCIA de leitura, NÃO como
## veredito automático. O estudo entrega o painel COMPLETO dos dois grupos (todas as métricas, ambas as
## variantes, null, semestres) e a decisão sobre se "presta" é do CRIS sobre a evidência inteira.
