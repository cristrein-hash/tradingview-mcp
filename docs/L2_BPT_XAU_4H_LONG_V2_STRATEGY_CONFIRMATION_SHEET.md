# STRATEGY CONFIRMATION SHEET — L2/BPT XAU 4H LONG · RTSE V2 ZONA-PURA

**Data:** 2026-07-02
**STATUS:** `USER_APPROVED_NOT_PRODUCTION` (Cris 2026-07-02, escopo B — integral + caveats) · **NOT_PRODUCTION**
**FLAGS:** `OK_FINAL_BY_CRIS_2026_07_02` · `VISUAL_REVIEW_COMPLETED_BY_USER` · `FINAL_APPROVED_BY_USER` · escopo B integral + caveats
**Natureza:** confirmação integral pré-OK-final. Sem mudar lógica, sem otimizar, sem procurar gates novos, sem rebaixar a tese. Números reproduzidos a partir dos scripts aprovados (`phase47/48`), não backtest novo. Devil's Advocate executado (secção 8).
**Regras respeitadas:** sem produção, sem Telegram/monitor/catalog/strategy_rules/runtime, sem push, sem editar status master.

---

## 1. Identidade da estratégia

| Campo | Valor |
|---|---|
| Nome completo | L2/BPT XAU 4H LONG — Engine estrutural de níveis de regime, **V2 zona-pura** |
| Módulo/pasta | `regime_turnstate_engine/validation/` (scripts `phase47_zone_entries.py`, `phase48_bear_deep_zone.py`) |
| Detector de regime | `regime_turnstate_engine/validation/phase10_hybrid_regime.py` (FSM híbrido evento+estrutura) |
| Timeframe | 4H |
| Ativo | XAUUSD |
| Direção | LONG only |
| Universo/base | Livro L2/BPT canónico = **N128** sinais (régua `l2_bpt_regua_structural.csv`), período efetivo com regime ≥ 2023 |
| Relação L2/BPT ↔ RTSE | Os **sinais de entrada** (candidatos LONG) vêm do motor L2/BPT (BOS-CHoCH bottom); o **RTSE** (regime + zonas) é a camada de **seleção estrutural** que filtra QUAIS sinais L2 tomar, por regime e por zona. V2 = L2 (o quê) × RTSE (quando/onde) |

---

## 2. Tese operacional (linguagem simples)

- **O que compra:** sinais LONG do motor L2/BPT (reversão de fundo BOS-CHoCH), mas **apenas** quando o preço de entrada cai **dentro de uma zona estrutural** definida pelo regime anterior, escolhida conforme o regime corrente.
- **Leitura de mercado:** cada regime (BULL/RANGE/BEAR) deixa níveis (topo/fundo). O regime seguinte tende a **reagir** a esses níveis. A estratégia posiciona a entrada onde a estrutura anterior dá suporte, e evita comprar "no ar" (esticado) ou "na faca" (no meio de um bear precoce).
- **Ideia de edge (declarada):** a **posição do entry vs os níveis hi/lo do regime anterior**, condicional à direção, separa entradas boas de más. → **Ver secção 8: o DA mostra que o efeito realizado é maioritariamente beta de regime (long em RANGE/BULL, evitar BEAR) + convexidade colhida pelo let-run, não alpha puro de timing de entrada. Isto é caveat documentado, não refutação da tese — a estratégia continua aprovada pendente da tua decisão.**
- **"Posição do entry vs níveis hi/lo do regime anterior":** para cada trade olha-se o **segmento de regime imediatamente anterior** (ou os anteriores, no BEAR). O seu `hi` e `lo` são conhecidos **no fecho desse segmento** (antes do atual começar) → causal. A zona = um terço (`amp/3`) junto ao nível relevante.
- **Como BULL/RANGE/BEAR entram:**
  - **BULL** → só entra se o entry cair no **terço superior** do regime anterior (`[hi_prev − amp/3, hi_prev]`) = reteste-suporte após rompimento. Corta esticadas (acima) e middle.
  - **RANGE** → só entra no **fundo do range corrente** (`pos < 0,34`).
  - **BEAR** → só entra na **capitulação profunda** (terço inferior da acumulação de onde partiu a subida que o bear corrige). Corta as facas precoces no topo do bear.
