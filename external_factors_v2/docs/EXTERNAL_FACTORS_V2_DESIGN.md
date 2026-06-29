# External Factors v2 — Design canônico (2026-06-29)

Módulo NOVO de fatores externos macro para o sistema XAU. **NÃO reativa** a estrutura antiga do iMac (CANCELLED/DO_NOT_REACTIVATE 2026-06-14). Greenfield, offline-first, production default-deny preservado.

## Princípio mestre
`Raw → Collectors → Normalization → Dedup → Validation → Evidence → Context → External Factor → Trading`. **NUNCA Internet→Claude→Trade.** Só fontes whitelisted (`config/sources_whitelist.json`).

## Two-tier (a espinha)
- **Tier-1 — macro numérico determinístico** (FRED **keyless** via `fredgraph.csv`, verificado: DGS10/DFII10/DTWEXBGS/T10Y2Y/VIX/CPI...). Tem histórico → **join as-of às barras das estratégias → backtestável → único candidato a edge** (só após validação). Séries em `config/factor_registry.json`.
- **Tier-2 — LLM-interpretado** (news/Fed-tone/geopolítica/severidade/gold-driver). Realtime-only, **não-backtestável → contexto/flag, human-in-loop, nunca edge, nunca emite número** (output=label).
- **Fronteira de determinismo (regra dura):** LLM só emite label; número só de pull determinístico; validador rejeita número não-fornecido.

## Autonomia (verificado 2026-06-29)
- FRED keyless ✅ (Tier-1 NÃO depende de API key do operador). gh/git/clone ✅. curl HTTPS ✅. pip ✅. WebSearch/WebFetch ✅. Repos de referência clonados (anthropics/skills, financial-services-plugins).
- **Único insumo do operador:** eventualmente keys de vendor de NEWS (Tier-2, Phase 3) — e mesmo lá há fontes free.

## Fases (cada uma com gate checável)
- **Fase 0 ✅ FEITA** — scaffolding + whitelist + factor_registry + lint gate (PASS). Offline, zero secret.
- **Fase 1 (make-or-break)** — coletor FRED keyless (full history, stamp value/release_ts/as_of/vintage) → `as_of_join` (release_ts≤entry_ts, anti-revisão) → freeze por trade → **validação** (jackknife/null/per-ano/beta-check + DA) contra L1/L2/15M + **red-team de look-ahead** (injeta print futuro, tem que ser excluído). Null honesto = sucesso aceito.
- **Fase 2** — serviço Tier-1 on-demand (determinístico, keyless, frozen por timestamp) no schema `external_*` existente.
- **Fase 3** — **INSTALAR Anthropic Agent SDK (`pip install claude-agent-sdk`)** + frota LLM MVP (3 agentes: Calendar, News, Synthesizer) sobre Agent SDK + Skills próprias (autoradas no padrão anthropics/skills) + News MCP (research) / pull determinístico (daemon). Agentes = label only. → fase correta do Agent SDK (orquestração do Tier-2/runtime standalone deployável).
- **Fase 3b** — agentes restantes (Fed/Central-Bank, Geopolitical, Gold-Driver, Macro, Validation) só se MVP provar útil.
- **Fase 4** — integração live: repointar 1 URL (do morto `192.168.1.90:8765` p/ serviço local), passive-logging, default-deny, promover só com ≥50 eventos + aprovação.

## Mecanismos de correção
- **As-of join** (`join/as_of_join.py`): max(release_ts ≤ entry_ts), vintage da época, nunca forward-fill do futuro. = disciplina SHIFT1/close-only-causal.
- **Freezing** (`freeze/snapshot.py`): 1 JSON frozen por (scope, as_of) + provenance + SHA + git-SHA → replayável/auditável.
- **Validação Tier-1** (`validation/`): jackknife-episódio + null + per-ano + beta-check (não é só "long gold em alta?") + DA obrigatório antes de qualquer claim. Cânone: SEM OOS/cross-asset (proibido); validação mora nos dados.
- **Promoção:** `recorded_context` (default) → `validated_context` → nunca auto-gate sem sign-off.

## Integração (Fase 4, contexto/flag only)
Reusa schema existente do `claude_recheck.py` (external_bias/risk_level/trade_validation/...) — Tier-1 preenche numéricos, Tier-2 os labels. Passive-logging mantido (já proíbe macro alterar classificação). `_EXTERNAL_NEUTRAL_FALLBACK` preservado.

## O que NÃO construir ainda
Frota completa 8-agentes (só 3 no MVP); auto-gate/alteração de classificação; daemon KeepAlive ou bridge 2º-host; OOS/cross-asset; emissão numérica por Tier-2.

## Layout
`external_factors_v2/{config,collectors,normalize,join,freeze,validation,agents,runtime,snapshots,docs}` — isolado do runtime `alert-bridge/`.

Plano completo (Plan agent) + travas: ver memória `project_external_factors_v2_plan`.
