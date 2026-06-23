# XAU 4H L2/BPT — READER VIVO: LEITURA ANTIGA (backbone DERIVADO) vs REBUILD RAW-CLEAN — 2026-06-23

FASE 11 do bloco de eliminação de débito. Pergunta: **a correção da fonte (Camada-1 derivada → RAW
original) mudou as conclusões de leitura, ou as confirmou?** Comparação por episódio + classificação de
cada lente como RAW_CONFIRMED / RAW_MODIFIED / RAW_REFUTED / QUARANTINED_PENDING_RAW.

Inclui a **VISUAL POST-AUDIT REVIEW** (FASE 10) como seção final — prints = `VISUAL_AUX_ONLY` (manifest),
nunca fonte primária; reconciliação visual fica para Cris (não capturei screenshots).

Fontes:
- Leitura ANTIGA (backbone derivado): `results/blind_pack_cluster4918/reader_dossier_FROZEN.md` + `…/phase3_audit_FROZEN_vs_outcome.md`; idem `blind_pack_cluster2/`.
- Leitura RAW-CLEAN (backbone RAW Custom OB): `results/raw_rebuild_cluster{1,2}/reader_dossier_RAW_FROZEN.md` + `…/phase3_audit_RAW_FROZEN_vs_outcome.md`.
- Backbone RAW: `l2_bpt_raw_backbone_builder.py` → `results/l2_bpt_raw_backbone_episodes.jsonl`. Gate: `source_gate/check_reader_sources.py` (exit 0).

> CANON: diagnóstico de QUALIDADE de leitura por episódio (SANITY_PROBE declarada). NÃO é gate/edge/hit-rate,
> NÃO se conclui "promover". Unidade = episódio, não trade ([[feedback_episode_unit_of_analysis_canon]]).

---

## 1. O que a correção de fonte mudou — resposta direta

**As conclusões load-bearing NÃO mudaram; foram REPRODUZIDAS sobre dados autênticos.** A leitura antiga
rodou sobre backbone DERIVADO (sup_cat/clean_sky/dist_supply não-mapeados ao RAW); a leitura RAW-clean rodou
sobre Custom OB RAW. Apesar de readers cegos DIFERENTES e fonte corrigida, os MESMOS eixos sobreviveram ao
outcome nas duas rodadas, e o MESMO ponto cego único apareceu — agora mais nítido. **O bug de fonte NÃO
invalidou a leitura de auction; as lentes sobrevivem no RAW.** Esse é o resultado central de FASE 11.

Uma coisa a correção AGRAVOU (para melhor — mais honestidade): o que na auditoria antiga era um ponto cego
*menor* (1 miss, 4926 "supply-as-obstacle") aparece na auditoria RAW como uma falha **sistemática e dominante**
(a categoria REFUTED inteira). A fonte RAW + reader fresco promoveram "supply-WALL→fade" de "blind spot menor"
para **lente em QUARENTENA** que só funciona com o eixo SVP/acceptance — hoje BLOQUEADO.

---

## 2. Tabela por episódio — veredicto ANTIGO vs RAW

### Cluster 1 (sósia 3a + continuação 3b)
| EP | mfe_R / exit | Veredicto ANTIGO (derivado) | Veredicto RAW (Custom OB) | Δ |
|----|---|---|---|---|
| 4918 | 19.79 monster | ACERTOU (fundo legítimo, alta conf) | RAW_CONFIRMED (washout/change-of-character) | igual ✓ |
| 4926 | 18.03 monster | ILUDIDO (super-pesou supply 1.61ATR) | RAW_REFUTED (leu wall/morrendo; correu) | igual (miss) ✓ |
| 1661 | 0.0 STOP | ACERTOU (trap) | RAW_CONFIRMED (bear-pullback-trap) | igual ✓ |
| 5701 | 0.42 STOP | AMBIG-honesta (lean absorção errado) | RAW_CONFIRMED (incomplete-base; SVP era o árbitro) | igual ✓ |
| 6887 | 0.0 STOP | PARC. ILUDIDO (timing; comprou apex) | RAW_REFUTED (call bull alta-conf tomou stop imediato) | **mais severo no RAW** |
| 7426 | 4.61 SCRATCH | ACERTOU natureza (path violou pullback) | RAW_MODIFIED (parcial dir+timing, nenhum limpo) | ~igual |
| 8878 | 18.78 monster | ACERTOU (markup saudável, melhor convergência) | RAW_REFUTED (reader RAW leu pausa/EQH; rompeu vertical) | **DIVERGÊNCIA entre readers** |
| 8923 | 0.58 BE | AMBIG-honesta (exaustão fired) | RAW_CONFIRMED (RSI82 blow-off → −93) | igual ✓ |
| 8940 | 4.96 (ran +109) | ACERTOU (post-flush reclaim; exit clipou) | RAW_CONFIRMED (continuação construtiva) | igual ✓ |

