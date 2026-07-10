# SPEC — CLASSIFICADOR CAUSAL DE CONTEXTO DO RETESTE (Etapa 1 corrigida)

> Ordem Cris 2026-07-10. STATUS: `SPEC_ONLY_NOT_CODED`.
> Objetivo: classificar o CONTEXTO do reteste ANTES de falar em defesa/reclaim.
> Saída: `BULL_PULLBACK · RANGE_BASE · BEAR_CAPITULATION · BEAR_BOUNCE_RASO · UNCLASSIFIED`.

## Limites (Cris)
- NÃO inventar feature nova · NÃO usar GT por data · NÃO usar outcome · NÃO codar antes de aprovação.
- Só peças já existentes: macro/regime · ciclo/perna A2 · profundidade 1D/S2a · estrutura acima/S3 ·
  tipo da região detectada. (+ D2 apenas no uso sancionado: veto contextual BULL topo sem pullback.)

## §1 Peças usadas (existentes, com fonte exata — NADA novo)

| Peça | Fonte pinada | Semântica congelada |
|---|---|---|
| P1 `macro_at(t)` → BULL/BEAR/RANGE | `f1_structural_leg_machine.py:154` | regime 1D estável + override 1H |
| P2 ciclo A2 (r=4) | `a2_detector_v2.build_v2` | direção UP/DOWN por barra; virada = retração ≥4·ATR do extremo |
| P3 S2a `px1d = (close − EMA21_1D)/ATR15` | `virgin_window_skip_test.py:75-100` | congelado: BEAR & px1d ≥ 0 = RASO (mesma orientação N96); px1d < 0 = profundo |
| P4 S3 `bounce_peaks` (K=1,5·ATR) + `ndesc` | `skip_family_discovery.py:58` (sha b749b7a) · j_hi = argmax high 384b | ndesc ≥ 2 = estrutura acima PRESSIONANDO |
| P5 região v2 | `a2_detector_v2.py` | kind BOTTOM/TOP · `conv_at` (PLT/convertido) · `known_at` · banda · `inv_at` |
| P6 D2 `pos384` | `d1d3_minimal_test.py:61` | posição do close na janela 384b — SÓ reportada (ver §5.c) |

## §2 Evento avaliado — RETESTE (definição mínima proposta)
Reteste de região R = primeira barra `t` com `LOW(t) ≤ R.hi` E `HIGH(t) ≥ R.lo`, onde:
- R é suporte válido em t: (BOTTOM ou TOP com `conv_at < t`) · `known_at < t` · não invalidada;
- o preço SAIU da região antes: existe ≥1 barra k, `known_at ≤ k < t`, com `LOW(k) > R.hi`
  (garante "voltou à região" — exclui o candle que cria a região e o rompimento).
Retestes subsequentes da mesma região: novo evento só após nova saída (LOW > R.hi).

## §3 Árvore de classificação (ordem obrigatória: família → validade → movimento → carácter)

**Passo 1 — família estrutural** = `macro_at(t)`:
- BULL → ramo BULL_PULLBACK · RANGE → ramo RANGE_BASE · BEAR → ramo capitulação/repique.

**Passo 2 — região válida PARA a família**:
- BULL: BOTTOM ou convertida (PLT). Ambas aceites.
- RANGE: apenas BOTTOM (base). [PONTO ABERTO b — meio/topo do range]
- BEAR: BOTTOM (inclui nascida do flush — maquinaria LATE_CAP existente).

**Passo 3 — o movimento até ela faz sentido** (só peças A2):
- `corrigindo` = ciclo A2 em **DOWN** no reteste → o preço desceu ≥4·ATR do topo do ciclo
  (= pullback proporcional; régua existente, nenhum threshold novo).
- ciclo ainda **UP** no toque = micro pullback / toque sem virada (= "topo esticado sem pullback
  proporcional" da resposta #5 do Cris).

**Passo 4 — corrigindo, capitulando ou repicando** (só BEAR; peças S2a/S3):
- `capitulando` = px1d **< 0** (profundo abaixo da EMA21 1D) **E** ndesc **< 2** (estrutura acima
  deixou de pressionar).
- `repicando` = px1d **≥ 0** OU ndesc **≥ 2** (raso, ou teto descendente ainda ativo).

**Classes finais**:
| Classe | Condição (todas causais em t) |
|---|---|
| `BULL_PULLBACK` | macro BULL · região válida (P2) · ciclo DOWN no reteste |
| `RANGE_BASE` | macro RANGE · região BOTTOM · ciclo DOWN no reteste |
| `BEAR_CAPITULATION` | macro BEAR · região BOTTOM · px1d < 0 · ndesc < 2 |
| `BEAR_BOUNCE_RASO` | macro BEAR · região BOTTOM · (px1d ≥ 0 OU ndesc ≥ 2) |
| `UNCLASSIFIED` | resto: warmup · BULL/RANGE com ciclo UP no toque (micro pullback) · região TOP não convertida · conflito |

## §4 Saída por reteste (sem defesa/reclaim, sem outcome)
`{t, região_id, kind, convertida?, macro, ciclo_dir, retrace_ciclo_atr, px1d, S3_ndesc, pos384(reportado), classe}`

## §5 PONTOS ABERTOS — parar e perguntar (não codados até decisão Cris)
- **(a) Definição de reteste**: 1 barra inteiramente acima da banda basta como "saiu"? Ou exigir
  distância/tempo mínimo?
- **(b) RANGE_BASE**: região BOTTOM válida em macro RANGE basta como "fundo real do range", ou
  precisa régua de posição (ex.: pos384 baixo) para excluir zona antiga sentada no meio do range?
- **(c) Veto D2**: proposta usa SÓ "ciclo não virou" como veto de topo (régua existente, sem número
  novo); pos384 fica apenas reportado. Cris quer também corte numérico em pos384? (exigiria
  threshold que não existe congelado — não invento).
- **(d) BULL com toque mas ciclo ainda UP**: classificar `UNCLASSIFIED` (proposta) ou classe própria
  `BULL_VETADO_TOPO` para ficar visível na revisão?

## §6 Gate (só após aprovação da spec; sem outcome)
Classificar os retestes que precedem os 32 fundos cobertos pelo v2 e comparar a classe causal com a
tua família (verificação apenas — GT NÃO entra em nenhuma regra). + plot canónico de um período
curto para teu visual.
