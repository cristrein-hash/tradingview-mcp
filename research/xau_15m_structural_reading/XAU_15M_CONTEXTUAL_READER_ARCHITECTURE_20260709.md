# XAU 15M CONTEXTUAL READER — ARQUITETURA (2026-07-09)

> Reset ordenado pelo Cris: aplicar o MÉTODO do XAU 4H L2/BPT Reader Vivo ao 15M — leitura
> contextual de episódios, NÃO mais classificadores/estados/grids. Doc de arquitetura; ZERO código,
> ZERO backtest, ZERO labels de treino. Insumos: método L2/BPT extraído (canon do episódio, Evidence
> Library, sósias, Operating Manual RAW-CONFIRMED) · leitura de erros da história 15M · 34 dossiês
> (`reports/XAU_15M_CONTEXTUAL_READER_EPISODE_DOSSIERS.md`).

## A lei herdada do L2/BPT (transposta na íntegra)
1. **Não medir primeiro o trade. Ler primeiro o EPISÓDIO que produziu o trade.**
2. O LEITOR julga; o MEDIDOR não julga. O código monta contexto e regista — não decide.
3. A leitura segura o episódio INTEIRO; **PROIBIDO colapsar em score, voto, booleano ou threshold.**
4. Quantificação vem DEPOIS, como auditoria (blind→audit→status CONFIRMED/MODIFIED/REFUTED/
   QUARANTINED), nunca como árbitro. Outcome NUNCA é input da leitura (`_AUDIT_outcome_NOT_FOR_READING`).
5. Papéis separados: **DOSSIÊ** organiza · **READER** interpreta · **CHALLENGER** ataca · **MEDIDOR**
   regista e compara depois.

## 1. Unidade de análise
**O EPISÓDIO 15M** — a sequência de mercado que produz (ou nega) uma região de interesse, lida
dentro da perna-mãe que a contém. Nunca a vela, nunca o trade isolado, nunca a região geométrica.

## 2. Como se define episódio 15M (operacional, sem pivô mecânico)
Um episódio ABRE quando a trajetória em curso é interrompida de forma relevante (flush/queda que
devolve parte material da perna-mãe; ou entrada em base lateral prolongada) e FECHA quando o mercado
resolve (retoma a perna-mãe; quebra e estende a queda; ou converte-se noutra perna). O pacote de
episódio corta SEMPRE no instante de leitura (zero futuro) e carrega: lead-in de ~200-400 barras 15M,
path narrado (Camada 0), backbone (Camada 1), evidências (Camada 2), sósias (Camada 3). As 3 famílias
do GT são episódios-tipo, não classes: pullback-em-perna-forte · capitulação-fim-de-queda ·
base-de-range. Fronteiras exatas de abertura/fecho = calibradas na leitura dos dossiês (não por grid).

## 3. Separação região ↔ entry (lição nº 6 dos dossiês, medida: 2,2h-31h de lag)
A vela de FUNDO do GT **não é** a vela de ENTRY (sweeps de −6,3 ATR e retestes de −8 ATR entre marca
e entrada, medidos). O Reader produz **leitura de região** (este episódio está a construir fundo
legítimo?) e — só depois, em fase futura própria — a entry vive no retest/reação DENTRO de um
episódio já lido como válido. Nenhuma confirmação vira entry (A2-ANCHOR-ONLY mantém-se como lei).

## 4. Como o sistema sabe que uma região é relevante
**Região ≠ validade — eixos independentes** (padrão nº 3: A2 cobriu 3/4 INVALIDO e falhou 3 fundos
válidos). A relevância NÃO vem da geometria; vem da leitura em duas perguntas ordenadas:
1. **"A perna-mãe terminou (ou está exausta / é a favor)?"** — a pergunta nº 1 de TODOS os 34
   dossiês. Nível existente sem término de perna = isca. Término de perna sem nível histórico =
   fundo real que anchor nenhum vê (os 3 MISS do A2).
