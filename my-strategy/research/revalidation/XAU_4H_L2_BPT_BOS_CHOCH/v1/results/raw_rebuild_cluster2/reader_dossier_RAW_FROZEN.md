# READER DOSSIER — Cluster 2 (macro negativo) — RAW-FROZEN

> Leitura CEGA. Fonte 100% RAW. SVP/POC/VAL/VAH/acceptance = BLOCKED_UNMAPPED em TODOS os 10 episodios.
> Unidade = EPISODIO, nao trade. PROIBIDO score/TAKE/SKIP. Nenhum resultado/futuro consultado.
> Weekly negativo em todos os 10 → NAO e o discriminador. O eixo procurado e a MATURIDADE DA QUEDA
> e a relacao com o supply via os boxes Custom OB (supply-as-fuel vs supply-as-wall).

---

## NOTA DE METODO (limite estrutural imposto pelos BLOCKED)

A pergunta central deste cluster — "isto e absorcao/acceptance acima de uma area de valor, ou e
repique mecanico contra parede?" — e exatamente a pergunta que SVP/VAL/VAH/POC/acceptance
responderiam. Com esses campos BLOCKED, eu leio o PROXY do acceptance pela FORMA OHLC: sequencia de
closes, posicao do close dentro do range da barra, presenca de flush (mecha inferior longa) seguido de
recuperacao (close no topo), e a relacao close-vs-supply em ATR. Onde a forma e ambigua, a leitura fica
genuinamente sub-determinada e eu declaro isso — nao preencho com inferencia. O `dist_demand` do RAW
substitui parcialmente o "estamos sobre suporte?" mas nao diz se ha ACEITACAO de preco ali (volume-time),
so distancia geometrica.

---

# SUB-BLOCO A — macro negativo + CLEAN SKY (sem supply overhead proximo)

## EP 5826 (2023-10-06) — SUPPLY_FAR 5.86ATR, clean_sky=True
1. **Episodio em andamento:** queda madura (cascade -2). Forma OHLC mostra uma virada de carater clara:
   barras finais com expansao de range para CIMA (1820→1834 high, close 1831.78 no topo do range), depois
   continuacao. Saiu de compressao (barras 1-2 estreitas, ~3-4 pts) para impulso de ~14 pts com close forte.
2. **Fatores que mudam de significado no macro-negativo:** NAS 5×LONG + SMC alternando BOS/CHoCH em
   contexto BEAR = nao e tendencia de alta, e *reversao incipiente sendo registrada pelos detectores*.
   bubbles sell_mL=16 e MUITO sell-side acima — em clean sky (supply 5.86ATR distante) isso vira
   COMBUSTIVEL de shorts presos, nao parede: nao ha OB de venda proximo pra absorver a subida.
3. **NATUREZA:** washout-maduro-com-mudanca-de-carater. Expansao de range + close no topo apos cascade,
   sem supply proximo, com sell-bubbles distantes = trampolim.
4. **EXPECTATION:** continuacao da recuperacao com pouca resistencia imediata; ceu limpo ate ~5-6ATR.
5. **Confianca:** ALTA. Melhor convergencia forma+estrutura do cluster.
6. **BLOCKED:** sem acceptance nao confirmo se o close 1831 e aceito ou spike; a forma sugere aceitacao
   (close no topo, sem rejeicao), mas e proxy.

## EP 1623 (2021-01-20) — SUPPLY_FAR 9.63ATR, clean_sky=True
1. **Episodio:** subida em escada limpa (1840→1849→1852, closes subindo, ranges modestos e ordenados).
   demand muito perto (0.78ATR) — preco trabalhando logo acima de suporte. Supply absurdamente longe (9.63ATR).
