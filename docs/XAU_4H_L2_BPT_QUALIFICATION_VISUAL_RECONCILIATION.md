# XAU 4H L2/BPT Qualification — Reconciliação visual (full-res) + refutação das melhorias

**Status:** `RESEARCH · VISUAL RECONCILIATION · IMPROVEMENT CLAIMS REFUTED · NO_PRODUCTION` · **Data:** 2026-06-18
Leitura full-res dos 20 prints dos 32 TAKE + tentativa de achar (a) o que o engine não viu nos losers, (b) winners perdidos. **Resultado honesto: minha leitura visual foi viés de confirmação; as "melhorias" não sobrevivem ao DA.** Foundation: [[XAU_4H_L2_BPT_TRADE_QUALIFICATION_ENGINE]].

## 1. Losers — narrativa visual REFUTADA pelos dados
Afirmei (supply overhead capando 2R + reclaim não-confirmado) como causa dos 13 losers. Falso:
- `supply_blocks_2ATR=1`: 7/13 losers **mas 8/19 winners**. `reclaim_body<0`: 4/13 losers **mas 8/19 winners**.
- Regra de corte `supply_block2ATR OR reclaim_body<0` = **net −18.4R** (salva +9.9R loser, mata +28.3R winner).
- `trend_90` dos losers é MAIS forte (cohenD −0.35, invertido) → "cascata de baixa derrubou" é contradito.
- **Único separador real:** distância-ao-supply (winners supply mais longe +1.22 vs +0.87 ATR, cohenD +0.83). É a *distância* contínua, não a *presença* binária. Único lever honesto.

## 2. "Adicionar winners" — lane-continuação NÃO é edge
23 trades alto-legpos uptrend rejeitados (avgR +0.96, +22R, legpos90~93):
- vs baseline casado-no-contexto (legpos≥85 & trend>2, base +0.37): lift ~+0.6R, raw p0.037.
- 64 variantes de filtro plausíveis → mediana +0.87R, pior +0.75R (TODAS "boas" = drift do bull). Bonferroni → **p≈1.0, sem edge**.
- 19/23 em 2023-26; `trend>2` apaga 2022 sozinho (segurança circular); 2024 tocou 2, **0/2 −1.1R**.
- **Veredito: beta do bull empacotado como alpha (modo A1' SUPERTREND). Não recomendado sem out-of-sample.**

## 3. Conclusão
Winners/losers do engine estão **estatisticamente emaranhados** nos eixos nomeados → não há separador limpo escondido nesta base; o edge é fino e real (1º DA). Caminho pra melhorar NÃO é filtro novo sobre os mesmos 276 (overfit garantido no drift). Legítimo:
1. Trocar flag binário de supply por **distância-ao-supply contínua** no raciocínio (único sinal real, cohenD 0.83).
2. Pré-registrar UM filtro de continuação e validar em **regime não-bull** (2022 chop, correções 2024-25) vs base-rate +0.37.
3. Confirmar engine em anos held-out.

DA: a71e63332604c75d9 (refutou claims 1-4). Sem SLIM/look-ahead/produção. Nada promovido. Prints: zip do Desktop, lidos full-res.
