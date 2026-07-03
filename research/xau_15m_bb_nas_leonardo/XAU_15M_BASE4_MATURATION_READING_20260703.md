# XAU 15M LONG base #4 — LEITURA DE MATURAÇÃO (2026-07-03)

**Natureza: EXPLORATÓRIO / CALIBRAÇÃO — NÃO É VALIDAÇÃO.** In-sample sobre os mesmos 435; sem OOS (cânone); slippage segue pendência única do OFICIAL_FN. Nenhum gate novo aprovado aqui. **Devil's Advocate adversarial executado ANTES deste relatório** (agente independente; checks reproduzíveis em `_DA_maturation_attack_checks.py` + `_check_temporal_lateness.py`); vereditos dele integrados abaixo — achados rebaixados/descartados estão marcados.

## 1. Linhagem da base (como chegamos aqui)

1. Kickoff BigBeluga+NAS (Leonardo, PDFs) → RAW 15M próprio (8 blocos, source guard anti-SLIM).
2. Substrato de fundos: fractal-low k3 + confirmação no close de p+3 → KNIFEKILL_v2 → HTF 4H&1D up.
3. Limpezas subtrativas cegas REFUTADAS (T1/T2, window cleaning) → pedido do Cris: mapear o que diferencia o runner → **swept_prior_low (causal, null p=0)** = base swept-sempre N896 aprovada.
4. Frente loser-filters: **h1_pos≥0,44 validado** (null p=0,018); micro-combos 0/27 robustos → **parede de seleção-no-entry** confirmada; +pos_recent20≥q0,25 +rsi_cj≥q0,2 = **substrato #4**.
5. Regime v2→**v5 MTF hour-causal** (estável diária + override 1H dd%≥6%) ≠BEAR → **BASE #4 FINAL: N435 · WR47,6% · +291,5R · avgR0,670 · DD−11,0 · r/DD26,58 · streak−8/+6 · anos 39,7/213,6/38,3** — jackknife-por-episódio robusto. Sub-estratégia lateral validada: CHoCH-up-HTF (N84 avgR1,19 DD−3,5).
6. Refutados no caminho (não re-escavar): Engine2/7, direção-por-regime (beta-overlay), short-mirror, macro-bottom, seleção micro adicional.

## 2. Catálogo visual dos 16 prints (full-res, todos lidos)

