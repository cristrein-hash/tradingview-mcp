# Forward Candidate Matching — MVP Fase 2 (read-only, SEM R)

> Junta candidatos OPERACIONAIS da L1 com live signals XAU 240 do event store, por bar/símbolo/tf/janela. **Sem R, sem backtest, sem Telegram.** `signal_hash` (estratégico) e `ingestion_hash` (evento) NÃO são comparados entre si.

## Veredito: `insufficient_forward_sample`
- **`no_l1_candidates_yet`** — a L1 ainda não emitiu candidato OPERACIONAL forward (regime D-1 BEAR → todos os ciclos = `no_candidate`). Sem amostra para matar/confirmar match.
- O lado live está disponível e é mostrado abaixo (todos contam como `live_signal_no_strategy_candidate`).

## L1 (lado estratégico)
- Ciclos/avaliações lidos: **6**  ·  candidatos OPERACIONAIS: **0**
- Estados vistos: {'no_candidate': 6}
- Fontes lidas: l1_cycle.log  ·  parse errors: 0

## XAU 240 (lado live / event store)
- Sinais XAU tf=240: **140**  ·  range 2026-05-18T02:00:06.622513+00:00 → 2026-06-16T02:00:00+00:00
- Por indicador:
| indicador | sinais |
|---|---|
| Market_Bubbles | 57 |
| Custom_OB_Detector | 56 |
| RSI | 19 |
| NAS_TopBottom_Detector | 7 |
| (vazio) | 1 |
- Por provider:
| provider | sinais |
|---|---|
| PEPPERSTONE | 90 |
| (nenhum) | 50 |

## Classificação de match
- Janela tolerante: **250 min** (1 bar 4H + 10 min de folga), ancorada no `bar_ts` se persistido, senão no `ts` do ciclo (proxy documentado).
| classe | n |
|---|---|
| (sem candidatos) | 0 |
- `live_signal_no_strategy_candidate`: **140**

## Limitações
- **Amostra forward insuficiente:** 0 candidatos operacionais (regime BEAR). Match real só será exercitado em janela BULL.
- **`bar_ts` não persistido:** o `l1_cycle.log` grava o `ts` do ciclo, não o timestamp do bar do candidato. Quando houver candidatos, recomenda-se estender o log com `candidate_timestamp` (mudança de runtime — fora do escopo deste bloco read-only).
- **Log raso/rotacionável:** histórico forward começa com o scheduler recém-ativado; o log rotaciona.
- **Sem R / sem edge:** este bloco só localiza correspondência operacional, não mede resultado.

_Gerado por `match_candidates.py` (read-only). Não altera event store, journal nem runtime._
