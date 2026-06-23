# PHASE 3 AUDIT — FROZEN reading vs REAL outcome (Cluster 2 · XAU 4H · macro negativo)

> Auditor independente. A leitura do Reader foi CONGELADA antes deste arquivo existir.
> Canon: diagnóstico de QUALIDADE DE LEITURA por episódio. NÃO é validação de gate/edge/hit-rate. NÃO se conclui "promover".
> Convexidade (regra dada): desenvolveu = mfe_R ≥ 5 · falhou = mfe_R < 2.
> Fonte outcome: `l2_bpt_uncapped_or_proxy_outcomes_276.csv`. Fonte preço: `repro_recovery/raw_features_2020_2026.jsonl` (line idx = bar_idx).
> Sanity: os 10 timestamps de entry no JSONL batem 1:1 com as datas do FROZEN — mapping correto, cegueira preservada.

---

## TABELA POR EPISÓDIO

| EP | Sub | Natureza congelada (conf.) | Reader espera | mfe_R | Realidade | EXPECTATION cumprida? | VEREDICTO |
|----|-----|----------------------------|---------------|-------|-----------|------------------------|-----------|
| 5826 | A | (1) washout maduro c/ mudança de caráter (MED-ALTA) | desenvolve, holds >1831, sky 5.9ATR | **16.73** | DESENVOLVEU | SIM — closes seguram >1831 imediato (1848→1861 em 6b), nunca devolve <1820, runner +100pt em 40b | **ACERTOU a natureza** |
| 1623 | A | (6) timing ruim, comprou esticado (MED-BAIXA) | avanço imediato limitado + reteste/devolução <1840 | **0.31** | FALHOU | SIM — marginal new high (+21pt MFE em 6b) e depois colapso a 1831 (−21pt) em 32b; "comprou esticado" confirmado | **ACERTOU a natureza** |
| 4401 | B | (4) supply-as-fuel pós-capitulação (MED) | consome supply colado, aceita acima | **10.31** | DESENVOLVEU | SIM — rompe e aceita: +21pt em 3b, hold 1667–1680, runner +128pt em 39b | **ACERTOU a natureza** |
| 3825 | B | (5) supply-as-wall, momentum fraco (MED-ALTA) | rejeita no supply, lower high <1845, retoma bear | **0.96** | FALHOU | SIM — toca 1846 em 2b e devolve; cai a 1822 e segue a 1784 (−50pt em 38b) | **ACERTOU a natureza** |
| 1522 | C | (1) washout maduro, flush reabsorvido+aceito (ALTA) | desenvolve, holds >1873, pullbacks respeitam 1857 | **5.65** | DESENVOLVEU | SIM — segura a base, nunca volta ao fundo do flush, runner +76pt em 40b | **ACERTOU a natureza** |
| 1873 | C | (2) bear-pullback trap, entry vermelha (MED-ALTA) | nova rejeição <supply, retoma bear → 1719 | **1.20** | FALHOU | SIM — repica fraco a 1746 (+15pt) e morre; desce a 1705 (−25pt em 40b) | **ACERTOU a natureza** |
| 5627 | C | (5) supply-as-wall + vácuo 12.22ATR (ALTA) | rejeita no supply 1903–04, risco de queda ampla | **5.96** | DESENVOLVEU | **NÃO** — coila exatamente em 1902–1905 por 3 barras (nível certo!) e então ACEITA: rompe a 1917 em +5b, sobe a 1949 em 36b. O vácuo embaixo nunca foi acionado | **ILUDIDO** |
| 1775 | C | (3) base/absorção incompleta — resíduo honesto (BAIXA-MED) | V cru sem confirmação → reteste/indecisão antes de qualquer reclaim; se trap, low <1783 | **0.53** | FALHOU | SIM (cenário trap) — +8pt no 1º bar e morre; quebra 1783, despenca a 1687 (−110pt em 38b); foi a perna inferior do par | **resíduo-honesto confirmado (caiu p/ trap)** |
| 3949 | D | (1) washout maduro; etiqueta REJECTED_AT_RES engana (MED-ALTA) | desenvolve, aceita acima do supply, V continua | **6.62** | DESENVOLVEU | SIM — após 2 barras de digestão sobe a 1737 (+16pt), aceita, runner +57pt em 40b; nunca volta ao fundo 1680 | **ACERTOU a natureza (leu o inverso da etiqueta — correto)** |
| 3929 | D | (2) bear-pullback trap; etiqueta ACCEPTED_ABOVE_RES engana (MED-ALTA) | falha logo acima, lower high, retoma bear | **0.05** | FALHOU | SIM — entry vermelha já devolvendo; cai imediato a 1706, depois a 1681 (−38pt em 18b); nunca subiu | **ACERTOU a natureza (leu o inverso da etiqueta — correto)** |

