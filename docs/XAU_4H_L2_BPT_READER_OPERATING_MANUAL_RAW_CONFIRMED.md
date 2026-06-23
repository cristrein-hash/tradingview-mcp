# XAU 4H L2/BPT — READER VIVO OPERATING MANUAL (RAW-CONFIRMED) — 2026-06-23

FASE 12. Manual operacional do Reader Vivo contendo **apenas lentes confirmadas sobre backbone RAW autêntico
+ sobreviventes ao outcome audit** dos clusters 1 e 2 (19 episódios). Substitui o manual anterior
(`XAU_4H_L2_BPT_READER_OPERATING_MANUAL.md`, backbone derivado) como a versão RAW-clean.

> **NÃO é gate, score, policy de entrada, nem regra TAKE/SKIP.** É um manual de LEITURA: como o Reader (humano
> ou Managed Agent) deve PERCEBER o episódio. Unidade = episódio. O árbitro é a estrutura, não o outcome
> ([[feedback_episode_unit_of_analysis_canon]] · [[feedback_macro_engine_methodological_canon]]). Cada lente
> diz o que PERGUNTAR, não o que decidir. Fonte 100% RAW (gate exit 0). SVP/acceptance = BLOCKED (ver §3).

CSV-espelho: `results/l2_bpt_reader_operating_manual_raw_confirmed.csv`.

---

## 0.0 ATUALIZAÇÃO COM VALUE-AREA REAL (2026-06-23 — corrige a premissa "VA bloqueada")

A VA de volume estava DISPONÍVEL o tempo todo (erro de fonte corrigido em c1b24cf; guard estrutural ba1c51c).
Clusters 1/2 RE-LIDOS com a VA real (`_withva`) e auditados. Combinado: **12 CONFIRMED · 3 MODIFIED · 4 REFUTED**
(vs sem-VA 11C/3M/5R) — melhora MARGINAL. Detalhe: `docs/XAU_4H_L2_BPT_READER_NOVA_VS_WITHVA_COMPARISON.md`.

| Lente (VA) | Status com-VA |
|---|---|
| VA como **eixo causal** (par casado 3949 vs 3929: separados SÓ pela VA, +6.62R vs +0.05R) | **WITHVA_CONFIRMED — prova mais limpa do programa** |
| `svp_state = ACCEPTING_ABOVE_VALUE` (regime-permitindo) = construtivo/fuel | **WITHVA_CONFIRMED** (5826/4401/3949 3/3) |
| `dist_poc` GRANDE acima do POC = sobre-extensão/exaustão | **WITHVA_REFUTED** (invertido em bull: 4926 correu +18R; sair do valor = correr) |
| `IN_VALUE`/abaixo-POC = trap como **VETO** | **WITHVA_REFUTED** (over-condena runners: 5627 +5.96R, 1522 +5.65R) |
| supply-WALL próximo ⇒ fade (lente anterior `QUARANTINED_PENDING_VOLUME_VA`) | **segue QUARANTINED** — a VA-STATE ajuda, magnitude/veto não fecham; o eixo informa, não decide |

**Regra de ouro corrigida:** a VA é um **fator de leitura**, NÃO um veto/gate. O *estado* `ACCEPTING_ABOVE_VALUE`
é construtivo (regime-permitindo); a *magnitude* de dist_poc e o `IN_VALUE=trap` **não** viram regra (refutam
runners). FUEL-vs-WALL nos casos IN_VALUE segue ABERTO — exige validação dentro do corpus, nunca como regra.

## 0. ATUALIZAÇÃO PÓS-ANCHOR-FIX (revalidação causal 2026-06-23)

As lentes abaixo (§1-3) foram REVALIDADAS sobre o backbone CAUSAL (anchor as-of por timestamp real, commit
1267c8d — o backbone PRE-FIX tinha look-ahead de 1-2 barras em 13/19 casos). Readers cegos frescos + outcome
audits frescos sobre pacotes pós-fix. Resultado combinado: **11 CONFIRMED · 3 MODIFIED · 5 REFUTED · 0 INSUFFICIENT**
(n=19). Cluster 2 melhorou de 4C/4R/2INSUF (pré) → **7C/1M/2R** (pós). Detalhe:
`docs/XAU_4H_L2_BPT_CLUSTER{1,2}_PREFIX_VS_POSTFIX_REVALIDATION.md`.

