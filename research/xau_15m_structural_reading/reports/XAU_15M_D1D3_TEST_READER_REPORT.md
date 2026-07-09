# TESTE MÍNIMO D1-D3 — LEITURA DO READER (2026-07-09)

> **STATUS (Cris 2026-07-09):** `PARTIAL_READING_NEEDS_EDITS` (edits aplicados) ·
> `D2_CONFIRMED_AS_ANTI_TOP_BUY_SIGNATURE` · `D1_OPERATIONALIZATION_FAILED` ·
> `NO_STRATEGY_VALIDATED` · ~~`VISUAL_REVIEW_REQUIRED_BEFORE_ROUND_2`~~ →
> **`VISUAL_REVIEW_DONE_BY_CRIS_20260709` (3 prints, 9 episódios plotados em retângulos
> proporcionais)**.

## CONCLUSÃO VISUAL (Cris, 3 prints, 2026-07-09) — vinculante
- **`D2_CONFIRMED_VISUALLY_AS_ANTI_TOP_BUY_VETO`** — C4 ("recuo pequeno dentro de topo — compra
  cara"), C6 ("última tentativa de comprar força exausta"), C5+B4 (mesmo erro no mesmo dia: pausa
  alta ≠ demanda). pos384>0,70 captura assinatura legítima de erro. **É VETO contextual, NUNCA
  estratégia isolada.** B4 = "SKIP automático por leitura estrutural, sem indicador".
- **`D1_MUST_BE_REWRITTEN_HTF_LEVEL_PLUS_STRUCTURE_ABOVE`** — "D1 medindo renovações de low é pobre
  demais: olha para baixo, mas o que decide está ACIMA e no contexto maior." Separadores reais:
  (1) nível HTF / bottom do regime anterior; (2) profundidade real da queda no contexto 1D/4H;
  (3) falhas de bounce anteriores; (4) estrutura acima ainda dominando ou finalmente quebrando.
- **`B1_B2_B3_VS_A6_IS_THE_KEY_CONTRAST_SET`** — B1/B2 = bounces com perna viva; B3 = flush
  intermédio (faltava nível HTF final — seguiram-se ~600 pontos de queda); A6 = único candidato a
  TAKE *se* no bottom HTF correto. Caveat do reader: é n=1 par/perna — o conjunto de contraste
  operacional = 12 BEAR-reversal + 3 INVALIDO, TODOS no mesmo bear 2026 ⇒ calibração, nunca validação.
- **Definição do Cris (canónica): "Fundo válido = o ponto onde uma perna relevante terminou dentro
  de uma região estrutural correta."** Sem contexto superior, o sistema alterna entre marcar regiões
  demais e entrar tarde/no topo.
- **Vereditos por episódio (Cris):** C4 SKIP · C6 SKIP · B4 SKIP · B1 SKIP · B2 SKIP ·
  B3 SKIP/REVIEW (nunca TAKE) · A6 TAKE-candidato só se no bottom HTF · C3 fora (gestão).
- **Próximo medidor mínimo (a preregar, SÓ com ordem):** `HTF_depth_to_prior_regime_bottom` ·
  `distance_to_prior_regime_bottom` · `failed_bounce_count_above` · `lower_high_pressure_above` —
  medir se separam B1/B2/B3 de A6 (e dos 12 BEAR-reversal). **Sem entry. Sem backtest.**
- **`NO_ENTRY_BACKTEST_UNTIL_CONTRAST_OPERATIONALIZED`**.
> Leitura do Cris: D2/pos384>0,70 = assinatura real de compra-de-topo (preservar como leitura,
> NUNCA transformar em estratégia isolada); "perna-mãe terminou?" ainda não operacionalizado —
> vem de lower-highs/reclaims falhados/estrutura acima/nível HTF/profundidade 1D. Rodada 2 SÓ
> após revisão visual dele (N≥6 episódios críticos: B4+C1-C6 marcados por D2 · B1/B2 traps onde
> D1 falhou · par B3 vs A6).

> Prereg v1.1 executado por ordem do Cris. Script `d1d3_minimal_test.py` (MEDIDOR puro, contínuo,
> sha do cache verificado) · tabela em `results/d1d3_minimal_test_result.json` · null
> `d1d3_null_audit.py`. Este report = leitura do READER sobre os números; **o caminho é decisão do
> CRIS**. Amostra = calibração outcome-contaminada (declarado); nada aqui valida estratégia.

## Resultado em 1 linha
**O definition-freeze check fez o trabalho dele: D2 (proporcionalidade) CONFIRMOU; D1 (renovação de
lows) provou-se a OPERACIONALIZAÇÃO ERRADA da pergunta "a perna-mãe terminou?"; D3 fraco sozinho.
Referência informativa (≥7/10 e ≤2/10) NÃO atingida: leitura honesta = 5-6/10 negativos marcados,
0 winners atingidos.**

