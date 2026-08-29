#!/bin/zsh
# Extrai frames-chave de um video IE guiado pelas legendas VTT (momentos em que ele marca/desenha).
# Uso: ./extract_frames.sh <videoID>. Grava em frames/<id>/*.png (480p, ~10 frames). Zero tokens.
V="$1"; OUT="/Users/cristrein/tradingview-mcp/research/inter_equity_knowledge/frames/$V"
mkdir -p "$OUT"; cd /tmp && rm -f _fv.mp4 _fv*.vtt
python3 -m yt_dlp -f "worst[height>=480]/worst" --write-auto-sub --sub-lang "en.*" --sub-format vtt \
  --extractor-args "youtube:player_client=android,ios,web" -o "_fv.%(ext)s" "https://youtu.be/$V" >/dev/null 2>&1
[ -f _fv.mp4 ] || { echo "FALHOU download $V"; exit 1; }
vtt=$(ls _fv*.vtt 2>/dev/null | head -1)
# timestamps onde ele fala de marcar/desenhar/entrar (as acoes visuais)
python3 - "$vtt" <<'PY' > /tmp/_fv_times.txt
import sys,re
raw=open(sys.argv[1]).read()
blocks=re.findall(r'(\d\d):(\d\d):(\d\d)\.\d+ -->.*?\n(.*?)(?=\n\n|\Z)',raw,re.S)
KEY=re.compile(r'liquidity block|mark(ing)? (out|this)|draw|blue box|red box|stop loss goes|entry|sweep|stab|induc',re.I)
times=[]
for h,m,s,txt in blocks:
    if KEY.search(txt):
        t=int(h)*3600+int(m)*60+int(s)
        if not times or t-times[-1]>=45: times.append(t)
print("\n".join(str(t) for t in times[:12]))
PY
n=0
while read t; do
  [ -z "$t" ] && continue
  /opt/homebrew/bin/ffmpeg -y -loglevel error -ss "$t" -i _fv.mp4 -frames:v 1 -vf scale=640:-1 "$OUT/f$(printf %02d $n)_${t}s.png"
  n=$((n+1))
done < /tmp/_fv_times.txt
echo "$V: $n frames -> $OUT"
