# XAU 15M — Dossiês de Episódios para o Reader Contextual

**Data:** 2026-07-09 · **Natureza:** leitura contextual narrativa (estilo L2/BPT Reader) de 34 episódios 15M.
**O que é:** base qualitativa para desenhar a arquitetura do Reader 15M — como um humano lê cada episódio (contexto superior → path → região → decisão). **NÃO é** conjunto de labels de treino, **NÃO é** backtest, **NÃO produz** métricas de estratégia. Nenhum episódio aqui autoriza regra mecânica.

## Fontes (RAW-derivadas declaradas; nunca primitives)
- Barras 15M fechadas: `research/xau_15m_structural_leg_engine/results/f0_bars_cache.jsonl` (49.804 barras, 2024-05 → 2026-07-03; derivado 1:1 do RAW HD). Todos os números de path (queda em ATR, barras, reclaim, reteste, posição no range) foram **calculados deste cache** com sondas SANITY_PROBE read-only.
- GT do Cris: `research/xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json` (42 VELA DE FUNDO · 4 INVALIDO · 24 ENTRY · 50 círculos · 65 trades).
- Famílias/medições: `docs/architecture/XAU15M_MANUAL_BOTTOM_CATALOG_20260707.md`.
- A2 verdicts: `research/xau_15m_structural_leg_engine/results/a2_anchor_gt_gate_result.json`.
- Losers A-BULL: `research/xau_15m_bb_nas_leonardo/reports/xau_15m_option_a_candidates.csv`.
- Filtro capitulation: `docs/architecture/XAU_15M_N96_INTRA_BEAR_CAPITULATION_FILTER_20260708.md`.
- Estados INVALIDO: `research/xau_15m_structural_leg_engine/results/f15_diag_best_result.json`.

## Notas de método (honestidade)
- Timestamps GT = **UTC** (verificado: t=1782781200 ↔ "2026-06-30 01:00" bate com o cache, offset 0h).
- O campo `price` das notas GT é a **âncora-y do texto** (fica tipicamente 20-100 pts ABAIXO do low da vela) — usei sempre o OHLC do cache como verdade da vela.
- ATR = média simples do True Range das 14 barras anteriores, no instante do episódio.
- "pos96/pos384" = posição do close dentro do range das últimas 96/384 barras (0=fundo, 1=topo). Quedas medidas do máximo da janela indicada até o low da vela — quando o topo está na borda da janela, escrevo "≥".
- **Família por episódio é INFERÊNCIA por data** (o catálogo dá famílias agregadas, não por linha): mar-jun/2026 → BEAR-capitulação; ago+nov/2025 → RANGE-base; resto → BULL-pullback. Onde o regime não está medido em artefacto, digo "não medido — ler no chart".
- Reprodução: sondas em `/private/tmp/.../scratchpad/probe_episodes.py`, `probe_fix.py` (fora do repo, por design).

---

# A) 10 VELA DE FUNDO — winners fortes

## A1 · 2025-09-18 13:00 UTC — FUNDO GT · família BULL-pullback (inferida) · A2 = COVERED_BOTTOM (B00901, idade 82h)
**Contexto superior:** regime médio de alta (série vinha de +3,9 ATR nas 384 barras); correção dentro de perna de alta. Não medido por artefacto de regime — inferido do path.
**Path 15M:** queda de 10,6 ATR em 72 barras (~18h) desde o topo local; vela marcada fecha a pos96 0,34 com ATR 4,9. O low da vela (3655,7) NÃO era o mínimo — a zona de fundo tinha sido formada ~3,4 dias antes (idade A2 = 82h): isto é um **reteste de zona já defendida**.
**Depois:** ainda houve um flush adicional de ~6,3 ATR até ~3628 nas 24h seguintes (a âncora da nota do Cris está exatamente aí, 3628) e SÓ ENTÃO o rally: +27 ATR em 4 dias. A ENTRY GT veio 2025-09-19 12:00 (23h depois, pós-sweep).
**Região:** válida porque era demanda já testada e o contexto de alta seguia intacto; o sweep final varreu os stops abaixo dela antes de partir.
**Contraste:** C1 (2025-09-16, 2 dias antes) comprou o dip raso de 6,6 ATR no TOPO da mesma perna (pos384 0,87) e levou SL — mesma "compra em queda", contexto oposto: A1 é reteste de base madura, C1 é primeiro dip de perna esticada.
**Decisão humana:** TAKE — mas na ENTRY do reteste/sweep, nunca na vela de fundo em si.
**Lições para automação:** medir idade/defesa da zona e tolerar 1 sweep abaixo dela; não serve "low do dia = fundo"; erro a evitar: entrar na vela marcada (o flush de −6 ATR mataria stop curto).

## A2 · 2025-10-10 04:00 UTC — FUNDO GT · BULL-pullback (inferida) · A2 = COVERED_BOTTOM (B00939, idade 4,5h)
**Contexto superior:** bull de outubro vivo (net384 +4,8 ATR apesar da correção); pullback profundo dentro de perna de alta.
**Path 15M:** queda de 12,5 ATR em 134 barras (~33h), velocidade moderada (2,2 ATR/24b); vela fecha colada ao fundo do range de 24h (pos96 0,03). Reclaim da máxima da vela em **3 barras**; nunca mais fez low abaixo (fwd96_dn = 0,0 ATR).
**Depois:** +13,1 ATR em 24h, +32,7 ATR em 4 dias. ENTRY GT 2025-10-10 17:00 (13h depois, no pullback da reação).
**Região:** válida — pullback proporcional (~12 ATR) que devolve parte da perna e reverte com aceitação imediata; zona nova, fresca (idade 4,5h) mas com contexto de alta por cima.
**Contraste:** C2 (2025-10-09, ~22h antes!) comprou dip de só 3,9 ATR a pos384 0,91 e levou SL com −16 ATR — a diferença é a PROPORÇÃO do pullback: 12,5 ATR (A2) vs 3,9 ATR (C2) na mesma semana e mesmo regime.
**Decisão humana:** TAKE — pullback fundo em bull vivo, reclaim rápido.
**Lições:** a profundidade do pullback RELATIVA à perna é a evidência-chave; reclaim em ≤3 barras é confirmação barata; não serve distância à EMA-1D isolada (aqui estava positiva e deu certo).

