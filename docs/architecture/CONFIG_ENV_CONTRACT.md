# CONFIG / ENV CONTRACT — Fase 2 portability layer (Agentic OS)

**Data:** 2026-07-02 · **Escopo:** estritamente aditivo, zero-produção. Nenhum script vivo alterado; nenhum path trocado; nada movido/apagado.
**Objetivo:** base de portabilidade/comercialização — de-hardcoding via resolver central com defaults seguros (byte-idênticos aos paths atuais).

## Ficheiros criados
- `config/paths.py` — resolver central (8 roots env-overridable + helpers).
- `config/__init__.py` — torna `config` importável (`from config.paths import ...`).
- `.env.example` — contrato de variáveis (copiar para `.env` gitignored).
- `tests/test_paths_resolution.py` — teste mínimo (defaults byte-idênticos + env override).
- este doc.

## Contrato de variáveis de ambiente (todas opcionais)
| Var | Papel | Default seguro (= path atual) |
|---|---|---|
| `TRADING_SYSTEM_ROOT` | raiz do repo | auto-detetado (pai de `config/`) = `/Users/cristrein/tradingview-mcp` |
| `DATA_ROOT` | raiz de dados | `= TRADING_SYSTEM_ROOT` |
| `RAW_DATA_ROOT` | RAW replay/source (HD externo) | `/Volumes/GUTS_ LACIE/TradingData` |
| `OUTPUT_ROOT` | reports/outputs | `<repo>/reports` |
| `PRIVATE_ROOT` | pesquisa/estratégia privada | `<repo>/my-strategy` |
| `EXTERNAL_FACTOR_ROOT` | módulo EF v2 | `<repo>/external_factors_v2` |
| `LOG_ROOT` | logs | `<repo>/alert-bridge/logs` |
| `TEMP_ROOT` | scratch / bootstrap tmp | `/tmp` |

**Regra de defaults seguros:** se nada for definido, todos os paths resolvem byte-idênticos aos literais atuais → importar/usar o módulo não muda comportamento. Portabilidade = definir estas vars noutra máquina/cliente. Segredos (Supabase, chaves EF) ficam FORA deste contrato de paths, em `.env`/módulo EF.

## Helpers
`repo(*p)`, `tmp(name)`, `raw(*p)`, `private(*p)`, `external_factor(*p)`, `log(*p)`, `output(*p)`, `causal_segments()`, `ruler(*p)`. Todos devolvem paths idênticos aos hardcoded atuais sob defaults.

## Matriz: path atual → variável futura (categorizado do inventário)
| Padrão hardcoded | Ocorrências | Categoria | Var futura | Helper sugerido |
|---|---:|---|---|---|
| `/Users/cristrein/tradingview-mcp/my-strategy/...` | 110 | pesquisa/rulers privados | `PRIVATE_ROOT` / `TRADING_SYSTEM_ROOT` | `private(...)` / `ruler(...)` |
| `/Users/cristrein/tradingview-mcp/regime_turnstate_engine/...` | 81 | pesquisa RTSE | `TRADING_SYSTEM_ROOT` | `repo("regime_turnstate_engine", ...)` |
| `/Users/cristrein/tradingview-mcp/research/...` | 42 | lab research | `TRADING_SYSTEM_ROOT` | `repo("research", ...)` |
| `/Users/cristrein/tradingview-mcp/alert-bridge/...` | 8 | produção (gate) | `TRADING_SYSTEM_ROOT`/`LOG_ROOT` | `repo("alert-bridge", ...)` / `log(...)` |
| `/tmp/causal_segments_v10.json` | 65 | bootstrap reprodutível | `TEMP_ROOT` | `causal_segments()` |
| `/tmp/claude_recheck.paused` | 57 | **flag de produção (recheck)** | `TEMP_ROOT` | `tmp("claude_recheck.paused")` — **gate** |
| `/tmp/raw_features_2020_2026.jsonl` | 41 | cache research tmp | `TEMP_ROOT` | `tmp(...)` |
| `/tmp/plot_geometry.json`, `/tmp/XAU_1D_*.jsonl`, etc. | ~50 | scratch research | `TEMP_ROOT` | `tmp(...)` |
| `/Volumes/GUTS_ LACIE/TradingData/raw_replay/...` | ~55 | RAW replay (HD) | `RAW_DATA_ROOT` | `raw("raw_replay", ...)` |
| `/Volumes/GUTS_ LACIE/TradingData/slim_features/...` | 2 | SLIM (proibido) | — | não migrar (cluster HISTORICAL) |

## Lista priorizada de migração (opt-in, por ficheiro, com aprovação)
1. **EF v2 collectors (produto, não-runtime)** — baixo risco; adotar `external_factor()`/`raw()`. (runtime/plist = gate).
2. **Helpers partilhados em `scripts/`** que o produto chama.
3. **RTSE `validation/` (114 ficheiros)** — oportunístico; trocar 2 literais por ficheiro (`repo(...)` + `causal_segments()`), 3–5 primeiro como referência, validar output idêntico.
4. **`my-strategy/research/backtests/` + `research/` labs** — por último.
- **NUNCA** migrar sem plano/aprovação: `alert-bridge/` (produção), `/tmp/claude_recheck.paused` (flag de produção), qualquer runtime/plist. **Não quebrar D1A/Breakout Continuation.**

## Riscos
- `parents[N]` errado no resolver mudaria `TRADING_SYSTEM_ROOT` globalmente → mitigado por teste byte-idêntico.
- Migração de um ficheiro vivo sem validar output → regra: migrar por ficheiro + confirmar resultado idêntico.
- `/tmp/claude_recheck.paused` é controlo de produção → migrar só sob gate.

## Rollback
Adições puras. Rollback = apagar `config/`, `.env.example`, `tests/test_paths_resolution.py`, este doc. Nenhum comportamento existente depende deles ainda.

## Critérios de aceitação
- `python tests/test_paths_resolution.py` → OK (defaults byte-idênticos + env override).
- `python config/paths.py` imprime os 8 roots resolvidos + `causal_segments()` = `/tmp/causal_segments_v10.json`.
- `TRADING_SYSTEM_ROOT=/x` vira todos os roots derivados.
- Nenhum script vivo alterado; produção intocada; RTSE/EF v2 inalterados.

## Próximo (fora desta Fase)
Supabase (Fase 5) só APÓS portabilidade base. Migração real dos scripts = por ficheiro, com aprovação. Cold storage = passo dedicado.
