import cv2,numpy as np,sys
rng=np.random.default_rng(7)
src=cv2.imread('work/02_clean.jpg'); H,W=src.shape[:2]
A=cv2.imread('work/alpha.png',0)
# keep largest component (drops the stray newel fragment)
n,lab,st,_=cv2.connectedComponentsWithStats((A>40).astype(np.uint8))
big=1+np.argmax(st[1:,4]); keep=cv2.dilate((lab==big).astype(np.uint8),np.ones((9,9),np.uint8))
A=(A*keep).astype(np.uint8)
a=A.astype(np.float32)/255.; a=np.clip((a-0.04)/0.92,0,1)**1.15   # slight edge tighten, no halo
hsv0=cv2.cvtColor(src,cv2.COLOR_BGR2HSV)
sk0=((cv2.cvtColor(src,cv2.COLOR_BGR2YCrCb)[...,1]>133)).astype(bool)
def rm(y0,y1,x0,x1,cond):
    m=np.zeros((H,W),bool); m[y0:y1,x0:x1]=True; a[m&cond]=0
nonred=(hsv0[...,1]<150)
rm(705,925,0,326,nonred&~sk0); rm(705,925,0,290,np.ones((H,W),bool))
rm(712,752,418,462,nonred&~sk0)
a[300:552,762:]=0; a[315:342,680:730]=0
rm(790,885,0,312,np.ones((H,W),bool)); rm(790,885,0,340,nonred&~sk0)
a=cv2.morphologyEx(a,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8)) if False else a
holes=(a<128).astype(np.uint8); nh,lh,sth,_=cv2.connectedComponentsWithStats(holes)
for k in range(1,nh):
    if sth[k,4]<150 and sth[k,0]>300: a[lh==k]=255          # fill tiny interior holes only
