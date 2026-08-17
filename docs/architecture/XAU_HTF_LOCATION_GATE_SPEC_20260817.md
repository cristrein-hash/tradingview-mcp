# XAU — HTF LOCATION GATE (spec, Cris 2026-08-17)

> Fix da **cegueira de localização** medida no dia 17/08: o sistema lê estrutura LOCAL 15M (sweep/reclaim/rejeição)
> sem ancorar à LOCALIZAÇÃO HTF → shortou o local-top de uma perna que subia (grupo → stop a 4427) e comprou
> reclaims altos-no-ar (chop). Aplica-se ao **motor reclaim (live)** e ao **lab SHORT**. Fonte das zonas = leitura
> canónica de OB (`contextual_read.py`), nunca inventada. Forward = árbitro.

## Evidência medida (17/08, auditada — não asserção)
Cluster de demanda HTF real (leitura canónica): **1H OB DEM 4377,2-4394,4 · 15M OB DEM 4377,2-4385,3 ·
1H/15M Smart Money 4367-4386 · HTF Power 4379,1-4418,8 · abertura semana 4379,15 · abertura dia 4370,19**
(4H OB DEM maior 4311-4333). Cada reclaim do dia vs este cluster:
- **4381 (reclaim genuíno 13:00) → DENTRO, no FUNDO do cluster** → bounçou a 4427 (o reclaim que interessava).
- 4379,9 DENTRO mas **LOSS** (SL 4374 curto) · 4389,9 DENTRO survived (SL 4367 largo) · 4390,9 DENTRO mas **LOSS** (SL 4388, risco 2,7pt).
- 4395,8-4398,3 no **topo/acima** → 3 LOSS · 4400,9 · 4412,4 **acima** (POC/supply, chase).

**Conclusão medida:** a localização SOZINHA não separa (vários reclaims caíram DENTRO da demanda e perderam).
O que separou = **posição-na-zona (fundo vs topo) + SL abaixo de TODO o cluster** (winners SL 4367 = abaixo da zona;
losers SL curto dentro da zona = stopados pelo chop na própria demanda). = a leitura do Cris, provada.

## O gate = 3 componentes (localização define ONDE; posição+SL definem SE trabalha)

### 1) LOCALIZAÇÃO HTF (o set AMPLO — Cris 2026-08-17)
O candidato tem de estar **num cluster HTF**, não numa zona única. Set:
- **OB Detector DEM/SUP em 1H, 4H, 1D** (não só 4H/1D — 1H conta).
- **FVG** (fair value gap por preencher).
- **Abertura da SEMANA** e **abertura do DIA** (níveis de referência monitorados).
- Confluência secundária: **SVP VAL/VAH/POC**, **Smart Money** DEM/SUP, HTF Power.
Um cluster = ≥2 destes sobrepostos numa faixa. Fora de qualquer cluster (alto-no-ar) → **SKIP**.

### 2) POSIÇÃO-NA-ZONA
- **Reclaim (long):** entrar perto do **FUNDO** do cluster de demanda (`pos_in_zone` baixa), não no topo. Entrar no topo da demanda = chop mata.
- **Short:** entrar perto do **TOPO** do cluster de supply, na rejeição impressa.

### 3) SL — FORA DE TODO O CLUSTER (não apertado dentro dele)
- **Reclaim:** SL **abaixo do fundo de TODO o cluster de demanda** −0,1ATR (ex.: hoje ~4367, abaixo de 4377-4394). NUNCA SL curto dentro da zona.
- **Short:** SL **acima do topo de TODO o cluster de supply** +0,1ATR.
- Alvo 3R / RR≥2 medido a partir deste SL.

## Regras concretas

### RECLAIM (long) — gate ANTES do gatilho local
1. Localização: o sweep/retest→reclaim está DENTRO de um cluster de demanda HTF (set acima)? Se NÃO → SKIP (mata os altos-no-ar 4400+).
2. Posição: entrada no terço inferior do cluster (senão SKIP ou aguarda recuo ao fundo).
3. SL abaixo do cluster inteiro −0,1ATR; RR≥2 a partir daí; 3R.

