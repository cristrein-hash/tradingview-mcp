# XAU 4H L2/BPT — Atribuição de entrada: BOS/CHoCH NÃO é a fonte de edge

**Status:** `RESEARCH · FOUNDATIONAL · RECALLED 2026-06-18` · base para retrabalhar entradas.
Resgate do teste de atribuição (início da sessão; DA já executado então). Script `/tmp/attribution.py`.

---

## 1. O teste
L2/BPT (entrada = reclaim de polaridade após BOS/CHoCH) vs **LONG ALEATÓRIO casado por legpos bucket**, mesma mecânica (SL estrutural, target +3R, stop-first, time-stop 60, custo 0.10R). Pergunta: o gatilho BOS adiciona algo sobre estar comprado na mesma posição-da-perna?

## 2. Resultado
| legpos | L2/BPT | RANDOM-long | delta avgR |
|---|---|---|---|
| TODOS | n=264 WR46% avgR+0.24 | n=3153 WR40% avgR+0.12 | +0.12 |
| [75,101) | +0.40 (n=132) | +0.33 (n=1307) | +0.08 |
| [55,75) | +0.01 (n=43) | +0.07 (n=573) | −0.06 |
| [30,55) | +0.01 (n=46) | −0.08 (n=658) | +0.09 |

## 3. Veredito (DA)
- Deltas +0.12/+0.08 **< 1 SE** (t≈0.4-0.6) → **dentro do ruído**.
- No bucket alto (onde concentra o retorno) o aleatório já faz **+0.33 dos +0.40** → **~80% é legpos/drift**, não BOS.
- Sinais zigue-zagueiam por bucket (+0.09/−0.06/+0.08) = assinatura de efeito zero.
- **BOS/CHoCH NÃO demonstra edge sobre long-aleatório casado por legpos** — forma mais cara/menos frequente de expressar o mesmo drift (estar comprado alto-na-perna no bull).
- Ressalva: exit fixo +3R; valor em SL/caudas a média esconde. (SL contexto-demanda hoje aprovado melhora a base.)

## 4. Cruza com o achado consolidado
Features LOCAIS isoladas (supply/demand/bubbles/NAS/RSI/BOS) **não separam** (≈ base rate). Discriminador real = **posicional-estrutural (legpos + direção da perna macro)**. O BOS só seleciona longs alto-na-perna.

## 5. Implicação para o retrabalho de entradas
- **Não** refinar o trigger BOS (não é o edge).
- Retrabalhar entrada = achar o que adiciona edge **SOBRE "long casado por legpos"** (baseline a bater em qualquer teste de entrada).
- Componente de entrada já positivo: **remover entradas ruins** (F_STRICT topo/late = review flag).
- Hipótese de direção: **seleção/timing de entrada** (qual reclaim, quando NÃO entrar) e contexto posicional/macro > o evento BOS isolado. Sempre medir contra o long-aleatório-casado-por-legpos, não contra zero.

---

*Foundational. Sem produção, sem promoção. Próximo: bloco de retrabalho de entradas (pré-registro a aprovar).*
