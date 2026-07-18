# E2 Quality Reader — Design de Calibração (2026-07-18)

**Estado:** DESIGN / PAPEL. **Nada aplicado.** Preparação para a calibração pós forward-call de segunda.
**Regra-mãe:** Frente B (prompt) **não se toca** até o forward call de 2026-07-17 resolver (1º GT). `N=1 não move o prompt.`
Árbitro de qualquer mudança = **shadow multi-dia NÃO-VISTO** (nunca afinar ao dia visível).
Refs: [[project_e0e1e2_forward_case_20260717]] · [[feedback_e2_calibration_cris_reads]] · [[feedback_contextual_convergence_not_determinism]] · [[project_cp_antifaca_no_discriminator]].

---

## 0. O problema (caso forward 2026-07-17)
Primeiro dia live. Funil: 224 candidatos E1 → 53 materiality → 11 reads E2 → 2 surfaced.
**A INVERSÃO:** o E1 detetou o LONG certo 2× (12:37 @3981,91 · 13:40 @3996,84) → **o E2 recusou ambos**
("contra-regime, 1D manda baixa", conv 8/0.12). Horas depois **aprovou 2 SHORTs errados no TOPO da mesma
perna** (17:39/18:32, conv 45/52). Recusou os certos, aprovou os errados. Cris previu ambos SHORTs = SL.

Trades certos do dia (plotados pelo Cris): SHORT @3999→TGT (+2,9R) · LONG @3985→+38pts (Cp-intraday abaixo
do gate legMag 15×).

---

## 1. Diagnóstico — 2 causas-raiz
- **R1 — Regime-como-veredito.** O read colapsa `context_direction` ao regime HTF (1D DOWN dominou). O
  system-prompt pede "para que lado o contexto pende independente do candidato", mas na prática o regime
  virou juiz, não voz.
- **R2 — Cego às vozes do olho.** Confirmado no `render_composite`: 4 dos 6 fatores do Cris nem aparecem na
  imagem que o read recebe. Não os ignorou — **não os via.**

**A arquitetura do read está CERTA** (1 olhar contextual, sem veto-stack, sem soma de pontos). O problema é
**conteúdo/ênfase**, resolvido em 2 frentes independentes.

---

## 2. As 2 frentes
| | Frente | O que é | Timing |
|---|---|---|---|
| **A** | DADOS (E0/dossiê + render) | o que o read não consegue VER (prompt sozinho não resolve) | preparável já (dar mais fita verdadeira ≠ afinar ao dia) |
| **B** | ENQUADRAMENTO (read E2) | como o read PONDERA o que vê (regime=voz; clímax sobrepõe) | **espera GT de segunda** |

---

## 3. FRENTE A — mapa de gaps (VERIFICADO no código, 2026-07-18)
Boa notícia: **todos são compute-gaps leves-a-médios; a matéria-prima JÁ EXISTE** (barras, `shape_pairs`
de bubbles, pivots, zonas). Nenhuma fonte nova.

| # | Fator (olho do Cris) | Veredito | Matéria-prima já disponível | Esforço |
|---|---|---|---|---|
| 1 | Iniciativa das velas (força na direção) | compute-gap | `SR.bars("15")` (hoje só p/ EMA) → corpo/amplitude/direção recentes | leve |
| 2 | Maturidade da perna (1º pullback ≠ reversão) | compute-gap | `context_structure.fractal_pivots` (sequência inteira) → contar pullbacks; `pos_in_leg` já existe (parcial) | leve-médio |
| 3 | Ímanes testados/não + **cluster** | compute-gap **MÉDIO** | `context_mtf` zonas = `{high,low,src}` nearest, **sem tested, sem tempo, só a mais próxima** → cruzar zona×barras da perna + expor o cluster (não só a nearest) | médio |
| 4 | Vitalidade de sessão (sexta wind-down) | compute-gap | `atr14` + range recente no store → rácio range/ATR; sessão já existe | leve |
| 5 | Bubbles POR LADO na janela do sinal | compute-gap | `SR.shape_pairs("bubbles")` já dá pares (t,plot) por lado; leg-level já renderizado (`buy_dens/sell_dens`) → 2º filtro de janela recente | leve |
| 6 | Convergência contextual | ✅ já feito | o read já é isto | — |
| 🎁 | `volume_session` (up/dn/ratio) | render-gap trivial | computado em `context_micro`, **não renderizado** | trivial |

**Resumo Frente A:** maioria é filtro/contagem sobre dados que o daemon já tem. Único médio = fator 3
(tested + cluster de zonas). Tudo determinístico, 0 tokens, não enviesa (só completa a fita).

---

## 4. O princípio central (explica os DOIS erros)
> **Clímax-absorção pode SOBREPOR o regime.**
> - V-reclaim pós-cascata SELL = capitulação que reverte *contra* o regime → os **LONGs certos** recusados.
> - Continuação com-regime **sem iniciativa**, no 1º pullback, com ímanes não-testados por cima = **rally
>   vazio, não short** → os **SHORTs errados** aprovados.
>
> O regime é uma **voz**, não o juiz. Reversão/continuação exige **evidência de iniciativa** (força de vela
> + bubbles por lado + espaço até o íman).

