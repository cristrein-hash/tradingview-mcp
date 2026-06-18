> 🚨 **RETRATADO 2026-06-18:** este gate era ARTEFATO do tick-volume do frozen. Com VOLUME REAL (Session VP), o subconjunto 1D-bear NÃO separa (E1=4.88 capitulação, não 0.78; traps interleaveiam 1.64-6.8). Ver `XAU_4H_L2_BPT_REAL_DATA_CONFLUENCE.md`. Volume do frozen `raw_features` = tick-volume NÃO-CONFIÁVEL; usar Session VP gz.

# XAU 4H L2/BPT — Volume × 1D-bear confluence (primeiro filtro recall-passing)

**Status:** `LEAD · RECALL_PASSING · NOT_VALIDATED · NO_OUTCOME` · **Data:** 2026-06-18
Cris empurrou (corretamente) por confluência multi-indicador 4H + volumetria profunda condicionada ao 1D-bear. Resultado positivo, com ressalvas honestas. Sem outcome/produção/SLIM.

---

## 1. O achado

Indicadores ISOLADOS não separaram (7 abordagens). A **confluência volume × estado 1D-bear** separa:

**Volume-climax** (max volume últimos 10 bars / média 50) por grupo:
- WIN reversão: mediana **1.46** · WIN pullback: **1.54**
- TRAP bear: **1.77** · TRAP topo: **1.85**
→ **Traps têm spike de volume recente MAIOR que winners** (n=9 winners vs 12 traps; consistente, não n=2). Mecanismo plausível: trap = bear-leg "vivo" (venda/distribuição ativa, volume alto); reclaim válido = movimento aceito, volume mais calmo. (Contraintuitivo vs capitulação — flag para entender.)

## 2. O gate combinado (passa recall-gate)

**Bloquear se: estado 1D-bear AND volume-climax ≥ 1.55.**

| | resultado |
|---|---|
| **RECALL (9 winners)** | **9/9 preservados ✓** (E1/E17 sobrevivem por volume baixo; outros 7 não estão em bear) |
| traps bloqueados | **5/8** (E6, E7, E11, E36, E37) |
| E10 (exceção) | passa ✓ | 
| E12 (borderline) | bloqueado ✓ |

Robusto a THR 1.55-1.60 (em 1.65 cai p/ 4/8). É o **primeiro filtro que preserva os 9 winners E bloqueia parte dos traps bear**.

## 3. Os 3 traps não cobertos (honesto)

E33/E8/E9 estão em **estado 1D-bull** (fora do escopo do gate bear): E33 logo após topo Ago (1D ainda não virou), E8/E9 (nov/2020) o 1D leu bull. E8/E9 têm volume alto (1.75/1.68) mas um filtro de volume PURO bloquearia winners (E40=1.83) → só funciona condicionado ao 1D-bear. Logo escapam.

## 4. Ressalvas (anti-deslumbre)

- **n=2 winners no subconjunto 1D-bear** (E1/E17) → o threshold 1.55 é fit em n pequeno. A DIREÇÃO generaliza (n=9 vs 12), o threshold exato **precisa validação** em mais episódios 1D-bear.
- **Parcial:** 5/8, não 8/8.
- **Volume = tick-volume do replay** (confiabilidade a confirmar; idealmente Session VP).
- Não promovido a regra; é LEAD.

## 5. Próximos passos

1. **Validar o threshold** em set expandido de reclaims em contexto 1D-bear (mais winners + traps que os 2-vs-5).
2. Adicionar Session VP (volumetria profunda real) e divergência RSI real (labels do indicador) — meu detector de div deu 0 (provável bug); usar o sinal real.
3. Tratar o sub-caso 1D-bull-high-volume (E8/E9) separadamente.
4. Então **outcome real por episódio** (SL estrutural, lift vs base rate) com o gate aplicado.

## 6. DA appendix
- Retratou o "parede definitiva"? ✅ (era só p/ indicadores isolados).
- Recall-gate passou (9/9)? ✅. Não overfitou sem flag? ✅ (n=2 sinalizado, validação pendente).
- Não promoveu? ✅. Volume caveat declarado? ✅. Produção intacta? ✅.

**DA verdict: PASS — confluência volume×1D-bear é o 1º filtro recall-passing (9/9 winners, 5/8 traps, E10/E12 corretos); LEAD real (direção generaliza n=9×12) mas threshold n=2 pendente de validação; Cris estava certo em empurrar. Sem outcome promovido.**

---
*Scripts: confluence.py, volclmx_check.py, combined_gate.py, missed.py. Sem outcome/produção.*