2. **Mudam de significado:** NAS abre 4×SHORT virando LONG na ultima — *flip recente*, detector pegando o
   ponto de virada agora, nao tendencia ja-estabelecida. SMC 4×CHoCH apos BOS = mudanca de carater
   confirmada e repetida. bubbles 0/0 = SEM pressao de venda registrada → nada acima brigando. v3=TRANSITION
   (nao BEAR pleno): a queda esta menos madura/mais rasa que os BEAR plenos do cluster.
3. **NATUREZA:** washout-maduro-com-mudanca-de-carater (variante "ceu vazio"). Diferenca vs 5826: aqui a
   subida e mais suave/ordenada e o supply esta literalmente fora de alcance; risco e timing-cedo-demais,
   nao parede.
4. **EXPECTATION:** drift de alta de baixa-resistencia; sem obstaculo estrutural a vista.
5. **Confianca:** ALTA-MEDIA. Forma limpa mas menos explosiva que 5826; CHoCH-stacking e o melhor sinal.
6. **BLOCKED:** sem POC nao sei se 1852 ja e "valor justo" ou extensao acima de valor — limita confirmar
   sustentabilidade da escada.

---

# SUB-BLOCO B — macro negativo + SUPPLY PROXIMO (overhead colado)

## EP 4401 (2022-11-04) — SUPPLY_NEAR 0.27ATR, clean_sky=False
1. **Episodio:** rally vertical para DENTRO do supply. Closes 1629→1633→1647, ultima barra range enorme
   (1633→1648, +15pts, close no topo) parando a 0.27ATR do OB de venda. Demand longe (2.17ATR) — preco
   ja correu pra longe do suporte.
2. **Mudam de significado:** o impulso forte aqui e SUSPEITO, nao bom: ele entrega o preco colado na parede.
   NAS 3×LONG → 2×SHORT (flip PRA BAIXO na borda do supply) = detector ja virando vendedor exatamente onde
   o OB esta. bubbles sell_mL=11 acima + supply 0.27ATR = parede REAL com munição. SMC EQL+2×BOS = expansao
   sem confirmacao de reversao (so 1 CHoCH cedo).
3. **NATUREZA:** supply-as-wall. Empurrao bonito que termina debaixo do martelo; NAS ja virando short.
4. **EXPECTATION:** rejeicao no OB; subida sem espaco. O rally e a propria armadilha (compra na cara da parede).
5. **Confianca:** ALTA (na leitura de PAREDE).
6. **BLOCKED:** sem VAH nao confirmo se 1647 e o teto exato do value area acima; mas dist_supply 0.27ATR +
   sell-bubbles ja bastam pra ler parede.

## EP 3825 (2022-06-23) — SUPPLY_NEAR 0.39ATR, clean_sky=False
1. **Episodio:** isto NAO e impulso — e DERIVA/lateral fraca. Closes 1840→1837→1833→1834, range
   contraindo, sem direcao. Preso ENTRE supply 0.39ATR e demand 0.57ATR (corredor estreitissimo, ~1ATR total).
2. **Mudam de significado:** NAS 5×LONG mas forma nao confirma — detector otimista, preco indeciso.
   bubbles 0/0 (sem munição de venda) atenua a parede, MAS o supply colado (0.39ATR) e o range morto
   dizem que nao ha energia de compra pra romper. cascade -2, v3=BEAR pleno.
3. **NATUREZA:** base-absorcao-incompleta. Esta comprimindo entre duas areas mas sem mostrar o flush+reclaim
   que assinaria fundo; precisa de mais barras. Nao e parede com munição (bubbles 0), nao e trampolim (sem expansao).
4. **EXPECTATION:** indefinicao; mais provavel chop/escorregar que disparar. Entrada cedo na base.
5. **Confianca:** MEDIA. Forma morta e o sinal dominante; a ausencia de munição salva de ser parede dura.
6. **BLOCKED:** ESTE e o episodio mais penalizado pela falta de acceptance/VA. Num corredor de ~1ATR entre
   OBs, saber de que lado do POC o preco esta aceito decidiria base-vs-rejeicao. Sem isso, leitura genuinamente
   sub-determinada.