Placar: ANTIGO 5 acerto / 2 ambig-honesta / 2 miss · RAW 5 CONFIRMED / 3 REFUTED / 1 MODIFIED.
A única divergência REAL de leitura é **8878** (readers cegos diferentes: antigo leu buy-continuação=acerto;
RAW leu pausa/EQH=refutado). Não é efeito do backbone — é variância de reader. Em ambos os casos o **8923**
(blow-off) e o **4926** (supply absorvido) caem do mesmo jeito.

### Cluster 2 (macro negativo, 4 sub-blocos)
| EP | mfe_R / exit | Veredicto ANTIGO (derivado) | Veredicto RAW (Custom OB) | Δ |
|----|---|---|---|---|
| 5826 | 16.73 runner | ACERTOU (washout, fuel) | RAW_CONFIRMED (FUEL) | igual ✓ |
| 1623 | 0.31 STOP | ACERTOU (esticado, frágil) | RAW_REFUTED (washout-drift; não correu) | ~igual (reader auto-flagou fraco) |
| 4401 | 10.31 monster | ACERTOU (supply-as-fuel) | RAW_REFUTED (leu wall/trap; rompeu) | **DIVERGÊNCIA: antigo leu fuel→acerto** |
| 3825 | 0.96 STOP | ACERTOU (wall, momentum fraco) | INSUFFICIENT_RAW_CONTEXT (SVP era árbitro) | RAW mais honesto |
| 1522 | 5.65 runner | ACERTOU (washout reabsorvido) | RAW_REFUTED (leu wall/blocks; rompeu) | **DIVERGÊNCIA** |
| 1873 | 1.20 STOP | ACERTOU (bear-pullback trap, RSI div) | RAW_CONFIRMED (trap) | igual ✓ |
| 5627 | 5.96 runner | ILUDIDO (wall; absorveu) | RAW_REFUTED (wall extremo; correu) | igual (miss) ✓ |
| 1775 | 0.53 STOP | resíduo-honesto (caiu p/ trap) | INSUFFICIENT_RAW_CONTEXT (sub-determinado) | igual ✓ |
| 3949 | 6.62 runner | ACERTOU (leu inverso da etiqueta) | RAW_CONFIRMED (FUEL/open-sky) | igual ✓ |
| 3929 | 0.05 STOP | ACERTOU (leu inverso da etiqueta) | RAW_CONFIRMED (WALL/blocks; travou) | igual ✓ |

> Nota importante sobre 4401/1522: na rodada ANTIGA o reader leu fuel e ACERTOU; na RAW o reader leu wall e
> ERROU. Isso NÃO é o backbone mudando o dado — é o reader RAW pendendo para o polo WALL em casos de supply
> colado. Reforça a conclusão geral: **o polo WALL→fade é o que falha; quando o reader leu FUEL acertou.** A
> regra robusta não é "supply colado = fade" (refutada) nem "supply colado = fuel" — é que a distinção exige
> o eixo SVP/acceptance hoje bloqueado.

---

## 3. Classificação de LENTES (consolidado old+RAW, sobreviveu ao outcome?)

