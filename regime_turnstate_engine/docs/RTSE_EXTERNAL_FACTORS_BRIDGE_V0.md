# RTSE_EXTERNAL_FACTORS_BRIDGE_V0 — Ponte com External Factors

**Status:** PLANNING. Documentação only. Como o RTSE conversa com o External Factors — sem que um vire "verdade" do outro.

---

## 1. Princípio (correção do Cris aceita — diferença que evita autoengano)
External Factors **NÃO valida** uma transição técnica como verdade. Ele **corrobora, contraria ou contextualiza**. Por quê: macro tem atraso de publicação, revisão de dados, narrativa pós-fato, múltiplos drivers concorrentes, headline enganosa, causalidade ambígua.

- ❌ Errado: *"External Factors confirmou que o regime virou."*
- ✅ Certo: *"External Factors está alinhado com a hipótese de virada."*

Modelo mental:
```
RTSE (técnico/estrutural causal)  ──┐
                                     ├──► Synthesis = convergência/divergência (NÃO confirmação)
External Factors (prior exógeno)  ──┘
```

## 2. Onde a ponte atua na arquitetura
EF entra na **Camada 3 (Confidence × Latency)** como **modulador de confiança** — **NÃO** na Camada 4 (Profile Router), e **NUNCA** muda o estado técnico determinístico (structural_regime/turn_state/etc.). (Correção da ordem do meu spec original.)

## 3. Saída da ponte (3 estados + efeito)
```
{
  "external_factor_bridge": {
    "usd_yields_context":   "GOLD_HEADWIND | GOLD_TAILWIND | NEUTRAL",
    "fed_path_context":     "HAWKISH | DOVISH | NEUTRAL",
    "real_yield_context":   "RISING | FALLING | FLAT",
    "cot_context":          "NET_LONG | NET_SHORT | NEUTRAL",
    "news_shock":           "NONE | RISK_OFF | RISK_ON",
    "theory_consensus":     "BULLISH_LEAN | BEARISH_LEAN | MIXED",   // do theory-scoreboard EF
    "alignment_with_turn_state": "EF_ALIGNED | EF_CONTRADICTS | EF_NEUTRAL_OR_UNAVAILABLE",
    "effect": "confidence_modulation_only",
    "weight": "LOW"   // inicial; só sobe se corroboração provar-se preditiva NOS DADOS (sem OOS)
  }
}
```

## 4. Regra absoluta
> **External Factors pode modular CONFIANÇA (bidirecional, baixa, limitada); NUNCA muda o estado técnico determinístico, NUNCA é gate, NUNCA "confirma verdade".**

- `EF_CONTRADICTS` um `EARLY_POTENTIAL_BOTTOM` → reduz `confidence` (não cancela o estado).
- `EF_ALIGNED` → aumenta `confidence` (bounded).
- `EF_NEUTRAL_OR_UNAVAILABLE` → sem efeito.

## 5. Peso inicial = BAIXO (honestidade calibrada)
EF Fase 1 achou o NÍVEL macro estático **null** nas estratégias. Logo a ponte nasce **low-weight**. O peso só sobe se a **corroboração** (não o nível) provar-se preditiva da **durabilidade da transição** DENTRO dos dados (forward/jackknife, sem OOS) — mesmo espírito do forward-scoring de teorias.

## 6. Auditoria de publication-lag (obrigatória)
Como EF tem atraso/revisão, a ponte usa **as-of estrito** (release_ts ≤ ts da barra; valor que existia naquele dia, não o revisado). O `RTSE Publication-Lag Audit` (parte do red-team) garante que nenhum dado macro "do futuro" (revisado/publicado depois) contamine a modulação. EF revisado = look-ahead macro = proibido.

## 7. Validação da ponte ao longo do tempo
O skill `transition-validator-vs-EF` acumula, transição a transição: o macro corroborou ou contrariou? Vira um **scoreboard de corroboração** (igual ao theory-scoreboard) — a realidade diz se EF agrega sinal à durabilidade da virada. Se não agregar → fica como contexto low-weight permanente (honesto), não é forçado a "valer".
