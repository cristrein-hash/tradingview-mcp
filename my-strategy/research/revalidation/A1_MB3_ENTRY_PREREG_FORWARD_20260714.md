# PRÉ-REGISTO FORWARD — Gatilho de entry A1 "MICRO-BOS (MB3)" vs RECLAIM-EMA21

**Congelado em: 2026-07-14.** Documento de compromisso. As regras, métricas, vetor de falha, null e
critério PASS/FAIL abaixo ficam **imutáveis** a partir desta data. Qualquer alteração pós-forward =
**novo prereg + novo forward** (proibido mover a baliza depois de ver resultados).

**🚨 EMENDA 2026-07-15 (2 fixes — permitido, NÃO move-baliza) — Cris aprovou esta versão:**
**(1) LOOKAHEAD-FIX:** o DA (`a1a2_lookahead_da.py`) apanhou que a âncora do SL usava `[j−16, j+8]` =
espreitava **8 barras à frente**. Corrigido → timing por **swing-low fractal confirmado** (m=3, ≤ barra
de decisão). Removeu o lookahead: A1 14→11/14, A2 17→14/18.
**(2) SL ESTRUTURAL (low-real):** diagnóstico (`a1a2_loser_diagnosis.py`) provou que **7/7 losers
recuperavam ao 3R ignorando o SL** = SL apertado varrido, região certa. O fractal m=3 ancorava num
swing-low **raso/prematuro**. Corrigido → **SL = LOW REAL do pullback** (menor low até à entrada) −0,1ATR
(causal). Resultado: **A1 MB3 13/14 · A2 MB3 16/18** (ver §8). **Honesto:** melhoria líquida +2 cada, mas
NÃO grátis — o SL mais fundo (R↑→alvo↑) **partiu o A2#6** (WIN→LOSS) ao trocar 3 losers arrumados.
MB3 volta a ≥ reclaim (A1 13 vs 11; A2 16 vs 15). Implementação-mãe = `a1_causal_entry.causal_entry`.
O forward usa esta versão. Ambos fixes = correção de defeito/estrutura, não move-baliza.

Autoria: Claude (desenho) + Cris (aprovação). Status: **DESENHO in-sample selado; validação = FORWARD.**

---