## A3 · 2025-12-19 01:45 UTC — FUNDO GT · BULL-pullback (inferida) · A2 = COVERED_BOTTOM (B01055, idade 36h)
**Contexto superior:** bull de dezembro; correção rápida dentro de perna de alta (net384 +4,1 ATR).
**Path 15M:** queda VELOZ — 9,8 ATR em só 34 barras (6,9 ATR/24b, um flush); fecha a pos96 0,22. Reclaim da máxima da vela na **barra seguinte**.
**Depois:** +11,1 ATR em 24h, +35,3 ATR em 4 dias; reteste da zona só 52 barras depois (já em lucro). ENTRY GT 2025-12-19 14:45 (13h depois).
**Região:** válida — flush de liquidez num bull intacto que atinge zona de fundo formada 36h antes e reverte na hora; o clássico "lag curto" do catálogo (reação imediata, sem reteste longo).
**Contraste:** C4 (2025-12-25, 6 dias depois) comprou a pos384 0,83 depois de dip de 5,4 ATR e levou SL com −25 ATR a seguir (a correção de fim de ano) — A3 compra o flush fundo ANTES do topo; C4 compra o dip raso DEPOIS que a perna já deu o que tinha (POLARIDADE TOPO do GT marcada 2025-12-26).
**Decisão humana:** TAKE — flush veloz + reclaim imediato em bull vivo.
**Lições:** velocidade da queda (ATR/barra) separa flush-de-liquidez de perna-bear nascente; medir reclaim em barras; erro: tratar todo dip de dezembro como igual (C4 morreu na mesma quinzena).

## A4 · 2025-10-17 17:00 UTC — FUNDO GT · BULL-pullback (inferida) · A2 = LATE_ONLY
**Contexto superior:** fim do bull parabólico de outubro — no momento, alta ainda de pé (net384 +5,0 ATR), mas a 3 dias do topo 4381 de 20-out.
**Path 15M:** sexta-feira violenta: ATR inflado a 23,8 (3-4× o normal); queda de 8,1 ATR em 69 barras; o low DA VELA era o mínimo das 96 barras. Reclaim em 2 barras.
**Depois:** funcionou primeiro (+6,3 ATR em 24h; ENTRY GT 2025-10-20 06:00 pagou) — e DEPOIS o contexto virou: −8,5 ATR na janela de 4 dias (a correção 20-out → 28-out até 3886).
**Região:** válida no instante (pullback fundo, reversão), mas em preço recém-descoberto (por isso A2 só reconstrói a região tarde — LATE_ONLY: não havia estrutura histórica ali).
**Contraste:** A2 (10-out) teve o mesmo desenho e +32 ATR de continuação; A4 teve o mesmo desenho e a perna morreu 3 dias depois — a diferença não está no episódio, está na IDADE da perna superior (A4 é o enésimo dip de uma perna já parabólica).
**Decisão humana:** TAKE tático com alvo curto / REVIEW — o 3×1 rápido pagou, segurar não.
**Lições:** medir maturidade/extensão da perna superior (quantos ATR e dias desde a base da perna); ATR inflado = dimensionar por ATR corrente; erro: ler sucesso de 24h como validação da tese macro.

## A5 · 2026-01-08 12:00 UTC — FUNDO GT · BULL-pullback (inferida) · A2 = NEAR_MISS (converted_near T01076)
**Contexto superior:** bull secular intacto (net384 +4,3 ATR); correção pós-topo de dezembro terminando.
**Path 15M:** queda de 13,9 ATR em 143 barras; vela fecha NO extremo (pos96 0,01) e o low é o mínimo de 24h. Reclaim em 2 barras.
**Depois:** +11,3 ATR em 24h, +36 ATR em 4 dias, sem reteste. ENTRY GT 2026-01-08 14:15 (2,2h — lag curto).
**Região:** válida — o preço devolveu até uma zona de TOPO ANTIGO convertido em suporte (A2 viu converted_near T01076): topo rompido em dezembro virou demanda. Polaridade, não fundo prévio.
**Contraste:** B4 (2026-01-13, 5 dias depois, +180 pts acima) é o "fundo de pequena acumulação" INVALIDO do Cris: dip de 4,5 ATR sem pullback real — A5 devolve 13,9 ATR até estrutura convertida; B4 é ruído raso no meio do ar.
**Decisão humana:** TAKE — pullback proporcional em suporte por polaridade, reclaim imediato.
**Lições:** topo-convertido-em-suporte é evidência de região tão boa quanto bottom antigo (o Reader precisa das DUAS); erro: exigir "zona de fundo prévia" e perder polaridade.

## A6 · 2026-03-23 07:00 UTC — FUNDO GT · BEAR-capitulação · A2 = NEAR_MISS (B01007 + converted T00998)
**Contexto superior:** BEAR violento — queda de 33,7 ATR desde o topo 5419 de 02-mar (1383 barras, −24%); este é o clímax da perna.
**Path 15M:** capitulação: ATR explode a 38,3 (pânico); low 4126 é o mínimo de TUDO (96, 384, 1500 barras); vela fecha no chão absoluto (pos96 0,01). Reclaim da máxima em 4 barras; reteste do low em 2 barras segurou.
**Depois:** +10 ATR em 24h, +12,3 ATR em 4 dias. As FUNDO GT seguintes (24-mar 05:00 e 13:00, 26-mar, 27-mar) são os higher-lows da reversão que este clímax iniciou.
**Região:** válida — é o fim REAL da perna de baixa (critério do Cris: o fundo É o low recente que reverteu, d_vale ~0), com exaustão de velocidade e volume de pânico.
**Contraste:** B3 (16-mar, uma semana antes, 900 pts acima) tinha superfície de "fundo em queda funda" e era o MEIO da mesma cachoeira (−27,7 ATR nos 4 dias seguintes) — a diferença: em B3 a perna bear seguia viva (LEG_DOWN/DEEP, sem clímax); em A6 a perna terminou em pânico e o preço ACEITOU para cima.
**Decisão humana:** TAKE (tese reversão BEAR) — capitulação funda + reclaim, nunca antecipar antes do clímax.
**Lições:** medir "a perna terminou?" (velocidade terminal + low absoluto + reclaim), não "caiu muito"; erro fatal: comprar profundidade sem término — foi exatamente o erro dos INVALIDO e dos cortes F.

## A7 · 2026-06-24 18:00 UTC — FUNDO GT · BEAR-capitulação · A2 = NEAR_MISS (B00979)
**Contexto superior:** bear de junho maduro: −41 ATR desde 4540 (02-jun) em ~16 dias; perna de baixa em desaceleração (1,46 ATR/24b — grind, não pânico).
**Path 15M:** low 3959 é mínimo de 96 e 384 barras; vela larga (low 29 pts abaixo do close). Reclaim lento: 8 barras; sobe só +3,9 ATR em 24h e RETESTA o low 28 barras depois.
**Depois:** +7,6 ATR em 4 dias — reversão hesitante, em degraus (o fundo definitivo só em 30-jun, A8). Trade GT #S44 (24-jun 23:45) = ✓.
**Região:** válida mas de 2ª classe: fim provável de perna em bear esticado, porém SEM clímax — fundo em construção, não em pânico.
**Contraste:** A6 (23-mar) reverteu com pânico e nunca olhou para trás; A7, com o mesmo rótulo GT, precisou de reteste e mais uma perna (até A8) — grind-bottoms pagam menos e pedem entrada no reteste, não na vela.
**Decisão humana:** REVIEW/TAKE pequeno — fundo sem clímax exige confirmação extra (reteste segurado).
**Lições:** distinguir capitulação-clímax de exaustão-grind (velocidade terminal e amplitude da vela medem isso); erro: dimensionar grind-bottom como se fosse clímax.

