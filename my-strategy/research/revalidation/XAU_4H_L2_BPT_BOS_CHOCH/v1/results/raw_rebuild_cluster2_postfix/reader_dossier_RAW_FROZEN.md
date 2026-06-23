# READER DOSSIER — RAW-FROZEN — Cluster 2 (macro negativo, weekly<0, 10 episódios, 4 sub-blocos)

> Leitura CEGA, fonte 100% RAW, backbone CAUSAL pós-anchor-fix (commit 1267c8d, 19/19 causal+exato, sem look-ahead).
> NENHUM outcome/R/MFE/winner/loser foi consultado — não existe no pacote. Leio o SETUP, a NATUREZA do episódio.
> TPO acceptance = proxy de TEMPO (NÃO value-area de volume). LuxAlgo VOLUME POC/VAL/VAH = UNKNOWN_BLOCKED em TODOS os 10 — declaro onde isso limita.
> Eixo de raciocínio: regime × forma/trajetória × geometria-de-supply × indicadores × esforço-de-volume-real-por-barra. Nunca eixo único.
> Pergunta-mãe do cluster: "weekly negativo" FORÇA "trap", ou um episódio macro-negativo pode ser washout construtivo? Cada um lido fresco.

---

## NOTA DE MÉTODO — o que cada campo causal me dá e o que me NEGA

- `weekly`/`cascade`/`combined`/`v3`: macro derivado de preço RAW. Todos os 10 são macro_broken=True (pré-condição do cluster). Isso é o PANO DE FUNDO, não o veredito — é o que a pergunta-mãe testa.
- `sup_cat` + `dist_supply`/`dist_demand` (ATR) + `clean_sky` + `has_overhead`: GEOMETRIA causal do Custom OB. Aqui mora a maior parte do sinal discriminante deste cluster. `clean_sky=True` = sem supply sobreposto próximo (céu limpo acima); `SUPPLY_BLOCKS`/`SUPPLY_NEAR` = parede sobre a cabeça.
- Camada-0 forma (5 barras OHLC, última = barra de entry, frequentemente degenerada O=H=L=C porque é o close de ancoragem): leio TRAJETÓRIA (flush-and-reclaim vs grind vs push-into-supply).
- NAS/SMC/bubbles/RSI+div: indicadores RAW. bubbles sell_mL = pressão de venda plotada (NÃO inverter cegamente — em fundo, sell-bubble pode ser exaustão/clímax; em topo, é distribuição). SMC BOS/CHoCH = estrutura. RSI div = aviso.
- `entry_up` (up-ratio de volume da barra de entry) + `last6_up` (média 6 barras): ESFORÇO REAL POR BARRA — único pedaço de volume confiável. entry_up=1.0 = barra de entry 100% comprada; entry_up=0.0 = barra de entry 0% comprada (vendedor dominou a barra de gatilho).
- **BLOCKED em todos**: VOLUME value area (VAL/VAH/POC de volume). Sem ela NÃO sei se o preço está aceito DENTRO de valor de volume ou apenas tocando tempo. tpo_acceptance é proxy fraco de TEMPO. Onde a leitura depende de "aceito em valor", marco a limitação.

---

# SUB-BLOCO A — macro negativo + CLEAN SKY (céu limpo acima)

## EPISÓDIO 5826 (2023-10-06 18:00)
**Nature: washout-with-change-of-character (construtivo).**
Macro BEAR (weekly −0.21, cascade −2), MAS geometria é a melhor possível neste cluster: `clean_sky=True`, supply a 5.86 ATR (longe), demand a 1.7 ATR (suporte abaixo presente mas não colado). A trajetória das 5 barras é uma reclaim limpa: a 3ª barra varre o low (L1810.4) e fecha de volta no corpo (C1821.25), depois um push expansivo (H1834.85, C1831.78) — flush seguido de aceitação acima. entry_up=1.0 e last6_up=0.862 confirmam ESFORÇO COMPRADOR REAL dominante nas últimas barras. SMC alterna BOS/CHoCH com CHoCH final (mudança de caráter estrutural). NAS 5×LONG. RSI 51.6 neutro, sem div. O único contra é bubbles sell_mL=16 — mas em contexto de clean-sky + reclaim + volume comprador, leio isso como pressão de venda sendo ABSORVIDA, não distribuição validada. Macro-negativo NÃO força trap aqui: céu limpo + esforço comprador = washout com change-of-character.
**Expectation se correto:** continuação para cima sem reteste profundo do low varrido; supply a 5.86 ATR dá pista longa. **Falsificador:** reabsorção abaixo do low da 3ª barra (1810.4) com entry de volume revertendo para vendedor → tese de reclaim morta.
**Confiança: ALTA.** BLOCKED: o sell_mL=16 sem o VOLUME VA me impede de confirmar 100% que a venda foi absorvida (não-distribuída) — é o ponto mais cego. O céu limpo causal compensa parcialmente.

