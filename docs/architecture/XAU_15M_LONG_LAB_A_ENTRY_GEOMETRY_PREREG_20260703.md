# LAB A — ENTRY GEOMETRY · PRÉ-REGISTRO (2026-07-03, ANTES de qualquer cálculo)

**Bloco:** XAU_15M_LONG_LAB_A_ENTRY_GEOMETRY · research-only / prereg-first / multi-agent / LONG-only · sem produção/Telegram/runtime/chart/plot/RAW-write.

## 1. Strategy scope
XAU 15M LONG only · swept-runner base #4 · N435 · detector v5 retido · OFICIAL_FN (cost gate passed) mas **NOT production** · **SB $0,80 obrigatório em toda avaliação** · no SHORT · Labs B/C/D fora daqui (ideias de contexto/supply/SL/re-entry = ponte registrada, não executada).

## 2. Source/data mapping
- **Input:** os 435 sinais do engine aprovado real (`engine_substrate4_v5_hourcausal.py` via exec; seleção `cand[v5h≠BEAR]`), como nos Labs E/leitura.
- **Fields por sinal:** `p` (bar do flush low) · `cj = p+3` (bar de confirmação; entry0 = close@cj) · `entry_time = cj_t` · `sl = min(low p..cj) − 0,1·ATR` · `risk_usd = entry0 − sl` · `R` (let-run realizado) · `yr` · regime v5h · série completa do bloco (`PRIMK[block]["series"]`: t/o?/h/l/c/atr/rsi por barra) → permite simular execuções pós-sinal e re-executar `letrun` com (fill, sl) alternativos.
- **Lineage:** RAW gz HD → build_causal_primitives → primitives (source guard ativo; **zero SLIM**). Derived usados: entry_candidates_htf.jsonl (features dos candidatos, via engine). Episode id: cluster ≤8 barras (mesma definição da leitura de maturação).

## 3. Baseline reproduction (fail-loud)
N435 · WR47,6% · **+291,5R bruto** · **+233,6R líquido-SB** · DD−11,0 / r/DD 26,58 (bruto) e DD−14,2 / r/DD 16,4 (SB) · streak−8 · anos 39,7/213,6/38,3. Se não bater → PARAR, documentar, não interpretar.

## 4. Structural hypothesis
A confirmação atual custa **3 barras fixas + altura variável do bounce (mediana ~2,1 ATR)** → risco $ alto → compressão de R. Hipótese: existem geometrias **causais de execução pós-sinal** que reduzem preço de entrada/risk_usd sem destruir runners, robustez por episódio e painel líquido-SB.

## 5. Candidate families (espaço FIXADO antes do cálculo)

**Decisão de causalidade declarada ANTES:** famílias que disparam ANTES de cj (A1 earlier-confirmation, A3 altura-fixa pré-cj, A4 CHoCH-como-gatilho) **exigem re-scan completo do builder de candidatos** (avaliá-las só nos 435 episódios que confirmaram k3 = seleção sobre o futuro = look-ahead). O builder re-scan está FORA do escopo desta rodada → **A1/A3/A4 = BLOCKED_BY_SOURCE_MAPPING nesta rodada** (ponte registrada: A3 já vive na linha 5ATR/8ATR pré-aprovada; A1/A4 = rodada futura com builder). *Não é bloqueio de todas as famílias — o núcleo avaliável segue abaixo.*

**Núcleo AVALIÁVEL (pareado nos MESMOS 435 sinais; 100% causal — o sinal e todos os gates ficam intactos; só a EXECUÇÃO pós-sinal muda):**
- **A5/A2 — Execução limit/retest pós-sinal:** no close de cj (sinal completo), colocar limit abaixo de entry0; fill se low de alguma barra ≤ limit dentro de W barras (fill AO PREÇO do limit; sem fill = MISS contabilizado). SL inalterado (flush−0,1ATR) → risk_usd = fill − sl (menor). Exit = letrun a partir do bar de fill. Variantes pré-fixadas:
  - Depth δ = **0,3 · 0,5 · 0,8 ATR** abaixo de entry0 × validade W = **8 · 16 barras** (6 variantes)
  - Nível estrutural: limit no **midpoint do risco** (entry0 − 0,5·(entry0−sl)) com W=16 (1 variante)
  - Nível estrutural: limit no **high do bar p** (topo do bar do flush; se ≥ entry0, variante não-aplicável nesse trade → fica market) com W=16 (1 variante)
- **A6 — Propostas dos agentes:** SOMENTE dentro do espaço de execução pós-sinal causal, com definição EXATA (nível/validade/fill rule); máx. 4 aceitas; propostas de contexto/supply/SL/re-entry → ponte B/C/D (registrar, não executar).

## 6. Nulls (obrigatórios)
- Baseline #4 (market@close cj) bruto e SB-net.
- **Delay-null:** market@close de cj+2 e cj+4 (separa "ganho por profundidade" de "efeito de atraso puro").
- **Fill-rate null:** para a melhor variante, comparar com atribuição aleatória de misses na mesma taxa (500 reps) — o ganho deve vir de ONDE o limit enche, não de "menos trades".
- Jackknife por EPISÓDIO (leave-one-block) na melhor variante.
- Sem best-of-N pós-hoc: TODAS as variantes pré-registradas reportadas.

## 7. Metrics (por variante)
N sinais (435 fixo) · fills / **miss rate** · WR (sobre fills) · sumR bruto · **sumR SB-net** (custo $0,80/RT ÷ risk_usd do fill) · avgR · DD · r/DD · anos · streak · risk_usd mediana/quartis · **runners (R≥3) preservados vs base** (1ª classe) · R dos misses na base (o que se perdeu ao não encher) · sumR-com-miss=0 comparável ao baseline.

## 8. Sanity checks
Zero future leak (fill só com barras > cj; fill ao preço do limit; barra que abre abaixo do limit → fill no OPEN da barra, não no limit — anti-otimismo de gap) · entry_time causal · SL/exit policy inalterados salvo a definição da variante · mudanças de N explicadas (miss) · nenhum filtro escondido · custo SB sempre reportado · monotonicidade do custo · no SHORT.

## 9. Forbidden interpretations
Não escolher por sumR isolado · não aceitar variante que melhora R explodindo risk_usd/DD · **não assumir fill grátis** (miss modelado; gap-through = fill no open) · não concluir produção · não concluir SHORT · não substituir Labs B/C/D · WR maior por risco menor ≠ edge por si.

## 10. Acceptance criteria
Uma variante só avança se: melhora painel **líquido-SB** OU reduz risk_usd sem destruir runners · robusta por ano e jackknife-episódio · não depende de poucos trades (drop-top3 reportado) · DA não rebaixa · fill causal e conservador. Caso nenhuma: veredito honesto (FAILS / NO_CLEAR_WINNER) sem resgate pós-hoc.
