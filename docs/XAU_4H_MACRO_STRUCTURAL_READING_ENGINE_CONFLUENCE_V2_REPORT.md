# MACRO CONFLUENCE v2 (macro override + late-top) — RELATÓRIO DIAGNÓSTICO

**2026-06-22.** Diagnóstico/calibração. 62 = ensino. Sem outcome. Engine/decisions/produção intocados.
Reusa os 9 especialistas v1 como evidência; muda só a combinação. **CONCLUSÃO: v2 PIOROU — mas corrigiu
um erro de diagnóstico fundamental.**

## Resultado (honesto, negativo)
| | v1 | v2 |
|---|---|---|
| preserve (BULL) anchors | **12/14** | **6/14** (PIOR) |
| block (RISK) anchors | 0/1 | 0/1 (igual) |
| B-set block (RISK) | 5/18 | 5/18 (IGUAL) |
| A-set família | 20 BULL/6 RISK | **8 BULL/18 RISK** (colapso) |

**v2 é claramente PIOR:** o late-top detector matou 6 big winners de bull-run (S20, S29, S30, S31, S32, S38)
porque eles têm legpos alto (natural em bull-run forte) + ≥1 corroborador (weekly RSI OB / d1_supply perto) —
**repetiu o erro "legpos alto penalizado em bull-run"**. E NÃO melhorou o bloqueio do B.

## Tarefa 1 — o erro de diagnóstico revelado (o achado real)
O relatório v1 dizia: "macro_broken sobreposto por sinal local". **ERRADO.** O diagnóstico dos 13 falsos-BULL
do B-set mostra: **10 dos 13 NÃO têm macro_broken nem distribution** (macro_fatal=False). Apenas 3 (T18, T40,
T42) têm macro_broken. Os outros 10 (T2/T3/T4/T16/T20/T23/T24/T25/T26/T30) estão em **regime macro genuinamente
BULL** (MACRO_BULL + FULL_BULL_ALIGN + STRONG_MOMENTUM) — e o Cris ainda os marcou BLOCK.

**Por quê?** Porque são **MÁS ENTRADAS DENTRO de um macro bull correto** — topo de move, range, exaustão local.
O macro engine **lê o regime corretamente** (eles SÃO bull-macro). O problema NÃO é leitura macro/regime — é
**QUALIDADE/LOCALIZAÇÃO DA ENTRADA dentro do bull** (entrar no pullback-low de demanda vs perseguir o topo).

E os 3 macro_broken (T40/T42): nem a override condicional os pega, porque o local é totalmente bull (CLEAN_SKY +
momentum forte + full-bull-align) → sem sinal de risco para corroborar. Bloqueá-los exigiria override
incondicional do macro_broken — que mataria A-winners ocorridos em períodos macro_broken (trade-off ruim).

## Conclusão: PREMISSA REFUTADA — o gap não é macro, é ENTRY-QUALITY
- ❌ **v2 (macro override + late-top) NÃO é o caminho.** Override condicional não pega o B (sem corroboração);
  late-top-via-legpos mata winners (não distingue healthy-high-legpos de late-top — problema já conhecido).
- ✅ **Achado real:** o B-set é **entrada ruim dentro de bull-macro correto**, ortogonal à leitura macro. O
  macro engine v1 é um BOM leitor de regime/contexto macro (preserve 12/14); o que falta é uma **camada de
  ENTRY-QUALITY / LOCALIZAÇÃO-NA-PERNA** (este entry está num pullback-low defendido, ou no topo/meio-de-range?).
- **Manter o macro engine em v1** (bom leitor macro). **NÃO** adicionar mais override macro.

## Próximo passo recomendado
Bloco de **ENTRY-QUALITY specialist** (ortogonal ao macro): distinguir, DENTRO de um bull-macro, entrada em
pullback-a-demanda-defendida (bom) vs perseguição-de-topo/entrada-em-range (ruim). Features causais candidatas:
dist_4h_demand (perto da demanda=bom), demand_touched_on_retest, reclaim a partir da demanda, posição vs POC/VAL
(entrar perto do VAL=bom vs perto do VAH=ruim), dist do swing-low recente. **Provavelmente é a peça que separa o
B do A** — e o problema healthy-high-legpos-vs-late-top pode ser, no fundo, "entrei perto da demanda ou perto da
supply/topo". NÃO tunar a IDs; validar 276+OOS depois.