## A8 · 2026-06-30 01:00 UTC — FUNDO GT · BEAR-capitulação · A2 = LATE_ONLY
**Contexto superior:** o mesmo bear de junho no seu fim: −45 ATR desde 05-jun; segunda perna após o fundo A7 falhar em segurar tendência.
**Path 15M:** low 3942,5 = mínimo absoluto da queda toda; velocidade já morta (1,0 ATR/24b); reclaim lento (14 barras) mas sem nunca mais fazer low (fwd96_dn 0,8 ATR).
**Depois:** +10 ATR em 24h, +22,4 ATR em 4 dias — este era o fundo verdadeiro do ciclo (o rally de julho). Círculo GT em 30-jun 00:30.
**Região:** válida — preço em zona nunca negociada desde 2025 (por isso A2 = LATE_ONLY: não existe região histórica; o fundo se define pela ESTRUTURA da reversão, não por nível antigo).
**Contraste:** A7 (6 dias antes, 16 pts acima) parecia igual e era só o primeiro degrau; A8 é o segundo teste da mesma área com velocidade de queda já exaurida — o par A7→A8 é o padrão "primeiro fundo constrói, segundo fundo paga".
**Decisão humana:** TAKE — segundo teste de zona de exaustão com perna de baixa morta.
**Lições:** número do teste da zona (1º vs 2º) é evidência de primeira classe; anchors por região histórica são estruturalmente cegos em preço virgem — o Reader precisa de estrutura local, não só níveis.

## A9 · 2025-08-20 01:00 UTC — FUNDO GT · RANGE-base · A2 = COVERED_CONVERTED (converted_support T00816)
**Contexto superior:** agosto morto: ATR 2,2 (mínimo do ano); base lateral longa após deriva de −96 pts (43,9 "ATR-anões" em 8 dias) desde 3408.
**Path 15M:** low 3311,9 = mínimo de tudo (96/384); vela fecha a pos96 0,05; reclaim em 2 barras; reteste em 2 barras segurou.
**Depois:** +17,7 ATR (=+38 pts) em 24h; +33 ATR em 4 dias — o breakout da base veio dias depois. ENTRY GT 2025-08-22 12:00 (2,4 dias — lag longo, reteste). Trade #C7 (20-ago 06:00) ✓.
**Região:** válida — fundo de base: topo antigo convertido em suporte (A2 viu converted_support) no chão de um range comprimido; risco minúsculo em pontos.
**Contraste:** A10 (nov/2025, também RANGE-base) foi MISS do A2 por ser higher-low sem região — A9 é o caso simétrico onde a região existia e foi coberta; ambos pagaram: a família RANGE-base paga pelo LUGAR no range, com ou sem região histórica.
**Decisão humana:** TAKE — fundo de range comprimido sobre polaridade, stop curto.
**Lições:** em compressão, normalizar tudo por ATR corrente (17 ATR aqui = 38 pts); a régua absoluta de "queda funda" não serve em range morto; erro: filtrar por "drop mínimo em ATR" sem contexto de compressão.

## A10 · 2025-11-04 23:00 UTC — FUNDO GT · RANGE-base · A2 = **MISS** (também tratado em D3)
**Contexto superior:** base de novembro pós-crash de outubro: −75,9 ATR desde o topo 4381 (20-out); o low do movimento (3886, 28-out) já tinha sido feito 5 dias antes.
**Path 15M:** low 3933 é **higher-low** ~47 pts ACIMA do low de 28-out (não é mínimo de 96 nem de 384); pos96 0,09; reclaim em 8 barras; reteste em 11 barras segurou.
**Depois:** +9,3 ATR em 24h; +35,4 ATR em 4 dias (a recuperação de novembro). Trade #S23 (06-nov 23:45) ✓.
**Região:** válida — segundo fundo (mais alto) de uma base em W: a defesa acontece ACIMA da região do primeiro low, sinal de demanda mais agressiva.
**Contraste:** B2 (08-mar-2026) tinha REGIÃO coberta pelo A2 e era inválido (perna bear viva); A10 NÃO tinha região (A2 MISS) e era válido — cobertura de região e validade do fundo são eixos independentes.
**Decisão humana:** TAKE — higher-low defendido sobre base recente com queda-mãe já exaurida.
**Lições:** o A2 falha estruturalmente em higher-lows (a demanda chega antes do nível); o Reader precisa reconhecer "defesa acima da região" como upgrade, não como ausência de setup.

---

# B) Os 4 INVALIDO do Cris

## B1 · 2026-03-05 18:00 UTC — INVALIDO ("perna bear clara antecede") · f15: LEG_DOWN/ACTIVE, macro BEAR, reject=true · A2 = LATE_ONLY
**Contexto superior:** 3 dias após o topo histórico 5419 (02-mar); perna de baixa ATIVA — queda de 16,5 ATR em 319 barras ainda acelerando (ATR 22,3 e subindo).
**Path 15M:** low local a pos96 0,15, bounce com reclaim em 2 barras e +4,5 ATR em 24h — superficialmente PARECE fundo com reação.
**Depois:** o bounce morre (+7,5 ATR máximo em 4 dias, sem tendência) e semanas depois o preço colapsa até 4126 (23-mar) — ~900 pts abaixo.
**Região:** inválida — nenhum término de perna: sem clímax, sem low absoluto de estrutura maior, queda-mãe com só 3 dias de idade. O bounce é reação técnica DENTRO da perna.
**Contraste:** A6 (23-mar) é o mesmo bear, 18 dias e 900 pts depois: lá a perna TERMINOU (pânico, low absoluto, aceitação); aqui ela estava começando. Mesma superfície de "vela verde após queda", fase oposta da perna.
**Decisão humana:** SKIP — perna bear jovem e viva por cima; reação ≠ reversão.
**Lições:** idade e fase da perna-mãe são a primeira pergunta do Reader; reclaim rápido NÃO serve como validador isolado (aqui reclaim=2 barras e era armadilha); o f15 já classificava reject_state=true — leitura estrutural simples chega.

## B2 · 2026-03-08 23:00 UTC — INVALIDO ("perna bear clara antecede") · f15: LEG_FLAT/NEUTRAL, macro BEAR · A2 = COVERED_BOTTOM (B01179, idade 124h)
**Contexto superior:** mesmo bear de março; preço lateral (net96 +0,7 ATR) 14,7 ATR abaixo do topo — pausa no meio da descida, sem qualquer perna de alta estrutural.
**Path 15M:** range apertado (rng96 5,9 ATR); "fundo" a pos96 0,30; depois: só +2,5 ATR de teto e −4,0 ATR em 24h; reclaim da vela demorou 81 barras.
**Região:** inválida — é consolidação de continuação: o mercado descansa e segue. A IRONIA: o A2 cobria uma bottom_region ativa aqui (idade 124h) — nível existia, contexto o anulava.
**Contraste:** E4 (18-nov-2025) também era reteste de região com ~200h de idade e PAGOU — a diferença: em E4 a queda-mãe estava exaurida e a base tinha semanas; em B2 a perna bear tinha dias e seguia por cima.
**Decisão humana:** SKIP — região sem término de perna é isca.
**Lições:** este é O caso que mata anchor-sem-contexto (A2 cobriu 3 dos 4 INVALIDO); a evidência necessária é o estado da perna-mãe, não a existência do nível; erro: pontuar "região defendida antes" sem perguntar quem manda no fluxo acima.