**Efeito no 17/08 — TESTADO (gate de níveis-fixos: entrada em [~4367, ~4384] = abertura dia/semana ±, SL<~4367; abertura semana/dia SÃO as-of-válidas o dia todo):**
| sinal | entry | GATE | outcome real | veredito |
|---|---|---|---|---|
| 4381 (reclaim genuíno) | 4381,8 | FIRE | bounçou→4427 | ✅ apanha o que interessava |
| 4400,9 / 4412,4 (chases) | acima | SKIP | LOSS/OPEN | ✅ corta os chases |
| 4395,8-4398,3 (topo) | acima | SKIP | 3 LOSS | ✅ corta os losers de topo |
| 4389,9 | acima | SKIP | OPEN (sobreviveu) | ⚠️ **skipa um sobrevivente** |
| 4379,9 | 4379,9 | FIRE | LOSS (SL 4374 curto) | ⚠️ dispara; SL-largo **poderia** salvar — NÃO provado |

O gate troca **1 sobrevivente (4389,9) por cortar 4 losers de topo** — não é limpo, é honesto. **NÃO "corrige o SL" dos 4390-topo — SKIPa-os por localização.** O componente OB-do-cluster (4377-4394) é **as-of-16:17, não as-of cada sinal** → o efeito com OB real **não está testado** (precisa replay-collect com OB as-of). Só os níveis fixos (abertura semana/dia) foram testáveis agora.

### SHORT (mirror) — gate ANTES do gatilho local
1. Localização: a rejeição está num cluster de **supply** HTF **E** o preço **NÃO está sobre uma demanda HTF fresca por baixo** (senão é o fundo de outra pessoa) **E** a **perna imediata 1H é DOWN** (não shortar uma perna que sobe). Se falha qualquer → SKIP.
2. Posição: entrada no topo do cluster de supply, na rejeição impressa (fecho terço inferior + iniciativa sell + idealmente CHoCH 1H/15M).
3. SL acima do cluster de supply inteiro +0,1ATR; RR≥2; 3R.
→ Efeito no 17/08 sobre o short do grupo: **VERIFICADO = RECUSA.** O short-ao-grupo real = 08:02Z `zone_reject` 15M, **entry 4405,42 / SL 4417,19** (`surfaced=True` no `e2_verdicts.jsonl`), stopado (preço→4427). Regra SHORT do gate:
> - **Perna 1H:** o verdict das 08:02 registou **"PERNA 1H = BULL, 1H up pos 0.48"** (dado contemporâneo, as-of-válido). Perna imediata 1H = **UP**, não DOWN → **viola → SKIP.**
> - **Sobre demanda:** entry 4405,42 **acima** de abertura dia 4370 / semana 4379 + OB 4377-4394 → segunda violação → SKIP.
>
> O E2 enviou-o porque deixou o **sweep-reject 4H suspender o veto contra-perna** e shortou uma rejeição numa perna 1H que subia — a cegueira. O gate exige **perna 1H DOWN** (não aceita a suspensão-por-4H) → **recusa**. Razão primária (perna 1H UP) é as-of-válida, não depende do OB as-of-agora.

## Caveats
- A medição de hoje usou OB **as-of-agora** (16:17), não as-of cada sinal — aproximação. O backtest do lab SHORT exige OB **as-of** (replay-collect), o gate live consome o OB fresco do momento.
- Localização + posição + SL é **necessário, não garante edge** — forward/backtest+null decidem. Alinha com o playbook (Padrão 1 estrutura-primeiro + Padrão 4 gate-de-posição).

## Aplicação
- **Reclaim (live):** implementar o gate de localização+posição+SL no motor reclaim (`reclaim_engine`/router) — para parar a sangria de longs altos-no-ar. Requer o leitor de OB/FVG/aberturas as-of no ciclo.
- **Lab SHORT:** este gate É a "localização HTF" do manifest (`XAU_15M_SHORT_GATE_MANIFEST`) — o structural-first + o núcleo V1/V2 herdam-no.
