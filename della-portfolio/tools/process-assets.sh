#!/usr/bin/env bash
# Rebuilds every web asset in site/ from sources/. Strips ALL metadata (EXIF/GPS) on the way.
set -euo pipefail
cd "$(dirname "$0")/.."
S=sources/stills; O=site/assets/stills
# FR number : source file  (grid order)
declare -a MAP=( "01:Windy_fortkochi.jpg" "02:Sari1.JPG" "03:Toronto.JPG" "04:Biennale_weekend.jpg" "05:IMG_4865.JPG" "06:Sari2.JPG" )
: > tools/manifest.txt
for m in "${MAP[@]}"; do
  n="${m%%:*}"; f="${m#*:}"
  convert "$S/$f" -auto-orient -strip -resize '1600x1600>' -quality 80 -define webp:method=6 "$O/$n-lg.webp"
  convert "$S/$f" -auto-orient -strip -resize '800x>'      -quality 78 -define webp:method=6 "$O/$n-sm.webp"
  convert "$S/$f" -auto-orient -strip -resize '800x>'      -quality 80 -interlace Plane       "$O/$n-sm.jpg"
  echo "$n $f lg=$(identify -format '%wx%h' $O/$n-lg.webp) sm=$(identify -format '%wx%h' $O/$n-sm.webp)" >> tools/manifest.txt
done
# Hero: tight 4:5 crop around her face from Sari2
H=site/assets/hero
convert "$S/Sari2.JPG" -auto-orient -strip -crop 1018x1290+224+365 +repage -quality 82 -define webp:method=6 "$H/hero-lg.webp"
convert "$S/Sari2.JPG" -auto-orient -strip -crop 1018x1290+224+365 +repage -resize '800x>' -quality 80 -define webp:method=6 "$H/hero-sm.webp"
convert "$S/Sari2.JPG" -auto-orient -strip -crop 1018x1290+224+365 +repage -resize '800x>' -quality 80 "$H/hero-sm.jpg"
echo "hero lg=$(identify -format '%wx%h' $H/hero-lg.webp) sm=$(identify -format '%wx%h' $H/hero-sm.webp)" >> tools/manifest.txt
# Clips: H.264 MP4 (<8 MB, 9:16 kept, faststart) + poster JPG, for any local clip present in sources/clips
for c in sources/clips/*; do
  b="$(basename "$c")"; stem="${b%.*}"
  case "$stem" in tamil-monologue|british-accent)
    ffmpeg -v error -y -i "$c" -c:v libx264 -preset veryfast -crf 26 -pix_fmt yuv420p -c:a aac -b:a 96k -movflags +faststart "site/assets/clips/$stem.mp4"
    echo "clip $stem $(du -h site/assets/clips/$stem.mp4 | cut -f1)" >> tools/manifest.txt ;;
  esac
done
# Poster for the Hindi Drive-embed card (frame at 10 s, calm, eyes to camera)
ffmpeg -v error -y -ss 10 -i sources/clips/Monologue-Hindi.MOV -frames:v 1 -q:v 3 site/assets/clips/hindi-monologue.jpg
# Poster for the Tamil intro card (a still you supplied)
convert sources/clips/tamil-intro-still.png -strip -resize '600x>' -quality 82 -interlace Plane site/assets/clips/tamil-intro.jpg
cat tools/manifest.txt
