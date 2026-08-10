#!/usr/bin/env python3
"""TRACKER DE POLARIDADE PERSISTENTE (Cris 2026-08-10: "manutenção da leitura ativa das supply/demanda
furadas como região de provável pullback — lei de price action, implementar e validar a sério").

LEI VALIDADA (polarity_hold_study_v2, DA-auditado): uma ex-SUPPLY furada segura como SUPORTE no pullback
~62-64% vs ~52% de um nível aleatório = +10-12pp de edge REAL (com força/leg-impulso = +12pp). Espelho:
ex-DEMAND furada = resistência ~60%.

O PROBLEMA que resolve: o ob_watch só via a polaridade ENQUANTO a caixa OB existia; quando o OB Detector
removia a caixa (mitigação), a zona sumia — mas a POLARIDADE DO NÍVEL PERMANECE (o erro "supões demais" do
Claude, Cris 10/08). Este tracker PERSISTE a zona furada independentemente da caixa, e invalida-a só quando
o preço a perde de facto (fecho além por D·ATR).

Só FACTOS (nada inventado): tipo real DEMAND/SUPPLY do OB Detector (all_boxes.text via ob_watch._read_ob) +
fecho real das barras do store. D_ATR=1.0 = distância de invalidação VALIDADA no estudo (não arbitrária).
py3.9 stdlib. Single-writer: update() chamado 1× por ciclo pelo candle_reader; ob_watch/vela só LEEM."""
import os, json, time
from pathlib import Path
import ob_watch

BASE = Path(__file__).resolve().parent
STORE = BASE.parent / "my-strategy/core/bar_store/store"
STATE = BASE / ".polarity_state"; STATE.mkdir(exist_ok=True)
ZF = STATE / "zones.json"
CATF = STATE / "catalog.json"                       # catálogo de supplies/demands VISTOS (sobrevive à caixa sumir)
D_ATR = 1.0                                         # invalidação = fecho além da zona por D·ATR (validado v2)
NEAR_PTS = float(os.environ.get("POLARITY_NEAR_PTS") or 80.0)
# DESLIGADO POR DEFEITO (2026-08-10): a "lei de polaridade" NÃO passou validação — o DA provou que o edge
# (+12pp) era ARTEFACTO de ancoragem do null (edge real ≈ −2,7pp; ex-supply NÃO segura melhor que um nível
# aleatório na mesma posição). Não corre live com edge falso. Requer POLARITY_ON=1 explícito para reativar
# (só depois de a lei ser genuinamente demonstrada). Ver project_polarity_tracker_live (estado: REFUTADO).
ENABLED = os.environ.get("POLARITY_ON", "") == "1"
TFS = ("15", "60")


def _bars(n=60):
    try:
        rows = [json.loads(l) for l in open(STORE / "bars_15m.jsonl") if l.strip() and l[0] == "{"]
    except Exception:
        return []
    return [b for b in rows[-n:] if all(k in b for k in ("o", "h", "l", "c", "t"))]


def _atr14(bars):
    if len(bars) < 15:
        return 5.0
    trs = []
    for i in range(1, len(bars)):
        h, l, pc = bars[i]["h"], bars[i]["l"], bars[i - 1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-14:]) / 14 if trs else 5.0


def _load(f):
    try:
        return json.loads(f.read_text())
    except Exception:
        return []


def _write(f, obj):
    try:
        tmp = f.with_suffix(".tmp"); tmp.write_text(json.dumps(obj, ensure_ascii=False)); os.replace(tmp, f)
    except Exception:
        pass


def load_zones():
    return _load(ZF)


def _save(zs):
    _write(ZF, zs)


def _overlaps(a_lo, a_hi, b_lo, b_hi):
    return not (a_hi < b_lo or a_lo > b_hi)


