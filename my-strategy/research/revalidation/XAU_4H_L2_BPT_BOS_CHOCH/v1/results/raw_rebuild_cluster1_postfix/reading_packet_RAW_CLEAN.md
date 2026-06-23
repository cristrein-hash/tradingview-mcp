# PACOTE DE LEITURA RAW-CLEAN POS-ANCHOR-FIX — Cluster 1 (sosia 3a + continuacao 3b) — RAW-clean POS-FIX

> LEITURA CEGA, FONTE 100% RAW ORIGINAL, **backbone CAUSAL pos-fix** (commit 1267c8d: as-of join por
> timestamp real, 19/19 causal+exato, SEM look-ahead). Camada-1 (forma/supply-demand/regime), indicadores
> (NAS/SMC/bubbles/RSI) e volume RAW. TPO value-area = de TEMPO (proxy, NAO VA de volume). POC/VAL/VAH de
> VOLUME LuxAlgo = BLOCKED (nao serializado, nao inventado).
> SEM resultado/R/futuro pos-entry. NAO classifique TAKE/SKIP. Leia o EPISODIO; campos BLOCKED limitam a
> leitura — declare isso. (Esta e a base FINAL; os pacotes pre-fix sao historicos contaminados por look-ahead.)

## Contexto (regime RAW-derived price; supply/demand RAW Custom OB causal)
| sub | bar | data | weekly | cascade | sup_cat | clean_sky | distSup | distDem | tpo_acc | causal |
|---|---|---|---|---|---|---|---|---|---|---|
| c | 4918 | 2023-03-08 | 0.54 | -1 | SUPPLY_FAR | True | 4.01 | 0.02 | INSIDE_VALUE | True |
| c | 1661 | 2021-01-28 | -0.22 | -2 | SUPPLY_NEAR | False | 0.27 | 2.74 | INSIDE_VALUE | True |
| c | 5701 | 2023-09-07 | -0.22 | -3 | SUPPLY_FAR | True | 3.06 | 0.7 | ACCEPTED_ABOVE_VALUE | True |
| c | 6887 | 2024-06-14 | 0.9 | 1 | SUPPLY_FAR | True | 3.17 | 1.98 | ACCEPTED_ABOVE_VALUE | True |
| c | 7426 | 2024-10-18 | 0.85 | 3 | CLEAN_SKY | True | None | 2.6 | INSIDE_VALUE | True |
| c | 8878 | 2025-09-28 | 0.58 | 3 | SUPPLY_NEAR | False | 0.59 | 0.94 | INSIDE_VALUE | True |
| c | 8923 | 2025-10-08 | 0.85 | 3 | CLEAN_SKY | True | None | 3.7 | ACCEPTED_ABOVE_VALUE | True |
| c | 8940 | 2025-10-13 | 1.06 | 3 | CLEAN_SKY | True | None | 2.44 | ACCEPTED_ABOVE_VALUE | True |
| c | 4926 | 2023-03-09 | 0.54 | 1 | SUPPLY_BLOCKS | False | 1.61 | 1.92 | ACCEPTED_ABOVE_VALUE | True |

##########################################################################################
# SUB-BLOCO cluster 3a (superficie identica; discriminar pelo contexto causal)


========================================================================================
## EPISODIO 4918 (2023-03-08 11:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=0.5360961749936248 cascade=-1 combined=-1 macro_broken=True v3=TRANSITION (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_FAR clean_sky=True has_overhead=True dist_supply=4.01ATR dist_demand=0.02ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=0.919 last6_up=0.431 | tpo_acceptance(TEMPO,NAO-volume)=INSIDE_VALUE poc_tpo=1812.74 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1814.48 H1815.97 L1812.66 C1812.94
    O1813.49 H1814.36 L1810.59 C1810.96
    O1810.93 H1813.93 L1809.35 C1813.87
    O1813.85 H1815.21 L1812.31 C1814.1
    O1814.12 H1814.12 L1814.12 C1814.12

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'SHORT'] | SMC(RAW)=['CHoCH', 'CHoCH', 'BOS', 'BOS', 'BOS'] | bubbles sell_mL=6 buy_mL=0 | RSI=35.00 div=['Regular Bullish']

