#!/usr/bin/env python3
"""FONTE ÚNICA DE VERDADE — polaridade context-dependente das Market Order Bubbles (Leviathan).

Cris 2026-07-31: um sinal do claude_recheck bloqueou um LONG de reversão-em-demanda por "sem cluster de
compra", tratando sell-bubbles como bearish — ERRADO. A polaridade das bubbles é CONTEXTO-DEPENDENTE
(validado empiricamente 2026-06-03, n=1163 XAU 4H; memory feedback_bubbles_polarity_rule). Este módulo
exporta a regra canónica como STRING, importada pelos DOIS caminhos vivos (claude_recheck.py + e2_quality.py)
— renderizam os mesmos bytes, logo NÃO podem voltar a divergir. Sem lógica numérica no caminho vivo (a
leitura é feita pelo LLM contra esta regra); o helper classify_bubble_context fica disponível mas NÃO ligado.
"""

BUBBLE_POLARITY_RULE = """REGRA DE POLARIDADE DE BUBBLES (Market Order Bubbles/Leviathan — validada empiricamente 2026-06-03, n=1163 XAU 4H; memory feedback_bubbles_polarity_rule). Bubbles = ordens MARKET agressivas. O sinal NÃO é a cor por si só — é se a agressão está a ser ABSORVIDA num nível estrutural (reversão) ou a CONTINUAR com a perna (pullback). A polaridade FLIP pelo CONTEXTO: PRIMEIRO classifica o contexto do setup, DEPOIS aplica a polaridade. NUNCA usar 'sell-bubble = bearish' nem 'LONG exige buy-cluster' como regra fixa — foi esse o bug de 2026-06-03.
Mapeamento cru (correto, não confundir com o sinal): BUY(verde)=plot_0/plot_2/plot_4, SELL(vermelho)=plot_6/plot_8/plot_10 (small/med/large).

CLASSIFICA O CONTEXTO PRIMEIRO, depois lê a polaridade:
• REVERSAL-EM-FUNDO (drawdown profundo / capitulação / fundo genuíno a tocar DEMANDA, sobretudo 4H/1D; RSI oversold/reset; opcional CHoCH up): SELL-bubble recente = POSITIVO/BULLISH (agressão vendedora no low ABSORVIDA por limit-buyers = acumulação). BUY-bubble aqui = ANTI-PADRÃO (exaustão de topo local). → Um LONG de reversão-em-fundo com cluster SELL absorvido está CONFIRMADO pelo fluxo, NÃO bloqueado por 'falta de buy-cluster'.
• PULLBACK EM UPTREND CONFIRMADO (FRAME/regime BULL, toque de demanda em uptrend estabelecido, 1º pullback a amadurecer): BUY-bubble recente = POSITIVO/BULLISH (iniciativa compradora a retomar). SELL-bubble = neutro.
• REVERSAL-EM-TOPO (SHORT em SUPPLY; RSI overbought; opcional CHoCH dn): BUY-bubble recente = sinal BEARISH (agressão compradora no high ABSORVIDA por limit-sellers = distribuição). SELL-bubble aqui = ANTI-PADRÃO.
• BREAKOUT / NEWS-VERTICAL: agressão no sentido da perna = combustível de continuação; contra a perna = faca.

GUARDA (não confundir ABSORÇÃO com FACA): 'absorvido' exige RECLAIM/HOLD/V ao longo de >=2 barras FECHADAS no nível. Um movimento vertical news-driven (FOMC-spike, high_impact_now, 1º toque sem reclaim) que ATRAVESSA o nível NÃO é absorção — é faca/continuação (FALLING_KNIFE). Só chamar 'absorção' com reclaim confirmado."""


def classify_bubble_context(dossier):
    """Helper determinístico (DISPONÍVEL, NÃO ligado ao gate vivo — a leitura viva é do LLM contra a regra).
    Classifica o contexto do setup a partir de campos já presentes no dossiê e devolve o lado bullish esperado.
    Retorna {"context", "bullish_side", "why"}. Tolerante a campos ausentes."""
    d = dossier or {}
    def g(*keys, default=None):
        cur = d
        for k in keys:
            if not isinstance(cur, dict):
                return default
            cur = cur.get(k)
        return cur if cur is not None else default
    regime = str(g("regime", default="") or g("frame", default="")).upper()
    zone_below_src = str(g("zone_below", "src", default="") or "").lower()
    zone_above_src = str(g("zone_above", "src", default="") or "").lower()
    rsi = g("rsi")
    pos = g("pos_in_leg")
    high_impact = bool(g("high_impact_now", default=False))
    if high_impact:
        return {"context": "news_vertical", "bullish_side": None,
                "why": "high_impact_now — agressão = continuação/faca, não absorção (aplicar GUARDA)"}
    demand_below = "demand" in zone_below_src
    supply_above = "supply" in zone_above_src
    oversold = isinstance(rsi, (int, float)) and rsi <= 38
    overbought = isinstance(rsi, (int, float)) and rsi >= 62
    if demand_below and (("BEAR" in regime or "RANGE" in regime) or oversold or (isinstance(pos, (int, float)) and pos <= 0.15)):
        return {"context": "reversal_bottom", "bullish_side": "sell",
                "why": "demanda + regime down/range ou RSI oversold/pos-baixa = reversão-em-fundo → SELL-absorção=bullish"}
    if "BULL" in regime and demand_below:
        return {"context": "pullback_uptrend", "bullish_side": "buy",
                "why": "regime BULL + toque de demanda = pullback em uptrend → BUY=bullish"}
    if supply_above and (("BULL" in regime or "RANGE" in regime) or overbought):
        return {"context": "reversal_top", "bullish_side": "buy_absorbed_bearish",
                "why": "supply + regime up/range ou RSI overbought = reversão-em-topo → BUY-absorção=bearish(short)"}
    return {"context": "indeterminado", "bullish_side": None,
            "why": "sem classificação clara — deixar o LLM ler contra a regra sem forçar polaridade"}


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        cases = [
            ({"regime": "BEAR", "zone_below": {"src": "Custom OB Detector demand"}, "rsi": 34}, "reversal_bottom"),
            ({"regime": "BULL", "zone_below": {"src": "demand"}, "rsi": 50}, "pullback_uptrend"),
            ({"regime": "RANGE", "zone_above": {"src": "supply"}, "rsi": 66}, "reversal_top"),
            ({"high_impact_now": True, "regime": "BEAR"}, "news_vertical"),
        ]
        ok = True
        for dsr, exp in cases:
            got = classify_bubble_context(dsr)["context"]
            flag = "OK" if got == exp else "FAIL"
            if got != exp:
                ok = False
            print(f"  [{flag}] esperado={exp} obtido={got}")
        assert "REVERSAL-EM-FUNDO" in BUBBLE_POLARITY_RULE and "GUARDA" in BUBBLE_POLARITY_RULE
        print("selftest PASS" if ok else "selftest FAIL")
        sys.exit(0 if ok else 1)
    print(BUBBLE_POLARITY_RULE)