## EPISÓDIO 1623 (2021-01-20 03:00)
**Nature: incomplete-base-absorption / timing-ambíguo (céu limpo mas esforço fraco).**
Geometria também favorável: `clean_sky=True`, supply MUITO longe (9.93 ATR), demand a 0.48 ATR (suporte colado abaixo). Trajetória das barras é um grind para cima modesto culminando num push (H1850.43, C1849.83). MAS o esforço de volume é o INVERSO de 5826: entry_up=0.143, last6_up=0.217 — a barra de gatilho e as 6 anteriores são DOMINADAS por vendedor mesmo enquanto o preço sobe. Isso é alta de baixa convicção / ausência de comprador real. SMC quase todo CHoCH (estrutura reativa, sem BOS de continuação limpo). NAS 4×SHORT→LONG (vira só no fim). bubbles 0/0 (sem sinal de clímax nem de distribuição). RSI 49.5 neutro. Céu limpo é convidativo, mas a base não foi absorvida com esforço — preço sobe sem comprador. Não é trap óbvio (não há parede), mas também não é reclaim convicto; é base incompleta.
**Expectation se correto:** subida sem patrocínio tende a estagnar/reverter perto do primeiro obstáculo; ou exige nova barra de absorção comprada para validar. **Falsificador:** próxima barra com entry_up alto (>0.6) confirmando entrada de comprador → vira para construtivo legítimo.
**Confiança: MÉDIA.** BLOCKED: aqui o VOLUME VA seria decisivo — saber se o preço está aceito acima/abaixo do valor de volume separaria "base incompleta" de "fuga real". O proxy TPO ACCEPTED_ABOVE_VALUE é fraco demais para resolver dado o esforço comprador ausente.

**Contraste A (5826 vs 1623):** mesma geometria de céu limpo, macro idêntico-negativo — o DESEMPATE é o ESFORÇO DE VOLUME REAL e a forma do flush. 5826 = flush-and-reclaim com volume comprador (entry 1.0) → washout construtivo. 1623 = grind sem comprador (entry 0.14) → base incompleta. Clean-sky habilita, mas não basta; o motor é o esforço por barra.

---

# SUB-BLOCO B — macro negativo + SUPPLY PRÓXIMO

## EPISÓDIO 4401 (2022-11-04 02:00)
**Nature: supply-as-WALL / bear-pullback-trap (push direto na parede).**
Pior macro do bloco B (weekly −0.47). `SUPPLY_BLOCKS`, clean_sky=False, supply a apenas 1.57 ATR, demand a 0.87 ATR — preço espremido entre parede acima e suporte fino abaixo. Trajetória: rali de quatro barras direto PARA a parede (de C1619.3 a C1633.85), ou seja, está COMPRANDO contra supply imediato. entry_up=1.0 mas last6_up=0.723 — esforço comprador existe, porém está sendo gasto subindo para dentro do supply, não saindo de um washout. SMC termina BOS/BOS (continuação) mas dentro de zona de oferta. NAS vira LONG→SHORT (deteriora). bubbles sell_mL=11 = oferta plotada coincidindo com a parede. **Anchor warnings**: close_fidelity=False, "regime close fidelity vs RAW >1pct" e "anchor close vs frozen >0.5pct" — o ponto de entry é menos confiável aqui, o que reduz minha confiança na geometria fina. Macro-negativo AQUI tende a trap: subir para 1.57 ATR de uma parede de supply em weekly forte-negativo é comprar combustível dos vendedores.
**Expectation se correto:** rejeição na/ logo abaixo do supply (~1.57 ATR acima); a parede vira teto. **Falsificador:** rompimento limpo e aceitação ACIMA do bloco de supply com entry_up mantido alto → supply vira fuel, não wall.
**Confiança: MÉDIA-ALTA (para trap).** BLOCKED: VOLUME VA diria se já há aceitação dentro do supply (breakout real) vs apenas toque. Agravado pelos anchor warnings — geometria fina menos confiável.

