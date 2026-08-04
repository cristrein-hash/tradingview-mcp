#!/usr/bin/env python3
"""VIGIA DE DEMANDA + JUÍZO DO READER (Cris 2026-07-28: "permite o reader julgar, não mecaniza os sinais,
deixa ele analisar reclaim legítimo"). Fundo previsto pelo Cris = 4050-4053 (primário); fallbacks 4044 e
4022-4043. O TOQUE é só um heads-up GEOGRÁFICO (olha aqui) — NÃO decide nada. Quando um reclaim se FORMA
na zona, chama O MESMO READER do E2 (render_composite + run_read, importados — nunca reader paralelo) sobre
o dossiê VIVO e devolve o JUÍZO dele sobre a legitimidade. 1 leitura Opus por barra 15M qualificante (dedup).
Read-only, 0 Telegram (advisory no chat via o vigia)."""
import sys, json, time, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
R = "/Users/cristrein/tradingview-mcp/"
sys.path.insert(0, R + "alert-bridge")
sys.path.insert(0, R + "my-strategy/strategies/xau_15m_long/reversal/CP_CAPITULATION")
import e2_quality as E2                      # O READER SANCIONADO (consome, não reconstrói)
import cp_engine_live as cp                  # atr_series verbatim
hm = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%d/%m %H:%M")

# ZONA (Cris 2026-07-30, pós revisão do chart via MCP): RANGE macro-estrutural 3995↔4116. A procura REAL é o
# ORDER BLOCK 3995-4010 (OB Detector v11), não o pivô 4042. Long estrutural = RECLAIM LEGÍTIMO no OB (fecho de
# volta acima de 4010) — o reader julga; o toque é só heads-up. Macro: petróleo↑ → DXY a recuperar → dólar a
# firmar = sobe a hipótese de o preço DESCER a testar o OB antes do repique. Boa chance de repique de alta lá.
# Mantenho também o teto CHoCH 4051 (reclaim de momentum) como 2ª zona qualificante.
# Cris 2026-07-31: "possível compra nesta região, qualquer reclaim genuíno sinalizado". Cobre as 3 zonas
# vivas: OB Detector 15M 4028-4036 (demanda real onde a retoma disparou), OB 4H 3995-4010 (estrutural profundo),
# e o teto CHoCH 4051 (momentum). Reclaim = fecho de volta acima do topo da zona; o reader julga a legitimidade.
DEMANDS = [(4028.0, 4036.66, "OB Detector 15M 4028-4036 (demanda real — reclaim acima de 4036 = juízo do reader)"),
           (3995.84, 4010.0, "OB demand 4H 3995-4010 (ESTRUTURAL profundo — reclaim acima de 4010 = juízo do reader)"),
           (4040.0, 4051.0, "teto CHoCH 4051 (reclaim de momentum acima de 4051 = juízo do reader)")]
# Cris 2026-08-03: "tendência claramente BEAR; o ouro vem fazer RETESTE nas demandas superiores antes de
# descer". Lado SHORT: toque na supply = heads-up; REJEIÇÃO real (tocou e FECHOU de volta abaixo da borda
# inferior, vela vermelha) = juízo do reader (agora com os blocos fade-sequência + compressão).
SUPPLIES = [(4047.0, 4062.0, "supply 1H 4047-4062 (reteste p/ VENDER — juízo do reader)"),
            (4065.0, 4072.0, "supply 15M 4065-4072 (reteste superior — juízo do reader)"),
            (4101.07, 4116.28, "OB Detector supply 4H 4101-4116 (reteste PREMIUM — Cris 2º cenário — juízo do reader)")]
TOUCH_BUF = 1.0

def bars(name, n=20):
    with open(R + f"my-strategy/core/bar_store/store/bars_{name}.jsonl", "rb") as f:
        f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 20000))
        rows = [json.loads(l) for l in f.read().decode(errors="ignore").splitlines() if l.strip() and l[0] == "{"]
    return rows[-n:]