## B3 · 2026-03-16 00:00 UTC — INVALIDO ("perna bear clara antecede") · f15: LEG_DOWN/DEEP, macro RANGE · A2 = COVERED_BOTTOM (B01159, idade 579h)
**Contexto superior:** 22,5 ATR abaixo do topo de 02-mar, mas a perna de baixa segue DEEP e sem clímax; bounces anteriores (B1, B2) já falharam.
**Path 15M:** "fundo" a pos96 0,34 num range de 8,6 ATR; depois: +0,8 ATR de teto em 24h e −2,8 ATR; reclaim 54 barras; nos 4 dias seguintes **−27,7 ATR** — o pior resultado forward de todo este dossiê: era a boca da cachoeira final até 4126.
**Região:** inválida — low intermediário (d_vale 27-36 no catálogo: o low real estava longe); região histórica de 579h de idade coberta pelo A2 de novo NÃO salvou.
**Contraste:** A8 (30-jun) também era "segundo teste em queda longa" — mas com velocidade de queda morta (1,0 ATR/24b) e low ABSOLUTO da estrutura; B3 tinha low intermediário e vendedores ainda com iniciativa.
**Decisão humana:** SKIP — profundidade sem término; terceiro bounce da mesma perna viva é o mais letal.
**Lições:** contar bounces falhados da mesma perna (1º B1 → 2º B2 → 3º B3, cada um mais baixo) — sequência de reações falhadas é evidência CONTRA o próximo; profundidade em ATR sozinha não serve.

## B4 · 2026-01-13 19:00 UTC — INVALIDO ("pequena acumulação") · f15: LEG_FLAT/NEUTRAL, macro BULL · A2 = COVERED_BOTTOM (B01095, idade 5,8h)
**Contexto superior:** BULL de janeiro na parte ALTA do movimento (pos384 0,83; net384 +14,9 ATR) — não há correção real a comprar.
**Path 15M:** dip de só 4,5 ATR em 17 barras; range de 24h comprimido (5,4 ATR); "fundo" a pos96 0,36. Depois: chop (+4,2/−2,3 ATR em 24h; +8,4/−5,2 em 4 dias) — sem edge.
**Região:** inválida — sem capitulação nem pullback proporcional; micro-acumulação no meio do ar, longe de qualquer base (critério do catálogo: drop 0,8 ATR, retr 0,04 = ruído).
**Contraste:** A5 (08-jan, 5 dias antes) devolveu 13,9 ATR até topo-convertido e disparou +36 ATR; B4, na mesma perna bull, dá dip de 4,5 ATR sem estrutura — proporção do pullback é a diferença inteira. (O loser C5 comprou A MESMA área em 13-jan e levou SL em 7h.)
**Decisão humana:** SKIP — nada foi devolvido; não há fundo porque não houve queda.
**Lições:** exigir pullback proporcional à perna (retr/ATR mínimos contextuais); A2 cobriu isto com região de 5,8h — regiões recém-nascidas em topo de perna são as mais falsas; erro: confundir pausa lateral rasa com acumulação.

---

# C) 6 losers A-BULL — "compraram topo" (CSV option A, regime BULL, out=0)

## C1 · 2025-09-16 22:00 UTC — entrada A-BULL 3691,44 · SL em 14 barras (risk 6,6 ATR)
**Contexto superior:** regime BULL (v5); px_vs_ema_1d **+73,6** — o mais esticado de todo o CSV; net384 +23,5 ATR de run-up quase vertical.
**Path 15M:** o "pullback" comprado tinha só 6,6 ATR e 27 barras, a pos96 0,60 / pos384 0,87 — um degrau raso no topo de perna parabólica.
**Depois:** −22,3 ATR em 24h (a correção de 17-set); SL em 3,5h.
**Região:** inválida como compra — preço no ar: nenhuma base, nenhum nível defendido, só a inércia da subida.
**Contraste:** A1 (18-set, 2 dias depois, ~35 pts abaixo) foi o fundo REAL dessa mesma correção: reteste de zona de 82h + sweep — o que C1 antecipou sem existir.
**Decisão humana:** SKIP — dip raso a 0,87 do range de 4 dias com extensão recorde sobre a EMA-1D.
**Lições:** medir posição no range superior (pos384) e extensão vs EMA-1D ANTES de qualquer gatilho; reclaim/momentum não servem aqui (a subida-mãe garante gatilhos falsos); erro: tratar força da tendência como licença para comprar qualquer dip.

## C2 · 2025-10-09 05:45 UTC — entrada A-BULL 4039,83 · SL em 43 barras (risk 6,6 ATR)
**Contexto superior:** BULL parabólico de outubro; px_vs_ema_1d +41,6; net384 +30,5 ATR; pos384 0,91.
**Path 15M:** dip de apenas **3,9 ATR** em 49 barras — o menor pullback dos 6 losers; compra a pos96 0,67.
**Depois:** teto a +3,0 ATR; −16,1 ATR em 24h (o flush de 09/10-out); SL em ~11h. O fundo verdadeiro veio em A2 (10-out 04:00), 12,5 ATR abaixo do topo.
**Região:** inválida — não devolveu nada; comprou a pausa, não a correção.
**Contraste:** A2 (22h depois) é o espelho perfeito: mesma semana, mesma perna, pullback de 12,5 ATR vs 3,9 ATR — o mercado foi buscar a profundidade proporcional antes de pagar.
**Decisão humana:** SKIP — esperar a devolução proporcional (a régua do catálogo: BULL-pullback médio ~2,8 ATR de drop é para pernas normais; perna parabólica pede múltiplos disso).
**Lições:** profundidade-do-dip RELATIVA à perna é a feature; "regime BULL + dip" sozinho é o gerador de losers da opção A; erro: gatilho cedo dentro de correção que mal começou.

## C3 · 2025-10-19 22:00 UTC — entrada A-BULL 4259,23 · SL em 155 barras (risk 5,5 ATR)
**Contexto superior:** véspera do TOPO do bull de outubro (4381, 20-out); px_vs_ema_1d +20,7; a perna de alta tinha semanas de idade e extensão histórica.
**Path 15M:** aqui o pullback até era fundo (9,9 ATR/85 barras, pos96 0,38) — a superfície é de fundo legítimo.
**Depois:** subiu +8,9 ATR (quase pagou), depois a perna-mãe MORREU: −18,6 ATR em 4 dias (crash 20-28 out); SL em ~39h.
**Região:** tecnicamente razoável, estrategicamente péssima — último dip antes da virada de regime; nenhum nível segura quando a perna superior acaba.
**Contraste:** A4 (17-out, 2 dias antes) teve o mesmo problema e ESCAPOU pagando o 3×1 rápido antes da virada — em fim de perna madura, a diferença entre winner e loser foi o timing de saída, não a entrada.
**Decisão humana:** REVIEW — pullback ok, mas perna superior velha e parabólica: se tomar, alvo curto e zero re-entry.
**Lições:** o Reader precisa de "idade/extensão da perna superior" como dial de risco; pullback proporcional NÃO basta em perna terminal; erro: mesma mão para dip em perna jovem e dip em perna exausta.

