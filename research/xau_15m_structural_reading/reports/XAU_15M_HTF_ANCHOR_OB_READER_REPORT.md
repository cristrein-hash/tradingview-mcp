# MAPA HTF (BEAR) + OB CAUSAL — LEITURA DO READER (2026-07-09)

> **STATUS (Cris 2026-07-09):** `HTF_MAP_BEAR = CALIBRATION_SIGNAL_CONFIRMED_NOT_VALIDATED` ·
> `OB_DETECTOR = STERILE_FOR_THIS_QUESTION` ·
> `CAPITULATION_READING = PROMISING_BUT_NEEDS_PREREG_COMPOSITE_AND_VIRGIN_TEST` ·
> **thresholds NÃO viram regra** · sem entry/backtest até prereg do composto.

> Prereg `XAU_15M_HTF_ANCHOR_OB_PREREG.md` executado por ordem do Cris. Manifest próprio
> (RAW_LINEAGE_PASS strict, 16 RAW: 9×15M + 3×1H + 4×30M). Medidores contínuos, sem cortes;
> leitura = READER; caminho = CRIS. Calibração declarada (GT conhecido/queimado; tudo bear-2026 no
> set BEAR). Sem entry, sem backtest.

## RESULTADO 1 — MAPA HTF: SEPARAÇÃO PERFEITA 12/12 vs 3/3 (o achado do dia)
`dist_prior_episode_bottom_atr` (distância ao bottom do episódio de regime ANTERIOR fechado, causal):

| população | dist ao bottom anterior (ATR) | 1D (ATR) |
|---|---|---|
| **12 fundos BEAR reais** | **−8,7 a −73,7 (TODOS abaixo)** | −8,2 a −35,7 |
| **3 INVALIDO** | **+1,8 · +0,4 · −4,7 (em cima/mal abaixo)** | −2,9 · −4,4 · −7,4 |

- **Gap: −4,7 (pior INVALIDO) vs −8,7 (fundo mais raso) ≈ 4 ATR** — mas a fronteira assenta num
  ÚNICO par (04-02 vs B3); e **(DA edit 3) os 12 fundos partilham UMA âncora** (o RANGE 13-19/mar,
  bot 4727) — o mapa contribuiu com UM nível para este bear inteiro.
- **B3 vs A6 — o par que D1-D3 não separava — resolve-se: −4,7 vs −16,3 (3,5×).** E este é o ponto
  load-bearing (DA edit 1): **a profundidade RELATIVA-à-janela (dev_atr do D1-D3) NÃO separa
  (A8 16,3 cai DENTRO de [B3 14,5, B2 17,4]); a profundidade ABSOLUTA vs estrutura anterior separa.**
- **(DA edit 1 — deflação obrigatória): NESTE sample, px_vs_ema1d sozinho, dist_prior_range_bottom
  (gap 15,4 — maior que a headline), o PREÇO CRU e até a DATA também separam 12v3 perfeitamente** —
  tudo codifica profundidade/tardividade da queda. O conteúdo ESPECÍFICO da âncora HTF vs
  profundidade-absoluta genérica fica **NÃO-demonstrado até haver episódios onde as medidas
  divirjam**. O que fica demonstrado: absoluto separa, relativo não.
- Null exato: **P = 0,0022 (1/455)**, medida pré-registada; **(DA edit 2) Bonferroni ~4 looks ≈
  0,0088 (sobrevive)** + caveat de exchangeability: 8/12 fundos em Mar23-Abr2 com 2 pares
  mesmo-dia e âncora única ⇒ **n efetivo < 15**; a permutação sobreconta. Caveats: mesmo bear 2026,
  GT queimado ⇒ CALIBRAÇÃO; árbitro = próximo bear/forward.
- `lh_staircase` NÃO separa (LH=3 em ambos em março) — estrutura acima pressionada nos dois casos;
  contexto, não discriminador no instante do fundo.

## RESULTADO 2 — OB DETECTOR nos HTFs: ESTÉRIL para as três perguntas (sem drama, como pré-declarado possível)
- **BULL 26 vs C-losers 6 (OB-1H):** inside 11/26 (42%) vs 2/6 (33%); dist-abaixo 0,2-13,4 vs
  2,1-5,3 — **sobreposição total, zero discriminação**. Causa visível: 9-30 zonas VIVAS por
  instante — com essa densidade, "estar perto de uma zona" é ruído de base (a mesma lição das 698
  regiões do A2).
- **BEAR set (1H+30M):** fundos reais e INVALIDO com dists sobrepostos; detalhe interessante mas
  não-separador: nos extremos das capitulações (A6 1H; 05-04 30M) o preço está ABAIXO de TODAS as
  zonas OB (`dist=None`) — preço virgem, consistente com o A2.
- **RANGE 4 (OB-30M):** inside 0/4; as bases formaram ABAIXO das zonas (dist 1,5-11,6). Descritivo
  (n=4): OB-30M não marca as bases do range do GT.
- **Veredito do reader: o OB Detector, lido causalmente nos HTFs, NÃO acrescenta discriminação a
  nenhuma das três famílias NESTAS perguntas.** Fica anotado como camada de contexto possível para
  outras perguntas (F2/entry-fine), sem estatuto de evidência.

## O que isto monta (com a moldura do DA — edit 4)
Componentes candidatos da leitura de capitulação: `VETO alto-demais (D2) + profundidade ABSOLUTA vs
estrutura anterior (âncora HTF e/ou 1D — correlacionados, contribuição incremental NÃO medida)`.
**O composto NÃO está pré-registado e NÃO tem thresholds** — qualquer gate derivado da fronteira
−4,7/−8,7 seria calibração pós-hoc num par n=1. Antes de F2: (a) prereg do composto com thresholds
fixados ANTES; (b) teste incremental "âncora HTF acrescenta sobre 1D sozinho?" (este sample não
responde); (c) episódios virgens/próximo bear. O OB sai; LH fica como contexto.

## Confirmação negativa
Sem entry · sem backtest · sem tuning pós-olhar (medidas pré-registadas; zero thresholds novos) ·
UNSCORABLE declarados (3 marcas pós-freeze 30M/1H) · calibração, nunca validação.