- **O que é V2 zona-pura:** a versão "sem variáveis inventadas" — a entrada é decidida **puramente pela zona estrutural** (terço do regime anterior + pos do range), sem `dist`/`rsi`/`nearest_below` (que eram aproximações da V1 mal-calibradas).
- **V1 (superseded):** esqueleto por `dist=(entry−nível)/ATR` + RSI + regras skip-faca/cap-bull (+53,7→+63,1R). Deixava passar esticadas/facas por o `dist` ser uma aproximação. **Superseded** pela V2 (mais segurável, zona direta).
- **V3 (rejeitada):** "gatilho-de-zona" — a zona DEFINE a entrada (entra no toque da zona, não no sinal L2). N31 +64,6R, **mas** o excesso era beta do let-run (RANGE +43R carregado por 3 held-120); Cris rejeitou (piorou vs V2). Único resíduo não-beta: bull-fallback n6.

---

## 3. Predicados exatos (V2 zona-pura)

**Fonte da lógica:** `phase48_bear_deep_zone.py` (definição BEAR canónica da memória) e `phase47_zone_entries.py` (variante BEAR — ver secção 8/Q3). Ambos consomem:
- `phase10_hybrid_regime.py` via `reg = P.run(0.03, 1.15, 0.88)` → produz `/tmp/causal_segments_v10.json` (lista de segmentos de regime, cada um `{start, end, regime, hi, lo}`).
- Régua de R: `my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv`.

**Para cada sinal L2 (linha da régua, `bar_idx`):**
1. `t = T[bar_idx]`; `idx = seg_idx(t)` (segmento de regime que contém o entry). Se `idx is None` ou `idx == 0` → **excluído** (trades antes do 1º segmento / sem prior).
2. `s = segs[idx]` (regime corrente); `prev = segs[idx-1]` (regime anterior); `entry = float(row["entry"])`.
3. `amp = prev.hi − prev.lo`.
4. **Zona BULL (ztop):** `[prev.hi − amp/3, prev.hi]`.
5. **Zona BEAR:**
   - `phase48` (**canónica**): `bear_deep(idx)` = `lo_min` dos segmentos com `bars ≥ 15` nos `180 dias` antes de `s.start`; zona = `[lo_min, lo_min + amp_max/3]` (amp_max = maior amplitude entre esses candidatos). Se não houver candidatos em 180d, alarga para todos ≥15 barras.
   - `phase47` (**variante**): `refs = segs[idx-3 : idx-1]`; `zbot = [min(refs.lo), min(refs.lo) + max(refs.amp)/3]`.
6. **RANGE:** `pos = (entry − rmin)/(rmax − rmin)`, onde `rmin/rmax = min L / max H` de `s.start` até `bar_idx` **inclusive** (só barras até ao entry).
7. **Regra `keep(x)`:**
   - `BULL` → `ztop.lo ≤ entry ≤ ztop.hi`
   - `BEAR` → `zbot.lo ≤ entry ≤ zbot.hi` (zona conforme script)
   - `RANGE` → `pos < 0,34`
8. **Exclusões:** tudo o que não cai na zona do seu regime; trades sem prior (`idx≤0`).
9. **R:** `R = round(letrun_struct − 0,35, 2)` — **let-run** (HZ120), UNCAPPED, com **SL_CONTEXT** (SL e risco por trade já embutidos na régua nas colunas `sl`/`risk`), menos custo fixo **0,35R**.
- **Dependência `phase10_hybrid_regime.py`:** total — define os segmentos, os regimes e portanto TODAS as zonas. Thresholds `run(0.03, 1.15, 0.88)` (ver secção 8/Q2: escolhidos por grid contra `cris_regime_boxes.csv`).
- **Dependência SL_CONTEXT / let-run:** o R vem da coluna `letrun_struct` da régua = saída let-run com SL estrutural contextual. Não há target fixo; a saída é horizonte/SL.

---

## 4. Fonte de dados e causalidade