**Placar de naturezas: 9/10 corretas. 1 ILUDIDO (5627). 0 resíduos não-honestos.**
O único resíduo declarado (1775) confirmou-se como caso genuinamente difícil — e o Reader o tratou com a confiança mais baixa do bloco e o registrou como tensão honesta, não como acerto forçado.

---

## TABELA POR PAR

| Par | Hipótese do Reader ("qual se desenvolve") | Realidade (mfe_R) | Hipótese bateu? |
|-----|--------------------------------------------|-------------------|-----------------|
| **A** 5826 vs 1623 | 5826 desenvolve (hold pós-base) · 1623 falha (esticado) | 16.73 vs 0.31 | **SIM, ordenação perfeita** |
| **B** 4401 vs 3825 | 4401 consome supply (fuel) · 3825 rejeita (wall) | 10.31 vs 0.96 | **SIM, ordenação perfeita** — mesma etiqueta HOLDING_SUPPORT, leitura oposta correta |
| **C** 1522/1775/1873/5627 | ordem de maturidade: 1522 desenvolve · 1873+5627 rejeitam · 1775 indeciso | 1522=5.65 ✓ · 1873=1.20 ✓ · 1775=0.53 ✓(trap) · **5627=5.96 ✗** | **3/4** — errou só 5627 (chamou wall, virou fuel) |
| **D** 3949 vs 3929 | 3949 desenvolve · 3929 falha — INVERSO das etiquetas de aceitação | 6.62 vs 0.05 | **SIM, ordenação perfeita** — o par-armadilha foi lido exatamente ao contrário das labels, e a forma mandou |

---

## SÍNTESE DO TESTE

### 1. O Reader QUEBROU a regra falsa "weekly negativo = pullback que falha"?
**Sim, decisivamente.** Todos os 10 têm weekly<0 e cascade profundo. Um Reader preso à regra falsa cortaria tudo como trap → acertaria os 5 losers e perderia os 5 runners (incl. 5826 +16.7R, 4401 +10.3R, 3949 +6.6R, 1522 +5.65R). O Reader chamou **4 dos 5 runners de desenvolvíveis em macro negativo** (5826, 4401, 1522, 3949), inclusive em macro EXTREMO (3949, weekly −0.666). E chamou **5/5 losers de falha/parede/trap**. O eixo de discriminação NÃO foi o weekly — foi a forma do ciclo capitulação→reabsorção→aceitação. A regra falsa foi quebrada na prática, não só na retórica.

### 2. O eixo de discriminação SUSTENTOU contra a realidade?
**Sustentou em 9/10.** Onde sustentou bem:
- **Maturidade da queda (clímax real vs declínio morno):** todos os 4 runners que o Reader leu vieram de exausto/clímax visível e superado (5826 rsi 30.8; 4401 rsi 29.4 + drop 5.2ATR; 1522 flush 5.32ATR; 3949 rsi 27.9 + V de range 29.5). Todos os losers vieram de declínio sem clímax (3825 vel 0.0; 3929 drop 1.72 sweep 0; 1623 drop 1.25 esticado). O eixo funcionou.
- **Entry-bar HOLD vs comprando-recuperação:** a cor/energia da barra de entrada foi um discriminador BRUTO e correto. As duas barras de entrada **vermelhas** (1873 body −3.3; 3929 body −3.1) falharam ambas. As barras de HOLD/digestão verde (5826, 1522) e expansão fresca pós-clímax (4401, 3949) desenvolveram. "Comprar uma recuperação que já está falhando" (entry vermelha) provou-se sinal de morte.
- **Reclaim aceito por barras inteiras vs tocado:** 1522 (lateralização aceita) e 3949 (continuação+BOS após V profundo) desenvolveram; 1873 (reclaim rejeitado) e 3929 falharam. O eixo segurou.