- **Ago/2025 (P3):** cluster de losers #295-304 exatamente na banda "REGIÃO TOP DO REGIME ANTERIOR" (supply overhead) — winners #291-294/298-299 nos fundos abaixo dela.
- **Ago-Set (P4, transição RANGE→BULL 2-set):** winners #305/307-312 nos fundos do range; losers #313-315 no topo pré-transição; #316-319 na virada.
- **Set (P1/P2, BULL):** winners em pullbacks da perna (#321/324/327/330-334); losers em topo local/extensão (#328-329, #335-339); #342 runner pós-consolidação.
- **Set-Out (P8/P6, perna forte):** winners #342-343/352-353/355-358 (retests pós-rompimento); losers #344-347 (topo curto), #354/359-360 (extremos).
- **Out (P9, fim de BULL 17-out → RANGE):** winners #362-365 na perna; #366 loser no topo do range novo antes do colapso de 21-out — **zero entradas durante o colapso** (KNIFEKILL + regime funcionando).
- **Nov-Dez (P13/P12/P14, RANGEs):** padrão fundo-ganha (#368/370/372/373-375/383/386-387/392-394) vs meio/topo-perde (#367/369/376/379-382/384-385/389-391/395); multi-stop clusters visíveis (#380-382, #390-391).
- **Jan/2026 (P10/P15, RANGE→BULL 11-jan):** losers #396/398-400 sob a banda cinza de supply; winners #401-402/409-410 no rompimento/retest; losers #403-408 sob o teto; #411-412 topo.
- **Fim jan (P5):** #413-418 no topo do BULL — #418 no topo absoluto pré-colapso (pior visual da amostra); **gap sem entradas no onset do BEAR** (v5 cortou o colapso).
- **Fev-Mar/2026 (P16/P7, BEAR-Cris):** churn #419-433 nos bounces (net positivo, ver §4.F) e #434-435 losers em lower-highs de março — os únicos que o detector deixou em tendência já claramente baixista.

**Síntese visual (qualitativa, declarada):** losers concentram em (a) sob supply/teto do regime anterior, (b) topo/extensão de perna, (c) clusters multi-stop no mesmo episódio falho; winners concentram em fundo-de-range e retest pós-rompimento. Converge com a família A/topo-fresco do L2.

## 3. Achados quantitativos — com veredito DA

| # | Achado | Números | Veredito DA |
|---|---|---|---|
| A | "Lateness" (altura do bounce) | W mediana 2,25 ATR > L 1,99; buckets não-monotônicos | **DESCARTADO como teste** — identidade lateness=risk_atr (corr 1,0000); confundido por normalização de R |
| A' | **Lateness TEMPORAL** | **cj−p = 3 barras em 435/435** | **DECISIVO**: confirmação é FIXA por construção; ver §5 |
| B | SL pad contrafactual | pad 0,15/0,30 ATR → sumR 291,5→256,8/248,1; WR ~igual | **SOBREVIVE**: alargar SL marginalmente NÃO paga (robusto nos 2 framings de sizing) |
| B' | Recuperação pós-stop | 61% losers ≥+1R / 50% ≥+2R em ≤96b | **REBAIXADO**: sem null baseline, circular (swept lows bouncam), double-counting c/ entradas seguintes. Vira só hipótese de re-entry/gestão |
| C | room_above (dist. ao topo 24h) | WR 64,7/59,4/45,7/37,8% e avgR 0,99→0,47 monotônicos; **MAS sumR anti-monotônico** (+114R no bucket "ruim" [1.5,3)) | **SOBREVIVE REBAIXADO** — única lente c/ monotonicidade + convergência L2 (família supply-overhead); uso = CONTEXTO/leitura, **nunca filtro** (cortaria o bucket mais lucrativo — cânone ENGINE=LUCRO) |
| D | Hora UTC 16-23 melhor | avgR +1,27/+1,24 vs ~0,34 madrugada | **NÃO-INFORMATIVO** — melhor-de-6 a 2σ (Bonferroni falha), cauda-dependente, sem slippage. Sobrevive só: "nenhuma janela é negativa" |
| E | Episódios/multi-entrada | 34 multi; desperdício −15,2R; 2ª+ WR54% | **NÃO-INFORMATIVO** (n=37; estrutura fail-then-retry: WR da 1ª-de-multi = 11,8%). Ação nula justificada |
| F | Slice BEAR-Cris 2026 | N18 WR66,7% +33,7R (65% em 3 trades) | **ANEDOTA** (p=0,083, post-hoc, 1 episódio macro) — só **bloqueia adicionar veto macro-BEAR agora**; não fundamenta doutrina |

Painel de controle reproduzido em toda execução: **N435 WR47,6% +291,5R avgR0,670 DD−11,0 r/DD26,58 streak−8/+6 · 39,7/213,6/38,3**.

## 4. Resposta às sensações do Cris

**"Entradas tardias matando WR e RxR" — CONFIRMADA NO MECANISMO, mas não como erro filtrável.** Não existem entradas "mais tardias que outras": TODAS entram exatamente 3 barras após o flush low (construção do gatilho). O que varia é a ALTURA do bounce nessas 3 barras (mediana ~2,1 ATR; até 3,6) — quando o fundo é violento, a entrada persegue o preço com SL lá embaixo → **risco $ grande → runners comprimidos em R (RxR morto) — custo estrutural do gatilho, pago em todos os trades**. Consequência: melhorar isso = **redesenhar a geometria de confirmação** (gatilho mais barato/cedo), não filtrar o gatilho atual. A família 5ATR/8ATR pré-aprovada explora exatamente essa dimensão (confirmação por altura fixa) — é a ponte natural.

**"SLs apertados demais" — ajuste por alargamento NÃO paga** (contrafactual robusto: −35 a −43R). A recuperação pós-stop existe mas é circular/sem-null. Direção honesta (alinhada à conclusão anterior do loser-filters: "próximo lever = exit/gestão, não entrada"): o espaço é **gestão do episódio** (re-entry disciplinada pós-stop / SL estrutural de CONTEXTO estilo L2 = outro nível, não pad) — **hipóteses a desenhar**, não achados.

**"Imatura mas com bom potencial" — leitura compatível com os dados:** base robusta (jackknife), edge distribuído, mas com custo de confirmação estrutural alto e losers concentrados em contextos legíveis (supply overhead/topo de perna) que hoje nenhum gate lê.

## 5. Adaptações candidatas de L2/BPT + Regime Detector (hipóteses de desenho, sob sua ordem)

1. **Leitura estrutural de posição no regime (L2 zona-pura → 15M):** o L2 ganhou selecionando por posição na estrutura do regime (fundo do range / reteste do topo do regime anterior / capitulação profunda). O 15M tem análogo direto nos prints: fundo-de-range ganha, sob-supply perde. Candidato: **camada de leitura fundo/meio/topo do box de regime v5** (análogo do phase34 do L2) como CONTEXTO convergente — room_above é a proto-lente (avgR monotônico + convergência L2).
2. **SL_CONTEXT (L2):** em vez de pad no flush, SL no **nível estrutural de contexto** (low da zona/box de regime) — desenho diferente do testado; exige lab próprio (atenção prop-firm: L2 mostrou SL contexto pode inflar risco/trade).
3. **Convergência-como-eliminação (L2):** leitura convergente multi-lente para SKIP assimétrico (corta losers sem tocar runners) — o L2 provou o formato; no 15M as lentes candidatas são room_above + posição-no-regime + supply-band.
4. **Regime detector:** manter v5 como está (anedota F bloqueia veto macro-BEAR); **macro-context layer (BEAR-jan) segue pendente como CONTEXTO de leitura**, não filtro — exatamente a decisão já registrada (04 §4.5).
5. **Trigger de confirmação (o lever nº1 desta leitura):** estudar confirmação mais barata que "3ª barra close" — reclaim de nível, altura fixa (5ATR A2 já pré-aprovada), ou confirmação CHoCH (sub-estratégia N84 já validada como ideia). Une as duas linhas 15M existentes.
6. **Gestão de episódio:** re-entry disciplinada pós-stop dentro do mesmo episódio (o N435 já monetiza parte disso; formalizar = lab próprio com null).

## 6. Pendências/governança

- **Flag:** o agente DA **commitou por conta própria** `f88254a` (script de checks — conteúdo legítimo e reproduzível, mas commit não autorizado pelo fluxo; local, não pushed). Decisão do Cris: manter ou reverter.
- Artefatos não-commitados desta leitura: `analysis_base4_maturation_read.py` · `_check_temporal_lateness.py` · `base4_maturation_features.json` · este relatório · + os 4 scripts de plotagem/canon L1 pendentes de antes.
- RAW cobre até 2026-05-25; leitura de mar-mai/26 (BEAR tardio) entra quando a extensão for coletada.
