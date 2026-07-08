# XAU 15M LONG · N96 Entry Engine · User Approval

**Cris 2026-07-08.** Registo oficial de aprovação da estratégia atual.

## Decisão do Cris
`XAU_15M_LONG_N96_ENTRY_ENGINE = USER_APPROVED_NOT_PRODUCTION`. Cris aprovou a estratégia atual como está.

## Status
`USER_APPROVED_NOT_PRODUCTION` · `NOT_PRODUCTION` · `NO_RUNTIME` · `NO_TELEGRAM` · `NO_AUTO_TRADING` · `NO_STRATEGY_RULES_WIRING` · `NO_MONITOR` · `NO_BROKER`.

## Escopo aprovado — componentes INCLUÍDOS
1. **N96 entry engine** atual — pullbacks markup/demanda, 96 entradas, 52W/44L, alvo fixo 3R, +112R. Reproduz byte (`entry_engine_master_20260707.py` + `agent_ctx_kit.py`).
2. **Filtro intra-BEAR capitulation:**
   - dentro do regime **BEAR v5 hour-causal** (`regime_hourcausal`, zero look-ahead);
   - **SKIP se `1D_px_vs_ema >= 0`** (preço no/acima da EMA 1D = repique raso, não capitulação);
   - corta **13 trades = 13 losers / 0 winners**;
   - impacto **+4R a +13R** conforme detector (v5 hour-causal +13 · day-causal +11 · v2 +4);
   - **DA = `PROFITABLE_BUT_FRAGILE`**; feature-search null P=0.005; stale-free; não é skip-all-bear (mesma feature +78R fora do bear / −13R dentro).
3. **RANGE / distribuição:** **não gate** — `REVIEW_LAYER` / gestão / size-down apenas.
4. **BULL-excess RSI-HTF (~80):** **não gate** — `REVIEW_LAYER` apenas (perm-P=0.028 mas corta 3 winners → flag size-down, não auto-skip).
5. **D-bear adicional:** **nenhum gate adicional aprovado** — intra-BEAR já basta; cortes +R in-sample morrem a multiplicidade (mining-null best +6R P=0.40); deep-bear/faca = **review fraco**, não auto-skip. Caveat: 4/8 deep-losers em Jun/2026 sobre EMA 1D congelada.
6. **Gestão humana preservada:** **#24, #32, #64, #77** não são corte automático (BE / timing / quase-winner / gestão).

## Componentes EXPLICITAMENTE NÃO incluídos
Produção · runtime · Telegram · auto-trading · wiring em `strategy_rules` · monitor · broker · SHORT · alteração de RAW · aplicação em Supabase.

## Lista dos 13 cortados intra-BEAR
#24, #25, #55, #56, #57, #58, #59, #66, #67, #79, #83, #84, #85 — todos losers, 0 winners, 0 stale. Detalhe: `XAU_15M_N96_INTRA_BEAR_CUT_TRADES_20260708.md` + `results/n96_intra_bear_cut_trades.csv`.

## Review-layers (não gates)
- **RANGE:** perseguir spike/falso-rompimento na balança = flag; não sobreviveu como gate (perm-P=0.103, N=7). Hipótese registada.
- **BULL-excess:** compra em RSI-HTF ~80 no topo = flag size-down (perm-P=0.028) mas corta winners → review, não gate.
- **D-deep (faca):** dip fundo quieto + range estreito + sem demanda-4H = risco de faca = review fraco; não sobrevive multiplicidade como gate.
- **Achado metodológico:** o eixo robusto é **EXCESS de RSI-HTF** (loser compra exaustão), partilhado por BULL e BEAR a níveis diferentes. Indicadores só discriminam após leitura estrutural (regime + perna) — cruzamento global é estéril.

## Caveats
- N pequeno por regime; o filtro intra-BEAR é `PROFITABLE_BUT_FRAGILE` (magnitude +4…+13R).
- **Daily/4H HTF primitives congelam 2026-05-24 / 06-09** → o filtro não dispara live até extensão RAW; parte da evidência 2026 monta em referências stale.
- Forward nas ops live do Cris = árbitro final.
- Não produção. Não alterar strategy_rules. Não usar como SHORT.

## Próximos passos possíveis (NÃO iniciados)
- Estender htf_1D/htf_4H pós-2026-05-24/06-09 e re-validar filtro + deep-bear.
- Forward-ledger nas ops live.
- Decidir adoção operacional dos review-layers (size-down).
- XAU 15M SHORT = estratégia futura separada (nunca espelho).
- D-bear = fechado por agora (intra-BEAR basta).