Onde NÃO sustentou:
- **5627** — único furo. O Reader leu "REJECTED_AT_RES honesto + flush fictício 1.87 + supply colado 0.85 + demanda 12.22ATR (vácuo)" → parede com a pior localização. A realidade: o preço coilou exatamente no nível de supply que o Reader nomeou (1902–1905, tocando 1905.4) por 3 barras e então **aceitou e rompeu** (+5.96R, +51pt em 36b). O Reader acertou ONDE estava a parede mas errou se ela seria consumida. A âncora que mais pesou contra (demanda 12.22ATR embaixo) é irrelevante quando o preço sobe — virou um falso agravante. **Lição:** "supply colado + flush raso" não é suficiente para chamar wall; faltou ao Reader uma lente de *contexto de momentum/regime local* que distinguisse coil-antes-de-aceitar de rejeição-terminal. O drop raso (1.87) que o Reader leu como "nada para esgotar" também pode significar "nenhum vendedor pesado presente" — ou seja, range apertado sob supply pode ser acumulação silenciosa, não exaustão. O Reader leu o range estreito só como ausência-de-clímax (bearish), nunca como compressão-construtiva (bullish). Viés direcional na leitura de range apertado.

### 3. Sub-bloco D (acceptance textual invertida): o Reader leu o inverso das etiquetas — acertou?
**Acertou os dois, na ordem perfeita.** 3949 (etiqueta REJECTED_AT_RES) → leu reversão → +6.62R. 3929 (etiqueta ACCEPTED_ABOVE_RES) → leu trap → +0.05R. O diferenciador que o Reader nomeou — presença de clímax + V de grande amplitude + reabsorção profunda + cor da barra de entrada — foi exatamente o que separou. Este par é a evidência mais limpa de que a **acceptance textual isolada engana e a forma 4H manda**. Quem seguisse a etiqueta erraria os dois. O Reader fez o contrário e acertou os dois. É o resultado mais forte do cluster.

### 4. A lente OM1 (supply momentum-condicionado) ajudou no par B?
**Sim, foi o coração do acerto.** 4401 e 3825 carregam etiqueta idêntica (HOLDING_SUPPORT, supply ~0.3ATR colado). A lente que distingue "supply como combustível" (impulso fresco pós-clímax chegando à parede com energia) de "supply como parede" (momentum fraco arrastando-se à faca) separou 10.31R de 0.96R. A condicionalidade do supply ao **momentum/maturidade do impulso que chega nele** — não à distância do supply isolada — foi validada. OM1 sustentou.

### 5. Os erros/ambiguidades eram casos difíceis reais ou sinal recuperável?
- **1775 (resíduo honesto declarado):** caso difícil REAL, não preguiça. A barra de reabsorção era genuinamente forte (body +12, sweep depth 1.1) — o Reader registrou a tensão "base incompleta vs trap" e deu confiança BAIXA-MÉDIA. A realidade resolveu para trap brutal (−110pt). **Recuperável?** Sim, parcialmente: o discriminador que teria desempatado já estava na própria leitura do Reader e ele o sub-pesou — `BROKE_SUPPORT` + reclaim abaixo do supply + **rsi no fundo AGORA (comprando NO exausto, não DEPOIS dele)**. Esse "comprando no exausto vs depois do exausto digerido" é exatamente o que separou 1775 (falhou) de 5826/3949 (digeriram o exausto antes). A lente existe; faltou ao Reader confiar nela o suficiente para sair da ambiguidade. Não é resíduo irredutível — é resíduo **recuperável pela própria lente do Reader subponderada**.
- **5627 (o ILUDIDO):** caso difícil real, mas o erro foi **sistemático, não aleatório**: viés de ler range-apertado-sob-supply sempre como bearish (ausência de clímax) e nunca como compressão construtiva. Recuperável com uma lente nova (abaixo).