a=cv2.GaussianBlur(a,(0,0),0.8)
cv2.imwrite('work/alpha_clean.png',(a*255).astype(np.uint8))
f=src.astype(np.float32)/255.
# --- skin mask (face/neck/shoulder/hand), computed once from the clean crop
ycc=cv2.cvtColor(src,cv2.COLOR_BGR2YCrCb); hsv=cv2.cvtColor(src,cv2.COLOR_BGR2HSV)
sk=((ycc[...,1]>133)&(ycc[...,1]<178)&(ycc[...,2]>80)&(ycc[...,2]<135)&(hsv[...,1]<150)).astype(np.uint8)
reg=np.zeros((H,W),np.uint8); reg[320:780,470:800]=1; reg[720:960,290:490]=1
sk=sk*reg; sk=cv2.morphologyEx(sk,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)); sk=cv2.morphologyEx(sk,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
skin=cv2.GaussianBlur(sk.astype(np.float32),(0,0),2.0)
skin=skin*a
cv2.imwrite('work/skinmask.png',(skin*255).astype(np.uint8))
lab0=cv2.cvtColor(f,cv2.COLOR_BGR2Lab)
def curve(x,s=0.10,lift=0.025):
    y=x+s*np.sin(2*np.pi*(x-0.5))*(-1)*0.5*0+0  # placeholder
    y=0.5+(x-0.5)*1.0
    s_=3.5; y=1/(1+np.exp(-s_*(x-0.5))); y=(y-1/(1+np.exp(s_*0.5)))/(1/(1+np.exp(-s_*0.5))-1/(1+np.exp(s_*0.5)))
    y=0.55*y+0.45*x                      # gentle
    return lift+(1-lift)*y
def vignette(h,w,k):
    yy,xx=np.mgrid[0:h,0:w].astype(np.float32); cx,cy=w*0.62,h*0.42
    d=np.sqrt(((xx-cx)/(w*0.85))**2+((yy-cy)/(h*0.85))**2); return 1-k*np.clip(d,0,1)**2
def keylight(h,w):
    xx=np.linspace(1.06,0.93,w)[None,:]; yy=np.linspace(1.03,0.96,h)[:,None]; return (xx*yy).astype(np.float32)
def build(mood):
    img=f.copy()
    if mood=='heritage':
        g=cv2.cvtColor(cv2.cvtColor(img,cv2.COLOR_BGR2GRAY),cv2.COLOR_GRAY2BGR)
        bg=img*0.74; bg=bg*0.84+g*0.74*0.16           # darker, ~28% desaturated
        bg=cv2.GaussianBlur(bg,(0,0),1.1)*vignette(H,W,0.35)[...,None]
        # denoise bg only (strong-ish)
        bg8=cv2.fastNlMeansDenoisingColored(np.clip(bg*255,0,255).astype(np.uint8),None,5,5,7,15); bg=bg8.astype(np.float32)/255.
    else:
        yy,xx=np.mgrid[0:H,0:W].astype(np.float32); d=np.sqrt(((xx-W*0.58)/(W*0.75))**2+((yy-H*0.40)/(H*0.7))**2)
        c0=np.array([0x3A,0x52,0x2B],np.float32)/255.*1.0   # BGR of #2B523A? set below properly
        inner=np.array([0x52,0x62,0x2B][::-1],np.float32)  # placeholder overwritten
        inner=np.array([0x2F,0x52,0x50],np.float32)[::-1]/255.   # RGB #2F5250 -> BGR
        outer=np.array([0x14,0x26,0x25],np.float32)[::-1]/255.
        t=np.clip(d,0,1)[...,None]**1.4; bg=inner*(1-t)+outer*t
        bg=bg+rng.normal(0,0.004,bg.shape).astype(np.float32)
        # soft grounding shadow hugging the saree's left edge
        sh=cv2.GaussianBlur(np.roll(a,(10,-14),(0,1)),(0,0),16)*0.45; bg=bg*(1-sh[...,None])
        # decontaminate subject edge colours (no wall spill / halo)
        wgt=(cv2.erode((a>0.97).astype(np.uint8),np.ones((5,5),np.uint8))).astype(np.float32)
        num=cv2.GaussianBlur(img*wgt[...,None],(0,0),4); den=cv2.GaussianBlur(wgt,(0,0),4)[...,None]+1e-4
        prop=num/den; edge=((a>0.02)&(a<0.98)).astype(np.float32); edge=cv2.GaussianBlur(edge,(0,0),1)[...,None]
        img=img*(1-edge)+prop*edge
    comp=img*a[...,None]+bg*(1-a[...,None])
    cv2.imwrite(f'work/03_bg_{mood}.jpg',np.clip(comp*255,0,255).astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,98])
    # ---- 04 light: one soft key from the window side
    L=cv2.cvtColor(comp.astype(np.float32),cv2.COLOR_BGR2Lab)
    L[...,0]*=np.where(a>0.5,keylight(H,W),1.0).astype(np.float32)
    fm=np.zeros((H,W),np.float32); cv2.ellipse(fm,(650,450),(150,190),0,0,360,1,-1); fm=cv2.GaussianBlur(fm,(0,0),40)
    l=L[...,0]/100.; lift=np.clip(0.55-l,0,1)*0.10; L[...,0]=np.clip((l+lift*fm)*100,0,100)   # lift face shadows only
    lit=cv2.cvtColor(L,cv2.COLOR_Lab2BGR)
    cv2.imwrite(f'work/04_light_{mood}.jpg',np.clip(lit*255,0,255).astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,98])
    # ---- 05 grade
    x=lit.copy(); hs=cv2.cvtColor(x,cv2.COLOR_BGR2HSV); h_,s_,v_=cv2.split(hs)
    silk=((a>0.5)&(s_>0.58)&((h_<14)|(h_>330))).astype(np.float32); silk=cv2.GaussianBlur(silk,(0,0),2)
    zari=((a>0.5)&(h_>10)&(h_<42)&(s_>0.25)&(s_<0.85)&(v_>0.55)).astype(np.float32); zb=np.zeros((H,W),np.float32); zb[540:780,520:860]=1; zari=cv2.GaussianBlur(zari*zb,(0,0),1.5)*(1-skin)
    s2=s_*(1+0.10*silk); v2=v_*(1-0.09*silk)                      # deeper, richer, not neon
    v2=v2+0.06*zari*(v2**2); s2=s2*(1+0.12*zari); h2=h_-4*zari    # warm, lift zari highlights
    x=cv2.cvtColor(cv2.merge([h_*(1-zari)+h2*zari,np.clip(s2,0,1),np.clip(v2,0,1)]),cv2.COLOR_HSV2BGR)
    x=np.clip(x,0,1); x=curve(x)
    if mood=='studio': x[...,0]*=1.0
    # protect skin: hue/lum within small tolerance of original
    Lg=cv2.cvtColor(x.astype(np.float32),cv2.COLOR_BGR2Lab); L0=lab0
    dL=np.clip(Lg[...,0]-L0[...,0],-3.0,3.0); da=np.clip(Lg[...,1]-L0[...,1],-2,2); db=np.clip(Lg[...,2]-L0[...,2],-2,2)
    P=np.stack([L0[...,0]+dL,L0[...,1]+da,L0[...,2]+db],-1); P=cv2.cvtColor(P.astype(np.float32),cv2.COLOR_Lab2BGR)
    x=x*(1-skin[...,None])+P*skin[...,None]
    # grain on everything except skin
    x=x+(rng.normal(0,0.007,(H,W))[...,None]*(1-skin[...,None])).astype(np.float32)
    cv2.imwrite(f'work/05_grade_{mood}.jpg',np.clip(x*255,0,255).astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,98])
    # ---- 06 detail: clarity on saree/zari only, none on skin
    blur=cv2.GaussianBlur(x,(0,0),9); mask=np.clip(a*(1-skin),0,1)[...,None]*0.28
    fin=np.clip(x+(x-blur)*mask*1.0,0,1)
    out=np.clip(fin*255,0,255).astype(np.uint8); cv2.imwrite(f'work/06_final_{mood}.png',out)
    return out
for m in ['heritage','studio']: build(m)
