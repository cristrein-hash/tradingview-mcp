# LPPLS OURO 1D — research macro (D4, ordem Cris 28/08)
Pergunta: o 1D do ouro mostra HOJE assinatura LPPLS de bolha-em-exaustão (Sornette), e o método
teria marcado os topos históricos do próprio ouro (2020-08, 2025-26) neste dataset?
Método selado ANTES de correr: calibração Filimonov-Sornette (linearização A,B,C1,C2; grelha
tc=+1..+250d step10 · m=0.1..0.9 step0.1 · ω=6..13 step1), filtros canónicos da literatura
(B<0 · 0.1<m<0.9 · 6<ω<13 · damping m|B|/(ω√(C1²+C2²))≥1), confidence = fração de 10 janelas
(120..750d) cujo melhor fit passa os filtros. Varrimento histórico trimestral 2016→hoje.
Descritivo/contexto macro — NÃO gera sinal nem gate; leitura = Cris. Dados: 1D merged 2014-2026 (3031b).
