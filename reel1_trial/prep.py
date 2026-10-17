import numpy as np, glob
from PIL import Image, ImageFilter
S="/tmp/claude-0/-home-user-Practice/6b8363a1-55c5-5d6e-9fc0-4f4c21b30016/scratchpad/r1/fr/"
fs=sorted(glob.glob(S+"*.png"))
def load(t): return np.asarray(Image.open(fs[int(round((t-2.4)*30))]).convert("RGB")).astype(np.int32)
Y0,Y1,X0,X1=200,460,60,1020
a,b=load(3.3)[Y0:Y1,X0:X1],load(4.0)[Y0:Y1,X0:X1]
same=(np.abs(a-b).sum(2)<14)
light=(a.min(2)>190)
dark=(a.sum(2)<250)|((a[...,0]>120)&(a[...,1]<110)&(a[...,2]>70)&(a[...,0]-a[...,1]>60))  # letters: black / magenta
core=same&(light)
im=Image.fromarray((core*255).astype(np.uint8))
m=np.asarray(im.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.MinFilter(15))).astype(bool)   # close gaps between letters inside tile
# keep only blobs that are big enough (tiles), drop specks
from collections import deque
lab=np.zeros(m.shape,np.int32);n=0;sizes={}
H,W=m.shape
for sy in range(0,H):
    for sx in range(0,W):
        if m[sy,sx] and lab[sy,sx]==0:
            n+=1;q=deque([(sy,sx)]);lab[sy,sx]=n;c=0
            while q:
                y,x=q.popleft();c+=1
                for dy,dx in((1,0),(-1,0),(0,1),(0,-1)):
                    yy,xx=y+dy,x+dx
                    if 0<=yy<H and 0<=xx<W and m[yy,xx] and lab[yy,xx]==0: lab[yy,xx]=n;q.append((yy,xx))
            sizes[n]=c
keep=np.zeros_like(m)
for k,c in sizes.items():
    if c>900: keep|=(lab==k)
# fill holes (letters) : flood from border
inv=~keep;fill=np.zeros_like(inv);q=deque()
for x in range(W):
    for y in (0,H-1):
        if inv[y,x]: fill[y,x]=True;q.append((y,x))
for y in range(H):
    for x in (0,W-1):
        if inv[y,x] and not fill[y,x]: fill[y,x]=True;q.append((y,x))
while q:
    y,x=q.popleft()
    for dy,dx in((1,0),(-1,0),(0,1),(0,-1)):
        yy,xx=y+dy,x+dx
        if 0<=yy<H and 0<=xx<W and inv[yy,xx] and not fill[yy,xx]: fill[yy,xx]=True;q.append((yy,xx))
alpha=~fill
ys,xs=np.nonzero(alpha);print("tiles bbox",xs.min()+X0,xs.max()+X0,ys.min()+Y0,ys.max()+Y0,"blobs",sum(1 for c in sizes.values() if c>900))
np.save("text_alpha.npy",alpha);np.save("text_rgb.npy",a.astype(np.uint8));np.save("text_box.npy",np.array([X0,Y0]))
# when does the baked text disappear? mean diff inside mask vs sticker over time
ref=a
for t in np.arange(2.4,6.0,0.1):
    f=load(t)[Y0:Y1,X0:X1];d=np.abs(f-ref).sum(2)[alpha].mean()
    print(f"{t:.1f}:{d:.0f}",end="  ")
print()
# sun sprite from frame 3.2 (fully visible, lower-left): orange mask bbox
f=load(3.2);R,G,B=f[...,0],f[...,1],f[...,2]
m=(R>205)&(G>45)&(G<115)&(B<50);m[:int(0.28*1920)]=False;m[int(0.9*1920):]=False;m[:, :260]=False
ys,xs=np.nonzero(m);print("sun bbox",xs.min(),xs.max(),ys.min(),ys.max())
