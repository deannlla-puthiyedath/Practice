#!/bin/sh
# Final mix: Della's voice (de-clicked, gaps muted, -16 LUFS) + original pad score under it.
A="$1"   # path to the narration voice memo
ffmpeg -loglevel error -y -i reel3_silent.mp4 -i "$A" -i score.wav -filter_complex "[1:a]highpass=f=80,adeclick=w=55:o=75:t=2,adeclick=w=20:o=50:t=3,deesser=i=0.4,afftdn=nf=-25,volume=enable='not(between(t,1.45,2.70)+between(t,2.90,3.85)+between(t,4.85,6.35)+between(t,7.25,8.20)+between(t,13.85,16.35)+between(t,16.80,19.05)+between(t,20.00,21.95)+between(t,25.95,26.45)+between(t,27.55,30.05))':volume=0,loudnorm=I=-16:TP=-1.5,apad[v];[2:a]volume=0.22[m];[v][m]amix=inputs=2:duration=shortest:normalize=0[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 44100 -shortest -movflags +faststart della_antony_reel3_final.mp4
