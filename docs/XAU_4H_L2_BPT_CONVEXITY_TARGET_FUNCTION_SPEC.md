# XAU 4H L2/BPT — FUNÇÃO OBJETIVO DE CONVEXIDADE (spec)

**2026-06-22.** Régua econômica correta para julgar entrada/engine/automação, depois de provar que o realR capado
(+3.9R) apagava ~78% da edge. WR continua relevante, mas NÃO é árbitro único. DIAGNÓSTICO; nada promovido.

## 0. Por que esta spec existe
Mesma entrada (276 episódios), 3 exits: capado **+84.2R** · let-run static **+241.2R** · V-stair trailing
**+207.7R** (corrigido após bug do DA). Com custo 0.35R/trade: let-run **+144.6R**, V-stair **+111.1R**.
**Headline conservador = let-run +241R (custado +144R) ≈ 1.7–2.9× o capado +84R.** O nó Outcome/Exit era o
gargalo (Theory of Constraints): media hit-rate quando a estratégia vive de convexidade. Destruição honesta da
edge pelo cap ≈ +60R a +157R recuperáveis (≈45–65%), não os 78% inicialmente reportados (que dependiam do V-stair bugado).

## 1. A estratégia é um HARVESTER DE CONVEXIDADE, não um seletor de entradas
Perfil empírico: 168/276 não correm (MFE<2R), mas 72 são runners (MFE≥5R) e 30 são monstros (MFE≥10R, até +30R).
WR baixo é **feature**, não bug: poucos runners enormes pagam muitos losers pequenos. **O alvo econômico = capturar
o tail direito**, não acertar mais vezes.

## 2. Função objetivo (ranqueamento de candidatos de automação)
Métrica primária e secundárias, nesta ordem causal:

1. **Convexity capture (PRIMÁRIA)** — `sumR_realized` sob exit convexo (V-stair/let-run), UNCAPPED, por episódio.
   É o que paga a conta. Reportar sempre uncapped + por sub-janela P1/P2 (isolar beta 2023-26).
2. **Runner preservation** — fração dos 72 runners / 30 monstros preservada (não cortada por gate/SL). Cortar 1
   monstro (+15..30R) destrói mais que muitos losers evitados.
3. **Expectancy uncapped** = média de R realizado por episódio (não WR). Alvo prop-firm: positivo e dominado pelo tail.
4. **MAE-before-MFE / stop_before_2R** — qualidade de risco: quão fundo o trade vai contra antes de correr; quantos
   stopam antes de +2R. Lever de SL/timing, eixo próprio.
5. **maxDD e losing streak (RESTRIÇÃO, não objetivo)** — FundedNext streak ≤5, DD bounded. Uma estratégia convexa
   tem streaks longos de losers pequenos por design → exige sizing/gestão, não veto de entrada.
6. **WR capado (CONTEXTO, não árbitro)** — manter visível como sanity, NUNCA como critério de promoção. WR baixo
   com tail gordo = saudável.
7. **Frequência/ano** — convexidade exige amostragem suficiente do tail; n baixo demais = não captura o tail.

## 3. Como NÃO usar (anti-padrões provados)
- NÃO ranquear por WR/PF sobre R capado (apaga o tail — a coisa toda).
- NÃO cortar runners para subir WR (o gate destrói convexidade — bear-leg block retratado 2×).
- NÃO confundir convexidade-beta com alpha de entrada: o random-long capta o mesmo runner_freq (26%) — a convexidade
  é do MERCADO, não do trigger L2/BPT. Logo, "melhorar a seleção de entrada" NÃO é a alavanca.

## 4. Onde mora a edge (T6, classificação por episódio)
CONVEXITY_ALPHA 48 · EXIT_MANAGEMENT_EDGE 25 · RISK_SHAPING_EDGE 24 · BETA_ONLY 11 · NO_EDGE 168. A edge operável
está no **EXIT/risco** (capturar a convexidade-beta), não na entrada nem no engine de seleção.

## 5. Implicação para a automação
O objeto a automatizar **não é um seletor de entradas** — é um **harvester**: (a) entrada barata que põe o capital
long no contexto certo, (b) exit convexo (V-stair/let-run) que deixa o runner correr, (c) gestão de regime/capital
para sobreviver aos períodos onde long perde. **Ressalva honesta (DA a8122f3) sobre a entrada:** L2/BPT NÃO bate
random-long context-matched (26.1% vs 25.5%, p=0.42) MAS bate random-long GLOBAL (+4.2pp) — ou seja a entrada
não tem alpha de TRIGGER, mas concentra em REGIMES de maior convexidade (propriedade de timing/regime, ainda beta).
**O engine NÃO demonstrou valor de capital-preservation** — testado: ENGINE_SKIP teria rendido MAIS que ENGINE_TAKE
(SKIP per-trade > TAKE em let-run e V-stair), então o engine é anti-seletivo, não preservador. NÃO atribuir ao
engine um papel de salvação não demonstrado. Reorientação: parar de buscar separação winner/loser na entrada;
medir e maximizar captura de convexidade no exit. Se um gate de regime ajuda em capital-preservation é **questão
em aberto a testar**, não conclusão.

## 6. Limitações declaradas
- V-stair +390R é OTIMISTA (fills intrabar perfeitos, sem slippage/custo). let-run +241R é o piso conservador;
  ambos ≫ capado +84R — a ordem de grandeza (cap destruiu a maioria) é robusta à política de exit.
- Convexidade-beta é NÃO-ESTACIONÁRIA (clusters 2020 COVID, 2023-03, 2024-25); sizing tem que sobreviver aos vazios.
- Sem custo/slippage modelado ainda; próximo bloco deve modelar antes de qualquer número de promoção.