## C4 · 2025-12-25 23:00 UTC — entrada A-BULL 4488,94 · SL em 124 barras (risk 5,0 ATR)
**Contexto superior:** topo do bull de dezembro; px_vs_ema_1d +23,1; pos384 0,83; **POLARIDADE TOPO do GT marcada 2025-12-26 16:00 — 17h depois desta entrada**.
**Path 15M:** dip de 5,4 ATR em 71 barras, liquidez de feriado (25-dez); compra no meio do range (pos96 0,53).
**Depois:** +7,2 ATR de teto (não pagou 3R), depois −25,5 ATR em 4 dias (a correção até 4274 de 31-dez); SL em ~31h.
**Região:** inválida — meio do ar em topo de perna, véspera de virada de polaridade que o próprio GT registou.
**Contraste:** E5 (31-dez, 6 dias depois) comprou o FIM dessa mesma correção num reteste de região de 353h e pagou — C4 e E5 são o par antes/depois da mesma perna corretiva.
**Decisão humana:** SKIP — dip raso em topo + liquidez de feriado.
**Lições:** posição no swing superior é a evidência; calendário/liquidez merece flag; erro: comprar continuação quando a devolução ainda nem começou.

## C5 · 2026-01-13 13:30 UTC — entrada A-BULL 4617,97 · SL em 28 barras (risk 5,9 ATR)
**Contexto superior:** BULL alto (pos384 0,95; px_vs_ema_1d +28,4); **mesmo dia e mesma área do INVALIDO B4** ("pequena acumulação").
**Path 15M:** dip de 3,8 ATR em 81 barras (lento e raso), compra a pos96 0,79.
**Depois:** −6,3 ATR em 24h; SL em 7h. O chop seguiu (fwd384 +9,5/−10,6) — não havia trade para nenhum lado.
**Região:** inválida — exatamente o que o Cris invalidou à mão: micro-acumulação rasa no alto da perna, sem devolução.
**Contraste:** A5 (08-jan) — mesma perna bull, 5 dias antes: 13,9 ATR devolvidos até polaridade = +36 ATR; C5: 3,8 ATR devolvidos até nada = SL. A regra do Cris para B4 já cobria este loser.
**Decisão humana:** SKIP — o GT humano marcou a área como inválida no próprio chart.
**Lições:** os 4 INVALIDO são regras de corte diretamente transferíveis para os losers A-BULL (mesma assinatura); a automação deveria testar cada candidato contra "isto seria um INVALIDO do Cris?" antes de qualquer feature de gatilho.

## C6 · 2026-03-02 23:00 UTC — entrada A-BULL 5338,57 · SL em 41 barras (risk 6,1 ATR)
**Contexto superior:** HORAS depois do topo histórico 5419 (02-mar 07:15) — o pico de todo o bull 2025-26; px_vs_ema_1d +20,4; pos384 0,73; net96 ainda +5,9 ATR.
**Path 15M:** dip de 6,5 ATR em 59 barras a partir do topo; compra do "primeiro pullback" da nova perna bear que ninguém sabia que tinha começado.
**Depois:** teto +3,1 ATR; −25,7 ATR em 4 dias (início do colapso de março); SL em ~10h.
**Região:** inválida — primeiro dip pós-topo de ciclo: estatisticamente indistinguível de pullback normal ATÉ olhar a extensão acumulada e a perda de momentum da perna superior.
**Contraste:** F1 (29-jan) é o mesmo arquétipo no topo de janeiro (comprar o primeiro recuo raso após pico vertical) — ambos capturados pela mesma leitura "repique/dip raso com perna-mãe recém-virada", que o filtro capitulation formalizou DENTRO do bear.
**Decisão humana:** SKIP/REVIEW — depois de topo em máxima histórica com extensão recorde, o primeiro dip não é compra; exige defesa comprovada.
**Lições:** o regime v5 ainda dizia BULL (vira BEAR dias depois) — o Reader não pode depender só do rótulo de regime, precisa ler a transição (perna superior recém-quebrada); erro: confiar em regime causal atrasado no exato momento da virada.

---

# D) 5 casos onde o A2 (anchors por região) FALHOU

## D1 · 2025-10-15 09:00 UTC — FUNDO GT · A2 = **MISS** (nenhuma região; sem reconstrução tardia)
**Contexto superior:** bull parabólico de outubro em pleno voo (net384 +22,4 ATR; pos384 0,94).
**Path 15M:** a vela marcada está a pos96 **0,87**, só 2,1 ATR abaixo de um topo feito 3 barras antes; o low do dia (4097) tinha sido 76 barras (19h) antes. É um **higher-low raso de continuação**, marcado no alto do range.
**Depois:** consolidou 12h (reclaim 50 barras), depois +24,3 ATR em 4 dias. Pagou como continuação.
**Região:** não há região — o preço está em máxima histórica; o "fundo" é estrutura de fluxo (HL de micro-pullback), não nível.
**Contraste:** A2-dossiê (10-out) é fundo por devolução profunda a nível; D1 é fundo por posição RELATIVA na micro-estrutura de trend — os anchors por região cobrem o primeiro tipo e são cegos, por construção, ao segundo.
**Decisão humana:** REVIEW — só é comprável como continuação de trend (outra tese, outro risco), não como reversão.
**Lições:** o GT "VELA DE FUNDO" contém ≥2 espécies (reversão-em-nível e HL-de-continuação); qualquer detector single-espécie vai "falhar" no GT misto; primeiro passo da automação: separar as espécies ANTES de medir recall.

## D2 · 2026-03-24 13:00 UTC — FUNDO GT · A2 = **MISS**
**Contexto superior:** dia seguinte ao clímax A6; bear de março terminado; preço 40,7 ATR abaixo do topo de 02-mar, construindo reversão.
**Path 15M:** higher-low ~240 pts acima do low 4126 de 23-mar; ATR ainda gigante (25,9); pos96 0,35; reclaim em 4 barras; reteste em 18 barras segurou.
**Depois:** +8,6 ATR em 24h com só 1,0 ATR de risco abaixo — assimetria excelente; era o 2º degrau da reversão de março.
**Região:** válida por ESTRUTURA (HL pós-capitulação confirmando CHoCH), não por nível: o pânico criou preço onde não existe região histórica utilizável → A2 sem âncora.
**Contraste:** B1 (05-mar) também era "primeira reação após queda" e falhou — a diferença: B1 reagia DENTRO de perna viva; D2 reage DEPOIS do clímax terminal (A6), com low-mãe já defendido.
**Decisão humana:** TAKE — HL pós-clímax é a entrada clássica da família BEAR-reversal.
**Lições:** pós-capitulação, a evidência é sequência (clímax → HL → reclaim), não nível; anchors por região são inúteis nas primeiras semanas após pânico; erro: exigir "zona histórica" onde o mercado acabou de inventar o preço.

