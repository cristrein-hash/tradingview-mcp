#!/bin/zsh
# Extrai transcrição YouTube via yt-dlp (solução autónoma, Cris 28/08). Uso: ./fetch_transcript.sh <videoID_ou_URL>
V="$1"; OUT="/Users/cristrein/tradingview-mcp/research/inter_equity_knowledge/transcripts"
cd /tmp && rm -f _yt.*
python3 -m yt_dlp --skip-download --write-auto-sub --sub-lang "en.*" --sub-format vtt \
  --extractor-args "youtube:player_client=android,ios,web" -o "_yt.%(ext)s" "$V" >/dev/null 2>&1
f=$(ls _yt.en.vtt _yt.en-orig.vtt 2>/dev/null | head -1)
[ -z "$f" ] && { echo "FALHOU: sem legendas"; exit 1; }
id=$(echo "$V" | grep -oE '[A-Za-z0-9_-]{11}' | head -1)
python3 -c "
import re,html,sys
raw=open('/tmp/$f').read(); lines=[]
for l in raw.splitlines():
    if '-->' in l or l.strip().isdigit() or l.startswith(('WEBVTT','Kind:','Language:')) or not l.strip(): continue
    t=html.unescape(re.sub(r'<[^>]+>','',l)).strip()
    if t and (not lines or lines[-1]!=t): lines.append(t)
full=re.sub(r'\s+',' ',' '.join(lines))
open('$OUT/${id}.txt','w').write(full); print('OK ${id}.txt chars',len(full))
"
