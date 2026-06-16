# CANONICAL TRADE PLOTTING — XAU 4H (fonte única de verdade)

**Status:** CANÔNICO · **Atualizado:** 2026-06-16 · **Escopo:** plotar trades (entries de estratégia/backtest/candidatos) num chart TradingView via MCP `draw_shape`.

> Esta é a **única** referência canônica de plotagem. Onde memória/docs antigos divergirem (em especial sobre `stopLevel`/`profitLevel`), **este documento prevalece**. Script de referência vivo: `alert-bridge/draw_xau_4h_trades.py`.

---

## 0. Regra de ouro (o bug que custou tempo)

`long_position.overrides.stopLevel` e `profitLevel` são **OFFSETS EM TICKS** a partir do entry — **NÃO preços absolutos**.

- ❌ **ERRADO (BUG):** `overrides = {"stopLevel": 2390.0, "profitLevel": 2430.0}` → o TradingView interpreta como `entry ± preço/100`, gerando níveis-artefato (descoberto 2026-06-11; custou arrastar 26 targets à mão na L2 v0.3).
- ✅ **CERTO:** converter para ticks com `mintick = 0.01` (XAU):
  ```python
  stopLevel_ticks   = round((entry_price - stop_price)  / 0.01)
  profitLevel_ticks = round((target_price - entry_price) / 0.01)
  ```

---

## 1. Sempre 2 shapes por trade

Nunca usar `vertical_line` + texto como substituto de posição. Para CADA trade:

### Shape 1 — `long_position` (a caixa nativa)
```python
draw_shape({
  "shape": "long_position",
  "point":  {"time": entry_time, "price": entry_price},   # entry
  "point2": {"time": exit_time,  "price": target_price},  # ⭐ point2 NO TARGET → forma a caixa cheia
  "overrides": json.dumps({
    "stopLevel":   price_to_ticks_offset(entry_price, stop_price),    # offset em TICKS
    "profitLevel": price_to_ticks_offset(entry_price, target_price),  # offset em TICKS
  }),
})
```
- `point2` deve ficar **no target** (não no entry) — define a largura/altura da caixa. Usar `point2` no entry só pra largura **não** renderiza a caixa cheia.
- **Nunca** preço absoluto em `stopLevel`/`profitLevel` (ver §0).
- **Não** inventar overrides extras (`profitBackgroundTransparency`, `linewidth`, `showPriceLabels`, etc.) — o default do TV já renderiza.

### Shape 2 — `text` (o label)
```python
R_dollars = entry_price - stop_price          # 1R em USD
label_y   = entry_price + 0.5 * R_dollars     # 0.5R acima do entry (colado ao trade)
draw_shape({
  "shape": "text",
  "point": {"time": entry_time, "price": label_y},
  "text":  f"#{trade_id}",                      # ver §3
  "overrides": json.dumps({
    "color":    "#1a8917" if close_R > 0 else "#cc0000",   # ver §3
    "bold":     True,
    "fontsize": 12,
  }),
})
```

---

## 2. `long_position` — pontos e overrides

| Campo | Valor |
|---|---|
| `point.time` | `entry_time` (unix) |
| `point.price` | `entry_price` |
| `point2.time` | `exit_time` (ou target_time visual) |
| `point2.price` | `target_price` |
| `overrides.stopLevel` | `round((entry − stop)/mintick)` (ticks) |
| `overrides.profitLevel` | `round((target − entry)/mintick)` (ticks) |
| `mintick` (XAU) | **0.01** |

---

## 3. Labels

- **Texto padrão:** `#<número cronológico do trade>` (índice estável no conjunto; `#1` = mais antigo; preservado entre janelas/replots). Não usar R/métricas no texto salvo pedido explícito do Cris. Sem "BLOCK p…".
- **Cor (winner/loser):** aplicada **só no label de texto**, nunca no widget `long_position`.
  - **winner** (`close_R > 0`) → **`#1a8917`** (verde)
  - **loser** (`close_R <= 0`) → **`#cc0000`** (vermelho)
