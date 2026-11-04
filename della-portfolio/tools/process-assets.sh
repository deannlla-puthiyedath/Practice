#!/usr/bin/env bash
# Rebuilds every web image in site/ from sources/. Strips ALL metadata (EXIF/GPS) on the way.
set -euo pipefail
cd "$(dirname "$0")/.."
V=sources/v2; O=site/assets/photos; mkdir -p "$O"; : > tools/manifest.txt
conv() { # name  source  [crop geometry]
  local n="$1" src="$2" crop="${3:-}"
  local pre=(-auto-orient -strip); [ -n "$crop" ] && pre+=(-crop "$crop" +repage)
  convert "$src" "${pre[@]}" -resize '1600x1600>' -quality 80 -define webp:method=6 "$O/$n-1600.webp"
  convert "$src" "${pre[@]}" -resize '800x>'      -quality 78 -define webp:method=6 "$O/$n-800.webp"
  convert "$src" "${pre[@]}" -resize '1000x760>' -quality 74 -define webp:method=6 "$O/$n-rail.webp"   # slider size (about 2x its on-screen size)
  echo "$n 1600=$(identify -format '%wx%h' $O/$n-1600.webp) 800=$(identify -format '%wx%h' $O/$n-800.webp)" >> tools/manifest.txt
}
conv hero        $V/hero.jpg
conv green-shirt $V/green-shirt.jpg
conv saree       $V/saree.jpg
conv baby        $V/baby-screenshot.jpg 1125x1125+0+437     # crops the phone screen away
conv building    $V/building.jpg
conv church      $V/church.jpg
conv night-lights $V/night-lights.jpg
conv blue-dress  $V/blue-dress.jpg
conv kitchen     $V/kitchen-full.jpg
# Optional artwork: processed only if you've supplied them
[ -f $V/painting.jpg ] && { mkdir -p site/assets/bg; convert $V/painting.jpg -strip -resize '800x>' -quality 78 -define webp:method=6 site/assets/bg/painting-800.webp; }
[ -f $V/rose.jpg ]     && conv rose $V/rose.jpg
# Posters for the Drive-embed cards
P=site/assets/clips
ffmpeg -v error -y -ss 10 -i sources/clips/Monologue-Hindi.MOV -frames:v 1 -q:v 3 $P/hindi-monologue.jpg
convert sources/clips/tamil-intro-still.png -strip -resize '480x>' -quality 72 -interlace Plane $P/tamil-intro.jpg
convert sources/stills/Sari1.JPG -auto-orient -strip -resize '480x>' -quality 72 -interlace Plane $P/malayalam-song.jpg
# Modelling video: compress to H.264 (<8 MB, 9:16, faststart) + poster frame at 45 s
ffmpeg -v error -y -i sources/clips/model-details-malayalam.mp4 -c:v libx264 -preset veryfast -crf 26 -pix_fmt yuv420p -vf scale=478:850 -c:a aac -b:a 96k -movflags +faststart $P/modelling.mp4
ffmpeg -v error -y -ss 45 -i sources/clips/model-details-malayalam.mp4 -frames:v 1 -q:v 3 $P/modelling.jpg
convert $P/modelling.jpg -strip -quality 72 -interlace Plane $P/modelling.jpg
cat tools/manifest.txt
