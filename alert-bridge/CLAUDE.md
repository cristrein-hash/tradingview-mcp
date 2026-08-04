# KARPATHY'S FOUR RULES — PASTE FIRST

1. Ask, do not assume.
   If something is unclear, ask before writing a single line.
   No silent guesses about intent, architecture, or requirements.

2. Simplest solution first.
   Implement the simplest thing that could work.
   No abstractions, flexibility, or extra systems unless explicitly requested.

3. Do not touch unrelated code.
   If a file, function, component, script, or config is not part of the current task, do not modify it — even if you think it could be improved.

4. Flag uncertainty explicitly.
   If you are not confident about an approach, technical detail, dependency, risk, or side effect, say so before proceeding.
   Confidence without certainty causes damage.

5. Communicate with objectivity, synthesis, and assertiveness.
   Be clear, direct, and useful.
   No filler, no fluff, no excessive explanations, no performative reasoning.
   Say what matters, what changed, what is blocked, and what should happen next.

# MAPA DO TRADER (2026-08-04)
O ficheiro `alert-bridge/trader_map.json` é o canal de 1ª classe das zonas/teses pré-declaradas pelo Cris.
Convenção de atualização: o Cris diz em chat ou via Telegram-bridge, p.ex. "marca zona 4066-4073 tese SHORT,
crítica, válida até sexta" → Claude edita o JSON e valida com `python3 trader_map.py --validate`, devolvendo
o mapa ativo para confirmação. Zonas expiram sozinhas (`validade`). Consumidores: e2_quality (secção no
briefing + prefixo de CONFLITO em sinais contra-tese) e vela_no_nivel.py (leitura de barra nas zonas críticas).
Sem mapa = comportamento byte-idêntico. NUNCA editar teses/zonas sem instrução explícita do Cris.
