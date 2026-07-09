# PREREG — SKIP FAMILY DISCOVERY / LEDGER (2026-07-09)

> Decisão do Cris: NÃO composto ainda. Inventariar e medir ISOLADAMENTE as famílias de SKIP.
> "A pergunta não é 'qual composto usamos?' — é 'quais tipos de loser existem, e qual leitura
> contextual corta cada tipo sem matar winner?'. O composite vira consequência, não invenção."
> MEDIDORES contínuos, sem thresholds finais, sem regra, sem backtest novo, sem entry. RAW HD only.
> Leitura = READER; caminho = CRIS. NÃO RODA sem ordem explícita.

## Substrato de medição (congelado)
- **Primário: base causal live-fireable n=166** (universo honesto pós-reparação; outcomes 3R reais;
  regimes BULL/BEAR/RANGE) — cada candidato recebe TODAS as medidas S. Declarado: base estudada ⇒
  CALIBRAÇÃO; janela virgem 2024-25 reservada para validação futura.
- **Secundário (leitura, não estatística): 42 FUNDO + 4 INVALIDO + 6 C-losers** — verificação de
  coerência com as marcas do Cris.

## As 5 famílias (Fase 1 — inventário congelado)
**S1 — Top-buy / preço alto demais** (D2 confirmado; falta CONTEXTO para não cortar continuação):
medidas: pos384 · pos96 · dev/range ratio · **contexto: macro + idade/extensão da perna** (para
separar topo-de-range vs topo-de-perna-impulsiva vs pullback-raso-em-BULL vs fim-de-perna — o
"alto que continua" em BULL forte não pode ser cortado às cegas).
**S2a — Capitulação insuficiente (profundidade 1D)**: px_vs_ema1d_atr (feature do filtro VIVO).
**S2b — Capitulação insuficiente (âncora HTF)**: dist_prior_episode_bottom_atr ·
dist_prior_range_bottom_atr. **Pergunta central: S2b marca alguém que S2a não marca?** (matriz de
overlap; se ≡, âncora = redundante e declara-se).
**S3 — Estrutura acima ainda bear / reclaims falhados** (o próximo ouro; D1 falhou por olhar para
baixo): dos picos de bounce (máquina D3, causal): **nº de bounce-highs consecutivos DESCENDENTES**
antes do candidato · **fração de recuperação do último bounce vs anterior** (carácter mudou?) ·
tempo desde o último high reclaimed.
**S4 — Região velha sem autoridade** (lição B2): para a região A2 que "cobre" o candidato:
idade em barras · **nascida no episódio macro CORRENTE? (0/1)** · direção da perna no nascimento vs
agora · nº de violações próximas desde o nascimento. ("Distância à região" ≠ "autoridade da região".)
**S5 — Range mid/top** (régua 4H do Cris: range só presta no bottom): para candidatos em macro
RANGE: **posição dentro do episódio RANGE corrente** [bot→top] · candidato no terço inferior? ·
distância ao bottom real do range.

## Fase 2 — medir cada família ISOLADA (sem combinar)
Output por família: distribuição contínua por grupo de outcome (winner/loser) · losers marcados /
winners marcados / ambíguos (marcação DESCRITIVA: cláusulas já pré-registadas onde existem —
pos384>0,70 — e quartis declarados como descrição nas novas; NUNCA regra) · por família de
regime · **matriz de overlap entre S1-S5** (que losers cada família marca; redundância; falsos).
Perguntas finais por família: corta losers? mata winners? é redundante? é falsa?

## Fase 3 — composto SÓ DEPOIS (fora deste prereg)
Nasce do ledger: "S1 corta estes; S2 aqueles; S3 acrescenta X; S4 redundante ou não; S5 serve ou
ruído". Thresholds fixados nesse prereg futuro, nunca herdados dos quartis descritivos daqui.

## Outputs
`results/skip_family_discovery_ledger.csv` (candidato × família × medidas contínuas × outcome
[só na fase de audit] × marcações descritivas) · `results/skip_family_overlap.json` ·
report do READER + DA obrigatório + null episódico para separações observadas.

## Disciplina
Zero tuning pós-olhar (ajuste = novo prereg) · looks contados · UNSCORABLE declarados (caudas HTF) ·
manifest do bloco HTF_ANCHOR_OB cobre as fontes (15M/30M/1H + catálogo); base live-fireable
declarada como derived com sha ao rodar · sem entry/backtest/produção/chart.
