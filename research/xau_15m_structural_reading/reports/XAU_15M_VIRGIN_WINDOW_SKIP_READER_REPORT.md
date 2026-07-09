# JANELA VIRGEM 2024-25 · BEAR-ONLY SKIP · ONE-SHOT — REPORT FINAL (2026-07-09)

> **VERDICT (pós-DA): `PARTIAL_S2A_ONLY_REPLICATES` — DIRECTIONAL_ONLY · SEM SUPORTE ESTATÍSTICO ·
> ESTRUTURALMENTE UNDERPOWERED.** Não-PASS: C_OR mata 2/5 winners (false-skip 0,40). Não-FAIL:
> S2a manteve o sinal; S3 = no-test. One-shot cumprido; zero tuning; prereg
> `..._VIRGIN_WINDOW_2024_25_PREREG.md`.

## Setup verificado
- **Consistência do gerador RAW-only: 166/166 match exato por timestamp** na janela conhecida —
  plausível, não bom-demais (DA comparou ATR/EMA primitives vs F0 em ~49,7k barras: mediana e p95
  da diferença = 0,0; mesmas barras + mesmas fórmulas).
- Universo virgem congelado ANTES de outcomes: 136 candidatos (86 BULL / **17 BEAR** / 33 RANGE);
  BEAR resolvidos 17 = **12L/5W** (loser rate 70,6%). Flags S3 do código pinado (sha verificado).
- **Virgindade confirmada ao nível de outcome**: DA varreu todos os CSVs de outcomes do programa —
  0 rows na janela. Nível de preço: NOT_FULLY_VIRGIN (declarado). **Correção factual (DA):
  primitives 2024-25 EXISTEM (blocos 2024-05-25+) — a escolha RAW-F0 mantém-se pela ORDEM do Cris,
  não por inexistência.** Macro v5 gate o universo BEAR (nível seleção, mesma máquina de sempre).

## Resultados (17 BEAR virgem)
| composite | skips | L/W | precisão | false-skip |
|---|---|---|---|---|
| **A S2a** | 5 | **4L/1W** | 0,80 (base 0,706) | 0,20 |
| B S3 | 2 | 1L/1W | 0,50 | 0,20 |
| C OR | 7 | 5L/2W | 0,71 | **0,40 ← exclui PASS** |
| D AND | 0 | — | — | overlap S2a∩S3 = **0** (disjuntos em virgem; AND intestável) |

## Leitura estatística honesta (edits do DA)
- **S2a: hipergeom P(≥4L em 5)=0,528** — lift real = +0,47 loser vs acaso (esperado nulo 3,53).
  Direcional, nunca "replicado" estatisticamente. E a 1 winner cortada **quebra a perfeição
  13L-22L/0W** das bases anteriores — registado.
- **Power estrutural: nem um skip PERFEITO 5/5 daria P<0,05** (5/5=0,128; 6/6=0,075; só 7/7=0,041).
  O teste nunca poderia confirmar S2a nesta janela — caveat obrigatório.
- **Null cluster-aware DEGENERADO (falha minha, apanhada pelo DA):** com blocos semanais de tamanhos
  [1,2,3,3,4,4], o esquema troca-entre-blocos-de-igual-tamanho tem **4 assignments possíveis**;
  P exatos: B=0,5 · C=0,25; **piso alcançável = 0,25 — o null nunca poderia dar significância**; e o
  fallback "shuffle interno" estava declarado em comentário mas NÃO implementado (desvio
  código-vs-declarado, registado). Mitigação: a hipergeométrica (anti-conservadora) também é
  não-significativa em tudo (0,528/0,927/0,686) — "sem suporte estatístico" é robusto pelos dois lados.
- **S3: `UNTESTED_IN_VIRGIN_WINDOW`, não "weak/overfit"** — 2 disparos apenas; os 17 BEAR
  concentram-se na correção CURTA de nov-dez/2024 (6 semanas, dentro de bull secular); a escada
  ndesc≥2 (≥3 picos) é assinatura do bear ESTENDIDO tipo 2026 — regime plausivelmente ausente.
  n=2 não distingue overfit de ausência. **Pelo fallback do prereg §6: S3 encerra como CALIBRAÇÃO**
  até aparecer bear estendido virgem (o próximo bear real é o árbitro).
- Desvio de artefacto menor: `frozen.json` congelou IDs mas não os flags per-candidato (prereg
  dizia IDs+flags); flags determinísticos/recomputáveis do código pinado — risco ~nulo, anotado.

## Consequência (a regra que TU definiste no prereg)
- **S2a/capitulation preserva-se como filtro contextual** — sustentado pela validação
  out-of-population anterior (22=22L/0W) + direção mantida em virgem; a janela virgem não o
  promove nem o derruba (sem power).
- **S3 = calibração encerrada por agora** — sem bear estendido virgem, não há teste possível.
- **Nenhum composto aprovado.** Árbitro final = próximo bear real / forward.

## Confirmação negativa
One-shot único · zero ajuste pós-resultado · sem entry · sem produção/Telegram/broker/runtime/chart
· BULL/RANGE não tocados (86+33 candidatos virgem ficam disponíveis para blocos futuros SÓ com
prereg próprio).