---

# SUB-BLOCO C — macro negativo + FLUSH sob supply

## EP 1522 (2020-12-23) — SUPPLY_BLOCKS 1.92ATR, clean_sky=False
1. **Episodio:** subida ja consumada e desacelerando sob blocos. Barra 1 forte (1865→1876), depois
   3 barras de digestao estreita (closes 1873/1873/1876, ranges murchando) parando ~1.92ATR sob supply.
   demand 0.9ATR abaixo.
2. **Mudam de significado:** NAS 4×LONG → SHORT na ultima (flip pra baixo) + SMC terminando 2×CHoCH =
   carater virando JUSTO ao desacelerar sob os blocos. bubbles buy_mL=2 (raro: leve compra) mas fraco.
   SUPPLY_BLOCKS (multiplas zonas) = nao e uma parede, e uma escadaria de oferta.
3. **NATUREZA:** supply-as-wall (variante blocos escalonados). A digestao estreita sob blocos + NAS flip =
   exaustao do impulso encostando em oferta empilhada.
4. **EXPECTATION:** estancamento/rejeicao escalonada; pouco espaco antes do primeiro bloco.
5. **Confianca:** MEDIA-ALTA. O flip NAS + murchar dos ranges sob blocos e coerente.
6. **BLOCKED:** sem acceptance nao distingo "digestao saudavel pre-rompimento" de "exaustao pre-rejeicao";
   a desaceleracao + flip pendem pra rejeicao, mas e proxy.

## EP 1873 (2021-03-18) — SUPPLY_BLOCKS 1.54ATR, clean_sky=False, **RSI div=Regular Bearish**
1. **Episodio:** repique apos flush. Barra com mecha inferior longa (1736→L1719→C1723, rejeicao de baixo),
   depois recuperacao (1734/1736), depois ja recuando (close 1731 abaixo do high). demand COLADO 0.08ATR
   (preco praticamente em cima do suporte). cascade -3 (queda muito madura).
2. **Mudam de significado:** **divergencia Regular Bearish no RSI 54.9** e o unico div do cluster — em
   macro-negativo, sob SUPPLY_BLOCKS, num repique, isso e bandeira VERMELHA: momentum nao acompanha o preco.
   NAS 5×LONG e contradito pela divergencia. SMC virou BOS×3 (continuacao, nao reversao). buy_mL=1 trivial.
3. **NATUREZA:** bear-pullback-trap. Repique tecnico sob blocos com divergencia bearish e SMC em BOS de
   continuacao = a alta e o engodo. demand 0.08ATR significa que esta no limite — qualquer falha quebra o suporte.
4. **EXPECTATION:** falha do repique; risco de perder o suporte colado logo abaixo.
5. **Confianca:** ALTA (na leitura de TRAP). Divergencia + blocos + cascade -3 convergem.
6. **BLOCKED:** sem VAL nao confirmo se 1719 foi flush-abaixo-do-valor-com-reclaim (que salvaria) — mas o
   recuo final + divergencia pendem forte contra reclaim genuino.

## EP 5627 (2023-08-22) — SUPPLY_NEAR 0.84ATR, clean_sky=False, demand 11.59ATR (!)
1. **Episodio:** preco SUSPENSO no ar. Forma: barra forte (1895→1903) depois flush (1902→L1889→C1890,
   mecha) e recuperacao parcial (1897, mas abaixo do high). Supply colado 0.84ATR; demand a ABSURDOS
   11.59ATR abaixo — sem rede de seguranca embaixo.
2. **Mudam de significado:** o 11.59ATR de demand-vazio e o fato dominante: comprar aqui e comprar sem chao.
   NAS 2×SHORT→3×LONG (flip pra cima recente) mas contra supply 0.84ATR. bubbles sell_mL=15 acima = munição
   pesada na parede colada. SMC CHoCH→4×BOS (continuacao apos 1 virada).
