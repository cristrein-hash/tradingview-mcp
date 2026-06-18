# XAU 4H L2/BPT — SL Estrutural por-trade: mandato da sessão dedicada (pré-registro)

**Status:** `PLANNING · PRE-REGISTERED · NOT_STARTED` · **Data:** 2026-06-18
Mandato do Cris para a próxima sessão dedicada de SL. NÃO iniciada. Substitui o "SL estrutural swing-origin mecânico" como direção final.

---

## 1. Problema (Cris 2026-06-18)
O SL que vínhamos usando (swing-origin = pivô Williams 5/5 mais recente abaixo da entrada −0.1ATR, floor 0.3, sem teto) é **mecânico e EXAGERADO** — mediano **5.7 ATR**, largo demais na maioria dos trades. **Nunca foi a intenção.** Gera o problema de classificação (muitos time-exits/scratch porque o stop quase nunca é tocado) e R-múltiplos comprimidos.

## 2. Objetivo da sessão de SL
Cada trade deve ter **SL próprio, calculado pela estrutura MAIS SEGURA segundo o contexto daquele trade** — de modo que coexistam:
- **trades com SL CURTO bons** (quando a estrutura permite apertar);
- **trades com SL LARGO bons** (quando o contexto exige).
NÃO mecanizado, NÃO um multiplicador-ATR fixo, NÃO "sempre o swing mais fundo".

## 3. Requisitos de método (o que testar)
- **Leitura estrutural MAIOR, não só ATR:** testar variações que leiam a estrutura (não apenas distância em ATR). Candidatos a níveis: base/demanda defendida, micro-base do reclaim, swing-low de origem da perna, low de capitulação/reversal, invalidação de polaridade, retest low — **escolhidos por SEGURANÇA estrutural no contexto**, não por regra fixa.
- **Distinguir QUANDO apertar vs QUANDO deixar largo:** o cerne. Que sinal estrutural (contexto) diz "aqui o stop pode ser curto e seguro" vs "aqui precisa ser largo"? (ex.: base bem definida e próxima → curto; reversão de fundo sem base próxima → largo; topo/exaustão → não-trade, não SL).
- **Pensamento estrutural PROFUNDO**, não primeira conclusão. Evitar repetir o erro do bloco "defended-swing" (que tentou regra causal única e falhou: pivô-mais-recente raso demais E pivô-mais-fundo largo demais). A resposta provavelmente é **contextual/hierárquica**, possivelmente com componente de review humano.
- **Recall-gate** contra os winners conhecidos; medir por episódio; lift vs base-rate; classificação por TIPO DE SAÍDA (bateu alvo / stopou / scratch), NUNCA por R-sign (lição 2026-06-18).

## 4. O que NÃO repetir
- Swing-origin mecânico sem teto (exagerado).
- CAP4 (teto fixo — descartado).
- Defended-swing como regra causal única (falhou — opostos não separáveis automaticamente).
- Classificar win/loss por R-sign (mascara scratches sob SL grande).

## 5. Relação com o resto
- Exit FIXO durante a sessão de SL: partial50@2R+6R (não mexer).
- F_STRICT (entry filter top/late) = positivo, human-review flag — independente do SL.
- Provável interação: SL mais curto/contextual muda drasticamente os R-múltiplos e a fração de scratch → re-medir tudo após definir o SL.

---

*Pré-registro. NÃO iniciar sem autorização explícita do Cris. Relaciona [[project_l2_bpt_sl_structural]] (defended-swing + operating point).*
