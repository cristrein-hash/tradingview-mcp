# RELATÓRIO FINAL — Filtro FVG-localização A1/A2 (2026-08-10)

**VEREDITO (Devil's Advocate = CONFIRMED): o filtro FVG-fill NÃO melhora o A1/A2 na população que o live
negoceia (BULL). E a premissa "mid-leg = entrada má" está INVERTIDA — as entradas early/perto-do-fundo são
as PIORES.** 2 auditorias adversariais executadas (v2 all-firings + v3 BULL-gate).

## Trajeto (3 amostras — a 1ª estava errada)
1. **v1 — 32 fundos GT curados:** A/B FAIL, mas DA #1 = **UNINFORMATIVO** (fundos curados não têm mid-leg;
   NULL aleatório ganha 92% = amostra trivial). Não testa a hipótese.
2. **v2 — TODOS os disparos MB3 (605, janela completa):** informativo, mas mistura BEAR contra-tendência
   (longs que o live nunca dispara). DA #2 = gate de regime é o passo decisivo.
3. **v3 — GATE BULL causal (Layer1 aprovado):** a população-live. **Decisivo.**

## Painel por regime (605 disparos resolvidos)
| Regime | N | WR | sumR | avgR | ret/DD¹ |
|---|---|---|---|---|---|
| **BULL (live)** | 266 | 37% | +130 | +0.49 | 7.65¹ |
| RANGE | 195 | 25% | +1 | +0.01 | ~0 |
| BEAR | 144 | 22% | −16 | −0.11 | neg |

**A1/A2 é uma estratégia de BULL** — lucrativa em BULL, breakeven em RANGE, negativa em BEAR. Confirma
(descritivamente) o gate de regime que o live já tem.

## FVG-fill dentro do BULL — NÃO discrimina
| | N | WR | avgR |
|---|---|---|---|
| FVG=SIM | 192 | 38% | +0.52 |
| FVG=NÃO | 74 | 35% | +0.41 |

Δ avgR = **+0.12 = 0.45σ (p≈0.65) = RUÍDO**. E é artefato de acoplamento: o FVG-fill é **mecanicamente
quase-sempre-verdadeiro para pullbacks fundos** (pb_low mais baixo enche mais gaps abaixo), e pullbacks
fundos ganham mais — o FVG anda à boleia da profundidade (FVG ⊥ outcome | profundidade), não é edge próprio.

## A premissa está INVERTIDA (o achado que interessa ao Cris)
Bandas de localização **dentro do BULL**:
- **early ≤40% bounce: WR 30% — a PIOR**
- mid 40-60%: WR 47% — a melhor
- late >60%: WR 41%

Ou seja: comprar **perto do fundo/cedo** é o que tem pior taxa; o "mid-leg" que o Cris queria evitar é
**melhor**, não pior. Um filtro que empurra a entrada para mais cedo/fundo (as opções A e B) vai na direção
ERRADA — por isso ambas falham:
- **A (gate bounce≤50 OU FVG):** mata 4 winners, sumR +130→+125 → **FAIL**
- **B (limite no FVG):** expira 50, mata 32 winners, sumR +130→+84 → **FAIL**

## Caveats (para NÃO exagerar — imposição do DA)
1. **A separação por regime é IN-SAMPLE** (partição post-hoc dos mesmos 605), não OOS. +130R BULL = resultado
   descritivo/de-desenho forte, **forward continua a ser o árbitro** (como o próprio prereg exige).
2. **Não tratar ret/DD 7.65, DD, streak como robustos** — janelas de outcome 480b sobrepõem-se (~9×), N
   efetivo independente ≪ 266. WR/avgR ok; dispersão/cauda otimistas.
3. **+130R NÃO prova "skill" do A1/A2** — não corri NULL BULL-only; em BULL, longs aleatórios também são
   fortemente positivos (NULL all-regime já dava +69R). Boa parte dos +130R é **beta de BULL**, não timing.
   (Não afeta o veredito FVG, que é beta-neutro: SIM e NÃO partilham o mesmo beta.)

## Conclusão para o Cris
A tua ideia era razoável mas os **dados não a suportam**: o FVG-fill não separa winners de losers no BULL
(0.45σ), e a intuição "mid-leg = mau" está ao contrário — o A1/A2 sofre mais nas entradas **fundas/cedo**.
**Nenhuma edição ao sinal live** (o resultado é: não adicionar o filtro). A tua vantagem discricionária de
proteger no FVG (sexta @4300) continua válida COMO GESTÃO TUA — só não vira regra mecânica que melhore o motor.

## Não tocado
Daemon A1/A2 live, `a1_causal_entry` mecânica, forward, Telegram, env-locks, prereg 14/07, GT, RAW. Zero
edição live. Scripts: `fvg_localization_study{,_v2,_v3}.py` + este relatório + prereg (git).

¹ ret/DD do painel — otimista por sobreposição de janelas (ver caveat 2).
