# Rebuild v2 — XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5

**Data:** 2026-06-14 · **Tipo:** RECONSTRUÇÃO (correção do v1). **NÃO é validação, NÃO promove, NÃO popula registry.**

## Objetivo
Corrigir a reconstrução infiel do v1, testando as 2 hipóteses do DA v1: (1) cooldown serializando 38→3; (2) entry-trigger ausente no monumental 2024-03-26.

## Diagnóstico v1
- candidatos pré-cooldown: não eram logados; trades emitidos: 3 (spans curtos 12h–8d).
- v1 usava cooldown como **trade-active blocker global** (`busy_until=idx[t_exit]`).
- hipótese mínima de correção (DA v1): separar candidate-gen de trade-selection; cooldown = dedup local.

## Resultado v2 — MEDIÇÃO DECISIVA
- **candidate_count_pre_cooldown = 38** (distribuídos 2020:7, 2022:1, 2023:8, 2024:10, 2025:12). Confirma os 38 do DA.
- **trade_count = 3** mesmo com cooldown trocado por **dedup local K=6** (não exit-blocker).
- **dedup local dropou 0 candidatos.** → **o cooldown NUNCA foi a causa do 38→3.** Hipótese #1 do DA v1 **REFUTADA empiricamente.**
- **Causa real do 38→3: R_CEIL abort.** 35/38 candidatos têm **stop estrutural > 1.5 ATR** (risco mediano **2.28 ATR**, max 4.05) → abortados pela regra documentada "R ceiling 1.5×ATR". Só **3** têm risco ≤1.5 ATR.
- **2024-03-26 (monumental): rejeitado pelos GATES** em todos os 6 bars do dia (close_prev≤EMA21, ema21_slope3≤0, body_pct<0.35, zone_not_touched). Não é cooldown nem trigger-gap de seleção — é gate real. → **ENTRY_GAP_UNRESOLVED.**

## reconciliation_status = FAILED_RECONSTRUCTION
n=3, sumR −0.3R vs documentado n=16/+31.74R. Não aproximou. **MAS isto NÃO refuta a estratégia** — significa que a **config documentada é internamente inconsistente**: a combinação (stop estrutural min(low i..i-4, zone_low)−0.1ATR) + (R ceiling 1.5×ATR) aborta 35 dos seus próprios 38 candidatos. O original n=16 com esses mesmos gates é **incompatível** → o original tinha um **stop/trigger diferente do documentado** (exatamente a "variação não documentada" que a memória já flagrava: n=11 vs n=16).

## Devil's Advocate (Processo 4)
- **v2 aproximou do n=16 por mudança legítima ou relaxamento indevido?** Nem um nem outro — v2 **não aproximou** (ainda 3), e **não relaxou nenhum gate** (gates idênticos ao v1). v2 fez o certo: **mediu** e **refutou** a causa errada (cooldown), expondo a causa real (R_CEIL abort + gate-rejection do monumental).
- **O resultado ainda depende de ASSUMPTION?** Sim, fortemente: o stop estrutural exato (referência de swing-low, inclusão do zone_low que está longe), o R-ceiling 1.5ATR, e a definição de gate do bar 2024-03-26 são **não documentados** e perdidos. NÃO relaxei silenciosamente (marcado ENTRY_GAP_UNRESOLVED + STOP_POLICY_DIVERGENCE).
- **Deve parar e buscar definição humana?** **SIM.** A config documentada não reproduz o original porque os detalhes que importam (stop policy, trigger do monumental) se perderam. Reconstrução fiel exige **definição humana / fonte original**, não mais iteração de assumption.

## Veredito
**FAILED_RECONSTRUCTION — STOP, buscar definição humana.** A divergência não é cooldown (refutado), é stop-policy + gate-definition não documentados. Não há como reconstruir fielmente a partir da config documentada; ela é auto-inconsistente (aborta 35/38 dos próprios candidatos).

## Próximos passos (com autorização)
1. **Definição humana:** Cris confirmar o stop real do L1 original (a memória diz "stop estrutural ... − 0.1ATR, R floor 0.3 / ceil 1.5" — mas isso aborta 35/38; provavelmente o ceiling era maior OU a referência de swing-low era mais próxima OU não incluía zone_low).
2. **Trigger do monumental 2024-03-26:** confirmar em qual bar/condição o original entrou (os gates documentados rejeitam o dia todo).
3. Só após definição fiel: lookahead audit + walk-forward. **Nada de promoção/registry.**