| Item | Estado |
|---|---|
| RAW/source que alimenta | `my-strategy/research/revalidation/raw_4h_ohlc.jsonl` (OHLC 4H RAW) → `phase10` calcula regime; `l2_bpt_regua_structural.csv` (entry/sl/risk/letrun) derivada dos sinais L2/BPT sobre RAW |
| Campos RAW | OHLC 4H (`raw_4h_ohlc.jsonl`); ground-truth `cris_regime_boxes.csv` (regime desenhado por Cris, usado só para calibrar o detector) |
| Campos derivados | regime/segmentos (`phase10`), EMA/RSI/CUSUM (fechados), ATR (lag i−1), zonas (hi/lo prior), `letrun_struct`/`sl`/`risk` (régua) |
| **SLIM/proxy?** | **NÃO.** Usa RAW OHLC + régua derivada de RAW. Sem SLIM. |
| **Look-ahead?** | **NÃO (confirmado pelo DA, Q1 PASS).** Zonas usam só segmentos anteriores (`j < idx`); o hi/lo do segmento **corrente NÃO vaza** para a sua própria zona; `pos` usa só barras `≤ bar_idx`; pivôs do FSM aplicados na barra de **confirmação** (`piv[pi][0] ≤ i`), não na barra do pivô; EMA/RSI/CUSUM closed-bar; ATR lag i−1. `letrun_struct` é outcome forward a partir do entry (target legítimo, não feature). |
| Como os níveis do regime anterior são conhecidos no entry | O segmento anterior **terminou** antes do atual começar → o seu hi/lo está fixado no fecho dele, antes de qualquer barra do regime corrente. Causal por construção. |
| Usa informação futura? | Não para decidir a entrada. **Caveat estrutural (DA Q1):** a significância `bars ≥ 15` de um segmento só é conhecida após ele fechar — ok para segmentos anteriores, mas frágil se um segmento ainda está a formar-se (não afeta os 17 trades históricos, todos com priores fechados). |

---

## 5. Resultado principal da V2 zona-pura (reproduzido)

**Script `phase48_bear_deep_zone.py`, painel ZONA-COMPLETA:**

| Métrica | Valor |
|---|---|
| N | **17** |
| WR | **53%** |
| sumR | **+36,2R** |
| avgR | **+2,13** |
| DD | **−4,1R** |
| streak (perdas seguidas máx) | **3** |
| big (R≥3) | 5 |
| Composição | **BULL 6 / BEAR 1 / RANGE 10** |
| Base/período | livro N128, trades com regime ≥ 2023 (2023-03 a 2025-10) |
| Tipo de resultado | **let-run (HZ120), UNCAPPED, com SL_CONTEXT, menos custo 0,35R.** Não é close_R, não é target-hit, não é capped. |

Referência (sem seleção): **BASE N128 WR33% +26,1R DD−21,8 streak11 big18**.
✅ **Reproduz exatamente os números da memória da sessão anterior.**

---

## 6. Decomposição por regime

| Regime | N | sumR | avgR | WR | Rs individuais | Papel |
|---|---:|---:|---:|---:|---|---|
| **BULL** | 6 | +4,5 | +0,75 | 50% | −1,4 / −1,4 / −0,0 / +4,2 / +1,3 / +1,7 | Reteste-suporte no topo do regime anterior. Contribuição pequena mas positiva; sem winner isolado dominante. |
| **BEAR** | 1 | +8,0 | +7,99 | 100% | +8,0 | Só a capitulação profunda 2023-10-06. Estruturalmente correto (cai na zona [1805,1862]) mas **n=1**. |
| **RANGE** | 10 | +23,7 | +2,37 | 50% | **+12,0 / +8,6** / +7,0 / +1,7 / +1,1 / −1,4 ×4 | Fundo de range. **Metade do lucro total.** |

**Quem sustenta o edge realizado:** RANGE (+23,7R) + a única BEAR (+8,0R). BULL contribui pouco (+4,5R).
**Concentração (drop-top):** total +36,2 → drop-top1 **+24,2** → drop-top2 **+15,6** → drop-top3 **+7,6**. Top-3 = `2023-03-08 RANGE +12,0`, `2023-03-09 RANGE +8,6`, `2023-10-06 BEAR +8,0`. **O episódio RANGE de mar-2023 (bar_idx 4918+4926) sozinho = +20,6R dos +23,7R do RANGE.**

**Onde está o risco (sem rebaixar):**
- **RANGE** carrega o lucro mas está concentrado num episódio + é o componente que o DA marca como beta (ver 8/Q6). **Caveat, continua dentro da estratégia aprovada.**
- **BEAR** é n=1 → correto estruturalmente, sem robustez estatística. **Caveat aceite, continua dentro.**
- **BULL** é o componente mais "limpo em direção" mas de contribuição pequena.

---