## EPISÓDIO 3825 (2022-06-23 02:00)
**Nature: supply-as-WALL com forma de FALHA (rejeição já em curso).**
weekly −0.27, cascade −2, BEAR. `SUPPLY_NEAR`, supply colado a 0.61 ATR, demand a 0.35 ATR — preço quase em cima da oferta, dentro de uma faixa apertadíssima. Trajetória é o oposto de 4401: a 1ª barra empurra forte para cima (H1847.82) mas FECHA mais baixo e as barras seguintes DESCEM em sequência (C1844.53→1840.67→1837.95→1833.08) — rejeição da oferta já materializada na forma, lower-closes encadeados. entry_up=0.885 mas last6_up=0.244 (esforço comprador colapsou nas últimas 6 barras). tpo ACCEPTED_BELOW_VALUE (aceito abaixo — fraqueza). SMC alterna CHoCH/BOS sem continuação convicta. bubbles 0/0, NAS 5×LONG, RSI 47.75 (abaixo de 50, sem força). Tudo aponta: parede de supply muito próxima sob macro-negativo, com a forma já rolando para baixo. Trap/rejeição em andamento.
**Expectation se correto:** continuação da rejeição abaixo; o supply a 0.61 ATR é teto efetivo. **Falsificador:** retomada de closes mais altos com entry_up recuperando >0.6 e aceitação acima de 1847 → falha minha.
**Confiança: ALTA.** BLOCKED: VOLUME VA confirmaria se "below value" é distribuição real ou ruído; mas a forma de lower-closes + colapso de last6_up já dá o sinal sem ela.

**Contraste B (4401 vs 3825):** ambos macro-negativos com supply próximo = candidatos a WALL. Diferença de forma: 4401 sobe ATIVAMENTE para a parede (entry 1.0, last6 0.72, push-into) — trap por compra ingênua de combustível; 3825 já BATEU e está rolando (lower-closes, last6 colapsado em 0.24) — rejeição consumada. 4401 é "trap prestes a fechar", 3825 é "trap já fechando". Supply = wall em ambos; o esforço de volume diferencia o momento, não o veredito.

---

# SUB-BLOCO C — macro negativo + FLUSH sob supply (ordem de maturidade)

## EPISÓDIO 1522 (2020-12-23 23:00)
**Nature: incomplete-base-absorption (flush ainda imaturo, supply moderadamente longe).**
weekly −0.30, cascade −1 (o MENOS negativo do bloco C). `SUPPLY_FAR` (2.4 ATR — mais respiro que os outros do C), demand 0.77 ATR. Trajetória: barra 2 com range amplo varrendo low (L1857.06) e fechando forte (C1876.5), depois grind lateral-alto (1873/1873). entry_up=0.0 na barra de gatilho MAS last6_up=0.765 (comprador dominou as 6 barras anteriores, só a última barra de gatilho é vendedora). Essa divergência = flush absorvido recentemente mas barra de entry sem follow-through comprador. SMC termina CHoCH/CHoCH (reativo). NAS vira LONG→SHORT no fim. bubbles buy_mL=2 (leve viés de compra, raro neste cluster). RSI 52.77. Leio como base em formação porém ainda imatura — o flush foi absorvido (last6 forte) mas o gatilho não confirma.
**Expectation se correto:** precisa de mais uma barra de absorção comprada para amadurecer; risco de range antes de definir. **Falsificador:** próxima barra entry_up baixo + perda do C1865 → flush falhou, vira fraqueza.
**Confiança: MÉDIA.** BLOCKED: VOLUME VA crucial — INSIDE_VALUE(tempo) não me diz se está aceito no valor de volume. A divergência entry0.0/last6 0.765 é exatamente o caso que o VA resolveria.

