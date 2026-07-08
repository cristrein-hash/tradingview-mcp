# L2/BPT — Causal Selector of the Approved 17 · Formalization

**Cris 2026-07-08.** Formalização da regra causal que seleciona os 17 trades da estratégia L2/BPT trend-exit oficial. Research-only, não produção. Script standalone: `research/l2_bpt_causal_selector.py` (implementa a regra independentemente, não chama `phase48.keep`).

## Status
`SELECTOR_FORMALIZED_PENDING_FORWARD_VALIDATION` · **DA: `SELECTOR_CAUSAL_BUT_IN_SAMPLE_FIT`** · `NOT_PRODUCTION`.

> **CORREÇÃO PÓS-DA:** a causalidade está **provada** (0/17 na truncagem FSM ≤bi, 0/17 leak, outcome-blind), MAS a robustez da sensibilidade abaixo estava **sobre-afirmada** — ver §Sensibilidade (correção) e o doc DA `..._SELECTOR_17_DA_20260708.md`. A formalização é uma **descrição causal limpa dos winners in-sample**, não evidência de edge forward. Taxa real de seleção = **17/128 = 13%** (não 7% — 117 sinais pré-2023/segmento-0 não têm rótulo de regime e caem antes).

## A regra em português simples
Sobre cada **sinal-base L2/BPT** (reversão estrutural BOS/CHoCH numa zona de demanda — dá entry/SL/risco), mantém-se o trade **só se o preço estiver com desconto no lugar que o regime favorece**:
- **BULL** → entry no **terço superior do range do regime anterior** (reteste do topo/breakout numa alta).
- **RANGE** → entry no **terço inferior do range atual** (fundo da balança).
- **BEAR** → entry no **terço inferior da base de acumulação** de onde partiu a subida que o bear corrige (capitulação FUNDA, não repique raso).

Seleciona **17 de 245** sinais-base (~7%). Por regime: BULL 6 · RANGE 10 · BEAR 1.

## Pseudocódigo
```
para cada sinal-base (bar_idx bi, entry) na régua L2/BPT:
    idx = segmento de regime que contém t=T[bi]         # detector causal
    se idx é None ou idx==0: pular
    s = segs[idx]; prev = segs[idx-1]                     # regime atual e ANTERIOR (fechado)
    amp = prev.hi - prev.lo
    ztop  = [prev.hi - amp/BAND , prev.hi]                # BAND=3
    zdeep = bear_deep(idx, MIN=15, WIN=180d, BAND=3)      # base de acumulação anterior ao bear
    rmin,rmax = min L, max H de s.start .. bi (só barras ≤ entry)
    pos = (entry - rmin)/(rmax - rmin)
    KEEP = (regime BULL e entry∈ztop) ou (BEAR e entry∈zdeep) ou (RANGE e pos<0.34)

bear_deep(idx): lo_min = menor lo dos segmentos significativos (bars≥MIN) nos WIN dias antes do bear;
                amp = maior range desses; zona = [lo_min, lo_min + amp/BAND]
```

## Fonte / código original
- Regime: `config.paths.causal_segments()` (segmentos causais phase10). RAW 4H: phase10 `T/H/L`.
- Sinais-base: `l2_bpt_regua_structural.csv` (L2/BPT sobre RAW). **Zero SLIM/proxy.**
- Regra original: `regime_turnstate_engine/validation/phase48_bear_deep_zone.py` L20-46 (o selector re-deriva independentemente).

## Causalidade — ✅ ex-ante (zero look-ahead)
Todos os inputs conhecidos à entrada: rótulo de regime em t (detector causal, DA-verificado online); `hi/lo` do segmento **anterior** (fixado no seu fecho, antes do atual); `pos` só de barras `≤ entry`; `zdeep` só de segmentos `j < idx` (antes do bear). Nada usa o futuro.

## Lista dos 17 selecionados
`results/l2_bpt_causal_selector_selected17.csv` (bar_idx · entry · regime · pos · zona · R). Reproduz **byte-a-byte** os 17 canónicos (`l2_bpt_17_trades.csv`) — assert fail-loud PASS.

## Sensibilidade dos parâmetros (∩ com os 17 canónicos)
| variação | N | ∩17 | +/− |
|---|---|---|---|
| **BASELINE (3, 0.34, 15, 180)** | 17 | 17 | +0/−0 |
| BAND amp/2 (banda + larga) | 17 | 17 | +0/−0 |
| BAND amp/4 (banda + estreita) | 15 | 15 | +0/−2 |
| POS_THR 0.30 | 17 | 17 | +0/−0 |
| POS_THR 0.40 | 24 | 17 | +7/−0 |
| MIN 10 / 20 barras | 17 | 17 | +0/−0 |
| WIN 120 / 240 dias | 17 | 17 | +0/−0 |

**Leitura (CORRIGIDA pós-DA — a minha 1ª leitura estava otimista demais):** a sensibilidade é **evidência FRACA**, não prova de robustez. *Alargar a zona (`amp/2`, `POS_THR 0.40`) é quase-tautológico* — é um superset, não pode largar um kept → "17 iguais" carrega ~zero informação. *A direção informativa — estreitar — QUEBRA:* `amp/4` tira 2, um deles um **winner material (+4.19R)**; os entries BULL sentam-se **perto da borda `amp/3`** (não fundo na zona), por isso `amp/4` os corta. `POS_THR 0.40` +7 inclui 3 losers limpos → a fronteira 0.34 faz trabalho **outcome-seletivo**, não só estrutural. **Conclusão honesta: a estabilidade não distingue edge-real de fit-in-sample; os params foram calibrados para acertar os 17. Sensibilidade ≠ validação forward.**

**Forward canary:** kept por ano = 2023:6 / 2024:4 / 2025:7 / **2026:0** (de 18 sinais 2026). A regra evita o mau 2026 (encorajador) mas **0 kept = 0 confirmação forward**. **Ramo BEAR = n=1 (vazio, não validável).** Fonte de regime = `/tmp/causal_segments_v10.json` (temp regenerável, não versionado — reproduzível mas frágil).

## Caveats
- Sensibilidade ≠ validação forward. Os parâmetros são estáveis mas ainda **calibrados na mesma janela histórica**; o gate real = **out-of-sample / forward** (janela virgem ou próximas ops live do Cris).
- BEAR n=1 (só 1 trade nesse ramo) → o ramo BEAR da regra é estruturalmente correto mas estatisticamente vazio.
- Este selector formaliza a SELEÇÃO; os parâmetros de execução/risco sobre a seleção (gap, exposição) são bloco à parte (`..._EXECUTION_RISK_...`).

## Status / próximo passo
`SELECTOR_FORMALIZED_PENDING_FORWARD_VALIDATION`. Pronto para forward-validation (não iniciado; requer autorização). Não produção.