2. **Que ESPÉCIE de zona é esta?** — rotulada NA CRIAÇÃO: base-devolvida vs origem-de-impulso
   (DM do GT nasce no TOPO do range, pos96 0,81-0,98 — medi-las como "bottoms" foi erro de
   taxonomia, padrão nº 5) vs topo-convertido vs base-de-range.

## 5. Como evitar compra de topo (o erro A-BULL, agora com assinatura medida)
**Proporcionalidade do pullback dentro da perna-mãe**: losers A-BULL compram devoluções de
3,8-6,6 ATR em pernas com +14-30 ATR de extensão e pos384 0,73-0,95; winners devolvem 9,8-13,9 ATR
até estrutura (padrão nº 2; B4/C5 = mesmo erro no mesmo dia, GT e engine). O Reader lê "dip raso no
alto sem pullback proporcional" como assinatura de SKIP — proporcionalidade é LEITURA condicionada à
perna (não threshold fixo universal; a medição vem depois como auditoria). Complemento: idade/extensão
da perna-mãe regula o ALVO (padrão nº 9: fim-de-perna-madura, entrada boa + gestão errada = loser).

## 6. Como evitar repique raso em BEAR
Três evidências convergentes, todas já validadas em algum canal:
- **Perna bear VIVA por cima** = SKIP (os 3 INVALIDO de março; texto do próprio Cris);
- **Bounces falhados contam contra o próximo** (padrão nº 8: B1→B2→B3, cada bounce mais baixo,
  reclaims 2→81→54 barras, o 3º bounce foi o mais letal — evidência mensurável e causal);
- **Filtro capitulation VIVO** (BEAR-v5-causal & 1D_px_vs_ema≥0 → repique raso; VALIDATED_CAUSAL_
  RISK_CONTROL, 22=22L/0W out-of-population) — entra como evidência da Camada 2, não como gate cego.
- Convergência tripla como template de validação (padrão nº 10: 05-mar-2026 — INVALIDO manual +
  corte causal + SL real apontam à mesma leitura por caminhos independentes).

## 7. Como identificar bottom de range
Único episódio onde **região histórica é forte por si** (A2: RANGE_BOTTOM 3/3): base lateral longa
(d_vale ~19+, semanas), múltiplas defesas do mesmo nível, perna-mãe lateral (nem bear viva nem bull
esticada). O Reader exige: base madura + defesa repetida + toque da banda inferior — e lê a POSIÇÃO
dentro do range (a tua regra 4H: só a banda inferior/demanda originadora; meio/topo = loser).

## 8. Como identificar capitulação verdadeira
Preço virgem — NÃO procurar banda (A2: 0/14 em MACRO_BEAR, estruturalmente). Ler a SEQUÊNCIA
(lente-mãe do L2/BPT, OM-RAW-1/-3, re-derivar no 15M): perna bear **exaurindo vs impulsiva** —
clímax/aceleração final JÁ digerida por barras (não renovação de lows), reclaim com corpo, defesa
do low, profundidade compatível com capitulação (drops do GT: 7,9-22,4 ATR), e a régua 4H do Cris:
reteste profundo da região bottom do regime/range anterior quando existe. O reclaim rápido sozinho
NÃO valida (padrão nº 7: B1 reclamou em 2 barras e era o meio da cachoeira; grind-bottom válido
reclamou em 14).

## 9. Converted support sem marcar tudo
Só topos **da escada da perna-mãe corrente** (origem de impulso que ROMPEU estrutura — a definição
DM do teu PLT/DM), rotulados na criação com espécie e contexto; nunca "todo flip vira âncora"
(o A2 marcou 666 conversões — inundação). A conversão só é evidência se a perna-mãe que a criou
continua válida e o retest chega com pullback proporcional.

