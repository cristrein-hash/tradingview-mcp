# XAU 15M BigBeluga+NAS — MAPA DE FEATURES (fonte RAW exclusiva)

Régua: fonte canônica = RAW gz (`build_causal_primitives.py` → `primitives/*.json`). Zero dados secundários.
Causal: NAS/SMC/OB consumidos com **SHIFT1** (repintam). Candidato (setup) = evento NAS confirmado dentro de uma
zona Custom OB (=BigBeluga proxy) viva, de polaridade casada (LONG∈DEMAND, SHORT∈SUPPLY). Entrada = close do bar.

Auction Theory: zona = value area institucional; aceitação-vs-rejeição = núcleo; "reação estrutural verdadeira" =
iniciativa que rejeita o valor e abre perna; "absorção temporária"=aceitação que consome a zona (loser); fluxo
operacional 15M = direção da iniciativa vigente; let-run = re-leilão até a value area oposta.

## A. ZONA (identidade da value area) — registro de zonas (all_boxes id)
| feature | fonte RAW | Auction / discriminador |
|---|---|---|
| zone_type | all_boxes.text SUPPLY/DEMAND | polaridade da value area |
| zone_width_atr | (high−low)/ATR | risco; zona estreita→R maior (winner #4) |
| zone_age_bars | born_t→entry | frescor/relevância |
| zone_virgin | OHLC nunca entrou desde born_t | virgem>mitigada (disc. região virgem) |
| zone_mitig_count | nº toques OHLC desde born_t | retestes ↑ → rejeição ↓ (loser) |
| zone_origin | geometria (fundo de alta=DEMAND / topo de baixa=SUPPLY) + idade | origem/idade da região |

## B. INTERAÇÃO — aceitação vs rejeição (NÚCLEO) — OHLC dentro da zona
| feature | fonte RAW | Auction / discriminador |
|---|---|---|
| penetration_pct | (close vs high/low da zona) | 0-50%=rejeição (winner) / ~75%=consumo (loser) #4 |
| bars_in_zone | nº velas dentro até entrada | 2-5 rápido(win) / 7+ preso(loser) #5 |
| acceptance_beyond_mid | close aceitou além de 50% da zona | aceitação=zona falhando |
| arrival_velocity_atr | deslocamento N barras pré-zona /ATR | impulsiva atravessa(loser) vs desacelera(win) #7 |
| nas_dist_ema_atr | study NAS_DISTANCE_FROM_EMA_ATR | esticamento no sinal |

## C. NAS (qualidade do sinal) — eventos NAS first-appearance
| feature | fonte RAW | Auction / discriminador |
|---|---|---|
| nas_count_in_zone | nº NAS dir-casada na zona | cluster ↑prob reação, NÃO magnitude #6 |
| nas_cluster_span | janela do cluster | densidade |
| nas_before_touch | NAS antes de penetrar a zona | fraqueza: pullback≠reversão #6 |
| nas_polarity_match | dir NAS = polaridade zona | coerência |

## D. FLUXO OPERACIONAL / ESTRUTURA (regime) — SMC + eventos Custom OB
| feature | fonte RAW | Auction / discriminador |
|---|---|---|
| op_flow | sequência BOS/CHoCH SMC (HH/HL vs LH/LL) | tendência OPERACIONAL 15M (≠macro) #3 |
| setup_vs_flow | continuação(a favor) / reversão(contra) | continuação=maiores R; reversão=precisa absorção |
| last_struct_event | último BOS/CHoCH + direção | estado estrutural |
| recent_choch_dir | CHoCH recente na direção do setup | gatilho de mudança |

## E. PÓS-ENTRADA / DESLOCAMENTO (o discriminador #1/#2 — lado-saída, p/ label+let-run, NÃO filtro de entrada)
| feature | fonte RAW | uso |
|---|---|---|
| mae_atr, mfe_atr | OHLC pós-entrada | drawdown~0=winner #10 |
| displacement_struct | BOS na direção do trade pós-entrada | reação estrutural verdadeira vs absorção #2 |
| bars_to_struct_break, duration | OHLC + SMC | runner 1-3+ dias (let-run #13) |
| zone_left_fast | saiu da zona rápido | winner deixa a zona; loser fica preso #1 |

## F. CICLO DE VIDA / REENTRY (gestão) — persistência da zona (id)
| feature | fonte RAW | uso |
|---|---|---|
| zone_persisted_after_stop | id ainda vivo após stop | "BB permaneceu" = não-invalidado #8/#11 |
| choch_after_stop, pullback_after_stop | SMC + OHLC pós-stop | máquina REENTRADA: STOPADO_OBS→REENTRADA_CANDIDATA |
| zone_removed | id sumiu do all_boxes | INVALIDADO (cancela hipótese) |

## G. CONTEXTO (secundário)
RSI (study), hora/sessão + dia-da-semana (bar time), bubbles BUY/SELL (pine_shapes_bubbles activations_per_plot) como confluência. HTF = contexto, não gate (insight "15M carrega quase toda a info").

## Camada de SELEÇÃO + RISCO (alvos: 1-3 ops/sem, ≤12/mês, WR50%, DD FundedNext, streak≤3)
Seleção usa A–D + G (entry-side) para FILTRAR a poucos setups/semana; E–F para exit/reentry. Espelha o 4H: seleção =
risk-shaping (corta clusters de loss → streak≤3, DD baixo); let-run (E) = expectancy. NÃO perseguir gatilho fino —
edge mora no pós-entrada + contexto de fluxo. Validação dentro dos 8 blocos (sub-janelas/jackknife/null), sem OOS/cross-asset.

Status: primitivas RAW construídas+validadas (`build_causal_primitives.py`). Próximo: Stage-B (detector de setup +
cálculo das features A–G) sobre `primitives/*.json`.