## 7. Lista dos 17 trades (V2 zona-pura)

`chronological_id` = `bar_idx` (índice da barra 4H; serve de id estável). SL/risk das colunas `sl`/`risk` da régua (pts). Zona = zona de preço usada (RANGE usa `pos<0,34`, sem zona de preço fixa → "pos").

| # | bar_idx | data | regime | entry | zona [lo, hi] | pos | SL | risk(pts) | R | nota |
|--:|--:|---|---|--:|---|--:|--:|--:|--:|---|
| 1 | **4918** | 2023-03-08 | RANGE | 1820.4 | pos | 0.14 | 1804 | 16.4 | **+11.98** | fundo de range (top winner) |
| 2 | **4926** | 2023-03-09 | RANGE | 1830.7 | pos | 0.23 | 1811 | 19.6 | **+8.62** | fundo de range (2º winner) |
| 3 | 5016 | 2023-03-30 | BULL | 1980.2 | 1977.9–1999.7 | 0.61 | 1954 | 25.8 | −1.35 | reteste zona-top; stop |
| 4 | 5103 | 2023-04-21 | BULL | 1986.1 | 1977.9–1999.7 | 0.40 | 1968 | 18.0 | −1.35 | reteste zona-top; stop |
| 5 | **5826** | 2023-10-06 | BEAR | 1831.6 | 1804.7–1861.5 | 0.12 | 1812 | 19.3 | **+7.99** | capitulação profunda (única BEAR) |
| 6 | 5875 | 2023-10-18 | BULL | 1948.2 | 1923.1–1962.6 | 0.41 | 1911 | 36.9 | −0.01 | reteste zona-top; flat |
| 7 | 6376 | 2024-02-15 | RANGE | 2004.5 | pos | 0.27 | 1983 | 21.1 | +7.02 | fundo de range (winner) |
| 8 | 6791 | 2024-05-23 | RANGE | 2328.4 | pos | 0.04 | 2305 | 23.5 | −1.35 | fundo de range; stop |
| 9 | 7149 | 2024-08-15 | BULL | 2444.5 | 2436.8–2473.1 | 0.26 | 2422 | 22.2 | +4.19 | reteste zona-top (BULL winner) |
| 10 | 7549 | 2024-11-18 | RANGE | 2585.9 | pos | 0.22 | 2553 | 33.4 | +1.68 | fundo de range |
| 11 | 8133 | 2025-04-04 | RANGE | 3025.7 | pos | 0.08 | 2996 | 30.1 | −1.35 | fundo de range; stop |
| 12 | 8216 | 2025-04-25 | RANGE | 3280.9 | pos | 0.17 | 3256 | 25.2 | −1.35 | fundo de range; stop |
| 13 | 8236 | 2025-04-30 | RANGE | 3288.6 | pos | 0.23 | 3191 | 97.5 | −1.35 | fundo de range; stop (risco largo 97pts) |
| 14 | 8893 | 2025-10-01 | BULL | 3872.9 | 3861.2–3895.3 | 0.47 | 3790 | 82.7 | +1.34 | reteste zona-top |
| 15 | 8905 | 2025-10-03 | BULL | 3882.6 | 3861.2–3895.3 | 0.82 | 3817 | 65.9 | +1.68 | reteste zona-top |
| 16 | 8978 | 2025-10-21 | RANGE | 4111.2 | pos | 0.10 | 3938 | 173.1 | −1.35 | fundo de range; stop (risco 173pts) |
| 17 | 9007 | 2025-10-28 | RANGE | 3938.7 | pos | 0.11 | 3814 | 124.6 | +1.15 | fundo de range |

Campos **não disponíveis** na régua: target explícito (não há — saída é let-run/SL); MFE por trade existe (`mfe_struct`) mas não listado aqui.
Nota sobre os números que referiste: `4918/4926/5826` = bar_idx dos trades-chave (acima). `1661 / 6887 / 4401` **não** correspondem a nenhum dos 17 trades V2 — provavelmente pertencem a análises de outra fase/versão; sinalizado para confirmares se esperavas encontrá-los aqui.

---

## 8. Caveats e tensões (Devil's Advocate executado — read-only)

Veredito por dimensão (o DA reproduziu N17 exatamente):