## 10. Indicadores — só depois da região correta
Ordem inviolável (protocolo §C + tua ordem): episódio lido → backbone fixado → região julgada →
SÓ ENTÃO indicadores (RSI/Bubbles/NAS/OB/SVP) extraídos DIRETO do RAW do HD, avaliados DENTRO do
episódio como evidências com polaridade condicionada (a mesma feature dá +78R fora do bear e −13R
dentro — prova N96). Nenhum indicador acha fundo.

## As 5 camadas (estrutura de leitura, NÃO labels de treino)
- **Camada 0 — Forma/path 15M:** narrativa da trajetória (impulso, pullback, grind, flush, pausa,
  aceitação, rejeição, reclaim, reteste, absorção, falha) com medidas descritivas (profundidade em
  ATR, velocidade, barras) — descreve, não julga.
- **Camada 1 — Backbone condicionante (fixa-se PRIMEIRO):** regime 4H/1D (v5 verbatim) · estado da
  perna-mãe (viva / exaurindo / terminada / a favor) · relação com range/top/bottom anterior ·
  distância a demanda/supply real. Inverte a polaridade de tudo o que vem depois.
- **Camada 2 — Evidências contextuais:** região já defendida? · topo convertido legítimo? · fundo de
  range real? · capitulação digerida? · repique raso? · pullback proporcional? · lower-low
  destrutivo? · bounces falhados acumulados? · aceitação acima da região? Cada evidência com status
  de biblioteca (CORE_CONTEXT / CONDITIONAL / CONTRAST / POLARITY_DEPENDS / WARNING / DO_NOT_GATE),
  re-derivado no 15M via blind→audit — as lentes 4H NÃO são verdades importadas.
- **Camada 3 — Sósias/contraste:** match CEGO na superfície (episódios de aparência igual),
  discriminadores fora do match, clusters HARD (winner vs loser na mesma superfície) como bancada;
  pares casados mesmo-dia/mesmo-contexto = prova mais limpa (B4/C5 já é um).
- **Camada 4 — Decisão qualitativa:** TAKE provável / SKIP provável / REVIEW / OUT_OF_FAMILY /
  RESIDUAL — estrutura de dossiê para encontrar lógica objetiva, nunca alvo de classificador.

## O que fica de fora por enquanto
Entry/SL/exit (fase própria futura; SL V1 + 3R + capitulation filter = transfer intactos) · sizing ·
SHORT · automação do Reader (managed agents = fase futura, como no 4H) · indicadores (Camada 2 do
protocolo, só após regiões corretas) · qualquer backtest.

## Fasquia viva
O caminho só interessa se plausivelmente leva **losers ≤10** preservando os winners de continuidade
— medido como correção de mislabel (loser-takes cortados / skip-winners recuperados), R uncapped,
nunca agregado capado. A leitura L2/BPT provou-se **assimetricamente competente em EVITAR** (trap
lift 0,52) — é exatamente a competência que a fasquia exige.

## Honestidade de origem (correção do DA A5)
**Os 34 dossiês e os 10 padrões transversais são OUTCOME-CONTAMINADOS na origem** (secções rotuladas
por resultado antes da leitura; "Depois: +X ATR" no texto). São HIPÓTESES outcome-informadas para
calibrar a leitura — não achados. **A primeira leitura BLIND ainda não aconteceu**: será feita em
episódios virgens (blind → audit), como manda a lei nº 4. O GT 42/50 está queimado para seleção.

## Proibições ativas neste desenho
Sem "12 estados" · sem grid · sem slope/efficiency como solução · sem comprar reclaim · sem detectar
pivô como estrutura · sem labels novos para parecer progresso · RAW HD only · primitives proibidos.
Registos categóricos (TAKE/SKIP/REVIEW; TERMINADA/EXAURINDO/VIVA; espécies de zona) são estrutura de
leitura — **se algum dia virarem features de treino/threshold, violou-se a lei nº 3** (aviso do DA).