### 6. Algum acerto foi sorte / hindsight-friendly? (honestidade brutal)
- **1623** é o acerto mais frágil. O Reader chamou "timing ruim, comprou esticado" e esperou "avanço limitado + reteste OU devolução". A realidade fez um *new high marginal* (+21pt MFE) ANTES de colapsar — ou seja, o cenário do Reader de "continuação esticada com energia já consumida" estava certo no espírito, mas o trade nominalmente quase deu certo intraday antes de falhar. mfe_R=0.31 (proxy stop cedo + mae 1.35) classifica como falha pela regra, e a natureza "esticado que devolve" bateu — mas se a janela de avaliação fosse mais curta, o veredicto poderia inverter. Acerto **legítimo mas não limpo**; depende da definição de convexidade.
- **3949** foi lido com cautela explícita ("macro EXTREMO + algum esticamento") apesar da forma forte — a cautela calibrada significa que não foi overconfidence afortunada.
- Os demais acertos (5826, 4401, 3825, 1522, 1873, 3929) são limpos: forma diagnóstica clara → outcome consistente, sem necessidade de hindsight.
- **Nenhum acerto foi pura sorte.** O único caso onde o veredicto de convexidade é sensível à janela é 1623, e mesmo lá a *natureza* lida estava correta.

### 7. LIÇÕES p/ a biblioteca (lentes/perguntas NOVAS — diagnóstico, sem gate/score/promoção)
1. **Lente "range-apertado-sob-supply: compressão construtiva vs exaustão-de-nada" (de 5627).** O Reader tem viés de ler range estreito sem clímax como bearish (vácuo de venda / nada para esgotar). Mas range apertado COLADO ao supply, sem novos lows, com defesas repetidas, pode ser acumulação silenciosa que aceita o supply na primeira tentativa. Pergunta nova: *o range estreito está fazendo lower lows (corrosão → wall) ou higher lows / lateral defendido sob o supply (compressão → fuel)?* 5627 estava lateral-defendido sob 1904, não corroendo. Essa é a feature que faltou.
2. **Lente "comprando NO exausto vs DEPOIS do exausto digerido" (de 1775, já latente na leitura do Reader).** rsi_min8 no fundo AGORA na barra de entry = comprando o susto, não a recuperação confirmada. Promover esta distinção a discriminador de PRIMEIRA ordem (não nota de rodapé) teria desempatado 1775. Pergunta: *o exausto foi superado E digerido por barras antes da entry, ou a entry coincide com o fundo do rsi?*
3. **Confirmação da lente entry-bar-color como primeira ordem.** As 2 únicas entries vermelhas (1873, 3929) falharam. "Comprar uma barra de entrada vermelha em macro negativo" foi sinal de morte 2/2. Robustez n pequeno, mas o sinal é forte e mecanicamente coerente (entry já devolvendo = momentum virou antes da compra).
4. **Confirmação: acceptance textual é anti-sinal em macro negativo, a forma manda (sub-bloco D).** Não inverter cegamente, mas tratar a etiqueta de aceitação como ruído e reconstruir a aceitação pela FORMA (clímax + V + reabsorção profunda + cor da barra) provou-se superior 2/2 no par mais adversarial.
5. **OM1 validada como lente de par B:** supply é fuel-ou-wall condicionado ao momentum/maturidade do impulso que chega nele, NÃO à distância isolada do supply.

---

## CONCLUSÃO DO AUDITOR
A leitura cega **quebrou a regra falsa** e discriminou 9/10 episódios pela FORMA/mecanismo, não pelo weekly — incluindo a ordenação perfeita dos 4 pares de mesma-superfície (A, B, D) e 3/4 do bloco C. O sub-bloco D (etiquetas invertidas) foi lido exatamente ao contrário das labels e acertou os dois — o resultado mais forte do teste. O único furo (5627) é um erro sistemático recuperável: viés de ler range-apertado-sob-supply sempre como bearish. O único resíduo honesto declarado (1775) era caso difícil real, mas recuperável pela própria lente do Reader (comprando-no-exausto) que ele subponderou. Nenhum acerto foi sorte; o único veredicto sensível à janela de convexidade é 1623, onde a natureza ainda assim bateu.

Diagnóstico de qualidade de leitura: **ALTA**. Eixo (estado do ciclo capitulação→reabsorção→aceitação lido pela forma) **SUSTENTOU**. Duas lentes novas emergem (compressão-construtiva-sob-supply; comprando-no-exausto-vs-digerido). Sem conclusão de promoção — canon respeitado.