| Lente | Status pós-fix |
|---|---|
| Regime/weekly-sign inverte significado | **POSTFIX_RAW_CONFIRMED** |
| weekly-negativo NÃO é veto (macro-neg pode ser washout construtivo) | **POSTFIX_RAW_CONFIRMED** |
| **Geometria preço×supply sob macro casado** (3949 SUPPLY_FAR runner vs 3929 SUPPLY_BLOCKS stop, mesmo dia) | **POSTFIX_RAW_CONFIRMED — prova mais limpa, agora SEM look-ahead** |
| RSI-position / freio de blow-off | **POSTFIX_RAW_CONFIRMED** |
| Forma 4H > etiqueta textual de acceptance | **POSTFIX_RAW_CONFIRMED** |
| Entry-red-bar / esforço-comprador-ausente = trap | **POSTFIX_RAW_CONFIRMED** |
| Compression-runner vs washout-runner | **POSTFIX_RAW_CONFIRMED** |
| Polo FUEL (supply distante + forma) — direção | **POSTFIX_RAW_MODIFIED** (direção certa, exit/runner variável) |
| **supply-colado/geometria-WALL ⇒ fade como REGRA** (4926/8878/4401/5627 = wall + correram) | **QUARANTINED_PENDING_VOLUME_VA** |
| Discriminação cross-episódio 4918 vs 4926 (gêmeos-runner) | **POSTFIX_REFUTED** (árbitro = VA de volume, BLOCKED) |
| Compressão-sob-supply / casos INSIDE_VALUE | **STILL_INSUFFICIENT** (exige VA de volume) |

**Continuidade com o pré-fix:** o fix NÃO destruiu as lentes — confirmou as load-bearing e reconfirmou a
quarentena do "supply-WALL ⇒ fade". A novidade causal é a **prova limpa da geometria** (3949/3929) e a melhora de
calibração do Cluster 2. O eixo que fecharia WALL-vs-FUEL (aceitação no VALUE-AREA DE VOLUME) segue **BLOCKED**.

---

## 1. Lentes RAW-CONFIRMED (a base operável)

### OM-RAW-1 — Regime/weekly-sign é o INVERSOR de significado (load-bearing)
A MESMA superfície (FLUSH_V, reclaim, range) significa coisas OPOSTAS conforme o regime. weekly−/cascade
profundo sem virada → a superfície de reversão tende a TRAP; weekly virando/+ com clímax → tende a FUNDO
legítimo. Evidência: 1661 (weekly−0.22) trap→stop vs 4918 (weekly+0.54+turn) fundo→+19.8R, superfície idêntica.
**Pergunta:** o regime CONFIRMA a reversão que a forma sugere, ou a contradiz? Nunca ler a forma sem o regime.
Ressalva: weekly<0 NÃO é "tudo trap" — o cluster2 inteiro (10 episódios weekly<0) teve 4 runners. O regime
inverte o significado, não veta o lado.

### OM-RAW-2 — RSI-position-in-leg / freio de blow-off
A posição do RSI dentro da perna separa markup saudável (RSI com espaço) de clímax/exaustão (RSI esticado).
8878 RSI56 "room" → +18.8R vs 8923 RSI82/84 "blow-off" → spike e −93 em 10b, mesma perna, 10 dias. 5826 RSI30.8
exausto-superado → fuel. **Pergunta:** o RSI mostra espaço para estender, ou exaustão no apex? RSI extremo +
forma vertical sem base = tratar exaustão como leitura PRIMÁRIA, não co-igual.

### OM-RAW-3 — Polo FUEL (supply distante + clímax + flush/V-reclaim + expansão)
Supply distante (≥~2.4ATR) OU clímax visível superado + V/flush-reclaim + barra de expansão/close-no-topo →
o episódio tende a DESENVOLVER (correr). Evidência: 4918, 5826, 3949, 8940; cluster2 todos os runners vieram
de exausto/clímax superado. **Pergunta:** houve um clímax REAL que foi digerido por barras antes da entry, e a
forma é de expansão (não de toque tímido)?

### OM-RAW-4 — Forma da barra de entrada / TRAP
A cor/energia da barra de entrada é discriminador bruto e direto. Entry VERMELHA em macro negativo = morte
(1873 body−3.3, 3929 body−3.1 — ambas falharam, 2/2). Bear-pullback contra-tendência + RSI div + sem
confirmação = trap (1661, 1873). **Pergunta:** a entry está COMPRANDO uma recuperação que já está falhando
(barra vermelha/devolvendo), ou um hold/expansão? Comprar no exausto AGORA (RSI no fundo na própria barra) ≠
comprar DEPOIS do exausto digerido (1775 caiu por comprar no susto).

