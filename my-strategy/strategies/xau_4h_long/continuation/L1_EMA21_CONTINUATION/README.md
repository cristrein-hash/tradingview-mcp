# L1 · EMA21 CONTINUATION — módulo offline

Parte da suite **XAU 4H LONG — CONTINUATION**. Status: **USER_APPROVED_FINAL · HUMAN_DISCRETIONARY · CONTINUATION**.
Ver `STRATEGY.md` (regra + métricas) e `MANIFEST.md` (proveniência).

## O que é
Estratégia de **continuação de alta no XAUUSD 4H**, dentro de tendência estabelecida (EMA21/SMA50,
regime D-1 BULL, BOS, zona de demanda Custom OB, F5 volume calmo). Um **scanner** gera o candidato;
a **decisão final é humana**. O filtro `vol_entry_z≥1.993 OR rsi_vs_ma≤−9.35` sinaliza **exaustão**
(BLOCK/REVIEW), confirmado visualmente. **Não é mecânica total, não é automação.**

## Fluxo mínimo (offline, headless)
```
scanner.py  →  journal.py  →  outcome.py  →  telegram_draft.py
(candidato)    (KEEP/BLOCK)    (R post-hoc)    (rascunho, NÃO envia)
```

## Comandos básicos
```bash
# 1. Scanner — gera candidato (último bar do RAW, ou --at <unixts>)
python3 scanner.py
python3 scanner.py --at 1756317600

# 2. Journal — registra decisão humana (append-only; sem --journal-path = só stdout)
python3 scanner.py --at 1756317600 \
  | python3 journal.py --decision KEEP --reason "continuation clean" \
        --reviewed-by cris --journal-path ./l1_journal.jsonl

# 3. Outcome — mede R post-hoc, read-only sobre RAW (não altera o journal)
python3 outcome.py --journal-path ./l1_journal.jsonl --outcome-path ./l1_outcome.jsonl

# 4. Telegram draft — gera SÓ o texto do sinal (NÃO envia)
python3 scanner.py --at 1756317600 \
  | python3 journal.py --decision KEEP --reason "..." --reviewed-by cris \
  | python3 telegram_draft.py
```

## O que NÃO faz
- **Não** é live. **Não** envia Telegram (apenas rascunho; `telegram_allowed: false`).
- **Não** roda como daemon. **Não** executa ordens automaticamente.
- **Não** toca MCP/chart, receiver, monitor, recheck, strategy_rules, catalog, registry, secrets.
- Tudo headless e read-only sobre o RAW canônico; nenhuma escrita em produção/logs vivos.

## Próximo (fora do escopo deste módulo)
Ligar a produção (Production v2 runtime) e/ou permissão de envio via Strategy Registry são
**frentes separadas**, com autorização explícita. Por enquanto: scanner → revisão humana → journal → outcome → draft.