## EPISÓDIO 1873 (2021-03-18 22:00)
**Nature: bear-pullback-trap (com aviso explícito de divergência bearish).**
weekly −0.49 (o mais negativo do C), cascade −3. `SUPPLY_BLOCKS` a 1.23 ATR (parede próxima), demand LONGE a 2.31 ATR (sem suporte colado abaixo — vazio embaixo). Trajetória: flush profundo (L1719.23) com reclaim parcial para 1734/1736, mas estagnado sob a parede. entry_up=0.0, last6_up=0.573 (gatilho vendedor). **div=['Regular Bearish']** — único episódio do cluster com divergência bearish explícita, e ela aparece exatamente sob uma parede de supply em macro fortemente negativo. SMC vira CHoCH→BOS/BOS/BOS (continuação de baixa estruturalmente). bubbles buy_mL=1 (irrelevante). RSI 54.9 (subindo para o aviso de div). Reclaim de flush + parede próxima + demand vazio abaixo + div bearish = pullback-trap de manual.
**Expectation se correto:** rejeição sob a parede de 1.23 ATR; risco de novo leg-down dado demand a 2.31 ATR (sem rede). **Falsificador:** rompimento e aceitação acima do supply anulando a div bearish.
**Confiança: ALTA.** BLOCKED: VOLUME VA ajudaria a confirmar distribuição, mas div bearish + geometria já formam tese robusta sem ela.

## EPISÓDIO 5627 (2023-08-22 14:00)
**Nature: timing-bad / honest-residual sob supply (caso mais alterado pelo backbone causal).**
weekly −0.25, cascade −2. `SUPPLY_BLOCKS` a 1.87 ATR. **demand a 10.57 ATR** — vazio ENORME abaixo (nenhum suporte por 10+ ATR). Trajetória: grind lateral-alto (1895/1895/1902) seguido de uma barra de REVERSÃO forte: H1904.44 mas C1890.3 (rejeição do topo intrabar, fecha perto do low). entry_up=0.0, last6_up=0.443 (gatilho vendedor, esforço comprador morno). bubbles sell_mL=15 coincidindo com a rejeição do topo. NAS SHORT→LONG (misto). SMC BOS contínuo. RSI 48.77. **Backbone causal é decisivo aqui**: o dist_supply causal (1.87 ATR) coloca o preço MAIS LONGE da oferta do que a versão contaminada por look-ahead implicava — ou seja, NÃO está colado na parede, mas a barra de rejeição + sell_mL=15 + o vazio de 10.57 ATR embaixo dizem que se falhar, cai sem rede. Não é trap-na-parede (supply não tão perto), nem reclaim convicto (gatilho vendedor). É residual honesto / timing ruim: rejeição de topo num macro-negativo com chão muito distante.
**Expectation se correto:** indefinição/rejeição local; se perder o suporte imediato, queda destravada (demand 10.57 ATR). **Falsificador:** retomada com entry_up alto reabsorvendo o C1904 → vira construtivo, anula a rejeição.
**Confiança: MÉDIA.** BLOCKED: MAIS limitado pelo VOLUME VA de todo o cluster junto com 1623 — com demand a 10.57 ATR e sem VA de volume, não sei se o grind 1895 é acúmulo aceito ou apenas pausa antes de cair. O proxy ACCEPTED_BELOW_VALUE (tempo) sugere fraqueza mas é fraco.

## EPISÓDIO 1775 (2021-02-24 15:00)
**Nature: washout/flush sob supply — maturidade tardia mas esforço comprador ausente (residual).**
weekly −0.33, cascade −3. `SUPPLY_BLOCKS` a 1.73 ATR, demand 1.27 ATR (suporte presente). Trajetória: a barra mais notável é a penúltima — flush VIOLENTO (O1807.16 H1810.26 L1783.56 C1785.68), varredura de ~27 pts e fecho perto do low, depois a entry no próprio nível (1785.67). entry_up=0.0, last6_up=0.066 — esforço comprador QUASE NULO em 6 barras; este é o flush mais "puro vendedor" do cluster. tpo ACCEPTED_BELOW_VALUE. SMC alterna CHoCH/BOS. bubbles sell_mL=4. NAS 5×LONG. RSI 55.17 (curiosamente alto para um flush — possível leitura pré-flush remanescente). **Anchor warning**: close_fidelity=False ("feed RAW != frozen") — ponto de entry menos confiável. É um flush sob parede, mas SEM nenhuma evidência de absorção comprada (last6 0.066) — não é o reclaim de 5826. É washout em andamento ainda capitulando, não revertido.
**Expectation se correto:** capitulação pode continuar ou exigir base; sem comprador (last6 0.066) não há change-of-character ainda. **Falsificador:** próxima barra com reclaim do C1785 e entry_up alto → vira washout-construtivo (como 5826).
**Confiança: MÉDIA.** BLOCKED: VOLUME VA diria se o flush parou em valor (capitulação climática absorvida) ou rompeu valor (continuação). Agravado pelo anchor warning.