| Q | Dimensão | Veredito DA | Classificação |
|---|---|---|---|
| Q1 | Look-ahead | **PASS** — causal-limpo (zonas prior-only, sem vazamento do segmento corrente, indicadores closed-bar) | **Força confirmada** |
| Q2 | In-sample | **FAIL** — `run(0.03,1.15,0.88)`, `bear_deep ≥15 barras/180d/amp3`, `pos<0.34` todos escolhidos neste livro | **Risco aceito** (calibração dentro dos 276 = canon do projeto; NÃO vender como validação) |
| Q3 | Seleção | **FAIL** — `phase47` (BEAR idx-3..idx-1) apanha **9 losers −12,1R**; `phase48` redefine a zona BEAR e fica **N1 +8,0R** | **RISCO QUE EXIGE REVISÃO** (ver abaixo) |
| Q4 | Power | **FAIL** — N17, BEAR n1, ~3 episódios carregam; mar-2023 RANGE = +20,6R | **Caveat real + risco aceito** (N inerente) |
| Q5 | Execução | **CAVEAT→FAIL** — só custo fixo 0,35R; risco por trade até 173pts (trades 16/13) pode gapar; let-run HZ120 = captura de tendência | **RISCO QUE EXIGE REVISÃO antes de operacionalizar** |
| Q6 | Alpha vs beta | **FAIL** — beta de regime; RANGE-fundo ≤ random-median (phase52); entradas não batem p95 (phase51) | **Caveat real (já internalizado na memória)** |

**Detalhe das tensões citadas:**
- **`f53ac72`** (RANGE overfit, null **p=1.0**, rank 273–391/457, inverte sob let-run): ataca um **acceptance+structure RANGE filter** — coerente com Q6/phase52. **Caveat real** sobre o componente RANGE.
- **`26f6bca`** (6 vencedores hand-drawn = 5 BULL + 1 RANGE, 0 BEAR; **BEAR elegível avgR=−0,593**): materializa que a tese "BEAR capitula no bottom anterior" tem 0 instâncias entre os winners **hand-drawn** (phase35). **Refutação de versão antiga** (phase35 hand-drawn, já marcada refutada na memória) **+ caveat real** sobre a fraqueza do BEAR no livro elegível.
- **BEAR n=1:** caveat real, aceite — estruturalmente correto, estatisticamente não-robusto.
- **RANGE dominado por beta/let-run:** caveat real (Q6), já internalizado (phase51/52).
- **`phase51` "é BETA" / `phase52` "RANGE-fundo pior que random":** confirmam que o lucro é beta+convexidade, não alpha de entrada. **Caveat real.**
- **2024 piora** (memória +13,9→+6,5): a confirmar reproduzindo `phase40_debug_2024.py`. **Caveat a verificar.**
- **Custos/slippage não modelados:** **risco que exige revisão antes de produção.**

**Separação explícita (pedida):**
- **Caveat real (dentro da estratégia aprovada):** beta-dominância do lucro; concentração em ~3 episódios; RANGE-fundo fraco vs random; BEAR n=1.
- **Refutação de versão antiga (não afeta V2):** phase35 hand-drawn (0 BEAR winners), V3 gatilho-de-zona, V1 dist/rsi.
- **Risco aceito (por canon/objetivo):** thresholds in-sample (calibração dentro dos 276); N pequeno.
- **Risco que exige revisão antes de operacionalizar:** (a) discrepância `phase47` vs `phase48` na zona BEAR — decidir qual é a definição canónica e assumir explicitamente que a BEAR fica n=1; (b) modelo de slippage/gap para trades de risco largo (>80pts).

---

## 9. Relação com a aprovação anterior

- **Aprovado (memória `project_l2_bpt_structural_regime_level_engine.md`, Cris 2026-07-01):** a **V2 zona-pura integral** (BULL zona-top + RANGE fundo + BEAR capitulação profunda), N17 +36,2R, como a "versão viva". A memória é explícita: "V2-17 é a versão viva".
- **Subconjunto vs integral:** a aprovação era da **V2 integral** (os 3 regimes), COM os caveats já anotados (BEAR n=1 "não robustez estatística"; RANGE = beta em phase51/52).
- **V1/V3 fora:** sim — V1 superseded, V3 rejeitada por Cris. Ambas fora do escopo aprovado.
- **bull_break:** apenas **lead vivo** (`phase73–77`), NÃO parte da V2 aprovada; ganho concentrado em 2023.
- **"RANGE+BEAR como coração":** essa frase (índice de memória) é **linguagem excessiva** relativa à substância — a substância mostra RANGE = beta concentrado e BEAR = n=1. O **coração real defensável** é: *o esqueleto de SKIP/seleção estrutural por regime* (evitar facas/esticadas) + a convexidade colhida pelo let-run, mais do que "RANGE e BEAR geram alpha". Isto **não rebaixa** a aprovação; precisa a linguagem.

