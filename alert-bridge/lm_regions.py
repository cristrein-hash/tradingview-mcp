#!/usr/bin/env python3
"""LM_REGIONS — P1 da Máquina LM (arquitetura aprovada Cris 29/08). Detetor de REGIÕES de liquidez por
LIVRO DE EVIDÊNCIA por nível — sem fractal, sem ATR, sem confirmação de velas.
consolidation_check corrido (token): capacidade nova anunciada; CONSOME store (bars 5m/15m, pine_boxes,
smc_labels, bubbles, nas) — leitura direta de indicadores, nada re-derivado.

LÓGICA (assinatura medida nas 13 regiões do Cris, region_study_v2):
- Candidato a nível = extremo de pavio 5M (existe no fecho da própria vela; zero espera).
- Agrupamento por proximidade em PONTOS (TOL=3.0, largura medida nas regiões do Cris — parâmetro
  DECLARADO, a re-derivar quando o regime de volatilidade mudar; nunca ATR).
- EVIDÊNCIA por nível: toques 5M (pavio a ±TOL) · respeitos (sem fecho além) · BOLHAS no instante do
  toque · NAS no toque · zona OB v11 · zona SMC · EQH/EQL · extremo de SESSÃO (Asia 00-08/London
  08-13/NY 13-21 Lisboa, calculado das velas) · borda PO3.
- SCORE = nº de FATORES distintos; região VÁLIDA se score>=3 E >=2 toques respeitados (ou fator de
  indicador/sessão quando é nível fresco por testar).
- VIDA (regra Cris): morre SÓ por atravessou-e-ficou = fecho 15M além de TOL e SEM fecho de volta nas
  6 barras 15M seguintes (SWEEP_BARS canónico). Fura-e-volta = vivo.
- LADO: nível abaixo do preço = BUY (SSL); acima = SELL (BSL). py3.9 stdlib."""
import json
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
S = REPO / "my-strategy/core/bar_store/store"
LX = dt.timezone(dt.timedelta(hours=1))
TOL = 3.0
DEATH_BARS = 6           # SWEEP_BARS canónico (fecho além sem regresso em 6×15M = morto)
LOOK5 = 3 * 86400        # evidência dos últimos 3 dias (janela do estudo de região)


def _jl(p):
    try:
        return [json.loads(l) for l in open(p) if l.strip()]
    except Exception:
        return []


def _zones(fname, names):
    try:
        d = json.load(open(S / fname)).get("data") or {}
    except Exception:
        return []
    out = []
    for st in d.get("studies") or []:
        if any(n in (st.get("name") or "") for n in names):
            out += [(z["low"], z["high"]) for z in (st.get("zones") or []) if z.get("low") is not None]
    return out


def _eq_labels():
    try:
        d = json.load(open(S / "smc_labels_15.json")).get("data") or {}
    except Exception:
        return []
    return [l["price"] for st in (d.get("studies") or []) for l in (st.get("labels") or [])
            if str(l.get("text", "")).upper().startswith(("EQH", "EQL")) and l.get("price")]


def _sess(t):
    h = dt.datetime.fromtimestamp(t, LX).hour
    return "ASIA" if h < 8 else ("LONDON" if h < 13 else "NY")


def session_extremes(b5, t_now, days=2):
    out = []
    cur = None
    for x in b5:
        if not (t_now - days * 86400 <= x["t"] < t_now):
            continue
        key = (dt.datetime.fromtimestamp(x["t"], LX).date(), _sess(x["t"]))
        if cur is None or cur[0] != key:
            if cur:
                out.append(cur)
            cur = [key, x["h"], x["l"]]
        else:
            cur[1] = max(cur[1], x["h"]); cur[2] = min(cur[2], x["l"])
    if cur:
        out.append(cur)
    return out


