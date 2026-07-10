#!/usr/bin/env python3
"""SANITY_PROBE — distribuição size/cor/texto dos eventos BOS extraídos DIRETO do RAW HD
(re-extração com campos size/textColor para separar BOS de linha contínua/swing do internal)."""
import collections, json
import bos_gate
ev = bos_gate.extract_events()
print("total:", len(ev))
print("por size:", dict(collections.Counter(e.get("size") for e in ev)))
print("por texto:", dict(collections.Counter(e["text"] for e in ev)))
print("por cor:", dict(collections.Counter(e.get("tc") for e in ev)))