## D3 · 2025-11-04 23:00 UTC — FUNDO GT · A2 = **MISS** — ver dossiê completo em **A10**
Resumo da falha A2: o fundo válido era um higher-low 47 pts ACIMA da região do low de 28-out — a demanda chegou antes do nível, o anchor esperava o reteste exato que nunca veio. Mesma lição de D1/D2: região ≠ fundo; o A2 falha sistematicamente quando a defesa acontece acima da estrutura anterior (que é justamente o sinal de demanda mais forte).

## D4 · 2025-09-05 13:45 UTC — DM (demanda fresca do GT PLT/DM) · miss do matcher A2 (r=4, 6, 8)
**Contexto superior:** bull de setembro acelerando; net384 +14,3 ATR.
**Path 15M:** a zona de demanda nasce **no topo absoluto** do range (pos96 0,98 / pos384 0,99): é a origem de um impulso de rompimento (a vela marca o último pullback antes do breakout — 1,3 ATR do high, 0 barras do topo).
**Depois:** +5,5 ATR em 24h, +9,4 ATR em 4 dias; a zona segurou (dn máx 2,5 ATR).
**Região:** válida como DEMANDA (origem de perna compradora institucional), inválida como "fundo" — e o A2 procura fundos.
**Contraste:** E3 (02-set, 3 dias antes) é demanda de pullback raso COBERTA pelo A2 porque ficou perto de bottom_region; D4 é demanda de breakout no teto — mesma família DM do Cris, geografia oposta.
**Decisão humana:** REVIEW — tese de continuação/breakout-retest, fora do mandato de fundo; só operável com regra própria.
**Lições:** DM ≠ FUNDO no GT do Cris; misturar as duas famílias num único detector de bottoms garante misses "falsos"; a automação deve rotular a espécie da zona (origem-de-impulso vs devolução-a-base) na criação.

## D5 · 2025-10-15 13:00 UTC — DM (demanda fresca do GT PLT/DM) · miss do matcher A2 (r=4, 6, 8)
**Contexto superior:** mesmo dia de D1; bull parabólico (net384 +16 ATR; pos384 0,92).
**Path 15M:** demanda marcada 3,6 ATR abaixo de topo de 19 barras, a pos96 0,81 — de novo zona nascida no ALTO do range, origem do impulso da tarde.
**Depois:** reclaim em 4 barras; +7,2 ATR em 24h, +19,1 ATR em 4 dias (com invalidação tardia: dn 11,7 ATR quando o regime virou dias depois).
**Região:** válida como demanda de continuação enquanto a perna viveu; morreu com a perna (20-out).
**Contraste:** com D4: idêntico arquétipo; com A2-dossiê (10-out): a demanda "de baixo" sobreviveu à virada de regime muito melhor que estas demandas "de cima" — altura da zona no swing prediz a sua meia-vida.
**Decisão humana:** REVIEW — só continuação, com validade condicionada à perna-mãe.
**Lições:** registar a ALTURA da zona no swing superior como atributo permanente da zona; não medir cobertura de DM com matcher de bottoms; erro: dar às zonas de continuação a mesma longevidade das zonas de base.

---

# E) 5 casos onde o A2 ACERTOU (COVERED_BOTTOM com idade razoável)

## E1 · 2025-04-09 02:00 UTC — FUNDO GT · A2 = COVERED_BOTTOM (B00529, idade 27,8h; + converted_near T00450)
**Contexto superior:** pânico macro de abril/2025 (semana de tarifas); queda de 16,9 ATR em 4 dias até 2970.
**Path 15M:** o mínimo real (2970) foi feito 10 barras antes da vela marcada; a vela (close 3007) já é a reversão em curso. Zona = bottom_region de ~28h + topo antigo convertido.
**Depois:** +12,3 ATR em 24h com dn de só 0,8; +24,6 ATR em 4 dias. **ENTRY GT 2025-04-10 09:00 a 2971 = reteste EXATO da zona do low, 31h depois** — o padrão lag-longo do catálogo em estado puro.
**Região:** válida — capitulação por evento + nível histórico duplo (bottom + polaridade) + reteste defendido.
**Contraste:** B3 (16-mar-2026) também tinha região histórica coberta em queda funda e era o meio da cachoeira — em E1 o clímax JÁ tinha acontecido (low absoluto + reversão em curso); em B3, não.
**Decisão humana:** TAKE — no reteste da zona (a ENTRY do Cris), não no meio do pânico.
**Lições:** o acerto do A2 aqui depende de o low coincidir com nível pré-existente — quando isso ocorre, idade 20-30h + reteste dá a entrada de maior qualidade do dataset; medir "reteste da zona do clímax" como gatilho.

## E2 · 2025-05-15 16:00 UTC — FUNDO GT · A2 = COVERED_BOTTOM (B00589, idade 6,8h; + converted_near T00524)
**Contexto superior:** fim da correção de maio (−27,8 ATR desde o topo 3434 de 06-mai).
**Path 15M:** o low do ciclo (3120) foi às 06:00; a vela marcada às 16:00 (close 3217) é a **vela de confirmação** — o preço já tinha subido ~12 ATR desde o low intradiário (pos96 0,97). Cris marca o fundo na confirmação, com a âncora-y da nota apontando ao low 3121.
**Depois:** reteste profundo: −8 ATR nas ~9h seguintes até a zona 3155; **ENTRY GT 2025-05-16 20:00 a 3154 = exatamente esse reteste (28h depois)**; dali +13,7 ATR em 4 dias.
**Região:** válida — V-reversal sobre bottom_region jovem (6,8h) + polaridade; o reteste que "tinha" de vir, veio, e foi comprado.
**Contraste:** A3 (dez/2025) foi lag-curto (reclaim imediato, sem reteste); E2 é o lag-longo extremo — as DUAS pontas do espectro de entry do catálogo (1,5h-38h).
**Decisão humana:** TAKE — mas só no reteste; comprar a vela de confirmação a pos96 0,97 daria stop no reteste de −8 ATR.
**Lições:** a vela de FUNDO do GT nem sempre é a vela de ENTRADA (aqui distam 28h e 60 pts); automação que trate a marca GT como ponto de entrada mede o padrão errado; o gatilho real = reteste da zona do low.