### OM-RAW-5 — Forma 4H > etiqueta textual de acceptance (a mais forte)
A etiqueta textual de aceitação (ACCEPTED_ABOVE_RES / REJECTED_AT_RES) ENGANA; a forma 4H manda. Par D
(3949 etiqueta REJECTED→correu +6.62R; 3929 etiqueta ACCEPTED→travou +0.05R) lido ao INVERSO das labels,
ordenação perfeita. **Pergunta:** ignore a etiqueta; reconstrua a aceitação pela FORMA (clímax + V + reabsorção
profunda + cor da barra). Quem seguiu a label errou os dois; quem leu a forma acertou os dois.

### OM-RAW-6 — Geometria preço×supply é o eixo SOB macro controlado (condicional)
Quando o macro é mantido constante (par casado, mesmo dia), a geometria preço-vs-supply × forma do último
movimento É o eixo organizador e separa limpo (3949 espaço-aberto vs 3929 sob-blocos, +6.62R vs +0.05R).
**MAS cross-episódio a geometria sozinha engana** (4918 vs 4926, lidos opostos, ambos +18R). **Pergunta:** os
casos que estou comparando têm o MESMO macro? Se sim, geometria discrimina; se não, geometria sozinha não basta.

---

## 2. Lente em QUARENTENA (RAW_REFUTED como regra direcional)

### OM-RAW-Q1 — "supply-proximity = WALL/fade" — QUARANTINED_PENDING_RAW
**A regra "supply colado (≤~1.6ATR) → rejeição/fade" foi REFUTADA pelo outcome.** Quase todo call de WALL
próximo CORREU: 4926 (+18R), 8878 (+18.8R), 4401 (+10.3R), 1522 (+5.7R), 5627 (+6R). No cluster2 o polo WALL
segurou só 1/4 (3929). Sem o eixo de aceitação, **proximidade de supply NÃO é sinal de fade — frequentemente
precede os maiores runs** (absorção→breakout). O discriminador verdadeiro (a "parede" que de fato rejeita)
mora no **SVP/value-area/acceptance, hoje BLOCKED_UNMAPPED**. **Não usar proximidade-de-supply como sinal de
rejeição até o eixo SVP estar mapeado ao RAW.** Quando o reader leu FUEL nesses casos, acertou; quando leu
WALL, errou — a assimetria diz que o prior default perto do supply deve ser absorção, não rejeição.

---

## 3. Marcado INSUFFICIENT — o que falta mapear (prioridade #1)

### OM-RAW-I1 — compressão-sob-supply: construtiva vs exaustão — INSUFFICIENT_RAW_CONTEXT
3825, 1775, 5627 ficaram genuinamente sub-determinados sem SVP/acceptance. A pergunta certa existe
(*o range sob o supply faz lower-lows = corrosão→wall, ou higher-lows/lateral defendido = compressão→fuel? o
preço é ACEITO de que lado do value-area?*) mas o dado que a responde está BLOQUEADO. **Próxima frente RAW =
mapear `session_vp` → value-area (POC/VAL/VAH) + acceptance pela forma.** É o árbitro ausente que apareceu
repetidamente como o fator decisivo. Os itens VP brutos existem no bloco `..._SVP_LUX_RAW.jsonl.gz`; a
agregação de VA é o trabalho. NÃO inventar POC/VAL/VAH até mapear.

---

## 4. Resumo operável

- **6 lentes RAW-CONFIRMED** (OM-RAW-1..6) = como ler o episódio hoje, sobre dado autêntico.
- **1 lente QUARENTENADA** (OM-RAW-Q1, supply-WALL→fade): não usar como sinal de rejeição.
- **1 buraco declarado** (OM-RAW-I1, SVP/acceptance): próxima prioridade de mapeamento RAW.
- A troca derivado→RAW **reproduziu** as lentes (não as destruiu) — a leitura de auction é robusta à fonte;
  o que mudou foi promover supply-WALL→fade de "blind spot menor" para "quarentena", e nomear SVP como o
  próximo elo. Sem promoção, sem score, sem policy. Cris decide o próximo passo.
