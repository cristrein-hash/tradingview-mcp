# XAU 15M LONG · N96 · Intra-BEAR Cut Trades

**Cris 2026-07-08.** Lista explícita dos trades N96 cortados pelo filtro intra-BEAR capitulation. Research-only. `NOT_PRODUCTION`.

## Regra
Dentro do regime **BEAR v5 hour-causal** (`regime_hourcausal`, ZERO look-ahead): **SKIP se `1D_px_vs_ema >= 0`**.
Interpretação (auction): em BEAR, preço no/acima da EMA 1D = **repique raso responsivo, não fundo de capitulação**.

## Os 13 cortados (`results/n96_intra_bear_cut_trades.csv`)
| # | timestamp | regime v5 | 1D_px_vs_ema | 1D_ema_trend | 1D_rsi | close_R | família | resultado | stale HTF |
|---|---|---|---|---|---|---|---|---|---|
| #24 | 2025-10-22 16:30 | BEAR | 1,39 | — | 59,8 | −1 | MGMT | LOSER | fresh |
| #25 | 2025-10-24 12:30 | BEAR | 4,53 | — | 59,3 | −1 | C | LOSER | fresh |
| #55 | 2026-01-29 20:30 | BEAR | 14,99 | — | 90,1 | −1 | C | LOSER | fresh |
| #56 | 2026-02-04 19:00 | BEAR | 3,53 | — | 56,1 | −1 | C | LOSER | fresh |
| #57 | 2026-02-10 02:00 | BEAR | 7,85 | — | 58,1 | −1 | C | LOSER | fresh |
| #58 | 2026-02-10 17:15 | BEAR | 9,48 | — | 58,1 | −1 | C | LOSER | fresh |
| #59 | 2026-02-11 16:30 | BEAR | 7,83 | — | 56,9 | −1 | C | LOSER | fresh |
| #66 | 2026-03-04 20:30 | BEAR | 5,18 | — | 52,5 | −1 | D | LOSER | fresh |
| #67 | 2026-03-11 00:15 | BEAR | 12,21 | — | 55,8 | −1 | D | LOSER | fresh |
| #79 | 2026-04-15 11:45 | BEAR | 6,78 | — | 54,4 | −1 | C | LOSER | fresh |
| #83 | 2026-05-06 13:30 | BEAR | 1,76 | — | — | −1 | C | LOSER | fresh |
| #84 | 2026-05-07 23:45 | BEAR | 3,10 | — | 49,8 | −1 | C | LOSER | fresh |
| #85 | 2026-05-13 15:15 | BEAR | 0,62 | — | 51,5 | −1 | C | LOSER | fresh |

- **Confirmação: 13 losers / 0 winners.** Todos com `1D_px_vs_ema >= 0` (repique raso). `close_R` fixo 3:1 (loser = −1R). `SB_net_R` = unavailable (N96 sem ledger de slippage).
- **Stale-free:** 0 dos 13 na cauda HTF stale (todos < 2026-05-24). Motivo uniforme: "repique raso em BEAR".
- Nota: #24 é MGMT (BE/gestão) mas foi loser real e cai na regra; não prejudica (era −1R).

## Impacto
+4R…+13R conforme detector (v5 hour-causal +13 · day-causal +11 · v2-sem-override +4). Sinal robusto (0 winners cortados em toda variante); magnitude frágil.

## Caveats
`PROFITABLE_BUT_FRAGILE` · N pequeno · 11/13 num único bear 2026 · daily congela 2026-05-24 (não dispara live até extensão) · `USER_APPROVED_NOT_PRODUCTION`.
