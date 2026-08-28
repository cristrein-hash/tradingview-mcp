# MÉTODO INTER EQUITY × SISTEMA ATUAL — o que já existe, o que falta (28/08)
Objetivo: reader como modelo de entrada com o padrão dele. Cada regra dele mapeada ao sistema.

## CONVERGÊNCIA: o método dele é o que o sistema já persegue (em pedaços)
| Regra dele | O que o sistema JÁ tem | Estado |
|---|---|---|
| Liquidez real = extremo respeitado N vezes | liquidity_map: pools por `n_extremos`+`reacoes`+relevância | ✅ existe |
| Sweep do extremo (trap) | AMD F1 (sweep+reclaim H4), sweep_reject_guard, status CAPTURADA:SWEEP | ✅ existe, disperso |
| Entrada no Liquidity Block pós-sweep | R8 pool_touch (E1) — arma no fundo do pool ao toque | ✅ criado hoje |
| SL atrás do extremo varrido (nunca no meio) | R8 SL = fundo do pool − 0.1 ATR; reclaim_hold veta espeto | ✅ existe |
| Alvo = liquidez oposta (próximo pool/bloco) | liquidity_map roadmap acima/abaixo + LIQ_BLOCKs | ✅ existe |
| Bias HTF→LTF antes da entrada | regime v5-4H + Layer1-1D + leg multi-TF no E0 | ✅ existe (parcial) |
| NÃO entrar antes de news (red-folder) | news_gate + regra de notícia do pool_limit (hoje) | ✅ existe |
| NÃO mover stop cedo | doutrina, não mecânico | ⚠️ só texto |

## O QUE FALTA (as lacunas reais para o reader emitir com este padrão)
1. **INDUCEMENT explícito — o coração do método dele, o sistema NÃO tem.**
   Ele não entra no sweep qualquer: entra no sweep que TRAPEIA os induzidos (BOS recente que atraiu
   retail). O sistema deteta sweep, mas não distingue "sweep que trapeia inducement" de "sweep qualquer".
   FALTA: marcar o último BOS/extremo induzido e exigir que o sweep seja DESSE nível (o trap).
2. **Sequência "false run → stab → reação" como gatilho.** Ele exige a impressão do trap (o extremo é
   stabado e reage). O reclaim_hold já aproxima (vela que fura e fecha de volta) — mas não verifica que
   o extremo stabado era um nível de INDUCEMENT.
3. **Bias como FILTRO DURO da direção da liquidez.** Ele só compra liquidez do lado oposto ao induzido.
   O sistema tem bias (regime) mas não o usa para dizer "este pool SSL é alvo porque o topo acima foi o
   inducement". FALTA: ligar o pool-alvo ao lado induzido.
4. **Alvo = liquidez oposta específica, não 3R fixo.** Ele mira o extremo HTF real. O R8 usa 3R fixo;
   fiel seria alvo = próximo pool/bloco do roadmap (já existe no mapa, falta ligar ao R8).

## PROPOSTA DE CONSTRUÇÃO (para aprovação — NÃO implementado)
Reader vira "modelo inducement" em 4 passos, todos sobre features existentes (não rebuild):
A. INDUCEMENT DETECTOR: marcar o último BOS (extremo rompido que induziu retail) — já temos choch/BOS
   nos smc_labels + context_structure. Output: nível induzido + lado.
B. TRAP TRIGGER: R8 pool_touch só arma se o pool é do lado OPOSTO ao inducement E o extremo induzido foi
   varrido (sweep impresso). = compor R8 + inducement detector + reclaim_hold.
C. ALVO REAL: R8 target = próximo pool/bloco do roadmap (liquidity_map), não 3R fixo.
D. READER como juiz final: aprova se a sequência inducement→sweep→trap→LB está impressa (prompt já tem a
   doutrina de liquidez; acrescentar a gramática inducement).
Validação: forward shadow + scoreboard (não live antes de N). Bias/regime = filtro duro de direção.

## DECISÃO DO CRIS
Aprovar o desenho (A-D) e a ordem de construção. Cada passo = prereg + DA. Nada live sem forward.