---

## 10. Veredito técnico para decisão de OK final (não decido sozinho)

Recomendação: **(B) Confirmar a V2 zona-pura integral como estratégia aprovada, marcando RANGE e BEAR como caveated subcomponents.**

Justificação:
- A estrutura é **causalmente limpa** (Q1 PASS) — não há look-ahead, o que é a condição inegociável. ✅
- Os números **reproduzem exatamente** a memória. ✅
- Os FAILs do DA (Q2/Q4/Q6) são **os caveats que já aceitaste** (calibração dentro dos 276, N pequeno, beta) — são risco documentado, não invalidação. Manter integral respeita a tua diretiva de não rebaixar.
- O único item **novo que pede a tua decisão** é a **discrepância `phase47` vs `phase48` na zona BEAR** (Q3). Isto é o candidato a **(D) inconsistência factual**: qual das duas definições BEAR é a canónica? Se `phase48` (a que a memória descreve), a estratégia é N17 com BEAR=n1 assumido; se preferires a `phase47`, a BEAR muda (apanha 9 losers) e o painel muda para N25 +16R.

**Portanto: recomendo B, com um ponto de decisão (D-parcial) sobre a definição BEAR.** Não recomendo C (isolar BULL+bull_break) porque BULL sozinho é fraco (+4,5R/6) e bull_break não é parte da V2. Não rebaixo para lead de pesquisa.

**Precisas decidir:** (i) B integral com caveats? e (ii) confirmar `phase48` como a definição BEAR canónica (assumindo BEAR=n1)?

### DECISÕES REGISTADAS (Cris 2026-07-02)
- ✅ **(ii) `phase48_bear_deep_zone.py` = definição BEAR canónica. BEAR = n=1** (capitulação profunda 2023-10-06, bar_idx 5826) assumido explicitamente. Variante `phase47` (BEAR idx-3..idx-1, N25) descartada. Painel canónico = **N17**.
- ✅ **(i) ESCOPO = B — V2 ZONA-PURA INTEGRAL, `USER_APPROVED_NOT_PRODUCTION`.**
  - **Escopo aprovado: BULL + RANGE + BEAR** (os 3 regimes, N17 +36,2R).
  - **Caveats aceites (parte da estratégia, não escondidos):**
    - **RANGE** — parte da estratégia aprovada, **marcado como risco beta / concentrado / selection-overfit**.
    - **BEAR** — parte da estratégia aprovada via `phase48`, mas **n=1**; **NÃO tratar como coração estatístico**.
    - A linguagem **"RANGE+BEAR coração" fica CALIBRADA** — não usar como tese forte.
    - Estratégia **aprovada pelo utilizador, mas NOT_PRODUCTION**.
    - **Sem Telegram, sem monitor, sem catalog, sem strategy_rules, sem runtime.**
  - **Não rebaixar para lead. Não reduzir a BULL-only. Não esconder caveats.**

---

## 11. Próximo passo mínimo seguro (após a tua decisão)

1. **Registar a decisão** (B + definição BEAR) neste doc + na memória `project_l2_bpt_structural_regime_level_engine.md` (ajustar "RANGE+BEAR coração" → linguagem calibrada), com o status `USER_APPROVED_NOT_PRODUCTION`.
2. **Entrada no `04_STRATEGY_STATUS_MASTER.md`** como `USER_APPROVED_RESEARCH` / `NOT_PRODUCTION` (só depois da tua ordem — está fora do escopo desta sessão).
3. **Antes de qualquer operacionalização:** (a) modelar slippage/gap para trades de risco largo; (b) reproduzir `phase40_debug_2024.py` para confirmar o "2024 piora"; (c) opcional: revisão visual RAW dos 17 trades no chart (tu fazes o visual).
4. **Checkpoint final** (commit local dos docs; sem push) quando aprovares o texto.

*Nenhum destes passos executado nesta sessão além da criação deste documento. Sem push, sem status master, sem produção.*