3. **NATUREZA:** supply-as-wall. Parede colada com 15 sell-bubbles E sem demand de apoio embaixo = pior
   geometria risco/estrutura do cluster (teto duro, piso inexistente).
4. **EXPECTATION:** rejeicao no supply; se falhar, queda longa sem suporte ate 11.59ATR.
5. **Confianca:** ALTA (parede + ausencia de piso).
6. **BLOCKED:** sem POC nao sei se o flush de 1889 foi aceito como valor; mas demand 11.59ATR ja torna a
   leitura robusta sem isso.

## EP 1775 (2021-02-24) — SUPPLY_NEAR 0.65ATR, clean_sky=False, cascade -3
1. **Episodio:** flush profundo com reclaim parcial. Barra-chave: 1807→L1783.56→C1785 (flush violento de
   ~24pts), depois reclaim forte (1785→C1797, recupera ~12pts, close no MEIO-ALTO do range 1783-1804).
   demand 2.35ATR; supply colado 0.65ATR. cascade -3.
2. **Mudam de significado:** este flush+reclaim e a assinatura mais proxima de capitulacao-com-virada do
   bloco C, MAS termina colado sob supply 0.65ATR. bubbles sell_mL=4 (leve) acima. NAS 5×LONG. RSI 55.
   O reclaim e real (forma boa), mas o teto esta a 0.65ATR.
3. **NATUREZA:** AMBIGUO entre washout-maduro-com-mudanca-de-carater (o flush+reclaim) e supply-as-wall
   (o teto colado). A forma diz fundo; a geometria diz teto. Classifico como **base-absorcao-incompleta**:
   o reclaim mostrou demanda mas parou debaixo da oferta sem prova de rompimento.
4. **EXPECTATION:** tentativa de continuar o reclaim travada no supply 0.65ATR; resolve so com aceitacao
   acima do OB.
5. **Confianca:** MEDIA. Tensao genuina forma-vs-geometria, nao a forco resolucao.
6. **BLOCKED:** ESTE e o 2º mais penalizado. acceptance acima do supply 0.65ATR decidiria reclaim-genuino
   vs rejeicao-iminente. Sem VA, fica honestamente dividido.

---

# SUB-BLOCO D — macro negativo EXTREMO (weekly -0.67, cascade -2)

## EP 3949 (2022-07-21) — SUPPLY_FAR 2.42ATR, clean_sky=False, demand=None
1. **Episodio:** rally de capitulacao-reversa explosivo. Forma: flush (1693→L1682→C1684) seguido de
   DOIS impulsos enormes (1684→C1705, +21pts; depois 1705→C1713, fecha no topo). Expansao de range
   massiva pra cima apos o flush. Supply 2.42ATR (espaco). demand=None (sem OB de demanda mapeado abaixo).
2. **Mudam de significado:** weekly -0.67 (mais negativo do cluster) torna este o rally MAIS contra-tendencia
   — mas a forma (flush→reclaim duplo com close no topo) e exatamente o washout-com-mudanca-de-carater.
   SMC 5×BOS = momentum puro (sem CHoCH, e impulso nao reversao-confirmada). bubbles sell_mL=5 moderado,
   supply 2.42ATR = espaco antes da parede. demand=None remove a rede embaixo (risco se falhar).
3. **NATUREZA:** washout-maduro-com-mudanca-de-carater. O flush+duplo-impulso com close no topo e o
   trampolim mais forte do bloco D; macro extremo eleva o risco mas a forma e convincente.
4. **EXPECTATION:** continuacao do impulso ate o supply ~2.42ATR; primeiro teste do teto la.
5. **Confianca:** MEDIA-ALTA. Forma excelente; macro-extremo + demand=None descontam.
6. **BLOCKED:** sem acceptance nao confirmo se os 2 impulsos sao aceitos ou exaustao-vertical (que reverteria);
   a forma pende a aceitacao mas verticalidade extrema sem VA e ambigua.