- **Posição:** `price = entry_price + 0.5 * R_dollars` (0.5R acima do entry — colado ao trade, sem poluir; independe do tamanho do target).
- `bold = True`, `fontsize = 12`.
- **Candidatos SEM outcome** (ainda não resolvidos): cor neutra (ex. azul `#1565c0`) é aceitável, pois não há winner/loser ainda (ver `plot_new_only.py`).

---

## 4. SL/Target para candidatos SEM exit definido

Política confirmada pelo Cris (2026-06-16):
- **SL estrutural** = low da zona de demanda Custom OB tocada (ou swing low recente) **− 0.1 × ATR14**.
- **TARGET = +3R** = `entry + 3 × (entry − SL)`.

Se a fonte tiver política própria (V_stair, target dinâmico), usar a dela e **declarar**. Em dúvida, perguntar — não inventar.

---

## 5. Verificação (NUNCA por screenshot)

- Verificar por: **`success`** de cada `draw_shape` + **`draw_list`** (count + `entity_ids`).
- **Não** capturar screenshot como verificação operacional. O Cris vê o TradingView diretamente. Screenshot só se ele pedir explicitamente — e ainda assim não como conferência da própria plotagem.

---

## 6. Chart cleanup

- **Não apagar desenhos sem autorização explícita.**
- O Cris limpa o chart manualmente entre plotagens, salvo ordem contrária. Chart vazio antes de plotar = estado esperado, não anomalia.

---

## 7. Helper canônico

`alert-bridge/draw_xau_4h_trades.py`:
- `price_to_ticks_offset(entry_price, level_price, mintick=0.01)` → `int(round(abs(level − entry)/mintick))`; valida mintick>0 e preços finitos (hard stop).
- Desenha `long_position` (ticks) + label verde/vermelho por `close_R`.
- Constantes de exit default (se a fonte não tiver SL/TP): `STOP_R_MULT=1.0`, `TARGET_R_MULT=2.7`, `HORIZON_BARS=10` — **declarar** quando usadas.

Antes de plotar QUALQUER trade: ir **direto** a este helper / esta referência. Não auditar o MCP do zero nem inventar marcador.

### Validações obrigatórias do helper (hard stop em violação)
- `entry_price > stop_price` (long).
- `target_price > entry_price`.
- ticks resultantes **> 0**.
- campos faltando (`entry`/`stop`/`target`/`time`) → hard stop, não plotar.

---

## 8. Teste / dry-run (sem chart real)

Teste canônico: `alert-bridge/test_canonical_plotting.py`. Caso de referência:

| input | valor |
|---|---|
| entry | 2400 |
| stop | 2390 |
| target | 2430 |
| mintick | 0.01 |

Esperado:
- `stopLevel = round((2400−2390)/0.01) = 1000`
- `profitLevel = round((2430−2400)/0.01) = 3000`
- label verde (`#1a8917`) se `close_R > 0`; vermelho (`#cc0000`) se `close_R <= 0`.

---

## 9. Referências SUPERSEDED (não usar como autoridade de overrides)

- `memory/reference_trade_plotting_canonical.md` — o **bloco de código que mostra `stopLevel`/`profitLevel` como PREÇO ABSOLUTO é OBSOLETO** (pré-2026-06-11). Tudo o mais (2 shapes, label 0.5R acima, verde/vermelho, sem screenshot) continua válido. **Para overrides, usar ESTE doc (ticks).**
- `candidates/xau_4h_reversal_v1_4g_rws_a6/plot_script.py` — **DEPRECATED**: usa preço absoluto em `overrides` (BUG). Não executar; ver banner no próprio arquivo.
- `memory/feedback_canonical_trade_plotting.md` — correto (já diz ticks); aponta para este doc.

---

*Fontes: `alert-bridge/draw_xau_4h_trades.py`, `memory/feedback_canonical_trade_plotting.md`, `memory/reference_long_position_overrides_ticks_bug.md`, `…/L1_EMA21_CONTINUATION/reports/plot_new_only.py`.*
