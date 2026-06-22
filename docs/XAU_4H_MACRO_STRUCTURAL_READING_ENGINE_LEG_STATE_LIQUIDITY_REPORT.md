# LEG-STATE & LIQUIDITY-STRUCTURE SPECIALIST — RELATÓRIO DIAGNÓSTICO

**2026-06-22.** Diagnóstico/calibração. 62 = ensino. Sem outcome. Pivots causais. Engine/decisions/produção intocados.
**CONCLUSÃO: hipótese PARCIALMENTE confirmada (conceito certo) mas IMPLEMENTAÇÃO 4H REFUTADA (confound de escala).**

## Processado
62 trades · pivots fractais 3/3 causais (confirmação `p+k ≤ i`) sobre raw_features · SMC secundário · cruzamento condicional com camadas anteriores.
- leg_state: BULL_PULLBACK_WITH_HL_INTACT 14 · BULL_LEG_HH_HL 13 · RANGE_TRANSITION 12 · BEAR_LEG_LH_LL 11 · CORRECTIVE_BEAR_LEG 9 · BEAR_PULLBACK 3.
- liquidity_state: SWEEP_AND_RECLAIM 45 · LIQUIDITY_GRAB_REVERSAL_RISK 13 · NO_CLEAR_SWEEP 4.
- context_family: BULL 20 · RISK 33 · NEUTRO 9.

## Separação (FRACA) e anchor check
| | A-BULL/26 | B-RISK/18 | preserve anchor | block anchor |
|---|---|---|---|---|
| macro_v1 (D1 regime) | **20** | 5 | **12/14** | 0/1 |
| leg-state 4H | 12 | 8 | **7/14** | 0/1 |

leg-state 4H é **PIOR no preserve** (corta A-winners), marginalmente melhor no block. Não é melhoria.

## O confound de escala (o achado central, rigoroso)
**14 A-winners (bull bom) foram classificados RISK pela leg 4H. 12/14 são MACRO-BULL no D1** (regime_B v3_state=BULL,
combined>0) — ex.: S17/S26/S30/S31/S32/S34/S35 todos macro-bull. **A leg 4H capturou o PULLBACK LOCAL (que é
localmente bearish — um pullback faz lower-high/lower-low), NÃO a leg MACRO.** Um bull-pullback É um movimento
local de baixa dentro de um macro bull — e é exatamente nele que a L2/BPT entra. Logo a leg 4H conflaciona
"pullback local" com "macro bear leg".

## Síntese (convergência de toda a investigação)
1. **A leg MACRO vive no D1/weekly, não em fractais 4H.** Por isso o macro_v1 (que lê regime_B D1) preserva bull-run
   bem (20/26) e a leg-4H não. **O bom leitor de leg macro JÁ É o macro engine v1.**
2. **leg-state tem valor REAL mas específico:** bloquear robustamente longs em **macro-BEAR leg** (D1/weekly) — o maior
   bucket de losers. NÃO serve para separar o B-set late-top.
3. **O B-set late-top é auction-irredutível:** as B late-tops estão em macro-bull legs (iguais aos A pullbacks). Os
   ~3 macro-bear (T40/T42/T18) são blocáveis pelo regime D1; os ~10 late-top-em-bull são estruturalmente idênticos
   aos A pullbacks — o resíduo que o Cris já aceitou (o trap é feito idêntico à continuação, por design de liquidez).

## Camadas anteriores que ganharam/perderam utilidade
- **Macro engine v1 (D1 regime) = o keeper** para leg macro (confirma: D1 regime > 4H fractal para macro-leg).
- **Pivots 4H = ruído para macro-leg** (capturam pullback local). Úteis só para liquidity sweep local, não para leg macro.
- **SMC esparso** não mudou o resultado.

## Conclusão: PARCIALMENTE CONFIRMADA
- ✅ Conceito leg-state certo (separador é a leg, não localização/momentum).
- ❌ Implementação 4H-fractal refutada (confound de escala — captura pullback local).
- ✅ Achado: leg macro = D1/weekly (macro_v1 já a lê bem); valor da leg-state = bloquear macro-BEAR robustamente.
- ✅ B-set late-top confirmado auction-irredutível (resíduo aceitável).

## Próximo passo recomendado
**Leg-state no frame D1/weekly** (swing structure macro, não 4H fractal) — para bloquear macro-bear-leg longs com
robustez (o maior bucket de losers, incl. o OOS 2013-2016). NÃO tentar separar B late-tops por estrutura (irredutível).
O sistema realista converge: **macro_v1 (D1 regime, preserva bull) + bloqueio robusto de macro-bear-leg (D1/weekly) +
aceitar resíduo late-top.** Validar 276+OOS depois.