## EP 3929 (2022-07-18) — SUPPLY_BLOCKS 1.64ATR, clean_sky=False, demand 1.05ATR
1. **Episodio (3 dias ANTES do 3949):** subida ordenada sob blocos, mais madura/calma. Closes
   1714→1714→1722→1718 (ultima recua do high 1723). Range estreitando, parando 1.64ATR sob SUPPLY_BLOCKS.
   demand 1.05ATR (suporte presente). Mesmo weekly -0.67.
2. **Mudam de significado:** SMC 5×BOS (impulso) mas a forma desacelera sob blocos (vs 3949 que acelera no
   espaco). bubbles sell_mL=10 acima (dobro do 3949) + SUPPLY_BLOCKS empilhado = parede mais densa.
   O recuo da ultima barra (1722→1718) sob blocos densos e o tell.
3. **NATUREZA:** supply-as-wall (blocos). Mesmo macro do 3949, mas geometria oposta: aqui o impulso ja
   desacelera encostando em blocos com 10 sell-bubbles, nao corre em ceu aberto.
4. **EXPECTATION:** estancamento sob os blocos; subida sem espaco, ao contrario do 3949.
5. **Confianca:** MEDIA-ALTA. O contraste interno com 3949 (mesmo dia/macro, geometria invertida) reforca.
6. **BLOCKED:** sem acceptance nao distingo digestao-pre-rompimento de exaustao-sob-blocos; recuo + sell-bubbles
   pendem pra exaustao.

---

# CONTRASTES POR PAR

**A: 5826 vs 1623** — Ambos clean-sky/supply-far/CHoCH-stacking. Diferenca: 5826 e impulso explosivo com
expansao de range (trampolim ativo); 1623 e escada suave com flip NAS recente e v3=TRANSITION (queda menos
madura). 5826 = forca ja em movimento; 1623 = virada acabando de nascer. **Hipotese pos-entry:** ambos devem
estender com baixa resistencia; 5826 mais rapido, 1623 mais gradual. Se algum falhar, sera o 1623 (virada
mais nova, menos prova).

**B: 4401 vs 3825** — Ambos SUPPLY_NEAR colado. Diferenca decisiva: 4401 e impulso forte que ENTREGA o preco
na parede (com 11 sell-bubbles = parede armada → supply-as-wall); 3825 e range morto sem munição (bubbles 0
→ base-absorcao-incompleta). O perigo de 4401 e a propria forca; o de 3825 e a ausencia de forca. **Hipotese
pos-entry:** 4401 rejeita no OB colado; 3825 chop indefinido sem disparar.

**C (4 eps):** todos flush/repique sob supply, mas se separam por forma e momentum:
- 1873 = bear-pullback-trap (UNICA divergencia bearish + SMC BOS-continuacao + demand 0.08ATR no limite).
- 5627 = supply-as-wall extremo (parede 0.84ATR + 15 bubbles + demand-vazio 11.59ATR, sem piso).
- 1522 = supply-as-wall (blocos, flip NAS, ranges murchando — exaustao sob escadaria).
- 1775 = base-absorcao-incompleta (melhor flush+reclaim do bloco, mas trava sob supply 0.65ATR).
**Diferenciador visual:** so 1775 mostra flush+reclaim genuino (close no meio-alto apos -24pts); 1873/1522
mostram repique que JA recua; 5627 esta suspenso sem chao. **Hipotese pos-entry:** 1873 e o trap mais limpo
(deve falhar); 1775 e o mais propenso a tentar seguir mas travado no teto; 5627/1522 rejeitam na oferta.