## E3 · 2025-09-02 07:00 UTC — FUNDO GT · A2 = COVERED_BOTTOM (B00871, idade 13,2h)
**Contexto superior:** bull de setembro jovem e forte (net384 +22,2 ATR); pullback raso de 5,8 ATR em 21 barras.
**Path 15M:** vela a pos96 0,42; reclaim em 19 barras (5h) — reação sólida sem pânico; zona de 13h defendida.
**Depois:** +14,7 ATR em 24h, +32,5 ATR em 4 dias. ENTRY GT 2025-09-02 13:00 (6h depois). Trades reais: #S18 (02-set 11:15) ✗ e #S19 (04-set 23:45) ✓ — dentro do MESMO fundo válido, uma entry morreu e outra pagou.
**Região:** válida — pullback raso de perna jovem sobre região recém-formada; o caso BULL-pullback "de manual" (retr ~0,17 do catálogo).
**Contraste:** C1 (16-set, 2 semanas depois) comprou dip raso PARECIDO e levou −22 ATR — diferença: E3 está na base de perna jovem (net96 +2,3 ATR, extensão moderada), C1 no topo de perna exausta (px_vs_ema_1d 73,6). Raso-em-perna-jovem ≠ raso-em-perna-velha.
**Decisão humana:** TAKE — com a ressalva do par #S18/#S19: a região certa ainda exige a entry certa.
**Lições:** idade da perna-mãe transforma a MESMA profundidade de pullback em setup oposto; e o par de trades prova que fundo válido ≠ trade ganho — o Reader pontua a região, a entry é camada separada.

## E4 · 2025-11-18 08:00 UTC — FUNDO GT · A2 = COVERED_BOTTOM (B00983, idade 199,5h)
**Contexto superior:** base de novembro madura (3 semanas após o crash de outubro; −26 ATR do topo na janela de 4 dias estendida); fundo do range a ser re-testado.
**Path 15M:** reteste de bottom_region com **8,3 dias** de idade; pos384 0,11; reclaim em 2 barras; dn forward 0,4 ATR — defesa limpa e imediata.
**Depois:** +8,1 ATR em 24h, +11,9 em 4 dias. ENTRY GT 2025-11-24 05:15 (dias depois, no degrau seguinte).
**Região:** válida — o arquétipo "zona defendida antes": low de range com histórico de defesa, macro-queda exaurida, base construída por semanas.
**Contraste:** B2 (mar/2026) era também reteste de região com >100h — e falhou porque a perna bear por cima tinha DIAS e seguia viva; E4 tem a queda-mãe com um MÊS e morta. Idade da região só vale com idade da queda-mãe.
**Decisão humana:** TAKE — reteste de base madura em queda exaurida.
**Lições:** par de features contextual mínimo = (idade da região defendida, idade+estado da perna de queda); qualquer uma sozinha falha (B2 é o contra-exemplo exato).

## E5 · 2025-12-31 06:00 UTC — FUNDO GT · A2 = COVERED_BOTTOM (B01051, idade 353,2h; + converted_near T01018)
**Contexto superior:** fim da correção pós-topo de dezembro (POLARIDADE TOPO GT em 26-dez); −17,1 ATR desde 4550 em ~2,5 dias.
**Path 15M:** low 4274 = mínimo de 96 E 384 barras, cravado sobre região de **2 semanas** de idade + polaridade; reclaim na barra seguinte; dn forward 0,4 ATR.
**Depois:** +6,1 ATR em 24h, +12,5 em 4 dias; trade GT #C10 (31-dez 09:30) ✓; ENTRY GT 2026-01-02 19:00 no degrau seguinte.
**Região:** válida — confluência dupla (bottom antigo + topo convertido) no término de uma correção proporcional (~50% da perna de dezembro devolvida).
**Contraste:** C4 (25-dez) comprou o INÍCIO desta mesma correção 214 pts acima e levou SL; E5 comprou o FIM dela em nível histórico — o par ilustra que a mesma perna corretiva contém o pior e o melhor trade da quinzena, separados só pelo LUGAR.
**Decisão humana:** TAKE — término proporcional + confluência de níveis + reclaim imediato.
**Lições:** o A2 acerta exatamente quando a correção morre EM CIMA de estrutura antiga; medir devolução proporcional (% da perna-mãe) como pré-condição; não serve entrar cedo só porque a correção "já caiu bastante" (C4).

---

# F) 4 cortes do filtro intra-BEAR capitulation (todos losers reais; SKIP correto)

## F1 · corte #55 · entrada 2026-01-29 20:30 UTC a 5354,63 · regime BEAR (v5) · 1D_px_vs_ema +14,99 → SKIP · resultado real: SL em 44 barras
**Contexto superior:** 21h após o topo histórico 5598 (28-jan); o "bear" tem HORAS de idade; ATR explodiu a 39,5.
**Path 15M:** a entrada compra um recuo de só 7,3 ATR abaixo do pico, a pos96 0,51 — repique/dip raso colado no topo do ciclo.
**Depois:** teto +2,4 ATR; −24,1 ATR em 4 dias (o crash de fevereiro). SL em ~11h.
**Região:** inválida — nenhuma capitulação: o preço está a 1 dia da máxima histórica; comprar LONG "em bear" aqui é comprar o topo com outro nome. O filtro (preço muito ACIMA da EMA-1D dentro de bear = repique raso) captura isto exatamente.
**Contraste:** A6 (23-mar) é o oposto polar: 33,7 ATR abaixo do topo, EMA-1D muito acima do preço, clímax terminal — o mesmo regime BEAR, pontas opostas da perna; o filtro mantém A6-likes e corta F1-likes.
**Decisão humana:** SKIP — bear recém-nascido não tem fundo para comprar.
**Lições:** dentro de BEAR, a posição vs EMA-1D é proxy honesta de "quanto da perna já aconteceu"; não serve nenhum gatilho local (reclaim havia); erro: deixar o engine de pullback operar em regime que acabou de virar.

## F2 · corte #57 · entrada 2026-02-10 14:15 UTC a 5070,08 · regime BEAR · 1D_px_vs_ema +7,85 (doc; CSV recalcula 15,74) → SKIP · resultado real: SL em 191 barras
**Contexto superior:** bear de fevereiro estabelecido (−40,8 ATR desde 28-jan), mas a entrada acontece no TOPO de um rally de urso: pos96 0,84, pos384 0,96 da janela local.
**Path 15M:** o preço subia havia dias (net96 +4,9 ATR) — compra-se a força DENTRO do bear, o repique clássico.
**Depois:** teto +3,7 ATR (nunca perto de 3R); reclaim da vela só 77 barras depois; −14,4 ATR na janela de 4 dias; SL em ~48h.
**Região:** inválida — topo de bear-market-rally: acima da EMA-1D dentro de bear = comprado em cima do repique, não no fundo dele.
**Contraste:** E5 tem superfície parecida (correção após topo, nível próximo) mas em regime BULL com correção proporcional terminada; F2 é a mesma foto com a perna-mãe apontando para baixo — o regime inverte o significado do MESMO desenho (a tese estrutural do doc N96: features invertem sinal por regime).
**Decisão humana:** SKIP — nunca comprar o alto de um repique dentro de bear vivo.
**Lições:** discrepância doc(7,85)/CSV(15,74) na feature = lembrete de fixar a definição canónica antes de automatizar; a evidência necessária é dupla (regime + posição na perna local); erro: usar o valor da feature sem a fase.