def regions_at(b5, b15, t_now, price):
    """Regiões válidas no instante t_now (b5/b15 JÁ cortados a t<=t_now pelo chamador).
    Devolve [{level, side, score, factors, touches, alive}] ordenado por |level-price|."""
    w5 = [x for x in b5 if x["t"] >= t_now - LOOK5]
    if len(w5) < 50:
        return []
    ob = _zones("pine_boxes_15.json", ["OB Detector"])
    smcz = _zones("pine_boxes_15.json", ["Smart Money"])
    po3 = _zones("pine_boxes_15.json", ["Power of Three"])
    eq = _eq_labels()
    bub = {r["t"] for r in _jl(S / "bubbles_15m.jsonl")}
    nas = {r["t"] for r in _jl(S / "nas_15m.jsonl")}
    sess = session_extremes(b5, t_now)
    # candidatos: extremos de pavio 5M agrupados por TOL
    lows = sorted(x["l"] for x in w5)
    highs = sorted(x["h"] for x in w5)

    def clusters(vals):
        """Agrupa por SPAN (v - primeiro do cluster <= TOL) — chain-merge por gap fundia 3 dias de
        pavios num cluster gigante (mesmo bug corrigido no liquidity_map a 27/08)."""
        out = []
        for v in vals:
            if out and v - out[-1][0] <= TOL:
                out[-1].append(v)
            else:
                out.append([v])
        return [c for c in out if len(c) >= 2]

    regions = []
    for side, vals, wick in (("BUY", clusters(lows), "l"), ("SELL", clusters(highs), "h")):
        for c in vals:
            b_lo, b_hi = round(min(c), 2), round(max(c), 2)      # BANDA real (min/max dos pavios)
            lv = b_hi if side == "BUY" else b_lo                  # borda do lado do preço = onde a limit toca 1º

            # evidência
            touches = [x for x in w5 if abs(x[wick] - lv) <= TOL]
            resp = [x for x in touches if not ((x["c"] < lv - TOL) if side == "BUY" else (x["c"] > lv + TOL))]
            factors = []
            if len(resp) >= 2:
                factors.append(f"toques={len(resp)}")
            bt = sum(1 for x in resp if (x["t"] - x["t"] % 900) in bub or x["t"] in bub)
            if bt:
                factors.append(f"bolhas={bt}")
            nt = sum(1 for x in resp if (x["t"] - x["t"] % 900) in nas)
            if nt:
                factors.append(f"nas={nt}")
            if any(z[0] - TOL <= lv <= z[1] + TOL for z in ob):
                factors.append("OB")
            if any(z[0] - TOL <= lv <= z[1] + TOL for z in smcz):
                factors.append("SMC")
            if any(abs(p - lv) <= TOL for p in eq):
                factors.append("EQ")
            if any(abs(lv - s[1]) <= TOL or abs(lv - s[2]) <= TOL for s in sess):
                factors.append("SESSAO")
            if any(abs(lv - z[0]) <= TOL or abs(lv - z[1]) <= TOL for z in po3):
                factors.append("PO3")
            # vida (regra Cris, relativa ao PRESENTE): conta o ESTADO FINAL, não a história — o preço
            # pode ter estado do outro lado ANTES de o nível se formar. Morto só se o ÚLTIMO fecho-além
            # não teve regresso em DEATH_BARS e nada de novo o reviveu.
            w15 = [x for x in b15 if x["t"] >= t_now - LOOK5]
            alive = True
            last_beyond = None
            for i, x in enumerate(w15):
                beyond = (x["c"] < lv - TOL) if side == "BUY" else (x["c"] > lv + TOL)
                if beyond:
                    last_beyond = i
            if last_beyond is not None:
                back = any(((y["c"] >= lv - TOL) if side == "BUY" else (y["c"] <= lv + TOL))
                           for y in w15[last_beyond + 1:last_beyond + 1 + DEATH_BARS])
                if not back:
                    alive = False
            score = len(factors)
            ok_side = (lv < price) if side == "BUY" else (lv > price)
            if alive and ok_side and score >= 3:
                regions.append(dict(level=lv, band=[b_lo, b_hi], side=side, score=score,
                                    factors=factors, touches=len(resp)))
    # dedup por nível (fica o de maior score)
    # candidatos HTF: bordas de zonas OB/SMC (sem exigir cluster de toques) — niveis frescos por testar
    for z in ob + smcz:
        for side, lv in (("BUY", z[1]), ("SELL", z[0])):
            ok_side = (lv < price) if side == "BUY" else (lv > price)
            if not ok_side:
                continue
            if any(abs(lv - r["level"]) <= TOL and r["side"] == side for r in regions):
                continue
            factors = ["OB/SMC_zona"]
            if any(abs(lv - s_[1]) <= TOL or abs(lv - s_[2]) <= TOL for s_ in sess):
                factors.append("SESSAO")
            if any(abs(p - lv) <= TOL for p in eq):
                factors.append("EQ")
            if any(abs(lv - z2[0]) <= TOL or abs(lv - z2[1]) <= TOL for z2 in po3):
                factors.append("PO3")
            bt = sum(1 for x in w5 if abs((x["l"] if side == "BUY" else x["h"]) - lv) <= TOL
                     and ((x["t"] - x["t"] % 900) in bub))
            if bt:
                factors.append(f"bolhas={bt}")
            if len(factors) >= 2:                     # zona de indicador + 1 confluência = nível HTF fresco
                regions.append(dict(level=round(lv, 2), band=[round(min(z), 2), round(max(z), 2)],
                                    side=side, score=len(factors), factors=factors, touches=0))
    # 3) FLIP DE POLARIDADE: nível cujo lado original foi atravessado-e-ficou vira nível do lado oposto
    #    (ex-suporte = resistência). Implementação: para clusters MORTOS no lado original, se o preço está
    #    agora do outro lado, renascem com side invertido (fatores mantidos, +flip).
    #    (a morte por estado-final já deixa o nível fora do lado original; aqui reavaliamos o oposto)
    for side_o, vals, wick in (("BUY", clusters(lows), "l"), ("SELL", clusters(highs), "h")):
        for c in vals:
            b_lo, b_hi = round(min(c), 2), round(max(c), 2)
            side_n = "SELL" if side_o == "BUY" else "BUY"
            lv = b_lo if side_n == "SELL" else b_hi
            ok_side = (lv > price) if side_n == "SELL" else (lv < price)
            if not ok_side:
                continue
            if any(abs(lv - r["level"]) <= TOL and r["side"] == side_n for r in regions):
                continue
            # so flippa se o lado ORIGINAL morreu (preco atravessou-e-ficou do outro lado)
            w15_ = [x for x in b15 if x["t"] >= t_now - LOOK5]
            lb = None
            for i, x in enumerate(w15_):
                beyond = (x["c"] < b_lo - TOL) if side_o == "BUY" else (x["c"] > b_hi + TOL)
                if beyond:
                    lb = i
            if lb is None:
                continue
            back = any(((y["c"] >= b_lo - TOL) if side_o == "BUY" else (y["c"] <= b_hi + TOL))
                       for y in w15_[lb + 1:lb + 1 + DEATH_BARS])
            if back:
                continue
            touches_n = [x for x in w5 if abs((x["l"] if side_n == "BUY" else x["h"]) - lv) <= TOL
                         and x["t"] > w15_[lb]["t"]]
            factors = ["FLIP_polaridade"]
            if len(touches_n) >= 1:
                factors.append(f"toques_novo_lado={len(touches_n)}")
            if any(z[0] - TOL <= lv <= z[1] + TOL for z in ob):
                factors.append("OB")
            if any(abs(lv - s_[1]) <= TOL or abs(lv - s_[2]) <= TOL for s_ in sess):
                factors.append("SESSAO")
            if len(factors) >= 2:
                regions.append(dict(level=round(lv, 2), band=[b_lo, b_hi], side=side_n,
                                    score=len(factors), factors=factors, touches=len(touches_n)))
    regions.sort(key=lambda r: (-r["score"], abs(r["level"] - price)))
    ded = []
    for r in regions:
        if not any(abs(r["level"] - d["level"]) <= TOL and r["side"] == d["side"] for d in ded):
            ded.append(r)
    ded.sort(key=lambda r: abs(r["level"] - price))
    return ded


