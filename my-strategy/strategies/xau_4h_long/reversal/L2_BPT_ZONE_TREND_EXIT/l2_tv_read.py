#!/usr/bin/env python3
"""L2/BPT — leitor MCP TAB-PINNED da tab 4H (resolution 240). READ-ONLY, fail-closed.

Lê da tab 240 pinada por TVMCP_TARGET_CHART_ID (recurso geral core/tab_pin.py, Cris 2026-07-17).
NUNCA troca symbol/timeframe, NUNCA pausa daemons, NUNCA fallback manage-chart (decisão de
simplicidade L2: tab 240 ausente = HARD_STOP no runner).

Fontes lidas (todas fail-closed; estudo ausente/oculto -> status blocked_missing_study:<qual>):
  (a) data_get_ohlcv paginado (from_time/to_time, count<=500) -> barras 4H; caller filtra FECHADAS
  (b) data_get_pine_boxes verbose:true -> zonas DEMAND/SUPPLY do "Custom OB Detector" (texto do box)
  (c) data_get_pine_shapes "Market Order" -> bolhas; SELL = plot_6/8/10 (mapeamento validado Cp)
  (d) data_get_study_values_at_bar "Relative Strength" -> RSI por barra (gate categórico >=70)

Cliente: reusa _MCP de my-strategy/core/tv_read_adapter.py (INALTERADO). py3.9 stdlib.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _repo(p):
    for d in [p] + list(p.parents):
        if (d / "my-strategy").is_dir() and (d / "alert-bridge").is_dir():
            return d
    return p.parents[5]


REPO = _repo(HERE)
CORE = REPO / "my-strategy" / "core"
sys.path.insert(0, str(CORE))
from tv_read_adapter import _MCP  # noqa: E402  (client JSON-RPC partilhado; NÃO alterado)

SYMBOL_SUFFIX = "XAUUSD"
TF = "240"
TF_SEC = 14400
# substrings dos estudos necessários no chart 4H (fail-closed se ausentes)
STUDY_OB = "OB Detector"            # boxes DEMAND/SUPPLY (context_sl)
STUDY_BUBBLES = "Market Order"      # Market Order Bubbles (is_tipo_B_contextual)
STUDY_RSI = "Relative Strength"     # RSI (gate TOP_EXHAUSTION)
SELL_PLOTS = {"plot_6", "plot_8", "plot_10"}   # mapeamento validado Cp (context_confluence.py)
BUY_PLOTS = {"plot_0", "plot_2", "plot_4"}


def _sec(t):
    """Normaliza tempo p/ unix-seconds (ms -> s)."""
    if t is None:
        return None
    t = int(t)
    return t // 1000 if t > 10**12 else t


class L2Reader:
    """Sessão MCP única na tab pinada. Uso: with L2Reader() as r: ..."""

    def __init__(self, target_id=None):
        # o pin tem de existir ANTES do spawn do server.js (env herdado pelo subprocess)
        if target_id:
            os.environ["TVMCP_TARGET_CHART_ID"] = target_id
        self.pinned = os.environ.get("TVMCP_TARGET_CHART_ID")
        self.m = None

    def __enter__(self):
        self.m = _MCP()
        self.m.start()
        return self

    def __exit__(self, *a):
        try:
            self.m.stop()
        except Exception:
            pass

    # ---------------- chart state ----------------
    def verify_chart(self):
        """Confirma tab pinada = XAUUSD 240. Devolve (ok, info|status)."""
        if not self.pinned:
            return False, "blocked_missing_tab_240:env_TVMCP_TARGET_CHART_ID_ausente"
        st = self.m.call("chart_get_state")
        if not isinstance(st, dict) or st.get("_error"):
            return False, f"blocked_chart_state:{st.get('_error') if isinstance(st, dict) else st}"
        sym = st.get("symbol"); res = str(st.get("resolution"))
        if not (sym and str(sym).endswith(SYMBOL_SUFFIX)):
            return False, f"blocked_wrong_symbol:{sym}"
        if res != TF:
            return False, f"blocked_wrong_timeframe:{res}"
        names = [s.get("name", "") for s in st.get("studies", [])]
        missing = [lbl for lbl, sub in (("ob_boxes", STUDY_OB), ("bubbles", STUDY_BUBBLES),
                                        ("rsi", STUDY_RSI)) if not any(sub in n for n in names)]
        if missing:
            return False, "blocked_missing_study:" + ",".join(missing)
        return True, {"symbol": sym, "timeframe": res, "studies": names}

    # ---------------- (a) OHLCV ----------------
    def get_ohlcv(self, count=400, from_time=None, to_time=None):
        """Barras normalizadas {'t','o','h','l','c','v'} ordenadas por t (inclui a em formação;
        caller filtra fechadas). Devolve (ok, bars|status)."""
        args = {"count": int(count)}
        if from_time is not None:
            args["from_time"] = int(from_time)
        if to_time is not None:
            args["to_time"] = int(to_time)
        r = self.m.call("data_get_ohlcv", args)
        if not isinstance(r, dict) or r.get("_error"):
            return False, f"blocked_ohlcv:{r.get('_error') if isinstance(r, dict) else r}"
        raw = r.get("bars") or r.get("ohlcv") or []
        out = []
        for b in raw:
            t = _sec(b.get("time"))
            if t is None:
                continue
            try:
                out.append({"t": t, "o": float(b["open"]), "h": float(b["high"]),
                            "l": float(b["low"]), "c": float(b["close"]),
                            "v": float(b.get("volume") or 0)})
            except (KeyError, TypeError, ValueError):
                return False, f"blocked_ohlcv:bar_malformada:{b}"
        out.sort(key=lambda x: x["t"])
        # dedup por t (mesma barra devolvida 2x na paginação)
        ded = {}
        for b in out:
            ded[b["t"]] = b
        return True, [ded[t] for t in sorted(ded)]

    def get_ohlcv_paginated(self, from_time, to_time, page=500):
        """Pagina data_get_ohlcv por janela temporal até cobrir [from_time, to_time].
        Devolve (ok, bars|status)."""
        allb = {}
        cursor = int(from_time)
        for _ in range(60):                     # guarda-fogo: 60 páginas x 500 barras
            ok, bars = self.get_ohlcv(count=page, from_time=cursor, to_time=int(to_time))
            if not ok:
                return False, bars
            new = [b for b in bars if b["t"] not in allb]
            for b in bars:
                allb[b["t"]] = b
            if not bars or not new:
                break
            last_t = max(b["t"] for b in bars)
            if last_t >= int(to_time):
                break
            cursor = last_t + 1
        return True, [allb[t] for t in sorted(allb)]

    # ---------------- (b) zonas DEMAND/SUPPLY ----------------
    def get_demand_supply(self):
        """Boxes do OB Detector com texto DEMAND/SUPPLY (verbose p/ ter o `text`).
        Devolve (ok, {'demand':[(hi,lo)..],'supply':[(hi,lo)..],'study':nome}|status).
        Ordem preservada como devolvida (quirk 'inside[0]' do dsq builder)."""
        r = self.m.call("data_get_pine_boxes", {"study_filter": STUDY_OB, "verbose": True})
        if not isinstance(r, dict) or r.get("_error") or r.get("success") is False:
            return False, "blocked_missing_study:ob_boxes"
        studies = r.get("studies") or []
        cob = next((s for s in studies if STUDY_OB in (s.get("name") or "")), None)
        if cob is None:
            return False, "blocked_missing_study:ob_boxes"
        dem, sup = [], []
        for b in (cob.get("all_boxes") or []):
            hi, lo = b.get("high"), b.get("low")
            tx = (b.get("text") or "").upper()
            if hi is None or lo is None:
                continue
            if tx == "DEMAND":
                dem.append((float(hi), float(lo)))
            elif tx == "SUPPLY":
                sup.append((float(hi), float(lo)))
        return True, {"demand": dem, "supply": sup, "study": cob.get("name")}

    # ---------------- (c) bolhas ----------------
    def get_bubble_activations(self, max_bars=120):
        """Ativações do Market Order Bubbles: lista [(t_sec, plot_id)] (todas as plots; o
        detector filtra SELL). Devolve (ok, acts|status). Estudo ausente -> blocked."""
        r = self.m.call("data_get_pine_shapes", {"study_filter": STUDY_BUBBLES,
                                                 "max_bars": int(max_bars)})
        if not isinstance(r, dict) or r.get("_error") or r.get("success") is False:
            return False, "blocked_missing_study:bubbles"
        studies = r.get("studies") or []
        if not studies:
            return False, "blocked_missing_study:bubbles"
        acts = []
        for s in studies:
            for a in (s.get("activations") or []):
                t = _sec(a.get("time"))
                if t is None:
                    continue
                for plot in (a.get("shapes") or {}):
                    acts.append((t, plot))
        return True, acts

    # ---------------- (d) RSI por barra ----------------
    def get_rsi_by_bar(self, count=60):
        """RSI por barra via data_get_study_values_at_bar (bar-aligned, ≠ data-window forming).
        Devolve (ok, {t_sec: rsi}|status)."""
        r = self.m.call("data_get_study_values_at_bar",
                        {"study_filter": STUDY_RSI, "count": int(count)})
        if not isinstance(r, dict) or r.get("_error"):
            return False, "blocked_missing_study:rsi"
        out = {}
        for s in (r.get("studies") or []):
            for b in (s.get("bars") or []):
                t = _sec(b.get("time"))
                vals = b.get("values") or {}
                v = vals.get("RSI")
                if t is None:
                    continue
                try:
                    out[t] = float(v)
                except (TypeError, ValueError):
                    pass
        if not out:
            return False, "blocked_missing_study:rsi"
        return True, out


def bubbles_recent_for_bar(bar_idx, T, acts_by_t, window=10):
    """bubbles_recent (contrato do detector: {'plot_id','bars_ago','time'}) p/ a barra bar_idx,
    reconstruído das ativações por-tempo. bars_ago = distância em BARRAS do ledger (não calendário)."""
    out = []
    lo = max(0, bar_idx - window)
    for j in range(lo, bar_idx + 1):
        for plot in acts_by_t.get(T[j], ()):
            out.append({"plot_id": plot, "bars_ago": bar_idx - j, "time": T[j]})
    return out


if __name__ == "__main__":
    # smoke-test read-only na tab pinada (env TVMCP_TARGET_CHART_ID tem de estar setado)
    with L2Reader() as r:
        ok, info = r.verify_chart()
        rep = {"verify": info if ok else info}
        if ok:
            ok2, bars = r.get_ohlcv(count=10)
            rep["ohlcv_last"] = bars[-1] if ok2 and bars else bars
            ok3, ds = r.get_demand_supply()
            rep["boxes"] = ({"demand": len(ds["demand"]), "supply": len(ds["supply"])}
                            if ok3 else ds)
            ok4, acts = r.get_bubble_activations(60)
            rep["bubble_acts"] = len(acts) if ok4 else acts
            ok5, rsi = r.get_rsi_by_bar(10)
            rep["rsi_bars"] = len(rsi) if ok5 else rsi
        print(json.dumps(rep, ensure_ascii=False, indent=2, default=str))
