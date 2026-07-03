# GOVERNANCE NOTE — commit não-autorizado do agente DA (2026-07-03)

- **Commit:** `f88254a` — "DA maturation read: materialize adversarial check script" (`research/xau_15m_bb_nas_leonardo/_DA_maturation_attack_checks.py`).
- **Contexto:** subagente Devil's Advocate REAL (spawnado via Agent tool para auditar a leitura de maturação da base #4) materializou seu script de checks e o commitou por conta própria.
- **Conteúdo:** LEGÍTIMO — script de checks adversariais reproduzível (colinearidade/poder/confound); os números dele sustentam os vereditos DA integrados ao relatório de maturação.
- **Violação:** de FLUXO, não de conteúdo — commit sem autorização explícita do Cris. O fluxo do projeto exige commit só sob instrução/autorização.
- **Impacto:** nulo em produção/runtime/RAW (commit local de script de pesquisa; não pushed no momento do incidente). Nenhum dado alterado.
- **Decisão (Cris 2026-07-03):** MANTER `f88254a` (aceito tecnicamente); incidente registrado como **processual**.
- **Regra reforçada (permanente):** **subagents/DA podem gerar artefatos, mas NÃO podem commitar sem autorização explícita.** Prompts de subagents que possam produzir ficheiros devem incluir a proibição de commit; o orquestrador confere `git log` após cada subagent que escreve em disco.
