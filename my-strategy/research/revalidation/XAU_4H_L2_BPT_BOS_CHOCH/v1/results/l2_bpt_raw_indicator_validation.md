# Validacao — extracao NAS/SMC do RAW original (corrige DERIVED_ARTIFACT_BUG)

Fonte RAW: /Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_240m_replay_*.jsonl.gz | metodo: first-appearance diff as-of-bar (tail, nao head).

| ep | entry | close RAW==frozen | OLD nas_recent (derivado, head) era-preco | NOVO nas_events recent era-preco | stale antigo? |
|---|---|---|---|---|---|
| 4918 | 2023-03-08 11:00 | 1814.53==1820.38 (OK) | (1179.89, 1275.1) | (1805.66, 1857.76) | STALE |
| 4926 | 2023-03-09 19:00 | 1830.74==1830.74 (OK) | (1179.89, 1316.66) | (1805.66, 1857.76) | STALE |
| 1661 | 2021-01-28 11:00 | 1855.11==1854.61 (OK) | (1125.33, 1261.07) | (1823.35, 1957.39) | STALE |
| 5701 | 2023-09-07 22:00 | 1925.82==1925.82 (OK) | (1270.91, 1388.3) | (1926.32, 1950.21) | STALE |
| 6887 | 2024-06-14 18:00 | 2334.13==2332.69 (OK) | (1457.71, 1725.22) | (2285.88, 2452.58) | STALE |
| 7426 | 2024-10-18 14:00 | 2713.71==2715.82 (OK) | (1760.19, 2073.45) | (2602.44, 2715.37) | STALE |
| 8878 | 2025-09-28 22:00 | 3783.05==3778.67 (OK) | (1715.24, 1832.87) | (3706.43, 3793.05) | STALE |
| 8923 | 2025-10-08 10:00 | 4029.24==4038.0 (OK) | (1715.24, 1832.83) | (3775.96, 3982.15) | STALE |
| 8940 | 2025-10-13 06:00 | 4063.64==4077.17 (OK) | (1715.24, 1832.83) | (3783.44, 4059.58) | STALE |
| 5826 | 2023-10-06 18:00 | 1831.83==1831.58 (OK) | (1275, 1454.69) | (1814.96, 1864.92) | STALE |
| 1623 | 2021-01-20 03:00 | 1844.69==1852.75 (OK) | (1125.33, 1261.07) | (1823.35, 1957.39) | STALE |
| 4401 | 2022-11-04 02:00 | 1647.8==1647.09 (OK) | (1225.78, 1314.79) | (1619.67, 1728.29) | STALE |
| 3825 | 2022-06-23 02:00 | 1835.23==1834.79 (OK) | (1283.93, 1364.5) | (1795.7, 1855.22) | STALE |
| 1522 | 2020-12-23 23:00 | 1877.03==1876.96 (OK) | (1121.49, 1226.63) | (1763.08, 1897.87) | STALE |
| 1873 | 2021-03-18 22:00 | 1731.21==1731.25 (OK) | (1195.23, 1293.94) | (1677.83, 1767.14) | STALE |
| 5627 | 2023-08-22 14:00 | 1895.08==1897.68 (OK) | (1270.91, 1325.36) | (1883.78, 1988.81) | STALE |
| 1775 | 2021-02-24 15:00 | 1796.22==1797.64 (OK) | (1195.23, 1266.62) | (1762.87, 1788.69) | STALE |
| 3949 | 2022-07-21 18:00 | 1713.82==1718.18 (OK) | (1301.77, 1364.5) | (1689.26, 1737.9) | STALE |
| 3929 | 2022-07-18 10:00 | 1719.02==1718.96 (OK) | (1301.77, 1364.5) | (1720.88, 1761.49) | STALE |

## Spot-check obrigatorio (6)

### #5826 (2023-10-06 18:00) close RAW 1831.83 (frozen 1831.58, OK)
- NAS tail recente (RAW, causal): [('LONG', 1864.92, 'era'), ('LONG', 1817.44, 'era'), ('LONG', 1821.62, 'era'), ('LONG', 1815.14, 'era'), ('LONG', 1814.96, 'era'), ('LONG', 1817.16, 'era')]
- SMC tail recente (RAW, causal): [('CHoCH', 1930.7, 'era'), ('BOS', 1937.33, 'era'), ('CHoCH', 1913.9, 'era'), ('BOS', 1884.77, 'era'), ('BOS', 1857.63, 'era'), ('EQH', 1879.84, 'era')]
- bubbles (RAW): {'buy_total': 0, 'sell_total': 18, 'buy_mL': 0, 'sell_mL': 16, 'buy_L': 0, 'sell_L': 2, 'total_bars_evaluated': 20, 'raw_field': 'pine_shapes_bubbles.activations_per_plot'}
- RSI 51.60 | divergencias RAW: nenhuma no payload
- OLD derivado nas_recent (head/stale): [('LONG', 1276.21), ('LONG', 1275), ('SHORT', 1300.04), ('SHORT', 1313.67)]

### #4401 (2022-11-04 02:00) close RAW 1647.8 (frozen 1647.09, OK)
- NAS tail recente (RAW, causal): [('LONG', 1619.67, 'era'), ('SHORT', 1704.64, 'era'), ('SHORT', 1728.29, 'era'), ('SHORT', 1724.53, 'era'), ('LONG', 1659.09, 'era'), ('LONG', 1625.9, 'era')]
- SMC tail recente (RAW, causal): [('EQL', 1661.34, 'era'), ('BOS', 1661.34, 'era'), ('BOS', 1640.2, 'era'), ('BOS', 1622.41, 'era'), ('CHoCH', 1645.62, 'era'), ('CHoCH', 1638.27, 'era')]
- bubbles (RAW): {'buy_total': 0, 'sell_total': 12, 'buy_mL': 0, 'sell_mL': 11, 'buy_L': 0, 'sell_L': 3, 'total_bars_evaluated': 20, 'raw_field': 'pine_shapes_bubbles.activations_per_plot'}
- RSI 50.02 | divergencias RAW: nenhuma no payload
- OLD derivado nas_recent (head/stale): [('LONG', 1314.79), ('LONG', 1314.65), ('LONG', 1300.9), ('LONG', 1288.73)]