## O que CONFIRMOU — D2 proporcionalidade (a assinatura anti-compra-de-topo)
Leitura RASO-NO-ALTO (devolução pequena vs range + candidato no alto do range):
| ep | ratio | pos384 | grupo |
|---|---|---|---|
| B4 | 0,24 | 0,83 | negativo ✓ |
| C1 | 0,27 | 0,87 | negativo ✓ |
| C2 | 0,26 | 0,91 | negativo ✓ |
| C4 | 0,36 | 0,83 | negativo ✓ |
| C5 | 0,25 | 0,95 | negativo ✓ |
| C6 | 0,53 | 0,73 | negativo (borderline) |
**0 winners** têm esta assinatura (winners: ratio 0,47-1,0; pos384 0,0-0,54). Null episódico exato
(hipergeométrico): **P=0,0163** (core 5) / **P=0,0054** (com C6). C3 NÃO marcado — **exatamente como
pré-declarado** (loser de GESTÃO em fim-de-perna, não de entrada; a previsão do prereg acertou).
**Precisão do DA (edits 3/4):** a cláusula PRÉ-REGISTADA "pos384>0,7" SOZINHA marca
{B4,C1,C2,C4,C5,C6} = **6 negativos, 0 winners, P=0,0054** — gap robusto (max winner 0,54/A5 vs min
marcado 0,73/C6 = 0,19). O "ratio≤0,40" foi descrição PÓS-HOC minha, redundante e conservadora (só
despromovia C6); **pos384 é o eixo carregador**; a borda do ratio é frágil (A5 0,47 vs C6 0,53 =
margem 0,06). Caveat inline: os P são DESCRITIVOS (amostra hand-picked outcome-contaminada, ~3
famílias de leitura ⇒ P efetivo ~0,02-0,05 core / <0,03 preregistado) — nunca evidência.

## O que FALHOU — e é o achado mais valioso
**D1 (renovação de lows) não mede "a perna-mãe terminou?":**
- **B1/B2 (os teus bounce-traps de março) saem INVERTIDOS**: last_new_low 195/307 barras, zero
  renovações — D1 lê "pausado/terminado" quando a perna estava VIVA. A perna viva lê-se pela
  ESTRUTURA ACIMA (lower-highs, reclaims falhados) — que D1 não olha; os dossiês (B1: reclaim em 2
  barras e era o meio da cachoeira) já o diziam.
- **B3 vs A6 = indistinguíveis nas 3 leituras** (B3: last_nl 3, renov 16, ratio 1,0, D3=9 · A6:
  last_nl 0, renov 27, ratio 1,0, D3=9). São a MESMA perna bear com 7 dias de diferença — B3 é o
  flush penúltimo (inválido, teu), A6 o terminal (fundo real, teu). No instante, nenhuma leitura
  local 15M os separa. O separador é o que a TUA régua 4H sempre disse: **capitulação verdadeira =
  reteste profundo do bottom do regime/range ANTERIOR** (contexto de nível HTF) + profundidade vs
  EMA-1D (o filtro capitulation VIVO) — nenhum dos dois estava em D1-D3.
- D3 (bounces): winners de capitulação têm 5-9 bounces como os traps; A5 (winner) tem 7. Sozinho não
  separa; pode servir como agravante DENTRO de perna viva, nunca como leitura própria.

## Desvios vs expectativas pré-declaradas (episódio a episódio, sem ajuste)
- Esperado "B1-B3 com perna VIVA": B3 sim; **B1/B2 NÃO** (inversão do D1 — falha da operacionalização,
  não do conceito).
- Esperado "B4 ambíguo": saiu LIMPO como raso-no-alto (melhor que o esperado).
- Esperado "C3 falha a separação": **CONFIRMADO** ✓.
- Esperado "A4/A7 ambíguos": A4 ratio 0,64 (aceitável), A7 perfil capitulação puro — sem dano.

## O que isto significa (leitura, não decisão)
1. **A assinatura anti-A-BULL existe e é medível**: dip raso no alto (ratio baixo + pos384 alto)
   marca 5-6/10 negativos sem tocar UM winner. É o candidato mais forte a evidência da Camada 2.
2. **"A perna-mãe terminou?" precisa de outra operacionalização**: estrutura ACIMA (lower-highs /
   reclaims falhados / aceitação), não renovação de lows. É leitura de forma, não de mínimos.
3. **Capitulação terminal vs flush intermédio não se lê COM ESTAS 3 OPERACIONALIZAÇÕES** (edit 5 do
   DA: não provado que "não se lê no 15M local" em geral): candidato natural = nível HTF (bottom do
   regime anterior — a tua régua dos 35 prints) e/ou profundidade 1D (filtro capitulation). Já
   temos ambos como camadas vivas; estavam OUT-OF-SCOPE deste prereg.
4. C3 confirma o padrão nº 9: gestão/alvo em fim-de-perna é dial próprio, fora da leitura de região.

## Pendências e desvios declarados (edits 1/2/6 do DA)
- **Desvio de prereg (passo 1)**: a reprodução dos números dos dossiês (profundidades,
  reclaim-barras) está INCOMPLETA — o script emite pos96/pos384 mas não compara contra os valores
  citados; pendência aberta.
- **Convenção de instante corrigida**: a marca referencia a barra retrospetiva do GT (bisect inclui
  a barra que abre na marca; close conhecido em marca+15m) — reconstrução causal-no-instante,
  irrelevante em janelas de 384 barras, MAS relevante para B3/A6-A8 cujo novo-low é NA barra da
  marca; declarado.
- **A cláusula "e/ou D3≥1" do expected-result era VÁCUA** (satisfeita por 10/10 winners e 9/10
  negativos) — lição para o próximo prereg; B1/B2 foram declarados como falha do D1 mesmo podendo
  ser reclamados por essa cláusula (leitura anti-conveniente mantida).

## Caminho (ordem correta — edit 7 do DA)
**PRÉ-CONDIÇÃO OBRIGATÓRIA: revisão visual TUA de N≥6 episódios** (passo 5 do prereg — é BLOCKER,
não opção). Só depois: (a) rodada 2 com novo prereg curto (D1 re-operacionalizado pela estrutura
ACIMA + nível HTF como leitura — nos MESMOS 20 seria classifier-drift; exigirá episódios virgens ou
declaração explícita de calibração), ou (c) mais dossiês/episódios virgens blind primeiro.

## Confirmação negativa
Sem entry · sem backtest · sem indicadores · sem cortes automáticos (as descrições numéricas acima
são LEITURA do reader sobre a tabela contínua, não gates) · medidor não arbitrou · GT desta amostra
continua queimado para seleção.