**Contraste C — ordem de maturidade (1522 → 5627 → 1775 → 1873):**
- **Menos maduro / base imatura: 1522** — flush absorvido recentemente (last6 0.765) mas gatilho sem follow-through; supply mais longe (2.4 ATR) dá tempo. Base em construção.
- **Flush ainda capitulando: 1775** — flush violento e puro-vendedor (last6 0.066), nenhum sinal de absorção; o mais "no meio do washout".
- **Rejeição de topo / timing ruim: 5627** — não está colado na parede (causal 1.87 ATR), mas rejeitou topo com vazio de 10.57 ATR abaixo; residual.
- **Mais maduro como TRAP: 1873** — reclaim sob parede próxima (1.23 ATR) com demand vazio (2.31 ATR) E div bearish explícita = o pullback-trap mais formado do bloco.
Eixo de maturidade = quanto o flush foi ABSORVIDO (last6_up) versus quanto ainda há parede+vazio acima/abaixo. Nenhum mostra esforço comprador convicto na barra de entry (todos entry_up=0.0) — o que separa C de 5826 é justamente a ausência de reclaim com volume.

---

# SUB-BLOCO D — macro negativo EXTREMO (mesmo dia, macro idêntico, geometria invertida)

Ambos: weekly_slope=−0.6657 (idêntico), cascade −2, BEAR, macro mais extremo do cluster. Separados por ~3 dias. SMC 5×BOS em ambos. entry_up=1.0 em ambos. Diferença = GEOMETRIA de supply.

## EPISÓDIO 3949 (2022-07-21 18:00)
**Nature: washout-with-change-of-character (apesar de macro extremo) — geometria de céu mais aberto.**
`SUPPLY_FAR` a 2.42 ATR (mais respiro), **demand=None** (sem suporte mapeado abaixo — vazio, mas o preço está SUBINDO, não caindo nele). Trajetória forte: barra 2 cai (C1684.46) e barra 3 faz reversão V expansiva (L1680.87 → C1705.76, range ~30 pts) seguida de continuação (C1713.81). entry_up=1.0, last6_up=0.627 — esforço comprador real e sustentado. SMC 5×BOS (continuação estrutural limpa de alta). bubbles sell_mL=5 (modesto), NAS 5×LONG, RSI 54.01. Mesmo sob o macro MAIS negativo do cluster, a forma é reversão-V com volume comprador e supply a respiro de 2.42 ATR. Washout construtivo — macro extremo NÃO força trap quando a forma é reclaim convicto e há espaço acima.
**Expectation se correto:** continuação da reversão sem reteste profundo; supply a 2.42 ATR é o primeiro teste. **Falsificador:** falha em sustentar acima do C1705 com entry_up revertendo → V falsa.
**Confiança: ALTA.** BLOCKED: demand=None + sem VOLUME VA me deixa cego para o suporte abaixo, mas como a tese é de CONTINUAÇÃO PARA CIMA, o vazio abaixo importa menos no cenário-base; importaria muito no falsificador.

## EPISÓDIO 3929 (2022-07-18 10:00)
**Nature: supply-as-WALL / push-into-supply (geometria invertida vs 3949).**
Mesmo macro extremo, mas `SUPPLY_BLOCKS` a 1.34 ATR (parede próxima), demand a 1.35 ATR (suporte simétrico). Trajetória: rali de quatro barras direto para cima (C1707→1714→1714→1722) — está SUBINDO PARA a parede de 1.34 ATR. entry_up=1.0, last6_up=0.64 (esforço comprador real, mas gasto subindo para dentro da oferta, igual a 4401). SMC 5×BOS. bubbles sell_mL=10 (mais oferta plotada que 3949, coincidindo com a parede). NAS 5×LONG, RSI 51.02. Forma quase idêntica de momentum a 3949, MAS a geometria coloca esse momentum colidindo com supply próximo em vez de espaço aberto. Mesmo esforço comprador, destino diferente: aqui o rali compra combustível para os vendedores na parede.
**Expectation se correto:** rejeição/estancamento na oferta de 1.34 ATR. **Falsificador:** aceitação ACIMA do bloco de supply com entry_up mantido → supply vira fuel.
**Confiança: MÉDIA-ALTA (para wall).** BLOCKED: VOLUME VA diria se a parede já tem aceitação (breakout) ou só toque — exatamente o que separa wall de fuel aqui.

