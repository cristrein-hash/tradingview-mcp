# XAU 4H L2/BPT — READER: SEM-VA vs COM-VA (value-area real) — 2026-06-23

Comparação das releituras dos Clusters 1/2 SEM a value-area (pacotes `_postfix`) vs COM a value-area real
(`_withva`), ambas sobre o MESMO backbone causal. Pergunta: incluir a VA de volume (que estava disponível o tempo
todo e foi erroneamente bloqueada) melhora a leitura? SANITY_PROBE — diagnóstico, NÃO regra/gate/score.

## Placar combinado
| | CONFIRMED | MODIFIED | REFUTED | INSUFFICIENT |
|---|---|---|---|---|
| SEM-VA (_postfix) | 11 | 3 | 5 | 0 |
| **COM-VA (_withva)** | **12** | **3** | **4** | 0 |

**+1 CONFIRMED, −1 REFUTED. Melhora MARGINAL, não transformadora.** A VA redistribuiu a calibração mais do que a melhorou.

## Onde a VA MUDOU o veredito (por episódio)
| ep | sem-VA | com-VA | efeito | causa |
|---|---|---|---|---|
| 8878 | REFUTED | **CONFIRMED** | **VA ajudou** | IN_VALUE pullback lido certo (estado da VA) |
| 4401 | REFUTED | **CONFIRMED** | **VA ajudou** | ACCEPTING_ABOVE_VALUE → fuel (correu) |
| 1522 | MODIFIED | **REFUTED** | **VA atrapalhou** | IN_VALUE over-condenado (correu, lido undecided) |
| 8923 | CONFIRMED | MODIFIED | leve piora | — |
| 4926 | REFUTED | REFUTED | igual | gêmeo-runner; VA não salvou |
| 6887 | REFUTED | REFUTED | igual | VA deu falsa confiança |
| 5627 | REFUTED | REFUTED | igual | VA flipou p/ trap (correu); superfície era certa |
(demais: iguais)

## O que a VA realmente é (achado honesto)
1. **EIXO CAUSAL REAL — confirmado:** o par casado **3949 vs 3929** (mesmo dia/regime/superfície/indicadores) é
   separado SÓ pela VA e o outcome separa total (+6.62R vs +0.05R). Prova mais limpa de que a aceitação de valor é
   um eixo de verdade, não artefato.
2. **Braço bullish robusto:** `svp_state = ACCEPTING_ABOVE_VALUE` (regime-permitindo) → construtivo/corre — 5826,
   4401, 3949 (3/3 em macro-negativo); 4918 (bull). Resgatou 3949 do auto-trap-por-weekly.
3. **DOIS modos de uso da VA falharam (over-interpretação):**
   - **magnitude-como-exaustão:** "dist_poc grande acima do POC = sobre-extensão/topo" → INVERTIDO em bull (4926
     correu +18R; em alta, sair do valor = correr, não exaurir). **REFUTADO.**
   - **IN_VALUE/abaixo-POC = sempre-trap:** over-condena runners (5627 +5.96R, 1522 +5.65R lidos como trap/undecided).
     A VA virou veto onde devia ser só um fator. **REFUTADO como veto.**

## Classificação de lentes (com-VA)
| Lente | Status |
|---|---|
| VA como eixo causal (3949 vs 3929, par casado) | **WITHVA_CONFIRMED (prova mais limpa)** |
| `ACCEPTING_ABOVE_VALUE` (regime-permitindo) = construtivo | **WITHVA_CONFIRMED** |
| `dist_poc` grande = sobre-extensão/exaustão | **WITHVA_REFUTED** (invertido em bull) |
| `IN_VALUE`/abaixo-POC = trap como VETO | **WITHVA_REFUTED** (over-condena runners) |
| supply-WALL próximo ⇒ fade (do bloco anterior) | segue **QUARANTINED** (a VA não fechou; o STATE ajuda, a magnitude não) |

## Síntese
A correção valeu: a VA é um **eixo causal real e útil no estado ACCEPTING_ABOVE_VALUE** — e o caso 3949/3929 é a
evidência mais limpa de todo o programa. MAS a VA **não é bala de prata**: a melhora agregada é marginal (12C vs
11C), e as duas interpretações naturais (magnitude=exaustão; in-value=trap-veto) **refutam runners**. O eixo
informa, não decide. Nada vira regra/gate/score. O fechamento de FUEL-vs-WALL nos casos IN_VALUE continua aberto —
a VA-STATE ajuda mas não resolve sozinha; exige validação dentro do corpus (não como regra).
