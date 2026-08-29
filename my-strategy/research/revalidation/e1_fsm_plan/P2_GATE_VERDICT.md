# GATE P2 — VEREDITO DA: PASS-VAZIO (registado antes de avançar; decisão Cris)
- 42/42 casos LONG têm buyers-induced antes da entrada — MAS o null (200 instantes aleatórios) dá 94%
  no mesmo critério: quase qualquer momento "tem inducement". O 100% não discrimina.
- Onde está o sinal real (medido, sem escolher): ORIGEM PERTO da entrada (|origem−entry|<=1ATR):
  casos 50% vs null 12.5% (contraste +37.5pp). Recência (48b) quase não discrimina (+9.7pp).
- Semântica declarada: o detetor é de ROMPIMENTOS (dispara em toda subida); a discriminação
  trap-vs-continuação fica DELEGADA à composição do P3 (pool+sweep+LB), com null repetido lá como árbitro.
- Limitações: 11% dos eventos sem origem (descartados); dedup por preço suprime re-rompimentos (relevante p/ P3).

# GATE P3 — VEREDITO DA (29/08): NÃO PASSA
- Níveis: 55% casos vs 45% null simétrico — indistinguível de acaso (mínimo detetável ~17pp; observado 10pp).
- Qualificadores do método (sweep-em-curso / respeitado) dão contraste NEGATIVO nos casos — ou o t do GT
  é o instante de COLOCAÇÃO da ordem (não do fill no wick), ou o gatilho não captura o discriminador.
- A peça que decide continua em falta: inducement/narrativa (delegada do P2). Os componentes níveis+limit+SL
  não bastam sozinhos.
- Ações possíveis (decisão Cris): corrigir o GT (t = instante do FILL real, não da colocação) e re-medir;
  e/ou construir a camada de narrativa (P2 completo) antes de re-testar o P3.