**Contraste D (3949 vs 3929) — geometria ainda é o eixo em dados causais?**
SIM. Macro idêntico ao decimal (−0.6657), mesmo cascade, mesmo SMC 5×BOS, mesmo entry_up=1.0, forma de momentum parecida — TUDO controlado exceto a GEOMETRIA de supply. 3949 = SUPPLY_FAR (2.42 ATR), céu mais aberto → washout construtivo. 3929 = SUPPLY_BLOCKS (1.34 ATR), parede → push-into-wall. Em dados CAUSAIS, sem look-ahead, a distância/categoria de supply é o que separa as duas leituras de um mesmo dia. Isso é a confirmação mais limpa do cluster de que geometria-de-supply é eixo causal real, não artefato de contaminação.

---

# SÍNTESE — FUEL vs WALL, esforço de volume, backbone causal, e a pergunta-mãe

## Supply-as-FUEL vs supply-as-WALL (por caso)
- **WALL (parede que rejeita / push-into):** 4401, 3825, 1873, 3929 — todos `SUPPLY_BLOCKS`/`SUPPLY_NEAR`, supply ≤1.73 ATR, clean_sky=False. Em 4401/3929 o preço SOBE para a parede (compra combustível p/ vendedor); em 3825/1873 a rejeição já está em curso (lower-closes / div bearish).
- **Céu limpo / FUEL-como-respiro (washout construtivo):** 5826, 3949 — supply ≥2.42 ATR, espaço acima, forma de reclaim com entry_up alto. Aqui a venda anterior virou COMBUSTÍVEL absorvido, não parede.
- **Indeterminados / base imatura / residual:** 1623 (céu limpo mas sem comprador), 1522 (flush absorvido mas gatilho fraco), 5627 (rejeição de topo, vazio enorme abaixo), 1775 (flush ainda capitulando, comprador nulo).
Não há caso de "supply-as-FUEL" no sentido de breakout-aceito-acima-da-parede confirmado — porque o VOLUME VA está BLOCKED, não posso confirmar aceitação acima de nenhuma oferta. Essa é a fronteira BLOCKED estrutural do cluster.

## O volume real POR BARRA ajuda?
Sim, é o discriminador mais útil disponível. entry_up/last6_up separou pares que a geometria sozinha não separava:
- 5826 (entry 1.0) vs 1623 (entry 0.14) — mesmo céu limpo, esforço opôs as leituras.
- 1522 (last6 0.765, flush absorvido) vs 1775 (last6 0.066, flush puro-vendedor) — mesma família de flush, maturidade oposta.
- Em D, entry_up=1.0 idêntico NÃO desempatou — lá a geometria foi o eixo. Logo: volume desempata quando a geometria é igual; geometria desempata quando o volume é igual.

## Backbone causal — como moldou a leitura (esp. 5627)
O anchor causal (window termina EXATO no entry, sem barras futuras) significa que toda dist_supply/dist_demand reflete só o que era visível. **5627** é o caso onde isso mais importou: a versão contaminada por look-ahead implicava supply mais COLADO; o dist_supply CAUSAL (1.87 ATR) coloca o preço mais LONGE da oferta. Isso me fez NÃO ler 5627 como "trap-na-parede" e sim como rejeição-de-topo/residual com chão distante (demand 10.57 ATR) — uma leitura mais cautelosa e honesta que a contaminada teria forçado. Anchor warnings (close_fidelity=False) em 4401 e 1775 me fizeram REBAIXAR confiança na geometria fina desses dois.

## PERGUNTA-MÃE: "weekly negativo = trap"?
**QUEBRADA.** Macro-negativo NÃO força trap. 5826 e 3949 são macro-negativos (3949 é o MAIS extremo do cluster, −0.67) e leem como washout-construtivo com change-of-character, dado céu limpo + forma de reclaim + esforço comprador real. O que produz "trap" não é o weekly — é a CONJUNÇÃO: supply próximo (WALL) × forma de push-into ou rejeição × esforço comprador ausente/colapsando × (quando presente) div bearish. Weekly negativo é o pano de fundo; a geometria de supply e o esforço de volume são os eixos causais que decidem trap vs washout. O par D (mesmo dia, macro idêntico, geometria invertida → leituras opostas) é a prova mais limpa disso.