========================================================================================
## EPISODIO 1661 (2021-01-28 11:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.21810057484990794 cascade=-2 combined=-2 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_NEAR clean_sky=False has_overhead=True dist_supply=0.27ATR dist_demand=2.74ATR
- anchor: causal=True exato=True close_fidelity=False warnings=['anchor close fidelity vs frozen > 0.5pct (feed RAW != frozen)']
- SVP/acceptance: volume RAW entry_up=0.111 last6_up=0.089 | tpo_acceptance(TEMPO,NAO-volume)=INSIDE_VALUE poc_tpo=1839.08 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1845.09 H1849.07 L1839.17 C1844.05
    O1843.61 H1844.94 L1833.99 C1837.67
    O1837.64 H1839.28 L1835.12 C1837.26
    O1837.22 H1843.35 L1834.05 C1841.64
    O1841.61 H1841.61 L1841.61 C1841.61

### Indicadores (RAW): NAS(RAW)=['SHORT', 'SHORT', 'SHORT', 'SHORT', 'LONG'] | SMC(RAW)=['CHoCH', 'CHoCH', 'CHoCH', 'CHoCH', 'EQH'] | bubbles sell_mL=0 buy_mL=6 | RSI=48.96 div=nenhuma

========================================================================================
## EPISODIO 5701 (2023-09-07 22:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.2182182596028588 cascade=-3 combined=-3 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_FAR clean_sky=True has_overhead=True dist_supply=3.06ATR dist_demand=0.7ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=1.0 last6_up=0.493 | tpo_acceptance(TEMPO,NAO-volume)=ACCEPTED_ABOVE_VALUE poc_tpo=1918.0 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1917.49 H1920.48 L1917.1 C1920.23
    O1920.23 H1923.59 L1916.26 C1920.04
    O1920.03 H1921.51 L1917.23 C1918.43
    O1918.45 H1920.7 L1918.06 C1919.58
    O1919.67 H1926 L1919.38 C1925.82

### Indicadores (RAW): NAS(RAW)=['SHORT', 'SHORT', 'SHORT', 'SHORT', 'SHORT'] | SMC(RAW)=['BOS', 'CHoCH', 'EQL', 'EQL', 'CHoCH'] | bubbles sell_mL=10 buy_mL=0 | RSI=49.12 div=nenhuma

========================================================================================
## EPISODIO 6887 (2024-06-14 18:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=0.898919941913868 cascade=1 combined=1 macro_broken=False v3=TRANSITION (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_FAR clean_sky=True has_overhead=True dist_supply=3.17ATR dist_demand=1.98ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=1.0 last6_up=0.578 | tpo_acceptance(TEMPO,NAO-volume)=ACCEPTED_ABOVE_VALUE poc_tpo=2307.21 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O2306.02 H2311.58 L2303.48 C2309.84
    O2309.82 H2322.72 L2307.39 C2322.61
    O2322.67 H2336.63 L2320.94 C2330.23
    O2330.15 H2335.55 L2324.03 C2334.12
    O2334.13 H2334.13 L2334.13 C2334.13

### Indicadores (RAW): NAS(RAW)=['SHORT', 'SHORT', 'SHORT', 'LONG', 'LONG'] | SMC(RAW)=['CHoCH', 'BOS', 'BOS', 'EQL', 'CHoCH'] | bubbles sell_mL=0 buy_mL=3 | RSI=59.71 div=nenhuma

========================================================================================
## EPISODIO 7426 (2024-10-18 14:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=0.850560688153433 cascade=3 combined=3 macro_broken=False v3=BULL (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=CLEAN_SKY clean_sky=True has_overhead=False dist_supply=NoneATR dist_demand=2.6ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=0.957 last6_up=0.745 | tpo_acceptance(TEMPO,NAO-volume)=INSIDE_VALUE poc_tpo=2704.94 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O2692.43 H2706.83 L2692.27 C2704.65
    O2704.59 H2714.07 L2703.95 C2711.51
    O2711.42 H2713.11 L2701.68 C2711.14
    O2711.17 H2716.99 L2704.85 C2713.67
    O2713.71 H2713.71 L2713.71 C2713.71

### Indicadores (RAW): NAS(RAW)=['SHORT', 'SHORT', 'SHORT', 'SHORT', 'SHORT'] | SMC(RAW)=['CHoCH', 'BOS', 'BOS', 'BOS', 'CHoCH'] | bubbles sell_mL=0 buy_mL=13 | RSI=77.26 div=nenhuma

