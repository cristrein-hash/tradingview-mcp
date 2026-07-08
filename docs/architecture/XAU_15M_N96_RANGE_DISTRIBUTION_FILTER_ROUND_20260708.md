# XAU 15M LONG · N96 · Range/Distribution Filter Round (Auction-Theory)

**Cris 2026-07-08.** Research-only · RAW-first · LONG-only · NO production/Telegram/runtime/chart/plot/RAW-write/Supabase-write. **O ciclo N96 NÃO está fechado** — o filtro intra-BEAR é uma camada; esta rodada ataca RANGE/BULL.

## 1. Executive verdict (DA fechada — `..._RANGE_DISTRIBUTION_FILTER_DA_20260708.md`)
**Corrigido pela DA (nulls de permutação intra-regime, 20k).** O princípio de auction é real e causal (o loser compra **excess/exaustão** = lugar errado da estrutura), MAS o "três assinaturas distintas" que caracterizei é **parcialmente refutado**:
- **BULL = REVIEW-LAYER real** ✓ — `excess_rsi_htf` (loser compra RSI-HTF ~80 no topo) sobrevive ao null (perm-P=**0,028**, precisão 0,62 = 1,8× base). Mas corta 3 winners (#22,52,54) → flag de size-down, **não gate**.
- **RANGE = NÃO adotado** ✗ — a assinatura displacement/chase **não sobrevive** ao próprio null (perm-P=**0,103**; maxbar 0,082) a N=7 losers. Hipótese registada, sub-potenciada, **não** discriminador.
- **Unificação (DA):** é **UM eixo — EXCESS de RSI-HTF** — partilhado por BULL e BEAR a níveis diferentes (não distinto entre si como afirmei); RANGE não tem eixo próprio robusto neste N.
Zero resample/SLIM/fonte contaminada. **Ficam de pé: BULL-excess review-layer + filtro BEAR já aprovado. RANGE precisa mais episódios (extensão RAW).**

## 2. Lista dos 13 cortados intra-BEAR
Ver `XAU_15M_N96_INTRA_BEAR_CUT_TRADES_20260708.md` + `results/n96_intra_bear_cut_trades.csv`. 13 losers / 0 winners / 0 stale. Regra: em BEAR-v5-causal, SKIP se `1D_px_vs_ema>=0` (repique raso). Impacto +4…+13R por detector. USER_APPROVED, NOT_PRODUCTION.

## 3. Mapa corrigido dos 44 losers (reclassificações do Cris)
`results/n96_loser_family_map_corrected.csv`. **C [22]:** #17,18,20,21,23,25,31,36,42,46,48,55,56,57,58,59,60,65,79,83,84,85 · **D [14]:** #27,49,50,66,67,68,69,80,86,87,89,92,93,94 · **R [4]:** #5,6,7,8 · **MGMT/não-filtrar [4]:** #24,32,64,77. Validações: #55-60=C · #58=C · #80=D · #24(BE)/#32(timing)/#64/#77(quase-winner)=MGMT.

## 4. Definição de famílias
- **C** = distribuição de topo / topo de range bear (auction: *excess/premium*).
- **D** = bear ativo (auction: *downtrend imbalanced*).
- **R** = range/chop neutro (auction: *balance*), só se não for distribuição bear.
- **MGMT** = recuperável por gestão humana (BE/timing) — não filtrar.

## 5. RAW/MTF source mapping
15M `primitives/` (source guard PASS) · 30M/1H `htf_primitives/XAUUSD_{30m,60m}_*` (RAW nativo, extractor validado) · 4H/1D `htf_primitives/htf_{4H,1D}` (RAW nativo). Todos com primitives + causal. **SVP = unavailable** (poc/vah/val NULL no dataset → excluído, não improvisado). **Daily congela 2026-05-24** (gap conhecido). Zero resample, zero Fractal-MTF, zero FaseD, zero Kaufman-ER.

## 6. Feature audit por auction theory (intra-regime, RAW/MTF)
Features causais: range-position (prémio/desconto) · balance-vs-imbalance (rotação SMC) · excess/exaustão (RSI HTF extremo) · supply overhead / clean-sky · demand room · displacement (aceitação vs rejeição) · absorção (bubbles) · volume relativo. `n96_range_distribution_filter_analysis.py` → `results/n96_range_distribution_filter_{results.csv,summary.json}`.

## 7. Resultado — ASSINATURAS DISTINTAS POR REGIME (o achado central)
| regime | assinatura auction do loser | discriminante (WIN vs LOSER) | AUC/sep |
|---|---|---|---|
| **BULL** | **excess/exaustão no topo da perna de alta** (comprou a distribuição) | `excess_rsi_htf` 71 vs **80** · displacement fraco · momentum 1H a rolar | 0,25 |
| **RANGE** | **perseguir spike/falso-rompimento na balança** (iniciativa absorvida) | `displacement_15m` 0,28 vs **1,22** · `maxbar_atr` 1,32 vs **2,15** | 0,25 |
| **BEAR** (ref) | **repique raso responsivo** (sem capitulação) | `excess_rsi_htf` 46 vs **60** · range estreito · alto na balança 4H | 0,46 |

**São três lógicas de auction diferentes:** *excess* (BULL) ≠ *iniciativa-falhada* (RANGE) ≠ *bounce-sem-excess* (BEAR). A mesma feature (`excess_rsi_htf`) inverte de papel: em BULL o loser é RSI-extremo-alto; em BEAR o loser é RSI-alto-mas-raso vs winner-fundo. **Confirma que a estrutura/regime é a chave** — só discriminam após a leitura estrutural.

### Quantificação (`results/n96_range_regime_signature_eval.json`)
- **BULL excess_rsi≥80:** corta 8 = 5 losers/3 winners, precisão 0,62, dR −4, null P=0,076.
- **RANGE maxbar≥1,8:** corta 7 = 5 losers/2 winners, precisão 0,71, null P=0,138.
- **RANGE displacement≥1,0:** corta 6 = 4 losers/2 winners, precisão 0,67, null P=0,269.

## 8. DA adversarial
Ver `..._RANGE_DISTRIBUTION_FILTER_DA_20260708.md`. Ataca: causalidade, distinção real das 3 assinaturas, se corta runners, hindsight, fonte, e classifica gate/review/management por regime.

## 9. Gate vs Review vs Management (leitura provisória, DA arbitra)
- **Gate automático:** NÃO (cortar as assinaturas perde R — winners partilham contexto; nulls fracos).
- **Review-layer (recomendado):** SIM — flags regime-específicos com precisão 0,62–0,71: (a) BULL "compra em excess RSI-HTF ~80 no topo"; (b) RANGE "compra a perseguir spike ≥1,8 ATR / displacement ≥1,0". Valor = revisão humana / no-chase, não corte cego.
- **Management-layer:** não testável aqui (só `out` binário +3/−1; sem MAE/MFE) — declarado, não inventado.

## 10. Próxima rodada
- Endurecer as assinaturas review-layer com N maior (extensão RAW pós-2026-05-24).
- Testar a regra RANGE "no-chase pós-spike" como timing de entrada (não gate) — o gap WIN 0,28 vs LOSER 1,22 em displacement é o candidato mais nítido.
- D (bear ativo) fica para rodada própria (não misturar com RANGE/distribuição).

## 11. Caveats
N pequeno por regime (BULL C=9, RANGE C+R=7); nulls fracos (review não gate); daily stale pós-2026-05-24; sem MAE ⇒ management não testável; **não produção, não strategy_rules, não SHORT, não confundir com filtro global (morto)**.

## 12. Próxima ação recomendada
Aprovar/ajustar as assinaturas review-layer; decidir se a regra RANGE no-chase-pós-spike entra como timing. Sem push sem autorização.