## 0. Porquê (o que este prereg resolve)
O gatilho MB3 foi **desenhado sobre 14 fundos A1 curados** (in-sample: 14/14 WIN SL-first). Isso é
**desenho, não prova** — escolhemos a definição a olhar para esses 14 (risco de winner's curse), e
N=14 nada diz sobre situações não vistas. Este prereg congela a regra ANTES de dados novos para que o
resultado forward seja evidência honesta.

**Canon respeitado (Cris):** SEM OOS / held-out histórico (proibido). "Dados virgens" = **o FUTURO** —
os próximos fundos A1 reais (ops live/proxy do Cris / mercado a avançar a partir de hoje). Não se corta
pedaço do passado.

---

## 1. HIPÓTESE ÚNICA (declarada, congelada)
> Na camada A1 (fundo de pullback em macro BULL), o gatilho **MB3** (1º micro-higher-high após o low)
> tem **expectância positiva a 3R** e **bate o reclaim-EMA21** por **controlo de R / convexidade** —
> sobretudo nos fundos de **ATR alto**, onde o R inflado do reclaim mata o alvo 3R.

Uma hipótese, um gatilho primário (MB3), um comparador (reclaim). Sem grelha de variantes no forward.

---

## 2. REGRAS EXATAS (congeladas; implementação de referência = os scripts commitados)
Implementação-mãe: `a1_microbos_verify.py` + `a1_microbos_pin.py` (commits `32d6385` / a seguir).
Fonte de dados: **RAW 15M direto do HD externo** (`raw_replay/XAUUSD/15M`), barras fundidas
(max-high / min-low / último-close = barra completa). ATR14 e EMA21 causais.

**2.1 Gate de contexto (causal):** macro 1D = **BULL** (`macro_structural_v3.build_layer1`) no fundo,
e o fundo é um **pullback bottom A1** (leg 4H v3 corretivo). O FUNDO (a demanda/bottom a operar) é
identificado pela leitura do Cris / stack macro+leg — a **deteção do fundo é o input** (parte
discricionária já documentada); o que este prereg testa é a **MECÂNICA DE ENTRADA dado o fundo.**

**2.2 Timing + Âncora de low (SL) — CAUSAL (emenda 2026-07-15, versão aprovada):**
- **TIMING (quando o low é "válido"):** swing-low fractal **confirmado** (m=3: `L[p]` menor de
  `[p−3, p+3]`, confirma em `p+3` ≤ barra de decisão). O MB3/reclaim só pode disparar **após** essa
  confirmação. Sem espreitar à frente.
- **SL (onde fica o stop):** `low_real` = **menor low em `[fundo_bar−16, barra_de_entrada]`** (o fundo
  REAL do pullback, conhecido na entrada), `SL = low_real − 0.1 · ATR14(low_real)`. (Substitui tanto a
  janela `[j−16, j+8]` com lookahead como o fractal raso, que era prematuro.)

Implementação-mãe: `a1_causal_entry.causal_entry`.

**2.3 Gatilho MB3 (primário):** entrar no **fecho da 1ª barra 15M `k` após o low-âncora** tal que
`close[k] > open[k]` (verde) **E** `close[k] > high[k−1]` (fecha acima do high da barra imediatamente
anterior = 1º micro-higher-high). Janela máx. 48 barras. `entry = close[k]`.
Guarda: `risk = entry − SL` deve ser `> 0.05·ATR` (senão NO-TRADE).

**2.4 Gatilho RECLAIM (comparador):** 1ª barra `k` após o low com `close[k] > EMA21[k]` E
`close[k] > close[k−1]` (janela 48). Mesma âncora/SL.

**2.5 Alvo e outcome:** `target = entry + 3·(entry − SL)`. Outcome **SL-FIRST barra-a-barra** no RAW
15M: perde se `low[m] ≤ SL` antes de `high[m] ≥ target`; ganha se target primeiro; OPEN/timeout se
nenhum em 480 barras (~5 dias). **Onde houver fill real do Cris (proxy), usar o fill real** (a
verdade intrabar que o 15M não resolve).

---

## 3. MÉTRICAS (reportadas por lado — MB3 e reclaim — em cada fundo forward)
- **hit-3R** (WIN / N), LOSS, OPEN.
- **streak** = máx. de losses consecutivos (restrição FN).
- **tempo-no-mercado** = mediana de barras até 3R.
- **R/ATR** por trade; marcar **tight-R (R/ATR < 1,65)** como *fill otimista* (o 15M não resolve a
  ordem intrabar SL-vs-alvo; estes contam com ceticismo, idealmente com fill real).
- **expectância líquida** com custo real (slippage/spread do Cris).
- Log por-fundo (data, low, SL, entry MB3, entry reclaim, R, outcome, barras).

---

## 4. VETOR DE FALHA DECLARADO (medir, não assumir)
**SUPPLY OVERHEAD IMEDIATO.** Para cada fundo forward, registar a **zona OB SUPPLY causal** (born_t ≤
entry) mais próxima ACIMA do low e a sua distância em ATR. Hipótese a testar: entradas com supply
imediato (~≤1 ATR acima) falham mais (compra-se contra resistência). A curadoria in-sample limpou
isto (não testado). Se o forward confirmar, o supply-gate vira refinamento — **mas só via novo prereg.**

---

## 5. NULL (declarado)
Por fundo forward: 500× entrada **aleatória** em `[low+1, low+48]`, mesmo SL/3R, SL-first → distribuição
null de hit-3R. MB3 e reclaim têm de **bater o null** (agregado e, sobretudo, nos ATR-altos, onde
in-sample o null era 10-38% vs MB3 100%). No agregado in-sample o null foi **76%** — logo o edge real
vive nos poucos sharp; o forward tem de o confirmar.

---

## 6. CRITÉRIO PASS / FAIL (congelado AGORA, antes de qualquer dado forward)
**N mínimo:** não julgar antes de **≥ 20 fundos A1 forward** (~1-2/semana → ~3-4 meses). Antes disso =
**INCONCLUSIVO**.

**PASS (MB3 validado como gatilho A1)** exige TODAS:
1. MB3 **hit-3R ≥ 50%** (excluindo/deflacionando os tight-R conforme fills reais).
2. MB3 **streak ≤ 5** (restrição FundedNext).
3. MB3 **bate o null q95** no agregado.
4. MB3 **≥ reclaim** no eixo primário (hit-3R **OU** tempo-no-mercado/convexidade). *(Emenda: em causal
   in-sample MB3 e reclaim EMPATAM; o "MB3 domina" era artefato de lookahead. Se o forward mostrar MB3
   claramente ≥ reclaim, tanto melhor; empate NÃO é FAIL.)*
5. **Expectância líquida positiva** com o custo real do Cris.

**FAIL** se qualquer: hit-3R < ~breakeven+margem (≈ ≤ 33%), **ou** streak > 5, **ou** não bate o null,
**ou** o reclaim domina MB3, **ou** expectância líquida ≤ 0.

**PARCIAL/refinar:** se PASS exceto pelo supply-overhead (i.e., o vetor de falha explica os losers) →
**novo prereg** com o supply-gate, novo forward.

---

## 7. PROTOCOLO FORWARD
- A partir de 2026-07-14, cada novo fundo A1 (identificado pela leitura do Cris / stack) é pontuado
  **MB3 vs reclaim lado-a-lado**, com as regras da §2, registando as métricas §3 + vetor §4.
- Sem alterar regras. Sem espreitar resultados para ajustar. Acumular até N≥20 e então aplicar §6.
- Árbitro final = as **ops live/proxy reais do Cris** (fills verdadeiros).

---

## 8. REFERÊNCIA IN-SAMPLE (o que foi desenhado — explicitamente NÃO validação)
**Números CAUSAIS honestos (versão APROVADA 2026-07-15, `a1_causal_entry.py` — timing fractal + SL
low-real, SEM lookahead):**
- **A1 MB3: 13/14 WIN** (único loser #1, R1,17A) · reclaim 11/14 → **MB3 ≥ reclaim**.
- **A2 MB3: 16/18 WIN** (losers #6, #13) · reclaim 15/18 → **MB3 ≥ reclaim**.
- Evolução honesta: `+8-lookahead` dava 14/14 e 17/18 (**inflado**) → só-fractal 11/14 e 14/18 →
  **+ SL low-real: 13/14 e 16/18** (o SL low-real arruma os tight-R varridos, mas **partiu o A2#6** ao
  subir o alvo — melhoria líquida +2 cada, não grátis; ver §2.2 e a EMENDA no topo).
- Diagnóstico `a1a2_loser_diagnosis.py`: **7/7 losers do fractal recuperavam ao 3R ignorando o SL** =
  região certa, SL apertado (a base da correção estrutural).
- Caveats mantidos: N pequeno = desenho; winners curados (0 losers verdadeiros no set); winner's-curse
  leve no parâmetro SL (afinado sobre o set); supply-overhead não testado. O juiz é a §6 sobre forward.

---

*Fim do prereg. Congelado 2026-07-14. Não editar as §1-§6 após esta data — refinamentos = novo doc.*
