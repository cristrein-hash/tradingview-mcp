# GATE P2 — VEREDITO DA: PASS-VAZIO (registado antes de avançar; decisão Cris)
- 42/42 casos LONG têm buyers-induced antes da entrada — MAS o null (200 instantes aleatórios) dá 94%
  no mesmo critério: quase qualquer momento "tem inducement". O 100% não discrimina.
- Onde está o sinal real (medido, sem escolher): ORIGEM PERTO da entrada (|origem−entry|<=1ATR):
  casos 50% vs null 12.5% (contraste +37.5pp). Recência (48b) quase não discrimina (+9.7pp).
- Semântica declarada: o detetor é de ROMPIMENTOS (dispara em toda subida); a discriminação
  trap-vs-continuação fica DELEGADA à composição do P3 (pool+sweep+LB), com null repetido lá como árbitro.
- Limitações: 11% dos eventos sem origem (descartados); dedup por preço suprime re-rompimentos (relevante p/ P3).
