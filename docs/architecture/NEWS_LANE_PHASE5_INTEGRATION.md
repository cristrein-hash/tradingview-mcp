# News Lane — Ponto de Integração (Fase 5 wiring) — 2026-07-16

Como consumir o **gate de news advisory** (`alert-bridge/news_gate.py`) nos consumidores. Complementa a
news lane já viva (collector @240s → `investinglive_news.json` → merge em `latest.json.news_live` +
escalada Telegram). Origem: teste de trade ao vivo 2026-07-16 (o trade apodreceu numa headline HI em zona
morta — o gate teria avisado). Ver `reference_session_volatility_windows`, `project_live_trade_test_20260716`.

## Princípio
**AVISO CONTEXTUAL, nunca bloqueio.** O gate informa; a decisão fica no humano/loop. Decisão do Cris
(2026-07-16). Determinístico, sem LLM.

## API
```python
from news_gate import read_gate   # alert-bridge/ no sys.path
g = read_gate()
# g = {
#   ok, stale(bool), fetch_age_s,
#   session,            # asia|dead_zone|london_strong|ny_open|ny|ny_late|other (UTC)
#   high_impact_now,    # headline urgency=high e idade<=15min
#   escalate,           # high_impact_now AND (sessão forte OU evento FF iminente)
#   ff_event_le_min,    # evento FF alto-impacto em 0..30min, senão None
#   headline,           # top item {title,keywords,age_min,...} ou None
#   reason,
#   advisory,           # string humana pronta a mostrar (ex.: "⚠️ HEADLINE HI ... · 🕐 zona morta")
# }
```
Nunca lança; sem snapshot devolve estado `ok=False`/`stale=True` seguro.

## Alvo 1 — Workflow de monitorização LIVE (VIVO, integração real)
No loop de monitorização (o que dispara trades via proxy — ex. o do desafio 2026-07-16), chamar `read_gate()`
a cada ciclo e **imprimir o `advisory`** por cima da leitura multi-TF, ANTES de decidir sinalizar:
```python
from news_gate import read_gate
g = read_gate()
print("NEWS:", g["advisory"])          # contexto por cima do multi-TF
# regra advisory (NÃO bloqueio): se g["session"]=="dead_zone" ou g["high_impact_now"] ou
# g["ff_event_le_min"] is not None -> CAUTELA extra antes de sinalizar (timing/regime).
# Se g["stale"] -> news lane atrasada, não confiar no gate como fresco.
```
Uso pretendido: o advisory entra no raciocínio de "é boa altura para sinalizar?" — lição do trade que
entrou em zona morta sem catalisador. **Não automatiza a decisão; enriquece-a.**

## Alvo 2 — Engines XAU 4H/15M (research/dormentes)
**Honestidade:** um gate de news LIVE **não tem significado em backtest histórico** (não há RSS do passado;
seria lookahead/vazio). Por isso:
- **NÃO** cablar `read_gate()` na lógica de backtest/scan histórico dos engines.
- Quando um engine for **live-runtime** (a decidir em tempo real), chamar `read_gate()` no momento da decisão
  como camada advisory (mesmo padrão do Alvo 1): gate de timing/sessão + flag de headline HI.
- Ponto de integração recomendado: a fronteira "engine produz candidato → decisão de execução live". É aí
  (e só aí) que o contexto de news live é válido. O helper fica disponível; a decisão de o ligar é por-engine
  quando cada um for ativado para runtime.

## Fonte de frescura
- **Fresco (≤4min):** ler `external_factors_v2/snapshots/investinglive_news.json` diretamente (o que `read_gate`
  faz) — para decisões intra-barra 15M.
- **Contexto macro (≤30min):** `latest.json.news_live` — para consumidores que já leem o snapshot macro.
- `read_gate()` marca `stale=True` se `fetch_age_s > 900s` (1 barra 15M) ou `fetch_ok=False`.

## Não-objetivos (fora de scope até decisão futura)
- Auto-bloqueio de sinais (decisão = aviso contextual, não trava).
- Interpretação por LLM do conteúdo da headline (o gate é determinístico por keyword/urgency; escalada LLM =
  event-driven futuro, se desejado).
- Mapeador empírico de volatilidade/sessão (tarefa futura dedicada — os buckets atuais são a perceção do Cris).