| Lente | Status | Evidência |
|---|---|---|
| **L1 — Regime/weekly-sign como inversor de significado** (FLUSH_V idêntico: bear→trap, turn→fundo) | **RAW_CONFIRMED (load-bearing)** | 1661(−)trap vs 4918(+turn)monster; cluster2 inteiro quebrou "weekly<0=tudo trap" (4 runners em macro negativo) |
| **L2 — RSI-position-in-leg / freio de blow-off** | **RAW_CONFIRMED** | 8878 RSI56 corre vs 8923 RSI82/84 → crash; 5826 RSI30.8 exausto→fuel |
| **L3 — Polo FUEL** (supply distante ≥~2.4ATR + clímax + flush/V-reclaim + expansão/close-no-topo → corre) | **RAW_CONFIRMED** | 4918, 5826, 3949, 1522 (forma), 8940 |
| **L4 — Forma da barra de entrada / TRAP** (entry vermelha em macro neg = morte; bear-pullback + RSI div = trap) | **RAW_CONFIRMED** | 1873 & 3929 (2/2 entries vermelhas falharam); 1661 |
| **L5 — Forma 4H > etiqueta textual de acceptance** | **RAW_CONFIRMED (mais forte)** | par D 3949 vs 3929 lido ao INVERSO das labels, ordenação perfeita 6.62R vs 0.05R |
| **L6 — Geometria preço×supply é o eixo SOB macro controlado** | **RAW_CONFIRMED em par casado / RAW_REFUTED cross-episódio** | 3949v3929 (macro idêntico) separou perfeito; 4918v4926 (cross) quebrou |
| **L7 — supply-proximity-as-WALL / fade** | **QUARANTINED_PENDING_RAW** | REFUTED dominante: 4926/8878/4401/1522/5627 todos colados-ao-supply e CORRERAM; o discriminador real é SVP/acceptance (BLOCKED_UNMAPPED) |
| **L8 — compressão-sob-supply: construtiva vs exaustão** | **INSUFFICIENT_RAW_CONTEXT** | 3825/1775/5627 sub-determinados sem value-area; próxima prioridade de mapeamento RAW |

**Conclusão de lentes:** 6 lentes RAW_CONFIRMED (a base operável), 1 QUARENTENADA (L7), 1 marcada
INSUFICIENTE por dado bloqueado (L8). Nenhuma lente confirmada na rodada antiga foi DESTRUÍDA pela troca de
fonte — o débito derivado NÃO estava inflando as conclusões de auction (contraste honesto com o caso
slim→RAW de Caminho A/B, onde a troca destruiu números). Aqui a fonte autêntica REPRODUZIU os eixos.

---

## 4. O que a fonte RAW revelou de NOVO (não visível na rodada derivada)

1. **L7 (supply-WALL→fade) é sistemático, não um caso isolado.** A rodada antiga viu 1 miss (4926). A RAW,
   com Custom OB autêntico + reader fresco, mostra que TODO call de WALL próximo correu (cluster2: WALL 1/4
   segurou). "Perto do supply" sem o eixo de aceitação **precede os maiores runs** (absorção→breakout), não
   fades. Isto reorienta a próxima frente: **mapear SVP/acceptance é a prioridade #1**, é o árbitro ausente.
2. **A geometria é eixo APENAS com macro controlado.** Par casado (3949v3929, mesmo dia) → geometria manda.
   Cross-episódio (4918v4926) → geometria sozinha engana. Lente L6 é condicional ao controle de macro.
3. **clean_sky tem dois significados opostos** (vácuo de bear vs pista de bull) — confirmado RAW; não
   discrimina sozinho, só dentro do regime.

---

## 5. VISUAL POST-AUDIT REVIEW (FASE 10) — 8 checagens

Prints = `VISUAL_AUX_ONLY` no manifest (nunca fonte primária; reconciliação visual fica para Cris). Não
capturei screenshots (regra: não capturar sem pedido). Checagens estruturais sobre o RAW:

1. **Mapping bar_idx→data**: 10/10 (cluster2) e 9/9 (cluster1) timestamps batem com o frozen (close-match). ✓
2. **close RAW vs frozen**: anchor por close-match; 18/19 fidelity-PASS; 4401 fidelity-FAIL flagado (warning não-silencioso). ⚠ (4401)
3. **supply/demand RAW**: 19/19 Custom OB extraídos as-of-bar; sup_cat coerente com dist_supply. ✓
4. **Polo FUEL vs WALL no chart**: a reconciliação visual de "supply absorvido vs rejeitado" exige olho de Cris nos prints — flag para revisão humana (casos 4926, 4401, 1522, 5627). ⚠ humano
5. **SVP/acceptance**: BLOCKED_UNMAPPED em 100% dos episódios; nenhum valor inventado. ✓
6. **Sem outcome no pacote cego**: leak-check PASS (gate). ✓
7. **Indicadores RAW (NAS/SMC/bubbles/RSI)**: era-correta (tail as-of-bar), sem head stale. ✓
8. **Divergência reader-old vs reader-RAW (8878, 4401, 1522)**: variância de reader, não de dado — registrada; não invalida lentes. ✓

**Item que pede ação humana:** check #4 (reconciliação visual FUEL/WALL) e o warning de fidelity do 4401.
Nada bloqueia as conclusões de lente; ambos são refinamentos.
