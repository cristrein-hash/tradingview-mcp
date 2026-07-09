# XAU 15M MARKUP-DEMAND — BASE REPAIR (Opção B) · PRÉ-REGISTRO

**2026-07-09.** Protocolo 15M V1 ACTIVE. **Status: PREREG antes de qualquer teste.**

## 1. Objetivo
Construir o **universo live-fireable** de candidatos markup-demand **sem usar a confirmação futura do pivô** (o leak: zz r=6 só rotula demanda após rally futuro de 6 ATR; 94/96 entries do N96 disparavam antes de `conf_i`).

## 2. Não-objetivos
Não otimizar; não produção/Telegram/broker/runtime; não SHORT; não redesenho livre.

## 3. Unidade (congelada)
**Live-fireable markup-demand candidate:** low corrente (`running low elo`) de uma perna descendente cujo TOPO (pivô H) **já está confirmado** no momento da avaliação + gatilho de reclaim.

## 4. Base proibida
N96/N83 contaminado **não** é validação. Serve só de referência de comparação (matched/extra).

## 5. Definição EXATA do candidato (tudo conhecível na barra k)
- Estado do zz(6) atualizado **online** (mesma ordem de update do `zz()` do engine; pivôs só "existem" a partir do bar de confirmação).
- Candidato ativo quando `d==-1` (down-leg confirmada por H-pivot), `lastH` existe, `elo<k`, `k-elo<=24` — **OU** janela residual pós-confirmação (pivô L confirmado, entries até `elo+24`, como o master permitia; ~2/96 casos).
- **kind MARKUP live:** `prevL is None or candidate_low > último L confirmado` (higher-low com informação disponível).
- **1 entry por candidate low** (novo lower-low = novo candidato, janela reinicia).
- Janela: TS[candidate] em ago/2025→2026-07-04 (idêntica ao master).
- Gatilho de entry (idêntico): `close>EMA21 && close>close[-1]` dentro de 24 barras do candidato.

## 6. Filtro transferido (Intra-Bear Capitulation)
`SKIP se macro_regime==BEAR (v5 hour-causal, código VERBATIM engine_substrate4_v5_hourcausal linhas 1-73) E 1D_px_vs_ema>=0` — `1D_px_vs_ema = (entry_px − EMA21_1D_último_bar_FECHADO)/**ATR_15M[entry bar j]**` (normalização IDÊNTICA ao original `n96_exhaustive_mtf_discrimination.py:38`; correção do DA: a 1ª redação dizia ATR_1D — o código implementou o certo, sanity diff 0.0 vs cut CSV). htf_1D.primitives nativo.

## 7-8. SL/Exit transferidos
SL V1 = `candidate_low − 0.1·ATR[candidate_bar]` (causal: low passado) · guarda risco >0.05·ATR · Exit = **3R fixo first-touch SL-first, horizon 1440** (dominância/robustez auditadas no bloco SL/EXIT; transferem).

## 9. Proibições
Sem rally-futuro-6ATR p/ selecionar · sem lower-low futuro p/ excluir · sem MFE/MAE p/ seleção · sem outcome como seletor · sem membership no N96 como seletor · timestamps de features ≤ entry.

## 10. DA obrigatória
Source guard + DA adversarial (Agent real) antes de verdict.

## Expectativa declarada (do DA anterior)
~173 entries (aprox.; fail-loud com explicação se divergir) · WR pré-filtro ~28% · o teste real deste bloco = **o filtro capitulation salva a base live-fireable?** Reportar honestamente, sem salvar por thresholds.
