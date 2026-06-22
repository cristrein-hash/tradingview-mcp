# XAU 4H L2/BPT — REENQUADRAMENTO DO ACHADO 843a913

**2026-06-22.** Correção de enquadramento obrigatória (Cris). O bloco 843a913 mudou uma medição importante, mas
NÃO resolve o problema central, e a conclusão "só exit importa / entrada inútil" é superficial e perigosa.

## 1. O que 843a913 PROVOU
- O `realR` capado (+3.9R) distorce: apaga a convexidade. Mesma entrada rende +84.2R capado vs +144.6R let-run
  custado — o cap destruiu ~45-65% da edge recuperável.
- A convexidade EXISTE no path (72 runners MFE≥5R, 30 monstros ≥10R, até +30R).
- O nó Outcome/Exit era uma **restrição real de MEDIÇÃO**.

## 2. O que 843a913 NÃO PROVOU
- **NÃO provou que a seleção não importa.** Provou que a entrada não tem alpha de TRIGGER vs random no mesmo
  regime — coisa diferente. A seleção de CONTEXTO (regime/auction) é exatamente o que não foi resolvido.
- **NÃO provou que a entrada não tem edge estrutural.** O teste foi trigger-vs-random; a leitura de contexto bom
  vs ruim continua aberta.
- **NÃO provou que tudo é beta.** Provou que a CONVEXIDADE bruta é beta; não que o contexto bom/ruim seja indistinguível.
- **NÃO resolveu o problema real:** winners skipados vs losers mantidos — bear-regime longs, bull pullbacks dentro
  de bear legs, range/top traps, false supply rejection in bull, supply-as-markup vs rejection, regime lag.

## 3. Nova formulação — DOIS gargalos ACOPLADOS
1. **Outcome/Exit** = gargalo de MEDIÇÃO (mede mal a convexidade) → calibrar.
2. **Macro/Regime/Auction Reading** = gargalo de SELEÇÃO (não distingue contexto bom do ruim com precisão
   automatizável) → refinar.

**Acoplamento:** corrigir só o exit → "long convexity beta" (resignação). Corrigir só a seleção sob target
errado → treinar filtro contra a métrica errada. O caminho é **duplo e coordenado**.

## 4. A META permanece
Automação de uma **leitura de mercado PERENE** — não só XAU, mas qualquer estratégia: identificar winner-que-é-skip
e loser-que-é-mantido por convergência estrutural causal. NÃO resignação a beta, NÃO human-review endpoint.
Exit calibrado é condição necessária (medir certo), não suficiente (a leitura segue sendo o alvo).
