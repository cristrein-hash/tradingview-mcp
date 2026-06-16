# L1 — Teste de SL ESTRUTURAL sobre os 34 trades do cenário C — IN-SAMPLE / READ-ONLY (2026-06-16)

**IN-SAMPLE optimization — NÃO é OOS, NÃO é validação, NÃO é edge. Produção intocada.** 34 trades fixos (cenário C: stack v1 + nas_dist SHIFT1≥1.31). Só o SL muda; target = entry + 3R (3×risco); walk ≤60 barras. winrate = % que bate +3R.

## Resultados (10 regras de SL testadas; todas causais — só barras ≤ bar i)
| SL rule | winrate(target) | sumR | avgR | PF |
|---|---|---|---|---|
| **v1 (SALVA): zona_OB_low − 0.1ATR** | 47% | +35.2 | 1.04 | 3.20 |
| zona_exata | 47% | +35.3 | 1.04 | 3.21 |
| zona − 0.5ATR | 38% | +27.1 | 0.80 | 2.59 |
| **★ max(zona_OB_low, swing6_low) − 0.1ATR** | **53%** | **+41.0** | 1.21 | 3.74 |
| swing6_low − 0.1ATR | 50% | +41.1 | 1.21 | 3.93 |
| swing3_low − 0.1ATR | 53% | +40.9 | 1.20 | 3.73 |
| swing10_low − 0.1ATR | 38% | +35.3 | 1.04 | 3.51 |
| entrybar_low − 0.1ATR | 38% | +18.0 | 0.53 | 1.86 |

## Regra nova escolhida: `SL = max(zona_OB_low, swing6_low) − 0.1×ATR`
Stop logo **abaixo do suporte estrutural mais próximo** (o maior entre o low da zona de demanda Custom OB e o swing low de 6 barras). Razão estrutural (não só WR): usa o nível causal que a própria entrada já referencia (zona OB) OU o swing recente, o que estiver mais perto → stop mais justo mas ainda atrás de estrutura real.
- **winrate 47% → 53%** · **sumR +35.2 → +41.0** · PF 3.20 → 3.74.
- **Monumental-safe VERIFICADO per-id:** #48, #51, #52, #54, #61 batem TARGET sob a nova regra (5/5), igual à v1. O SL mais apertado NÃO mata nenhum monumental.

## DA — caveats (não promover sem isto)
1. **Look-ahead: CLEAN** — todo input do SL (zona i-1, swing/ATR/low até bar i) é conhecido no close da entrada; walk é só outcome.
2. **Ganho de WR é LARGAMENTE MECÂNICO:** SL mais apertado → alvo 3R mais perto em preço → mais fácil de bater. Não é edge por si só. sumR maior (+41 vs +35) está **dentro do ruído** (n=34, ~2 trades de diferença; Wilson CI do 53% ≈ [37%,69%]).
3. **Selection bias:** 10 regras testadas in-sample; a melhor é estimador enviesado p/ cima. Escolhi pela **lógica estrutural**, não pelo WR.
4. **n=34 pequeno** — sem poder p/ distinguir as regras entre si.
5. **Exit-defined:** sob 3R fixo + tie-break stop-antes-de-target no mesmo bar 4H. Revalidar sob exit real (V_stair) + OOS.

## Conclusão
v1 (zona−0.1ATR) **salva como baseline**. Nova regra **max(zona,swing6)−0.1ATR** adotada para a plotagem/estudo: estrutural, monumental-safe, melhor WR/sumR in-sample. **Continua hipótese in-sample** — exige OOS antes de qualquer promoção a produção.

_Script: `sl_structural_test.py`. Plotagem re-feita com a nova regra._