def zone_of(low, close):
    for zl, zh, lab in DEMANDS:
        if low <= zh + TOUCH_BUF:               # tocou/entrou (wick inclui)
            return (zl, zh, lab)
    return None

def build_short_cand(zh, close, atr):
    sl = round(zh + 0.1 * atr, 2)
    r = round(sl - close, 2)
    if r <= 0: r = round(0.5 * atr, 2); sl = round(close + r, 2)
    tgt = round(close - 3 * r, 2)
    return {"direction": "SHORT", "rule": "zone_reject", "tf": "15",
            "entry": round(close, 2), "sl": sl, "target": tgt, "rr": round((close - tgt) / r, 2),
            "materiality": {"sl_atr": round(r / atr, 1) if atr else None, "confluence": None, "confluence_breakdown": {}}}


def build_long_cand(zl, close, atr):
    sl = round(zl - 0.1 * atr, 2)
    r = round(close - sl, 2)
    if r <= 0: r = round(0.5 * atr, 2); sl = round(close - r, 2)
    tgt = round(close + 3 * r, 2)
    return {"direction": "LONG", "rule": "zone_reclaim", "tf": "15",
            "entry": round(close, 2), "sl": sl, "target": tgt, "rr": round((tgt - close) / r, 2),
            "materiality": {"sl_atr": round(r / atr, 1) if atr else None, "confluence": None, "confluence_breakdown": {}}}