## F3 · corte #66 · entrada 2026-03-05 00:15 UTC a 5173,31 · regime BEAR · 1D_px_vs_ema +5,18 (doc; CSV 9,12) → SKIP · resultado real: SL em 52 barras
**Contexto superior:** 3 dias após o topo 5419; perna bear de março ATIVA (23,2 ATR abaixo do topo mas ainda no primeiro terço da queda total).
**Path 15M:** compra num bounce a pos96 0,67 (meio-alto do range de 24h) com a perna-mãe acelerando; teto +2,0 ATR; −11,4 ATR em 24h; SL em ~13h.
**Região:** inválida — **mesma área e mesma semana do INVALIDO B1 (05-mar 18:00)**: o engine mecânico comprou precisamente o bounce que o Cris riscou à mão como "perna bear clara antecede".
**Contraste:** direto com B1/B3 (a sequência de bounces da mesma perna): F3 é a versão "trade executado" do erro que B1 documenta como leitura.
**Decisão humana:** SKIP — reação técnica dentro de perna de baixa jovem.
**Lições:** a convergência GT-manual (B1) + filtro causal (corte #66) + resultado real (SL) no MESMO episódio é o melhor caso de validação cruzada do dossiê: a regra humana e o filtro medem a mesma coisa por caminhos independentes.

## F4 · corte #83 · entrada 2026-05-06 00:30 UTC a 4610,39 · regime BEAR · 1D_px_vs_ema +1,76 (doc; CSV 4,29 na 2ª entrada do dia) → SKIP · resultado real: SL em 679 barras
**Contexto superior:** grind-bear de maio (−27,8 ATR desde 17-abr, lento: 0,6 ATR/24b); sem capitulação em nenhum ponto.
**Path 15M:** compra a pos96 **0,99** — o extremo superior do range de 24h — dentro de bear; caso limítrofe do filtro (só +1,76 acima da EMA-1D).
**Depois:** o mais traiçoeiro dos 4: subiu +10,9 ATR (~113 pts) sem nunca alcançar o 3R (alvo ~194 pts) e morreu 679 barras (~7 dias) depois no SL — capital preso uma semana para perder.
**Região:** inválida — em grind-bear sem clímax não existe o fundo-de-capitulação que a família BEAR-reversal exige; o repique raso pode andar, mas não paga 3×1.
**Contraste:** A7 (jun/2026) também é bear em grind — mas a compra lá é no low absoluto da perna exaurida, não a pos96 0,99 de um repique; F4 mostra que "quase-capitulação" (EMA-dist ~0) ainda não é capitulação.
**Decisão humana:** SKIP — sem clímax e comprando topo de range em bear, o melhor cenário é empate demorado.
**Lições:** o custo do erro não é só o −1R, é o TEMPO (679 barras presas); thresholds contínuos têm zona cinzenta (+1,76) — o Reader deve tratar a faixa próxima de 0 como REVIEW, não como corte binário; erro: avaliar filtro só por R sem custo de ocupação.

---

# PADRÕES TRANSVERSAIS (o que os 34 dossiês mostram em comum)

1. **A pergunta nº 1 é sempre "a perna-mãe terminou?"** — todos os 4 INVALIDO e os 4 cortes F têm queda (ou topo recém-virado) ainda VIVO por cima; todos os winners A/E têm a perna-mãe terminada (clímax A6/E1), exaurida (A8, A9, E4) ou intacta a favor (A2, A3, E3). Nenhuma feature local (reclaim, região, profundidade) sobrevive a essa pergunta mal respondida — B1 tinha reclaim em 2 barras e era armadilha.
2. **Profundidade proporcional separa winners de losers dentro do MESMO regime.** A-BULL losers compram devoluções de 3,8-6,6 ATR em pernas com +14 a +30 ATR de extensão e pos384 0,73-0,95 (C1, C2, C4, C5); os winners BULL-pullback devolvem 9,8-13,9 ATR até estrutura (A2, A3, A5). B4/C5 (mesma área, mesmo dia, GT e engine) confirmam: "dip raso no alto sem pullback proporcional" é a assinatura única do loser A-BULL.
3. **Região ≠ validade — são eixos independentes.** O A2 cobriu 3 dos 4 INVALIDO (B2, B3, B4 tinham bottom_region ativa) e falhou em 3 fundos válidos (A10, D1, D2). Nível existente sem término de perna = isca; término de perna sem nível histórico = fundo real que anchor nenhum vê.
4. **Os MISS do A2 são todos da mesma espécie: a defesa acontece ACIMA/AO LADO da estrutura anterior** — higher-lows (A10/D3, D2), HL raso de continuação (D1) e preço virgem pós-pânico ou em máxima histórica (A8, D2). A demanda mais forte chega ANTES do nível; um Reader por regiões precisa de um segundo olho estrutural (sequência clímax→HL→reclaim) para não perder justamente os melhores.
5. **DM ≠ FUNDO.** As demandas do GT PLT/DM nascem no TOPO do range (D4 pos96 0,98; D5 0,81) como origem de impulso — medi-las com matcher de bottoms produz "misses" que não são erros do detector, são erro de taxonomia. Rotular a espécie da zona na criação (base-devolvida vs origem-de-impulso) antes de medir recall.
6. **A vela de FUNDO do GT não é a vela de ENTRY.** Distâncias medidas: 2,2h (A5) a 31h (E1); E2 tem reteste de −8 ATR entre a marca e a entry; A1 tem sweep de −6,3 ATR depois da marca. Automação que trate a marca GT como ponto de entrada mede o padrão errado e "descobre" stops que o Cris nunca tomou.
7. **Reclaim rápido é confirmação barata, não validador.** Winners limpos reclamam em 1-4 barras (A2, A3, A5, E5), mas B1 reclamou em 2 barras e era o meio da cachoeira; grind-bottoms válidos reclamam lento (A8: 14 barras). O reclaim só informa DEPOIS da leitura da perna-mãe.
8. **Bounces falhados contam contra o próximo.** A sequência B1→B2→B3 (cada bounce mais baixo, reclaims 2→81→54 barras, forward cada vez pior até −27,7 ATR) mostra que o número de reações falhadas da mesma perna é evidência mensurável e causal — o terceiro bounce da perna viva foi o mais letal do dossiê.
9. **Fim-de-perna-madura é o único lugar onde entrada boa + gestão errada = loser.** A4 e C3 têm pullbacks tecnicamente corretos a dias do topo de outubro; A4 pagou o 3×1 rápido, C3 segurou e morreu. Idade/extensão da perna superior deveria regular o ALVO (dial), não só o gatilho.
10. **A convergência tripla existe e é verificável:** no episódio 05-mar-2026, a regra manual do Cris (B1 INVALIDO), o filtro causal (corte F3/#66) e o resultado real (SL) apontam para a mesma leitura por caminhos independentes. É o template de validação do Reader: cada regra contextual candidata deve ser testada contra os INVALIDO do GT e contra os losers reais do mesmo instante antes de ganhar estatuto.