**D: 3949 vs 3929** — MESMO dia/macro extremo (weekly -0.67), geometria INVERTIDA. 3949 = flush+duplo-impulso
em espaco aberto (supply 2.42ATR) = trampolim. 3929 = subida desacelerando sob SUPPLY_BLOCKS com 10
sell-bubbles = parede. O par isola perfeitamente o eixo do cluster: **nao e o macro (identico), e a relacao
com o supply (espaco vs blocos+munição).** **Hipotese pos-entry:** 3949 estende ate ~2.42ATR; 3929 estanca
sob os blocos.

---

# CONTRASTE DO CLUSTER (sintese)

O weekly negativo e ruido comum (10/10) — confirmado nao-discriminador. O eixo que ORGANIZA o cluster e a
**GEOMETRIA PRECO-vs-SUPPLY combinada com a FORMA do ultimo movimento**, lida como supply-as-FUEL vs
supply-as-WALL:

- **Supply-as-FUEL / washout-com-mudanca-de-carater** (5826, 1623, 3949): supply distante (≥2.4ATR) +
  forma de expansao/flush+reclaim com close no topo. Sell-bubbles existem mas estao LONGE → viram combustivel
  de shorts presos, nao teto. Trampolim.
- **Supply-as-WALL** (4401, 5627, 1522, 3929): supply colado (≤1.6ATR, frequentemente <1ATR) +
  frequentemente sell-bubbles densos (10-16) na parede + forma que desacelera/entrega o preco no OB.
  Teto com munição. Impulso forte aqui e sintoma, nao virtude.
- **Base-absorcao-incompleta** (3825, 1775): comprimido entre OBs OU reclaim genuino que trava sob supply,
  SEM prova de rompimento. Precisa de mais barras / aceitacao acima. Genuinamente indeterminado.
- **Bear-pullback-trap** (1873): a unica leitura de armadilha pura — divergencia bearish + SMC em BOS de
  continuacao + demand no limite. O sinal de alta e o engodo.

Padroes secundarios robustos: (a) **flip NAS pra baixo na borda do supply** (4401, 1522) e um tell de
rejeicao; (b) **expansao de range com close no topo apos cascade** (5826, 3949, parcial 1775) e o tell de
trampolim; (c) **sell-bubbles importam pela DISTANCIA, nao contagem** — 16 bubbles longe (5826) = fuel;
10-15 bubbles colados (3929, 5627) = wall. A polaridade bubble depende do contexto supply, confirmando o
canon "bubble_SELL como fuel em reversao-de-fundo vs wall em pullback".

---

# IMPACTO DA AUSENCIA DE SVP/POC/VAL/VAH/ACCEPTANCE

A leitura de **forma** (supply-as-fuel vs wall, washout vs trap) sobreviveu razoavelmente sem VP, porque
distancia-ao-supply em ATR + sell-bubble-distance + forma OHLC dao um proxy estrutural forte para os casos
de extremo (5826, 4401, 5627, 3949, 3929, 1873 — confianca media-alta a alta).

Onde a ausencia DOI de verdade — episodios sub-determinados:
- **3825** (corredor ~1ATR entre OBs): sem saber de que lado do POC o preco esta aceito, base-vs-rejeicao
  fica no ar. Maximo penalizado.
- **1775** (flush+reclaim travado sob supply 0.65ATR): acceptance acima do OB e exatamente o arbitro entre
  reclaim-genuino e rejeicao-iminente. Leitura honestamente dividida.
- Em **3949/1522/1873** o acceptance refinaria "impulso aceito vs exaustao vertical" e "digestao vs
  exaustao", mas outros eixos (demand=None, blocos, divergencia) ja resolvem a leitura.

Em sintese: SVP/acceptance teria movido principalmente os DOIS casos de absorcao-incompleta (3825, 1775) de
"indeterminado" para classificavel, e teria adicionado uma camada de confirmacao (nao de viragem) nos casos
ja-claros. Nenhuma leitura clara foi INVERTIDA pela ausencia; duas ficaram sub-determinadas por ela.
