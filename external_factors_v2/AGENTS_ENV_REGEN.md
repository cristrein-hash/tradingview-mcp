# External Factors v2 — Regeneração do ambiente de agentes (`.venv-agents`)

**Data:** 2026-07-02
**Porquê este doc:** `external_factors_v2/.venv-agents/` (259 MB, gitignored) é a **runtime do daemon EF v2**, que é **PRODUÇÃO** (LaunchAgent `com.cristrein.external-factors-v2`, ciclo 30min). Este doc versiona como recriá-lo em qualquer máquina (portabilidade) e após qualquer remoção futura autorizada.

## ⚠️ Estado (2026-07-02)
- O venv **NÃO foi apagado**: o daemon está **VIVO** (carregado no `launchctl`; último ciclo hoje 12:30 em `snapshots/daemon.log`). Apagar quebraria o daemon no próximo ciclo.
- Só apagar após **pausar daemon + cron** (ver `feedback_pause_daemon_and_cron`) — e reclamar 259 MB de um serviço vivo não traz ganho durável (regen re-descarrega ~mesmo tamanho). Decisão do Cris.
- Lockfile versionado: `external_factors_v2/requirements-agents.txt` (31 pacotes pinados, inclui `claude-agent-sdk`).

## Ambiente
- Interpretador base: **Python 3.12** (homebrew: `/opt/homebrew/opt/python@3.12/bin/python3.12`).
- Path do venv: `external_factors_v2/.venv-agents/`.

## Regenerar (do zero)
```bash
cd external_factors_v2
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .venv-agents
./.venv-agents/bin/pip install --upgrade pip
./.venv-agents/bin/pip install -r requirements-agents.txt
# validar:
./.venv-agents/bin/python -c "import claude_agent_sdk; print('ok')"
```

## Remoção segura (SÓ com autorização + daemon pausado)
```bash
# 1) pausar daemon E cron (feedback_pause_daemon_and_cron)
launchctl unload ~/Library/LaunchAgents/com.cristrein.external-factors-v2.plist
# 2) confirmar sem ciclos em curso; 3) então:
rm -rf external_factors_v2/.venv-agents
# 4) regenerar (secção acima) ANTES de recarregar o daemon
# 5) launchctl load ~/Library/LaunchAgents/com.cristrein.external-factors-v2.plist
```

## Portabilidade
Noutra máquina/cliente: instalar Python 3.12, clonar repo, correr a secção "Regenerar", copiar `.env` (segredos, gitignored). O daemon é reproduzível a partir de `requirements-agents.txt` + `.env` + plist.