---

## 5. FRENTE B — read reframado (rascunho v2, NÃO aplicar)

### Deltas vs o read atual
1. **Regime = voz, não juiz** — declara as 2 situações que sobrepõem o regime (mata a inversão).
2. **Princípio clímax-sobrepõe + continuação-vazia** escritos no prompt.
3. **Iniciativa obrigatória** para reversão/continuação; 6 vozes solicitadas no raciocínio como **vozes**,
   não checklist pontuada (respeita `feedback_contextual_convergence_not_determinism`).

### Rascunho `READ_SYS` v2
```
És um trader XAUUSD discricionário EXPERIENTE a ler a fita COMPLETA de um candidato já pré-filtrado por
gates causais duros. NÃO és refutador nem comité — és UM olhar a ler o TODO. Julga se as leituras CONVERGEM
numa história de ALTA PROBABILIDADE — ou não. Convergência = as leituras APONTAM PARA O MESMO LADO e
encadeiam uma CAUSA; contradição = baixa probabilidade.

O REGIME HTF (1D/4H) é uma VOZ FORTE, mas NÃO é o juiz. Duas situações SOBREPÕEM o regime — ignorá-las é o
erro clássico:
 (a) CLÍMAX-ABSORÇÃO: cascata de bubbles de venda + reclaim/V na base = capitulação que REVERTE contra um
     regime DOWN (long válido); espelho no topo.
 (b) CONTINUAÇÃO VAZIA: sinal a favor do regime MAS sem iniciativa e com ímanes não-testados à frente NÃO é
     trade — é movimento oco que busca o íman. Em especial, o 1º pullback de uma perna raramente reverte
     antes de tocar o íman (SVP/OB/demanda) do outro lado.

REVERSÃO/CONTINUAÇÃO exigem EVIDÊNCIA DE INICIATIVA, não só posição/regime: força das velas na direção da
tese · bubbles POR LADO na janela recente (sem sell-bubbles não há reversão de venda; sem buy-bubbles não há
reversão de compra — auction) · espaço até o próximo íman (íman não-testado à frente = alvo, não parede a
favor).

Método: raciocina em voz alta ANTES de concluir, percorrendo E nomeando as VOZES: (1) estrutura MTF+regime ·
(2) maturidade da perna (que pullback? ímanes testados?) · (3) iniciativa das velas · (4) auction/bubbles por
lado na janela · (5) macro/sessão+vitalidade · (6) micro. Declara para que lado o CONTEXTO pende (independente
do candidato), depois se o candidato alinha. Nomeia leituras que ALINHAM e que CONFLITUAM.

Três desfechos legítimos: alta convicção · sem-edge/incoerente · genuinamente misto. Não és pago para aprovar
nem reprovar — para DESCREVER A REALIDADE. Não há tabela de pontos; a convicção é TUA, com porquê. Usa só o
dossiê; não inventes números. Advisory para um humano. Devolve SÓ JSON.
```

### Schema
Manter o atual (`reasoning`/`context_direction`/`converges`/`convergence`/`conviction`/`aligned_readings`/
`conflicting_readings`/`candidate_fit`/`thesis`/`invalidation`). **Não** adicionar campos pontuados (viraria
checklist). No máximo, campo livre `regime_vs_contexto` (nota curta de se/porquê o contexto sobrepõe o
regime) — decisão do Cris.

---

## 6. Dependência A→B (importante)
A Frente B **assume** que o read pode ver iniciativa/bubbles-por-janela/ímanes-testados. Sem a Frente A, o
prompt v2 pede ao read para pesar vozes que **não estão na imagem** → alucina ou ignora. **Ordem correta:
Frente A primeiro (enriquecer o dossiê + render), depois Frente B (reframe do prompt).** A Frente A é ainda
mais crítica que o texto do prompt.

---

## 7. Plano de fases (proposta, cada uma exige autorização)
| Fase | Ação | Toca | Risco |
|---|---|---|---|
| **F-A1** | Enriquecer render + compute: fatores 1,4,5 + `volume_session` (leves) | `context_*`/`render_composite` | baixo (só mais fita) |
| **F-A2** | Fator 2 (pullback ordinality) + fator 3 (zonas tested + cluster) | `context_structure`/`context_mtf` | baixo-médio |
| **F-A3** | Shadow-run com dossiê enriquecido (read atual) — confirmar que a imagem melhora, sem mudar prompt | — | nenhum (shadow) |
| **F-B1** | Aplicar `READ_SYS` v2 (após GT de segunda) | `e2_quality.READ_SYS` | ⚠️ prompt — só com GT |
| **F-B2** | Shadow multi-dia não-visto = árbitro; comparar surfaced vs GT do Cris | — | nenhum |