========================================================================================
## EPISODIO 8878 (2025-09-28 22:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=0.5815620342583104 cascade=3 combined=3 macro_broken=False v3=BULL (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_NEAR clean_sky=False has_overhead=True dist_supply=0.59ATR dist_demand=0.94ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=None last6_up=0.543 | tpo_acceptance(TEMPO,NAO-volume)=INSIDE_VALUE poc_tpo=3762.01 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O3741.99 H3755.21 L3739.13 C3751.57
    O3751.56 H3766.22 L3742.88 C3761.74
    O3761.77 H3783.78 L3761.71 C3782.93
    O3783.05 H3783.24 L3760.63 C3761.24
    O3760.57 H3760.57 L3760.57 C3760.57

### Indicadores (RAW): NAS(RAW)=['SHORT', 'SHORT', 'SHORT', 'SHORT', 'SHORT'] | SMC(RAW)=['CHoCH', 'BOS', 'BOS', 'BOS', 'EQH'] | bubbles sell_mL=0 buy_mL=4 | RSI=65.03 div=nenhuma

========================================================================================
## EPISODIO 8923 (2025-10-08 10:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=0.8506313187533326 cascade=3 combined=3 macro_broken=False v3=BULL (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=CLEAN_SKY clean_sky=True has_overhead=False dist_supply=NoneATR dist_demand=3.7ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=1.0 last6_up=0.884 | tpo_acceptance(TEMPO,NAO-volume)=ACCEPTED_ABOVE_VALUE poc_tpo=3984.45 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O3980.8 H3986.53 L3974.06 C3984.49
    O3985.08 H4000.33 L3983.52 C4000.26
    O4000.32 H4037 L3995.47 C4029.03
    O4029.24 H4049.64 L4021.14 C4049.16
    O4049.21 H4049.21 L4049.21 C4049.21

### Indicadores (RAW): NAS(RAW)=['SHORT', 'SHORT', 'SHORT', 'SHORT', 'SHORT'] | SMC(RAW)=['BOS', 'BOS', 'EQH', 'BOS', 'BOS'] | bubbles sell_mL=0 buy_mL=18 | RSI=82.36 div=nenhuma

========================================================================================
## EPISODIO 8940 (2025-10-13 06:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=1.0583364987907347 cascade=3 combined=3 macro_broken=False v3=BULL (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=CLEAN_SKY clean_sky=True has_overhead=False dist_supply=NoneATR dist_demand=2.44ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=1.0 last6_up=0.711 | tpo_acceptance(TEMPO,NAO-volume)=ACCEPTED_ABOVE_VALUE poc_tpo=4006.93 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O3980.73 H4022.89 L3970.62 C3990
    O3990.1 H4021.41 L3984.11 C4018.46
    O4012.06 H4059.82 L4007.39 C4053.21
    O4053.22 H4078.21 L4041.58 C4063.2
    O4063.64 H4063.64 L4063.64 C4063.64

### Indicadores (RAW): NAS(RAW)=['SHORT', 'SHORT', 'SHORT', 'SHORT', 'SHORT'] | SMC(RAW)=['EQH', 'BOS', 'BOS', 'BOS', 'EQH'] | bubbles sell_mL=0 buy_mL=13 | RSI=66.32 div=nenhuma

========================================================================================
## EPISODIO 4926 (2023-03-09 19:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=0.5360961749936248 cascade=1 combined=1 macro_broken=False v3=TRANSITION (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_BLOCKS clean_sky=False has_overhead=True dist_supply=1.61ATR dist_demand=1.92ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=1.0 last6_up=0.778 | tpo_acceptance(TEMPO,NAO-volume)=ACCEPTED_ABOVE_VALUE poc_tpo=1815.18 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1813 H1816.01 L1812.59 C1813.3
    O1813.28 H1819.08 L1812.72 C1818.02
    O1818.02 H1831.85 L1815.42 C1831.31
    O1831.31 H1835.64 L1825.51 C1834.96
    O1834.97 H1834.97 L1828.96 C1830.74

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'SHORT', 'SHORT'] | SMC(RAW)=['CHoCH', 'CHoCH', 'BOS', 'BOS', 'BOS'] | bubbles sell_mL=6 buy_mL=0 | RSI=52.92 div=nenhuma