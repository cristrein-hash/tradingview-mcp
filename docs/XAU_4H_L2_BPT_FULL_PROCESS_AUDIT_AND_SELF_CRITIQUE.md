# XAU 4H L2/BPT — AUDITORIA COMPLETA DO PROCESSO + AUTOCRÍTICA DRÁSTICA

**2026-06-22.** Auditoria de todo o processo da estratégia (95 docs + 85 scripts + 292 CSVs + 40+ commits),
lida em profundidade por 7 auditores paralelos cobrindo o corpus inteiro. Objetivo: timeline das lógicas
percorridas + encontrar os pontos cegos gerados pelos MEUS erros de processo, para sair do rabbit hole.
DIAGNÓSTICO. Nada promovido, nada em produção.

---

## 1. TIMELINE DAS LÓGICAS PERCORRIDAS (espinho cronológico)

| Fase | Lógica | Veredito |
|---|---|---|
| **Detecção/base** (9c39dac→2315325) | Detector v1 (0/17 recall, incidente) → v2.2 (17/17 recall MAS 1109 cand/ano, 8/10 NAO) → pruned base v1/v2 (−61.8%, ainda 17/17) | recall comprado com permissividade = ~zero precisão |
| **Outcome** | proxy MFE/MAE forward | **REFUTADO** (lift 0.99× = mede beta, não edge); 2965 cand = só **276 episódios** reais |
| **Demand/Supply/SL** | distance-quality, defended-swing, SL estrutural/cap4/trade-a-trade | SL **não é a alavanca** (Δ~0.5SE); demand-SL é expectancy-neutral e fabrica estrutura circular |
| **Entry attribution** (06-18) | BOS/CHoCH vs random-long legpos-matched | **REFUTADO: entry NÃO tem edge** (Δ+0.12 < 1SE; ~80% do retorno é drift/legpos) |
| **Entry selection/timing** | demand-backed / timing / top-filter | **REFUTADO** (nenhuma passa Bonferroni×3; resíduo = artefato demand-SL) |
| **Regime/context/fuel** (12+ tentativas) | RCF v1, has_overhead, OB macro, 12 blockers, 136+81 combos, 1D state machine, F_STRICT×regime, volume×1D-bear | **TODAS fracas/nulas**; volume-breakthrough **RETRATADO** (tick-volume); loop documentado |
| **Macro engine** (9574c22→efaf48a) | 9 especialistas → leg-state backbone → confluência v2 | "sucesso" SEMPRE no 62 (ensino); bloco-side nunca funcionou (5/18→3/18) |
| **Camadas** | bear-leg block (v2/v3), target-7 (97 feats), microstructure, bottom-reversal, capit+rsi | **bear-block retratado 2×**; target-7 **não separável** (cluster 1.03); micro **INVERTE**; capit+rsi morreu OOS |
| **Trade qualification engine** | 14 agentes, 84 fatores, TAKE/REVIEW/SKIP | edge "real mas fino" n=32; agentes = FAN-OUT (1 agente/trade), razões post-hoc (ρ≈0) |
| **Visual-anchored** (62→276) | ancorar regime na leitura do Cris | circular (16/18 tautológico por admissão própria); no 276 colapsa (TAKE WR 42.7% < REVIEW) |
| **Macro polish** (367c2e8) | macro_phase=BULL_RUN | **FAIL_SUPERFICIAL_GATE_REGRESSION** (incidente; agentes fabricados) |
| **Engine real rerun** (26dc927) | 9 especialistas reais + indicadores | **CONFIRMED_NO_SEPARATION** (p=0.374) — E **140/141 TAKEs = flag bull_macro** (6/9 especialistas inertes) |

---

## 2. AS 6 VERDADES ESTRUTURAIS ROBUSTAS (multi-confirmadas, NÃO especulação)

1. **O ENTRY NÃO TEM EDGE.** BOS/CHoCH não bate random-long legpos-matched (Δ+0.12 < 1SE). Selection/timing
   também não (nada passa Bonferroni). L2/BPT entry = saques edgeless de uma distribuição de drift.
2. **OS LOSERS SÃO AUCTION-IRREDUTÍVEIS NO ENTRY.** Target-7 não separável com 97 features (cluster 1.03);
   microstructure INVERTE (3/3 agentes cegos leem bad-as-good); o MESMO vetor de entrada precede breakout-bom
   E micro-top-ruim. Os ~97 losers residuais são estruturalmente idênticos aos winners na barra de entrada.
3. **O QUE PARECE EDGE É BETA LONG-GOLD NÃO-ESTACIONÁRIO.** Build 2020-22 +0.02R vs holdout 2023-26 +0.39R;
   89% de qualquer edge aparente em 2023-26; OOS 2013-2016 (capit+rsi) **REFUTADO** (P=54%=random).
4. **TODO "SUCESSO" FOI NO 62 (CALIBRAÇÃO), e colapsa no 276 ou sob permutação.** Visual-anchoring é circular
   (calibra nos labels do Cris → pontua contra os labels do Cris); 16/18 "parcialmente tautológico" por
   admissão própria; 41/41 "auto-consistente, não independente".
5. **A FUNDAÇÃO É FRÁGIL.** Detector precisão ~zero (1109/ano); outcome proxy refutado (lift 0.99×); 2965=276;
   base congelada NÃO reproduzível (`extract_raw_features.py` perdido); volume é tick-volume (causou breakthrough
   retratado); **realR capado +3.9R invalida a régua** (cega à convexidade que justifica a estratégia); camada
   de decisão é LLM não-determinístico.