def update():
    """Chamar 1× por ciclo (single-writer). Regista novas polaridades furadas + invalida as que falharam."""
    if not ENABLED:
        return []
    bars = _bars(60)
    if len(bars) < 15:
        return load_zones()
    closes = [b["c"] for b in bars]
    cmax, cmin, last = max(closes), min(closes), closes[-1]
    atr = _atr14(bars)
    zones = load_zones()
    keys = {(round(z["low"], 1), round(z["high"], 1)) for z in zones}
    # 0) CATALOGAR supplies/demands VISTOS agora (first-seen) — sobrevive à caixa OB sumir depois.
    cat = {tuple(map(float, k.split("|"))): v for k, v in (_load(CATF) or {}).items()} if CATF.exists() else {}
    for tf in TFS:
        for z in ob_watch._read_ob(tf):
            lo, hi, txt = float(z["low"]), float(z["high"]), z["text"]
            typ = "SUPPLY" if "SUPPLY" in txt else ("DEMAND" if "DEMAND" in txt else None)
            if typ is None:
                continue
            ck = (round(lo, 1), round(hi, 1))
            if ck not in cat:
                cat[ck] = {"low": lo, "high": hi, "type": typ, "tf": tf, "seen": int(time.time())}
    # 1) REGISTAR polaridade a partir do CATÁLOGO (não só do OB atual): supply furada (fecho recente > topo)
    #    = suporte; demand furada (fecho recente < fundo) = resistência. Vale mesmo sem a caixa OB viva.
    for ck, c in cat.items():
        if ck in keys:
            continue
        lo, hi, typ = c["low"], c["high"], c["type"]
        if typ == "SUPPLY" and cmax > hi:
            zones.append({"low": lo, "high": hi, "type": "ex_supply_demand", "tf": c.get("tf"),
                          "broken_ts": int(time.time())}); keys.add(ck)
        elif typ == "DEMAND" and cmin < lo:
            zones.append({"low": lo, "high": hi, "type": "ex_demand_supply", "tf": c.get("tf"),
                          "broken_ts": int(time.time())}); keys.add(ck)
    # poda o catálogo (zonas muito longe do preço = irrelevantes; evita crescer sem fim)
    cat = {ck: c for ck, c in cat.items() if abs(c["high"] - last) <= 400 or abs(c["low"] - last) <= 400}
    _write(CATF, {f"{ck[0]}|{ck[1]}": c for ck, c in cat.items()})
    # 2) INVALIDAR: polaridade que o preço perdeu de facto (fecho além por D·ATR)
    alive = []
    for z in zones:
        if z["type"] == "ex_supply_demand" and last < z["low"] - D_ATR * atr:
            continue                                          # suporte perdido = deixou de valer
        if z["type"] == "ex_demand_supply" and last > z["high"] + D_ATR * atr:
            continue
        alive.append(z)
    _save(alive)
    return alive


def load_active_supports(price):
    """Zonas de polaridade ATIVAS perto do preço, como suportes LONG (para ob_watch/vela consumir). READ-only."""
    if not ENABLED or not price:
        return []
    out = []
    for z in load_zones():
        if z["type"] != "ex_supply_demand":
            continue
        hi = z["high"]
        if hi <= price + 3.0 and hi >= price - NEAR_PTS:      # abaixo/no preço, perto
            out.append(z)
    out.sort(key=lambda z: price - z["high"])
    return out


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        import polarity_tracker as _self
        _save([])
        z = [{"low": 4350.0, "high": 4362.0, "type": "ex_supply_demand", "tf": "60", "broken_ts": 0}]
        _save(z)
        ok_state = len(load_zones()) == 1                 # estado persiste
        _self.ENABLED = True                              # força-liga só p/ testar o mecanismo
        ok_near = len(load_active_supports(4390)) == 1    # perto = aparece
        ok_far = len(load_active_supports(4200)) == 0     # longe = não aparece
        _self.ENABLED = False                             # OFF por defeito (lei refutada)
        ok_off = load_active_supports(4390) == []         # gate: desligado devolve []
        _save([])
        allok = ok_state and ok_near and ok_far and ok_off
        print(f"  state {ok_state} · near {ok_near} · far {ok_far} · gate-OFF {ok_off}")
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    zs = update()
    print(f"polaridades ativas: {len(zs)}")
    for z in zs:
        print(f"  {z['low']:.1f}-{z['high']:.1f} {z['type']} [{z.get('tf')}]")
