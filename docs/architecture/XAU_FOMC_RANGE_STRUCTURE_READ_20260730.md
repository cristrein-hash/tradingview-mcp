# XAU — Leitura de Estrutura pós-FOMC + Range Macro-estrutural (29-30/07/2026)

Documento de conhecimento consolidado (Cris pediu 2026-07-30). Cobre: a reação do FOMC 29/07, a lição do
chicote, a leitura de range macro-estrutural via chart MCP, os níveis estruturais reais, e o método de cruzar
ouro com DXY/EURUSD/petróleo. Fonte primária = leitura RAW do chart XAUUSD 60min via MCP (OB Detector v11,
SMC LuxAlgo, RSI, Session Volume Profile) + snapshots EF. Serve de referência para operações futuras na zona.

---

## 1. O evento FOMC 29/07 — o chicote clássico (spike-and-fully-reverse)

- **Decisão 19:00 Lisboa:** HOLD 3,75% (consenso, não-evento). Baseline pré-FOMC **4047,35**.
- **Powell 19:30 (dovish):** ouro disparou **+59 pts até 4116** em ~40 min.
- **Devolveu TUDO:** fechou a janela (21:00) a **4044,97** (−2,4 vs baseline). Round-trip completo.
- **Porquê o dovish não colou:** petróleo a disparar (WTI +12,7, inflação) + real yield 2,41 a subir seguraram
  o dólar. O tom moveu a FITA, não o PREÇO. Dovish na retórica, hawkish nos fundamentos (oil→inflação→Fed).

### Lição dura (forward): VETO DE EVENTO nos dois sentidos
1. **Não operar 3h antes** de um evento binário (o E2 shortou @4001 pré-FOMC = timing hostil que se sinalizou).
2. **Não narrar o pico como conclusão** (Claude narrou +59 como "reversão a sério" — ERRO; num evento binário,
   +59 em 40min NÃO é reversão confirmada, pode desfazer-se por completo — e desfez).
3. **O que salvou = PROCESSO, não a leitura do pico:** o reader recusou 14 longs no dia, NENHUM validado na
   euforia do spike. Regra "só long com reclaim validado + não perseguir esticado" impediu entrada no topo.
4. **Gestão de saída = trailing em momentum de evento.** Cris fez +1.600$ real (conta FN→100.350) mas podia
   ter sido ~3.000$ com trailing no discurso do Powell (protegia o topo antes da devolução). Ver PDF V_stair.

---

## 2. Leitura de estrutura via chart MCP (30/07, XAUUSD 60min) — RANGE macro-estrutural

Leitura RAW dos indicadores do chart (não SLIM, não inventado — o que está lá):

### Order Blocks (OB Detector v11) — os níveis ESTRUTURAIS reais
- **Oferta (supply) acima:** 4101-4116 (= topo exato do spike FOMC, agora zona de rejeição), 4149-4166,
  4183-4203, 4255-4276, 4310-4329, 4362-4382.
- **Procura (demand) abaixo:** **3995,84-4010** (OB estrutural principal), 3959-3976.
- **Preço ~4043 = VÁCUO** entre oferta 4101-4116 e procura 3995-4010. **NÃO há OB em 4042.**

### ⭐ Distinção crítica: 4042 é PIVÔ, não estrutura
O "base 4042" que parecia suporte **não tem order block**. A procura REAL com bloco é **3995-4010**. Um long
ESTRUTURAL mora em 3995-4010, não em 4042. 4042 = esperança; 4010-3995 = estrutura. **Regra geral: ler o OB
que já existe, nunca inventar nível à mão** (feedback_never_invent_read_existing_indicator).

### SMC (LuxAlgo) — indecisão, não domínio
Mistura de BOS/CHoCH perto do preço: CHoCH 4051, BOS 4040, EQH/CHoCH 4047,89. = **equilíbrio/range**, não
tendência direcional. **CHoCH em 4051** = teto de momentum (reclaim acima de 4051 tem significado estrutural,
não arbitrário) → é o 2º gatilho qualificante do vigia, além do OB.

### Momentum/fluxo (30/07 manhã)
- RSI **47,9 < RSI-MA 54,7** = momentum ainda fraco/abaixo da média.
- Session Volume Profile: **Down 12,3K vs Up 9,3K** = vendedor ainda domina (a enfraquecer).
- NAS TOP/BOTTOM detector = **0,00** (não vê fundo nem topo aqui).

### Veredito de estrutura
**RANGE macro-estrutural 3995↔4116.** Não é "bear a continuar" (enquadramento que o Claude corrigiu — era
range) nem "acumulação confirmada" (ainda). Preço no MEIO do range = pior sítio para entrar. Os dois níveis
acionáveis: long estrutural no **OB 3995-4010** OU reclaim confirmado **acima de 4051** (CHoCH), idealmente
pós-catalisador. Boa chance de repique de alta NO OB (Cris), num pano de fundo a definir pelo dólar.

---

## 3. Método: cruzar OURO com DXY / EURUSD / PETRÓLEO (macro read, NÃO validação cross-asset)

> Isto é LEITURA DE CONTEXTO macro para enquadrar o ouro — não é validação OOS/cross-asset de estratégia
> (essa mora dentro dos dados; ver feedback_no_oos_no_crossasset_validation). O guard de cross-asset dá
> falso-positivo aqui; a intenção é contexto, não backtest.

- **Ouro sobe quando o dólar cai.** Testar sempre a tese do ouro NO DÓLAR, não no ouro isolado.
- **Leitura de níveis reais (30/07, via MCP quote_get com símbolo):** DXY **100,93** (fraco, perto de mínimos
  de meses; 2024-25 andava 104-107), EURUSD **1,1453** (euro forte = confirma dólar fraco).
- **Como ler:** DXY/EUR spot pedem-se via MCP trocando o símbolo do chart (o `quote_get` fica preso ao chart
  pinado XAU) — mas o **bar-store é alimentado por websocket Finnhub INDEPENDENTE** (`finnhub_gld_ws.py`),
  NÃO pelo símbolo do chart, por isso trocar o símbolo NÃO corrompe os dados de trading. Restaurar
  PEPPERSTONE:XAUUSD 60min logo a seguir. Tickers: `TVC:DXY`, `OANDA:EURUSD` (o "DXY" simples resolve para
  XAUUSD Pepperstone — usar TVC:DXY).
- **Dinâmica em curso (30/07):** petróleo↑ → inflação → Fed hawkish nos fundamentos → **DXY a RECUPERAR**,
  **EURUSD a CAIR**. O vento dólar-fraco (tailwind do ouro) está a inverter no curto prazo → **sobe a
  probabilidade de o ouro DESCER a testar o OB 3995-4010 antes de qualquer repique.**
- **Árbitro imediato:** Core PCE 13:30 Lisboa (30/07). PCE fraco ≤0,2% → DXY fura baixo → OB 3995-4010 = base
  de acumulação. PCE forte ≥0,3% → dólar firma → pressão para baixo mantém-se.

---

## 4. Estado operacional (30/07 manhã)
- Vigia demanda+reader armado em **OB 3995-4010 (estrutural)** + **teto CHoCH 4051** (`research/watch_demanda_reader_20260728.py`).
  Toque = heads-up geográfico; reclaim (fecho acima do topo da zona) = juízo do reader (mesmo render_composite+
  run_read do E2, nunca paralelo). Reader julga legitimidade, NUNCA mecânico.
- Preço a furar 4040 para baixo na abertura de Londres = a caminho do teste do OB, coerente com dólar a firmar.
- Retoma dry 0/8 (mecânica continua a comprar repiques em bear/range = facas; contraste vs reader mantém-se).