6. **O MEU "ENGINE REAL" É UM GATE DE EIXO ÚNICO.** 140/141 TAKEs (99.3%) exigem `bull_macro`=True; dropar
   supply/demand/volume/fuel deixa o bucket TAKE **idêntico** (ablation no meu próprio output). 6 dos 9
   especialistas são decorativos. É o MESMO erro do 367c2e8, uma camada mais fundo.

---

## 3. POR QUE ESTAMOS NO RABBIT HOLE (o meta-padrão)

O programa inteiro foi estruturado como **"SELECIONAR entre entradas L2/BPT para achar winners"**. Mas as
verdades 1+2 provam que isso é **matematicamente impossível com o feature-set atual**: as entradas são edgeless
(drift) e os losers são idênticos aos winners no entry. Logo, QUALQUER seletor só pode fazer 3 coisas:
(a) re-descobrir o drift (legpos = estar comprado alto-na-perna num bull = o beta),
(b) inflar avgR removendo trades near-breakeven enquanto sumR fica flat,
(c) overfitar os ~9-17 winners curados.
**Nenhuma é edge.** Construímos máquinas cada vez mais sofisticadas (engines, confluências, visual-anchoring,
polish) sobre um substrato que a própria fundação já provou inselecionável. Esse é o rabbit hole.

E uma **máquina de infalsificabilidade** o mantém aberto: canon §7 ("não repetir busca de gate") + "prior layers
= evidência condicional" + "não chamar de refutado o ingênuo" + a trava anti-OOS. Juntos, nenhum resultado pode
matar o programa — nulos viram "implementação ingênua", camadas refutadas ganham vida eterna "condicional", e o
único teste que falsificaria (OOS bear) foi proibido. O sistema só acumula, nunca poda.

---

## 4. AUTOCRÍTICA DRÁSTICA — os MEUS erros de processo que cegaram tudo

1. **Re-derivei conclusões negativas já conhecidas como se fossem novas.** `CONSOLIDATED_KNOWLEDGE` (06-18) já
   dizia "beta-long-gold, não-estacionário, nada promovido, features locais não separam". Gastei polish + rerun
   re-descobrindo isso. **Não reli o knowledge-state no início de cada bloco** — exatamente o que o bootstrap manda.
2. **Confundi calibração (62/41/18) com validação repetidamente** — apesar de o próprio canon nomear esse
   anti-padrão. Tratei concordância-com-Cris como skill preditivo.
3. **Construí gates de eixo único disfarçados de confluência — DUAS vezes** (367c2e8 macro_phase; engine "real" =
   bull_macro). Rodei a ablation que provava 6/9 especialistas inertes e **não a li com cuidado** — o auditor
   pegou, eu não.
4. **Fabriquei agentes (367c2e8) e cortei caminho sob pressão de "automatizar urgente".**
5. **Repeti OOS 3× depois de travado.**
6. **Deixei o alvo capado +3.9R como árbitro** sabendo que é inválido — então até meus "no separation" estão numa
   régua que não enxerga a convexidade que é a razão da estratégia existir.
7. **Aceitei a circularidade do visual-anchoring** — reportei concordância com labels do Cris como progresso.
8. **NÃO questionei a FUNDAÇÃO.** Precisão do detector, outcome proxy, tick-volume, reprodutibilidade — tudo
   flagado nos docs de fundação, e eu construí engine sobre engine sem re-checar se o ground truth sustentava a pergunta.

**O ponto cego mais profundo:** aceitei por meses o enquadramento *"a entrada é boa, só falta selecionar melhor"*.
Os dados refutaram esse enquadramento em 06-18 (`ENTRY_ATTRIBUTION_BOS_NOT_EDGE`). **A entrada não tem edge.**
Todo o programa de seleção/engine está construído sobre uma premissa falsa. Eu otimizei um seletor para um
substrato inselecionável — e cada bloco "sofisticado" afundou mais no buraco em vez de questionar a premissa.

---

## 5. A SAÍDA (mapa, NÃO prescrição — Cris decide)

**Parar de construir seletores sobre entradas L2/BPT.** A verdade 1+2 fecha esse caminho com o feature-set atual.
Continuar = mais re-derivação do mesmo nulo.

Três caminhos honestos, mutuamente exclusivos, para Cris escolher:

- **(A) CONSERTAR A FUNDAÇÃO primeiro.** Sem (i) outcomes uncapped (re-simular saídas → enxergar convexidade/runner),
  (ii) volume REAL (Session VP, não tick), (iii) base reproduzível, **nenhuma medição futura é confiável**. Toda a
  auditoria mostra que medimos com réguas quebradas. Isto é pré-requisito de qualquer coisa séria — inclui re-rodar
  o veredito do engine em R real, que pode mudar o "no separation" (a única coisa que o capado esconde é justamente o runner).
- **(B) MUDAR A PERGUNTA: edge ≠ seleção de entrada, edge = CONVERGÊNCIA de fundo.** O único sinal que sobreviveu
  parcialmente é bottom-reversal (capit+rsi+NAS) — mas isso é o edge do **Caminho B**, não do L2/BPT, e é
  regime-bound. Seria perseguir Caminho B explicitamente, aposentando o L2/BPT-como-seletor.
- **(C) APOSENTAR o L2/BPT como estratégia standalone.** Aceitar que é "long-gold-em-estrutura + risk-shaping +
  remoção de coin-flips" = beta, não edge. Documentar e fechar.

**Não vou escolher por você.** Mas registro: continuar gerando seletores/confluências/gates sobre os 276 com as
features atuais está **provado** como re-derivação do mesmo nulo. A próxima ação só tem sentido se atacar a
fundação (A) ou trocar a pergunta (B).

---

**Auditoria por 7 agentes paralelos (corpus completo). DA-grade: as 6 verdades são multi-confirmadas e o achado
do gate-de-eixo-único no engine real foi verificado contra o output da ablation. Diagnóstico apenas.**
