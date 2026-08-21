# A2 V1 RE-RUN (motor real) — MANIFEST + PREREG (selado 2026-08-21, ordem Cris "FAÇA ISSO")

## Objetivo
Avaliar V1 (fractal m=2 no ramo raso) com o DETETOR REAL — o caminho exigido pelo DA do estudo anterior
(3d3a232). Motivação adicional do Cris: entrada com 84% do bounce corrido é fraca por natureza — além do
V1, medir UMA variante de entrada-limite (E1) que ataca diretamente o bounce-corrido.

## Método (fecha as 4 objeções do DA)
1. MOTOR REAL: censo barra-a-barra com a1a2_runtime.detect PATCHED por source (M_FRAC=2 via patch da
   constante no módulo-mãe; identidade valida byte-a-byte com m=3 antes — padrão do estudo Layer1 v2).
   NADA de try_trigger simplificado.
2. INTERFERÊNCIA no A1: censo m=2 vs censo m=3 — sinais A1 que mudam/desaparecem/mudam de layer contados
   e reportados (gate: A1 aprovado não pode perder sinais WIN; qualquer mudança no fluxo A1 = reportar).
3. NULL corrigido: 300 réplicas/fundo (como selado no 1º prereg), COM a guarda 2.5×ATR aplicada ao null.
4. CUSTOS: painel com 0 / 0.2R / 0.35R por trade.
## Variante E1 (entrada-limite anti-bounce-corrido; selada, multiplicidade total = 2)
Nos sinais A2 do detect real (m=3 E m=2): em vez de market no fecho MB3, ordem LIMITE no retest_zone
que o próprio sinal JÁ publica (midpoint bounce↔high quebrado — campo retest_zone do runtime). Fill se
tocar em ≤16 barras; sem fill = sem trade (no-fill = resultado, lição do estudo L2). Mesmo SL/3R.

## Gates de veredito (selados)
V1 SUPORTADA se: no censo real, A2 capturados ≥1.5× os do m=3 E sumR-com-custo-0.35 > m=3 E fluxo A1
inalterado nos WINs E bate null corrigido (WR > null+3pp). E1 SUPORTADA se: sumR-pontos combinado
(fills + no-fill=0) ≥ versão market E bounce% mediano na entrada <60%. Unidade = episódio (sinais <8
barras do mesmo fundo = 1 episódio, primeiro conta). Sub-janelas por semestre; semestre ≤−5R reprova.
Qualquer SUPORTADA → proposta ao Cris (nunca produção direta). DA obrigatório.
