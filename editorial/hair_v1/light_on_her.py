import cv2,numpy as np
src=cv2.imread('work/01_crop.jpg'); H,W=src.shape[:2]
A=cv2.imread('work/alpha.png',0)
n,lab,st,_=cv2.connectedComponentsWithStats((A>40).astype(np.uint8)); big=1+np.argmax(st[1:,4])
a=((lab==big)*A).astype(np.float32)/255.
f=src.astype(np.float32)/255.; hsv=cv2.cvtColor(src,cv2.COLOR_BGR2HSV); ycc=cv2.cvtColor(src,cv2.COLOR_BGR2YCrCb)
# mask used for edits: tight (eroded) so no edge fringe/halo reaches the wall
core=cv2.erode((a>0.5).astype(np.uint8),np.ones((5,5),np.uint8)); M=cv2.GaussianBlur(core.astype(np.float32),(0,0),1.3)
# hair stays exactly as shot: neutral dark pixels on the hair side
hair=((hsv[...,2]<100)&(hsv[...,1]<110)&(a>0.3)).astype(np.uint8); hair[:, :330]=0; hair[380:,:440]=0
hair=cv2.morphologyEx(hair,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8)); hairm=cv2.GaussianBlur(cv2.dilate(hair,np.ones((3,3),np.uint8)).astype(np.float32),(0,0),1.2)
M=M*(1-hairm)
# pool of light: strongest on face/shoulder/arm, easing toward the hem
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
pool=np.clip(1.0-0.30*(np.clip((yy-250)/650,0,1)**1.2),0.70,1.0)*np.clip(1.0-0.25*np.abs(xx-430)/200,0.75,1.0)
Lab=cv2.cvtColor(f,cv2.COLOR_BGR2Lab); L=Lab[...,0]/100.
Lnew=100*np.power(np.clip(L,1e-4,1),0.58)                    # lifts shadows and mids, keeps highlights
Lnew=Lab[...,0]+(Lnew-Lab[...,0])*pool
# face: gentle extra light, luminance only (hue and chroma untouched)
fm=np.zeros((H,W),np.float32); cv2.ellipse(fm,(398,215),(52,72),0,0,360,1,-1); fm=cv2.GaussianBlur(fm,(0,0),16)
Lnew=Lnew+7.0*fm
out=Lab.copy(); out[...,0]=np.clip(Lnew,0,100)
# dress: richer blue so it separates from the cream wall (complementary), arm/skin chroma untouched
res=cv2.cvtColor(out,cv2.COLOR_Lab2BGR)
hs=cv2.cvtColor(np.clip(res,0,1).astype(np.float32),cv2.COLOR_BGR2HSV); h_,s_,v_=cv2.split(hs)
dress=((a>0.5)&(h_>200)&(h_<265)&(s_>0.2)).astype(np.float32); dress=cv2.GaussianBlur(dress,(0,0),1.5)
s2=np.clip(s_*(1+0.14*dress),0,1)
res=cv2.cvtColor(cv2.merge([h_,s2,v_]),cv2.COLOR_HSV2BGR)
# local contrast on fabric and arm only, none on face
blur=cv2.GaussianBlur(res,(0,0),10); faceprot=cv2.GaussianBlur(cv2.dilate((fm>0.05).astype(np.uint8),np.ones((15,15),np.uint8)).astype(np.float32),(0,0),6)
cm=(M*(1-faceprot))[...,None]*0.32; res=np.clip(res+(res-blur)*cm,0,1)
Mm=M[...,None]; final=f*(1-Mm)+res*Mm
out8=np.clip(final*255+0.5,0,255).astype(np.uint8)
cv2.imwrite('work/04_light.jpg',out8,[cv2.IMWRITE_JPEG_QUALITY,98]); cv2.imwrite('work/06_final.png',out8)
# ---- checks
far=cv2.dilate((a>0.02).astype(np.uint8),np.ones((15,15),np.uint8))==0
print('background pixels changed outside the subject:',int((np.abs(out8.astype(int)-src.astype(int)).max(-1)[far]>0).sum()),'of',int(far.sum()))
FACE=(350,145,450,290)
lab_=lambda im:cv2.cvtColor(im[FACE[1]:FACE[3],FACE[0]:FACE[2]].astype(np.float32)/255,cv2.COLOR_BGR2Lab).reshape(-1,3).mean(0)
print('face dL,da,db',np.round(lab_(out8)-lab_(src),2),'L*',round(lab_(out8)[0],1))
fc=lambda im:cv2.resize(im[FACE[1]:FACE[3],FACE[0]:FACE[2]],None,fx=4,fy=4,interpolation=cv2.INTER_CUBIC)
cv2.imwrite('della_hair_pop_v1_facecheck.jpg',np.hstack([fc(src),fc(out8)]),[cv2.IMWRITE_JPEG_QUALITY,93])
cv2.imwrite('della_hair_pop_v1_before_after.jpg',np.hstack([src,np.full((H,20,3),255,np.uint8),out8]),[cv2.IMWRITE_JPEG_QUALITY,92])
ycc=cv2.cvtColor(src,cv2.COLOR_BGR2YCrCb); sk=((ycc[...,1]>133)&(ycc[...,1]<178)&(ycc[...,2]>80)&(ycc[...,2]<135)&(hsv[...,1]<150)&(a>0.6))
sk[:130]=0; sk[300:]=0; sk[:,:350]=0; sk[:,460:]=0
L0=cv2.cvtColor(src.astype(np.float32)/255,cv2.COLOR_BGR2Lab)[...,0]; L1=cv2.cvtColor(out8.astype(np.float32)/255,cv2.COLOR_BGR2Lab)[...,0]
print('face-skin L* before/after',round(L0[sk].mean(),1),round(L1[sk].mean(),1))
cv2.imwrite('work/_up.jpg',np.hstack([src[100:760],out8[100:760]]))
