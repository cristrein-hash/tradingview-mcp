# L2/BPT Causal Selector of the 17 · Devil's Advocate

**2026-07-08.** Checagem adversarial do selector (`research/l2_bpt_causal_selector.py`, reproduz os 17 byte-a-byte). Read-only.

## Veredito: `SELECTOR_CAUSAL_BUT_IN_SAMPLE_FIT` (ramo BEAR VAZIO; forward validation ainda obrigatória; sensibilidade insuficiente).

## 1. Causalidade — ✅ PASS (provado empiricamente)
- **Teste de truncagem (decisivo):** recomputar o FSM phase10 só com dados `≤ bi` para cada um dos 17 → **0/17 mismatches** do rótulo de regime vs full-data. **O rótulo à entrada é conhecível à entrada.**
- **Vazamento do segmento anterior: 0/17** (`prev.end ≤ entry_t` em todos). O segmento CORRENTE nunca entra na zona (BULL usa `prev.hi`; RANGE `pos` de barras ≤ bi; BEAR só segmentos `j<idx`). A significância ≥15 barras aplica-se só a segmentos ANTERIORES → a entrada não depende do segmento atual confirmado.
- Zigzag revela pivôs na barra de **confirmação** (não a barra do pivô); RSI/EMA/CUSUM trailing. **Regra outcome-blind** (`keep` só de regime+geometria; `R` só nas linhas de display). **Não é `SELECTOR_HAS_LOOKAHEAD`.**

## 2. Estrutura estável vs fit in-sample — é FIT IN-SAMPLE
- **Kept 17: meanR +2.13, WR 53%. Rejeitados 111 (regime-válidos): meanR −0.09, WR 30%. Universo 128: +0.20, WR 33%.** A regra separa winners de losers massivamente — **no MESMO dado** onde os 4 params + 3 ramos foram escolhidos (docstring: bears 2023 "ficam FORA" = calibração). Separação consistente com edge real OU fit in-sample; **nada aqui discrimina os dois.**
- **A sensibilidade é evidência FRACA (correção ao meu doc):** *alargar é quase-tautológico* — `amp/2` e `POS_THR 0.40` aumentam a zona-keep (superset) → **não podem largar** um kept; "17 iguais" carrega quase zero informação. *A direção informativa — estreitar — QUEBRA:* `amp/4` tira 2, um deles **bi7149 R+4.19 (winner material)**. Os entries BULL sentam-se **perto da borda inferior `amp/3`** (frac 0.10/0.21/0.34), não "fundo na zona" — por isso `amp/4` os corta. `POS_THR 0.40` +7 inclui 3 losers −1.35 limpos → a fronteira faz trabalho **outcome-seletivo**.
- **Sensibilidade ≠ forward validation.** Suavidade local dos params ≠ generalização; o alvo (17) é fixo e os params foram escolhidos para o acertar.

## 3. Forward canary — ZERO evidência forward
Kept por ano: 2023:6 / 2024:4 / 2025:7 / **2026:0** (de 18 sinais regime-válidos 2026). O universo 2026 é meanR −0.42/WR 28% — período mau que a regra **evita** (encorajador), mas **0 kept = 0 confirmação forward**. Validação forward por iniciar, **obrigatória**.

## 4. Ramo BEAR — VAZIO (n=1)
25 sinais BEAR → **1 kept (+7.99)**; os 24 rejeitados meanR −0.95/WR 17%. Parece separador limpo mas é **n=1**; o pick está a meio-zona (frac 0.47), insensível a MIN/WIN por não estar perto de borda. `bear_deep` disparou 1× — **não validável**.

## 5. Defeitos de transparência (não fatais, logados)
- **Denominador inflado:** "17/245 = 7%" enganador. 117 de 245 (pré-2023 + segmento 0) **não têm rótulo de regime** e caem em silêncio; universo efetivo = **128**. Taxa real = **17/128 = 13%**.
- **Proveniência:** fonte canónica de regime = `/tmp/causal_segments_v10.json` = **temp regenerável** (via phase10), não artefacto versionado. Reproduzível mas frágil.

## Bottom line
Causal (sem look-ahead à entrada) = **SIM, provado**. Estrutura estável vs fit = **FIT IN-SAMPLE** (robustez apoiava-se na direção tautológica; estreitar larga um winner +4.19R). Forward validation ainda necessária, sensibilidade insuficiente = **SIM**. BEAR vazio = **SIM**. → `SELECTOR_CAUSAL_BUT_IN_SAMPLE_FIT` — a formalização é uma **descrição causal, coerente e limpa dos winners in-sample**, não evidência de edge forward. **Gate = out-of-sample / live apenas.**
