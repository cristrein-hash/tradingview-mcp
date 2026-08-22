# A2 POSICIONADA (limite-na-zona FVG) — MANIFEST + PREREG (selado 2026-08-22, APROVADO Cris)

## Classe
Entrada por LOCALIZAÇÃO pré-confirmação (mecanização do método FVG-confluência manual do Cris; motivada
pelo diagnóstico 6cc6900: WR 62% pré-MB3 vs 31.6% pós; bounce 107% na entrada confirmada).

## Dados
RAW 15M canónico (raw_reader.series_flat, 8 blocos 2024-05→2026-05, 47k barras). FVG computado
CAUSALMENTE do OHLC (estrutura pura de preço): FVG bullish na barra k = L[k] > H[k-2] (gap [H[k-2], L[k]]),
mesma definição do detetor AMD vivo. Sem OB histórico (indisponível — não se inventa zonas).

## Regras seladas (TODAS antes de olhar resultados; zero knobs livres)
SETUP (avaliado barra a barra, causal):
  s1. Perna de alta: high da janela [i-96,i-8] (HH_WIN/HH_GAP do A1/A2) está ≥1.5 ATR acima do C[i]... NÃO:
      perna = hh > C[i] e hh − min(L[hh_i..i]) até agora ≤ 2 ATR (pullback RASO em curso, mesmo domínio A2).
  s2. FVG bullish FRESCO abaixo do preço: formado nas últimas 32 barras, ainda não preenchido
      (nenhum L posterior ≤ fundo do gap), topo do gap < C[i], distância C[i]→topo ≤ 1.5 ATR.
  s3. ARMA-SE ordem limite: entry = topo do FVG · SL = fundo do FVG − 0.1×ATR · alvo = entry + 3R.
      Guarda de escala aprovada: risco ≤ 2.5×ATR e > 0.05×ATR.
  s4. Validade: 16 barras. Fill = 1º L[k] ≤ entry dentro da validade. Sem fill = NO-FILL (registado).
  s5. Outcome: SL-first, HORIZON 480 barras, custos 0 / 0.2 / 0.35R no painel.
  s6. Dedup por episódio: setups a <8 barras do mesmo FVG = 1 (primeiro conta).

## Métricas e validação
Painel completo (N·WR·sumR·avgR·DD·retDD·streak·por-semestre) em 3 custos · fill-rate · bounce%-na-entrada
(tem de ser ESTRUTURALMENTE baixo — é a tese) · null: 300 entradas aleatórias/episódio na MESMA janela de
validade com a MESMA regra de SL (guardas incluídas) · jackknife por semestre · comparação com A2-base
(31R/73eps custo-0) nos MESMOS semestres.

## Gates de veredito (selados)
SUPORTADA se: N≥40 episódios COM FILL · sumR a custo 0.35 > 0 · WR > null+3pp · nenhum semestre ≤−5R ·
sobrevive jackknife (nenhum semestre removido inverte o sinal). Qualquer falha = NÃO SUPORTADA (e fica o
mapa de porquê). SUPORTADA ⇒ F2 = proposta formal ao Cris (daemon de sinal, forward N≥20 pessoal) —
NUNCA produção direta. DA obrigatório antes do relatório. Claims só via claims_ledger.jsonl.
