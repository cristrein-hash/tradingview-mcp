# LAYER1 TURN-LAG — MANIFEST + PREREG (selado 2026-08-21, ordem Cris "FAZ PREREG")

## Problema (medido antes de selar, não inventado)
Layer1 1D preso em BEAR desde 26/07 com ouro +12% do fundo (4519 em 21/08). Diagnóstico exato no código
(macro_structural_v3.build_layer1): o gate de significância JÁ passa (run-up low252 = 33,5% >> ru_bull 12);
o bloqueio é o `rev_ref` — com `bull_rev_swing=True`, BEAR→BULL exige fecho acima do swing-high da 2ª
escala (m_sw=13) = **4773.53 hoje** (+5,6% acima do preço). O mesmo mecanismo explica o histórico: a regra
foi desenhada para matar bear-flags (bounce pós-crash rompe mini-highs mas não o swing maduro) e valida
100% dos bears 2026 — o custo é ficar cego a recuperações em V que sobem 12-30% sem tocar o swing antigo.

## Hipóteses (seladas ANTES de olhar resultados; multiplicidade declarada = 3, sem varrimentos)
- **T1 — rev_ref com decaimento**: rev_ref = min(sw_high, max(prot_high, low252×(1+ru_bull/100))).
  Intuição causal: depois de um run-up ≥ o gate, reconquistar o lower-high IMEDIATO (prot_high) chega;
  o swing maduro só é exigido enquanto o run-up é raso (a zona bear-flag).
- **T2 — idade+extensão**: BEAR→BULL se choch_up imediato E bull_gate E bear_age ≥ min_bear_age E
  ru ≥ 2×ru_bull (run-up ≥24% = já não é bear-flag por magnitude). Zero referência ao swing.
- **T3 — escala intermédia**: rev_ref = swing-high de m_rev=8 (entre o imediato m=5 e o maduro m_sw=13).
  Único knob novo, valor fixado ANTES de correr (média geométrica ≈ 8), sem varrimento.
Params tocados por variante: só os descritos. TUDO O RESTO da matemática congelada intocado
(onsets BEAR, crash, RANGE, DXY shift causal). Close-only-causal preservado por construção.

## Dados e ground truth
- Série: a MESMA fusão do serviço (layer1_cycle._merge_xau_1d + raw_dxy_1d) — 3000+ barras 2014→2026.
- GT de viragens (selado agora, ANTES de correr): os grandes fundos/topos já validados no projeto —
  bears 5/5 de 2026 do relatório de aprovação (13/07) + as viragens reais conhecidas: fundo 05/08/2026
  (4007→BULL real), fundo 07/07/2025, e todas as transições em que o próprio Layer1 atual virou (o
  baseline nunca pode piorar nelas). Régua de acerto: dias de lag entre o fundo/topo REAL (mín/máx local
  de 20 dias, computável mecanicamente) e o flip do label.
- NÃO se usa OOS/cross-asset (trava dura): validação = sub-janelas por ano + jackknife + null dentro da série.

## Métricas (seladas)
1. **Lag médio e mediano de viragem** BEAR→BULL e BULL→BEAR (dias após extremo real de 20d).
2. **Falsos flips**: nº de transições que revertem em ≤5 dias (whipsaw) — o baseline é quase-zero; variante
   que aumente falsos flips em >1 caso/12 anos FALHA independentemente do lag.
3. **Preservação dos onsets BEAR**: os onsets de crash/bear do baseline têm de reproduzir EXATOS (byte de
   labels nos dias de onset) — proteção do que está aprovado e a funcionar.
4. Dias-em-label-errado 2026 (26/07→21/08 conhecido: baseline = 26 dias BEAR em mercado que virou) — só
   DESCRITIVO (é o período que motivou; não pontua score, análogo à regra dos 4 forwards no estudo L2).
5. Null: 200 réplicas com flip-antecipado ALEATÓRIO de k dias (k ~ distribuição dos ganhos de lag da
   variante) — a variante tem de bater o null em falsos-flips (antecipar por regra ≠ antecipar por sorte).

## Vereditos possíveis (selados)
Variante SUPORTADA se: reduz lag mediano BEAR→BULL em ≥3 dias E falsos flips ≤ baseline+1 (em 12 anos)
E onsets BEAR reproduzem exatos E bate o null. Se nenhuma passar → Layer1 fica como está e o sistema
continua a mitigar por v5-4H (já em produção). Vencedora (se houver) NÃO vai a produção: vira proposta
com painel completo para aprovação explícita do Cris + shadow paralelo (labels novo vs velho lado a lado
no current_layer1.json) por ≥2 semanas antes de qualquer troca de autoridade.

## Passos
P0 este manifest (commit) → P1 harness baseline (reproduz labels atuais byte-a-byte, fail-loud) →
P2 GT mecânico de extremos 20d + lags baseline → P3 correr T1/T2/T3 → P4 null + sub-janelas + jackknife →
P5 DA adversarial → P6 relatório + decisão Cris. Claims só via claims_ledger.jsonl.
