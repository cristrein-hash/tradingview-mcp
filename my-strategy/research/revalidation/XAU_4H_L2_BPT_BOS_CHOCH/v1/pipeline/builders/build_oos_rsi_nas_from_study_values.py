#!/usr/bin/env python3
"""OOS 2013-2016 — ROTA A: extrai RSI/NAS DIRETO de study_values do RAW collection (NÃO reconstrói
raw_features). Causal por bar-time: para cada snapshot, o último bar de `ohlcv` é o bar corrente; o
RSI/NAS daquele snapshot é o valor disponível NO FECHAMENTO desse bar. Dedup por bar_time = KEEP-LAST
(manifest: dup_ts ~0.47%, keep-last downstream). Determinístico, CAUSAL, sem /tmp. Param via --gz/--out.

Saída: um registro por bar fechado (5100 esperado) com RSI, NAS signals, e flags de alinhamento causal.
NÃO usa forming/future bar: o valor é atribuído ao bar que o snapshot fecha (last ohlcv), nunca a um bar futuro.
"""
import argparse, gzip, json, sys, math


def fnum(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v) if math.isfinite(v) else None
    try: return float(str(v).replace('−', '-').strip())
    except Exception: return None


def studies_by_name(snap):
    out = {}
    for s in (snap.get('study_values') or []):
        out[s.get('name', '')] = s.get('values', {}) or {}
    return out


def build(gz_paths):
    by_bar = {}            # bar_time -> record (keep-last)
    seen = {}              # bar_time -> count of snapshots forming it
    n_snap = 0
    for gz in gz_paths:
        op = gzip.open if str(gz).endswith('.gz') else open
        with op(gz, 'rt') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try: snap = json.loads(line)
                except Exception: continue
                n_snap += 1
                oh = snap.get('ohlcv') or snap.get('ohlcv_last_40_bars') or []
                if not oh: continue
                last = oh[-1]
                bt = last.get('time')
                if bt is None: continue
                sv = studies_by_name(snap)
                rsi_v = fnum((sv.get('Relative Strength Index') or {}).get('RSI'))
                rsi_ma = fnum((sv.get('Relative Strength Index') or {}).get('RSI-based MA'))
                nas = sv.get('NAS TOP BOTTOM DETECTOR') or {}
                nas_sig = {k: fnum(nas.get(k)) for k in ('NAS_LONG_SIGNAL', 'NAS_SHORT_SIGNAL', 'NAS_BOTTOM_SIGNAL', 'NAS_TOP_SIGNAL')}
                seen[bt] = seen.get(bt, 0) + 1
                rec = dict(bar_time=bt, ohlcv_time=bt, rsi_value=rsi_v, rsi_ma=rsi_ma,
                           nas_value=json.dumps(nas_sig, separators=(',', ':')),
                           source_snapshot_time=snap.get('replay_current_dt') or snap.get('captured_at'),
                           source_bar_index=snap.get('bar_index'),
                           duplicate_snapshot_flag=(seen[bt] > 1))
                by_bar[bt] = rec     # KEEP-LAST: snapshot mais recente vence
    # finaliza flags
    rows = []
    for bt in sorted(by_bar):
        r = by_bar[bt]
        r['duplicate_snapshot_flag'] = seen[bt] > 1
        causal = r['rsi_value'] is not None
        r['causal_ok'] = causal
        r['alignment_status'] = 'OK' if causal else 'RSI_NULL'
        r['notes'] = '' if causal else 'rsi ausente no snapshot do bar'
        rows.append(r)
    return rows, n_snap, seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gz', nargs='+', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    rows, n_snap, seen = build(a.gz)
    import csv
    cols = ['bar_time', 'ohlcv_time', 'rsi_value', 'rsi_ma', 'nas_value', 'source_snapshot_time',
            'source_bar_index', 'alignment_status', 'causal_ok', 'duplicate_snapshot_flag', 'notes']
    with open(a.out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows: w.writerow({k: r.get(k) for k in cols})
    n_dup = sum(1 for bt in seen if seen[bt] > 1)
    n_rsi_null = sum(1 for r in rows if not r['causal_ok'])
    print(f"snapshots lidos: {n_snap}")
    print(f"bars únicos (fechados): {len(rows)}  -> {a.out}")
    print(f"bars com >1 snapshot (dedup keep-last): {n_dup} ({100*n_dup/max(1,len(rows)):.2f}%)")
    print(f"bars com RSI ausente: {n_rsi_null}")
    if rows:
        print(f"range bar_time: {rows[0]['bar_time']} .. {rows[-1]['bar_time']}")
        import datetime as _dt
        f0 = _dt.datetime.utcfromtimestamp(rows[0]['bar_time']).strftime('%Y-%m-%d %H:%M')
        f1 = _dt.datetime.utcfromtimestamp(rows[-1]['bar_time']).strftime('%Y-%m-%d %H:%M')
        print(f"range UTC: {f0} .. {f1}")
        print(f"sample mid: {rows[len(rows)//2]}")


if __name__ == '__main__':
    sys.exit(main())
