# L1 — Filtro discriminador winner/loser v1 (anti-extensão) — pré-registro READ-ONLY (2026-06-16)

**Objetivo:** separar winners de losers nos 63 candidatos (38 BOTH + 25 NEW_ONLY) sem look-ahead, só RAW, mantendo **100% dos winners/monumentais** (policy do Cris). NÃO implementado em produção — pré-registro para validação OOS.

## Método (sem look-ahead, só RAW)
- Universo: 63 candidatos da comparação OLD vs NEW (`l1_old_vs_new_regime_comparison.csv`).
- Outcome no RAW: entry=close do bar; **SL estrutural** = low da zona OB −0.1ATR; **target +3R**; walk forward ≤60 barras. **winner = bateu +3R (TARGET)**; loser = bateu SL (−1R); scratch = time-exit. (Definição corrigida após DA — antes contei partials como winner = ERRADO.)
- Features **at-entry, causais** (conhecidas no close do bar i, só barras passadas): `ret5` (retorno 5 barras), `ext_ema_atr` (extensão acima da EMA21 em ATR), `zone_w_atr` (largura da zona OB em ATR), `dist_zone_atr` (quão acima do topo da zona entrou). Nenhuma usa barra futura.

## Resultado (in-sample)
| Filtro | n | TARGET | STOP | winners cortados | sumR |
|---|---|---|---|---|---|
| BASELINE | 63 | 17 | 39 | — | +18.2 |
| `ret5<=0.0142` | 58 | 17/17 | 34 | 0 | +22.3 |
| `+ ext_ema_atr<=2.95` | 55 | 17/17 | 34 | 0 | +22.3 |
| `+ zone_w_atr>=0.6` | 52 | 17/17 | 31 | 0 | +25.3 |
| **`+ dist_zone_atr<=1.81` (stack)** | **49** | **17/17** | **29** | **0** | **+27.4** |

- **0 winners e 0 monumentais cortados** (policy respeitada). Corta 10 losers.
- NEW_ONLY (25) reconciliado sob definição correta: **4 TARGET / 18 STOP / 3 scratch, sumR −4.8** (líquido negativo — alinha com a leitura visual do Cris ~2W/23L; minha contagem anterior de 6W estava inflada por partials).

## Tese (Auction Theory — por que é principled, não só fit)
Não entrar continuação **esticada**: se o preço já correu >1.42% em 5 barras (`ret5`), está muito acima da EMA21 (`ext_ema`), ou entrou muito acima do topo da zona (`dist_zone`), a continuação tende a falhar (compra no clímax). Zona fina (`zone_w`<0.6ATR) = estrutura fraca. Coerente com os PDFs do Leonardo (chegada esticada → falha).

## ⚠️ DA — caveats obrigatórios (não promover sem isto)
1. **In-sample / overfitting:** os 4 thresholds foram fixados nos extremos dos 17 winners destes 63 → calibração, NÃO validação. **Exige OOS** (outros anos / sub-janelas / cross-asset) + Bonferroni antes de qualquer promoção. O stack de 4 condições é o mais overfitado; o **`ret5<=1.42%` sozinho** (cobre 5 stops, +22.3R) é o mais defensável/principled.
2. **n pequeno:** 63 total, subset 49. Poder estatístico baixo.
3. **Outcome é exit-defined:** winner/loser sob SL-estrutural+3R-fixo. A L1 real usa V_stair → a partição pode mudar. Revalidar sob o exit real.
4. **Erro de leitura corrigido:** "winner" = target-hit (não partial). DA pegou; recomputado.

## Próximo passo (sem tocar produção)
Validar OOS: rodar o mesmo filtro em janela/ativo independente; se segurar (mantém winners, corta losers), então propor como gate-extra da L1 — com autorização. Hoje fica como pré-registro.

_Script: `discriminator_search.py` (read-only sobre RAW; só lê). Nenhuma produção tocada._