touched = {}; read_bars = set()          # touched[label] = bar_time do último toque (dedup por barra)
ZTOP = max(z[1] for z in DEMANDS)         # topo do bloco de demanda (re-arme só bem acima disto)
print(f"vigia+reader armado: fundo previsto 4050-4053 (+ fallbacks 4044, 4022-4043). Toque=heads-up; reclaim=juízo do reader.")
while True:
    try:
        b15 = bars("15m", 30)
        if len(b15) < 16:
            time.sleep(45); continue
        cur, prev = b15[-1], b15[-2]
        H = [b["h"] for b in b15]; L = [b["l"] for b in b15]; C = [b["c"] for b in b15]
        atr = cp.atr_series(H, L, C)[-1] or 6.0
        z = zone_of(cur["l"], cur["c"])
        # heads-up geográfico: 1× por ENTRADA na zona. touched[label]=1 quando tocada; só re-arma quando o
        # preço FECHA bem acima do bloco todo (ZTOP+12) — evita o flood de re-toque ao oscilar no bordo.
        if z and not touched.get(z[2]):
            touched[z[2]] = 1
            print(f"TOQUE na demanda {z[2]}: low {cur['l']} @ {hm(cur['t'])} (close {cur['c']}) — a aguardar reclaim; o reader julga a legitimidade")
        # gatilho de LEITURA (não veredito): RECLAIM REAL = tocou a zona e FECHOU de volta ACIMA da borda
        # superior (Cris 2026-07-28: só consultar o reader na viragem verdadeira, não em cada verde abaixo).
        reclaim_shaped = (z and cur["l"] <= z[1] + TOUCH_BUF and cur["c"] > z[1]
                          and cur["c"] > cur["o"])
        # cooldown de CONSULTA (29/07: preço a serrar no bordo pré-FOMC gerava leitura igual por barra):
        # re-consulta só se passaram >=90min OU o preço fez algo NOVO (fecho 6+ pts acima da última consulta).
        _lr = getattr(sys.modules[__name__], "_last_read", None)
        _novel = _lr is None or (cur["t"] - _lr[0]) >= 5400 or cur["c"] >= _lr[1] + 6.0

        def _novel_s(bar):
            # cooldown das consultas SHORT: 90min OU fecho 6+ pts ABAIXO da última consulta short
            _ls = getattr(sys.modules[__name__], "_last_read_s", None)
            if _ls is None or (bar["t"] - _ls[0]) >= 5400 or bar["c"] <= _ls[1] - 6.0:
                setattr(sys.modules[__name__], "_last_read_s", (bar["t"], bar["c"]))
                return True
            return False
        if reclaim_shaped and cur["t"] not in read_bars and _novel:
            setattr(sys.modules[__name__], "_last_read", (cur["t"], cur["c"]))
            read_bars.add(cur["t"])
            cand = build_long_cand(z[0], cur["c"], atr)
            print(f"RECLAIM A FORMAR-SE na {z[2]} (barra {hm(cur['t'])} close {cur['c']}) — a pedir juízo ao reader…")
            dsr = E2.load_dossier()
            if not dsr:
                print("   (reader: dossiê indisponível neste instante — re-tento na próxima barra)"); time.sleep(45); continue
            th = E2.run_read(cand, dsr)         # MESMA leitura Opus do E2
            if th.get("error"):
                print(f"   (reader falhou: {str(th.get('error'))[:60]} — re-tento próxima barra)")
            else:
                surf = E2.surfaced(th, cand)
                print(f"   JUÍZO DO READER — reclaim {'LEGÍTIMO ✅' if surf else 'AINDA NÃO / não converge ❌'}")
                print(f"   convergência {th.get('convergence')} · convicção {th.get('conviction')} · contexto pende {th.get('context_direction')}")
                print(f"   tese: {th.get('thesis')}")
                if th.get('conflicting_readings'):
                    print(f"   contra: {'; '.join(th.get('conflicting_readings')[:3])}")
                print(f"   níveis lidos: entry {cand['entry']} · SL {cand['sl']} · alvo {cand['target']} (RR {cand['rr']})")
        # ---- lado SHORT: reteste de supply (Cris 2026-08-03) ----
        for szl, szh, slab in SUPPLIES:
            if cur["h"] >= szl - TOUCH_BUF and not touched.get(slab):
                touched[slab] = 1
                print(f"TOQUE na {slab}: high {cur['h']} @ {hm(cur['t'])} (close {cur['c']}) — a aguardar rejeição; o reader julga")
            # rejeição real: tocou a supply e FECHOU de volta ABAIXO da borda inferior, vela vermelha
            rej = (cur["h"] >= szl - TOUCH_BUF and cur["c"] < szl and cur["c"] < cur["o"])
            if rej and (cur["t"], slab) not in read_bars and _novel_s(cur):
                read_bars.add((cur["t"], slab))
                cand = build_short_cand(szh, cur["c"], atr)
                print(f"REJEIÇÃO A FORMAR-SE na {slab} (barra {hm(cur['t'])} close {cur['c']}) — a pedir juízo ao reader…")
                dsr = E2.load_dossier()
                if dsr:
                    th = E2.run_read(cand, dsr)
                    if not th.get("error"):
                        surf = E2.surfaced(th, cand)
                        print(f"   JUÍZO DO READER — rejeição {'LEGÍTIMA p/ SHORT ✅' if surf else 'AINDA NÃO / não converge ❌'}")
                        print(f"   convergência {th.get('convergence')} · convicção {th.get('conviction')} · contexto pende {th.get('context_direction')}")
                        print(f"   tese: {th.get('thesis')}")
                        print(f"   níveis: entry {cand['entry']} · SL {cand['sl']} · alvo {cand['target']} (RR {cand['rr']})")
                break
        # re-arma só as DEMANDAS quando o preço fecha bem acima do bloco (saiu de vez); NÃO tocar no estado
        # das supplies (bug 2026-08-04: touched.clear() global re-disparava o toque da supply a cada barra
        # quando o preço estava acima de ZTOP+12 mas ainda no reteste da supply).
        if cur["c"] > ZTOP + 12:
            for _d in DEMANDS: touched.pop(_d[2], None)
        # re-arma supplies quando o preço cai bem abaixo delas (saiu de vez do reteste)
        if cur["c"] < min(s[0] for s in SUPPLIES) - 12:
            for _s in SUPPLIES: touched.pop(_s[2], None)
    except Exception as e:
        print(f"vigia+reader erro transitório: {type(e).__name__}:{str(e)[:50]}")
    time.sleep(45)
