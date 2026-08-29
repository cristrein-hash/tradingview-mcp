# MÁQUINA LM — ETAPAS E ESTADO (atualizado 29/08 tarde)
- P0 Ground truth ✅ — SÓ esta semana (chart reorganizado): 13 ENTRY_LIMITs (vela-âncora+nível),
  14 posições, pools $$$, LIQ_BLOCKs. ground_truth_v2.json.
- P1 Detetor de regiões ✅ CONGELADO — lm_regions.py: livro de evidência por nível (toques 5M +
  bolhas na agressão + OB/SMC + sessão + EQ + PO3), sem fractal/ATR/confirmação; morte só por
  atravessou-e-ficou; bandas [lo,hi] p/ execução (limit na BORDA), centro p/ medição.
  Fidelidade 9/13 formal + 1 validado pelo Cris como leitura MELHOR que a dele (4668.6→mercado 4668.25)
  = 10/13 real. Misses restantes: 2 borderline de borda; 2-3 por repaint de snapshot (só validáveis em
  forward). DA do gate PENDENTE.
- P2 Inducement → EVENTO interno da máquina (não emissor); entra na composição do gatilho.
- P3 Gatilho ARMA-LIMITE ⬅️ PRÓXIMO — quando o preço se aproxima de região válida do lado certo:
  emitir limit na BORDA da banda + SL atrás do pavio + 3R (gestão do Cris). Regra de notícia herdada.
- P4 Reader como juiz — Opus julga só o discricionário (narrativa Asia/London/NY, região operável).
- P5 Shadow forward = ÁRBITRO — semana(s) no pessoal do Cris; scoreboard; nada ao grupo antes.
LIMPEZAS: E1 velho DELETADO · A1/AMD shadow · L2 só entrada · reader com doutrina liquidez · scoreboard diário.

## DA GATE P1 (29/08): PASS CONDICIONAL
- Sem bugs críticos; bolhas limpas (0 contagens em barra que não toca o nível); sensibilidade estável.
- Fidelidade causal-pura (sem fatores snapshot): 7/13 formal, 8/13 real. Null refeito n=150: 47.3% →
  contraste retroativo NÃO significativo (p=0.11). FIDELIDADE RETROATIVA NÃO É EVIDÊNCIA DE SKILL.
- Condições cumpridas: corte defensivo t<=t_now dentro de regions_at (aplicado); FORWARD = árbitro ÚNICO.