### #5627 (2023-08-22 14:00) close RAW 1895.08 (frozen 1897.68, OK)
- NAS tail recente (RAW, causal): [('LONG', 1913.42, 'era'), ('LONG', 1899.01, 'era'), ('LONG', 1888.35, 'era'), ('LONG', 1890.87, 'era'), ('LONG', 1891.49, 'era'), ('LONG', 1883.78, 'era')]
- SMC tail recente (RAW, causal): [('BOS', 1929.48, 'era'), ('BOS', 1910.76, 'era'), ('BOS', 1896.35, 'era'), ('CHoCH', 1892.94, 'era'), ('EQL', 1884.77, 'era'), ('EQL', 1885.25, 'era')]
- bubbles (RAW): {'buy_total': 0, 'sell_total': 16, 'buy_mL': 0, 'sell_mL': 15, 'buy_L': 0, 'sell_L': 8, 'total_bars_evaluated': 20, 'raw_field': 'pine_shapes_bubbles.activations_per_plot'}
- RSI 48.77 | divergencias RAW: nenhuma no payload
- OLD derivado nas_recent (head/stale): [('LONG', 1284.63), ('LONG', 1283.11), ('LONG', 1284.16), ('SHORT', 1310.11)]

### #3949 (2022-07-21 18:00) close RAW 1713.82 (frozen 1718.18, OK)
- NAS tail recente (RAW, causal): [('LONG', 1735.98, 'era'), ('LONG', 1737.03, 'era'), ('LONG', 1737.9, 'era'), ('LONG', 1721.2, 'era'), ('LONG', 1720.88, 'era'), ('LONG', 1689.26, 'era')]
- SMC tail recente (RAW, causal): [('BOS', 1805.11, 'era'), ('BOS', 1784.5, 'era'), ('BOS', 1733.44, 'era'), ('BOS', 1707.15, 'era'), ('CHoCH', 1716.5, 'era'), ('CHoCH', 1705.29, 'era')]
- bubbles (RAW): {'buy_total': 0, 'sell_total': 9, 'buy_mL': 0, 'sell_mL': 5, 'buy_L': 0, 'sell_L': 0, 'total_bars_evaluated': 20, 'raw_field': 'pine_shapes_bubbles.activations_per_plot'}
- RSI 54.01 | divergencias RAW: nenhuma no payload
- OLD derivado nas_recent (head/stale): [('SHORT', 1342.78), ('SHORT', 1342.58), ('SHORT', 1363.19), ('SHORT', 1364.5)]

### #3929 (2022-07-18 10:00) close RAW 1719.02 (frozen 1718.96, OK)
- NAS tail recente (RAW, causal): [('LONG', 1735.4, 'era'), ('LONG', 1735.98, 'era'), ('LONG', 1737.03, 'era'), ('LONG', 1737.9, 'era'), ('LONG', 1721.2, 'era'), ('LONG', 1720.88, 'era')]
- SMC tail recente (RAW, causal): [('BOS', 1812.05, 'era'), ('BOS', 1805.11, 'era'), ('BOS', 1784.5, 'era'), ('BOS', 1733.44, 'era'), ('BOS', 1707.15, 'era'), ('CHoCH', 1716.5, 'era')]
- bubbles (RAW): {'buy_total': 0, 'sell_total': 13, 'buy_mL': 0, 'sell_mL': 10, 'buy_L': 0, 'sell_L': 3, 'total_bars_evaluated': 20, 'raw_field': 'pine_shapes_bubbles.activations_per_plot'}
- RSI 51.02 | divergencias RAW: nenhuma no payload
- OLD derivado nas_recent (head/stale): [('SHORT', 1344.44), ('SHORT', 1342.78), ('SHORT', 1342.58), ('SHORT', 1363.19)]

### #4918 (2023-03-08 11:00) close RAW 1814.53 (frozen 1820.38, OK)
- NAS tail recente (RAW, causal): [('LONG', 1808.85, 'era'), ('LONG', 1805.66, 'era'), ('SHORT', 1856.82, 'era'), ('SHORT', 1857.76, 'era'), ('LONG', 1807.94, 'era'), ('LONG', 1810.96, 'era')]
- SMC tail recente (RAW, causal): [('BOS', 1869.02, 'era'), ('BOS', 1852.73, 'era'), ('BOS', 1831.76, 'era'), ('CHoCH', 1820.13, 'era'), ('BOS', 1844.5, 'era'), ('CHoCH', 1829.93, 'era')]
- bubbles (RAW): {'buy_total': 6, 'sell_total': 7, 'buy_mL': 0, 'sell_mL': 6, 'buy_L': 0, 'sell_L': 2, 'total_bars_evaluated': 20, 'raw_field': 'pine_shapes_bubbles.activations_per_plot'}
- RSI 35.00 | divergencias RAW: {'Regular Bullish': '27.13'}
- OLD derivado nas_recent (head/stale): [('LONG', 1180.97), ('LONG', 1181.12), ('LONG', 1179.89), ('SHORT', 1209.25)]