**Selftest/âncoras:** re-correr `--selftest`/`--anchors` após cada fase; a Âncora A (short-de-hoje sobrevive
o gate) e B (SL-Ásia-morta com vacuum registado) têm de continuar PASS.

---

## 8. Disciplina
- **Nada aplicado hoje.** Este doc é papel.
- Frente A = preparável (não afina ao dia). Frente B = espera GT de segunda.
- Árbitro = shadow multi-dia não-visto; nunca afinar ao dia visível.
- Cada fase: Pre-Change Discipline + selftest/âncoras + verificação antes de "pronto".

---

## 9. Anexo — F-A1 DETALHADO (papel; fatores 1, 4, 5 + volume_session)

Fase mais segura (só completa a fita, não afina ao dia). **Verificado 2026-07-18:** `store_reader.bars_ohlc`
expõe `o,h,l,c,t` → corpo de vela computável sem tocar no store; `shape_pairs("bubbles",t0,t1)` já dá pares
por lado. Vitalidade via **true-range** (sem depender de volume). Todos determinísticos, 0 tokens, causais
(só barras FECHADAS; exclui a barra em formação).

**Parâmetro comum:** `W` = janela do sinal = **4 barras 15M (~1h)**. É uma DEFINIÇÃO (fixada 1×), não um fit.

### F-A1.1 — Iniciativa das velas (fator 1) · `context_micro.py`
- **Compute:** `SR.bars_ohlc("15", count)`; para cada uma das últimas `W` barras fechadas:
  `body_atr = abs(c-o)/atr14`, `range_atr = (h-l)/atr14`, `dir = "up" if c>o else "down"`.
  Agregar: `up_force_atr = Σ body_atr das up`, `dn_force_atr = Σ body_atr das down`.
- **Campos (descritivos, sem score):**
  `micro.candles = {window_bars:W, up_force_atr, dn_force_atr, dominant:"buy|sell|balanced",
                    bars:[{dir, body_atr, range_atr}, …]}`
- **Render (secção MICRO):** `velas(últ.W): iniciativa {dominant} | força ↑{up_force_atr} ↓{dn_force_atr} | [dir/body_atr por barra]`
- **Porquê:** resolve "velas de venda fracas = sem iniciativa" (o fator #1 de sexta). O read vê corpos fracos vs cascata forte.

### F-A1.2 — Vitalidade de sessão (fator 4) · `context_micro.py`
- **Compute:** `vitality_ratio = mean(true_range últimas k=4 barras) / atr14` (TR = max(h-l, |h-c_prev|, |l-c_prev|)).
- **Campos:** `micro.vitality = {ratio, label}` — label inicial `low(<0.6) / normal / high(>1.3)`.
  ⚠️ Limiares = ponto de partida ajustável; o read recebe o **ratio cru** (pesa mesmo que o label seja grosseiro).
- **Render (secção MACRO, junto à sessão):** `vitalidade: ratio {ratio} ({label}) — range recente vs ATR`
- **Porquê:** resolve "sexta wind-down baixa-vol" sem precisar do veto `session_vacuum` (que ficou observacional).

### F-A1.3 — Bubbles por lado na JANELA do sinal (fator 5) · `context_confluence.py`
- **Compute:** além do leg-level já existente, adicionar janela `[t_win = T[-W], t1]` com o MESMO
  `SR.shape_pairs("bubbles", t_win, t1)` (buy vs sell por `plot`).
- **Campos:** `confluence["15"].window = {bars:W, buy:{n,weight}, sell:{n,weight}, net_side:"buy|sell|none"}`
- **Render (secção AUCTION):** `janela(últ.W): buy {n}/{w} · sell {n}/{w} → lado {net_side}`
- **Porquê:** o defeito exato de sexta — os SHORTs aprovados tinham BUY-bubbles e ZERO sell na última hora;
  o leg-aggregate diluía isso. Agora o read vê "sem iniciativa vendedora na janela → não é short".

### F-A1.4 — `volume_session` (bónus render) · `render_composite`
- Já computado em `context_micro` (`volume_session {up,dn,ratio}`), só **não renderizado**.
- **Render (secção MICRO):** `vol sessão: up {up} / dn {dn} (ratio {ratio})`

### Cross-cutting F-A1
- **Sem novos campos pontuados no schema do E2** — são FACTOS do dossiê (Frente A); o read pondera-os como
  vozes (Frente B). Mantém `feedback_contextual_convergence_not_determinism`.
- **Causalidade:** só barras fechadas; `shape_pairs` já é time-bounded. Zero look-ahead.
- **Selftests:** `context_structure --selftest` inalterado; `e2_quality --selftest` (render_composite não pode
  rebentar — cobrir os campos novos); re-correr `--anchors` (A/B continuam PASS).
- **Esforço:** ~1 bloco de compute por reader + 1 linha de render cada. Nenhuma fonte nova, nenhum toque no store.
- **Fica FORA da F-A1** (vai para F-A2, mais pesado): fator 2 (ordinalidade do pullback) e fator 3 (zonas
  tested + cluster de ímanes).