if __name__ == "__main__":
    import sys
    b5 = sorted(_jl(S / "bars_5m.jsonl"), key=lambda x: x["t"])
    b15 = sorted(_jl(S / "bars_15m.jsonl"), key=lambda x: x["t"])
    if "--selftest" in sys.argv:
        t = []
        rs = regions_at(b5, b15, b5[-1]["t"], b5[-1]["c"]) if b5 else []
        t.append(("devolve lista", isinstance(rs, list)))
        t.append(("lados corretos", all((r["level"] < b5[-1]["c"]) == (r["side"] == "BUY") for r in rs)))
        t.append(("scores>=3", all(r["score"] >= 3 for r in rs)))
        # causalidade: prefixo não muda com futuro
        if len(b5) > 600:
            cut = b5[-300]["t"]
            a = regions_at([x for x in b5 if x["t"] <= cut], [x for x in b15 if x["t"] <= cut], cut, 0) 
            b = regions_at([x for x in b5 if x["t"] <= cut], [x for x in b15 if x["t"] <= cut], cut, 0)
            t.append(("determinístico", a == b))
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        print("selftest", "PASS" if all(r for _, r in t) else "FAIL")
        sys.exit(0 if all(r for _, r in t) else 1)
    rs = regions_at(b5, b15, b5[-1]["t"], b5[-1]["c"])
    print(f"AGORA ({b5[-1]['c']}): {len(rs)} regiões válidas")
    for r in rs[:8]:
        print(f"  {r['side']} {r['level']} score{r['score']} {r['factors']}")
