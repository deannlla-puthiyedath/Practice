import cv2,numpy as np
im=cv2.imread('work/original_copy.jpg'); X0,Y0=222,380
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
mask=np.zeros(im.shape[:2],np.uint8)
# frames: dark pixels inside padded rects
for r in [(815,420,890,580),(948,400,1040,585),(1150,325,1242,540)]:
    x0,y0,x1,y1=r; sub=hsv[y0:y1,x0:x1,2]<110
    m=np.zeros_like(mask); m[y0:y1,x0:x1]=sub*255; mask|=m
mask=cv2.dilate(mask,np.ones((9,9),np.uint8),iterations=1)
# fitting: whole rect, soft
cv2.ellipse(mask,(1170,1063),(40,52),0,0,360,255,-1)
mask=cv2.dilate(mask,np.ones((5,5),np.uint8))
cl=cv2.inpaint(im,mask,6,cv2.INPAINT_TELEA)
# add grain to patched area to match texture
rng=np.random.default_rng(1); n=rng.normal(0,2.2,cl.shape[:2])[...,None]
mf=cv2.GaussianBlur(mask,(0,0),3)[...,None]/255.
cl=np.clip(cl+n*mf,0,255).astype(np.uint8)
# strap recolour: purple pixels near shoulder -> deep saree red-rose
h=hsv[...,0].astype(int);s=hsv[...,1];v=hsv[...,2]
zone=np.zeros_like(mask);zone[940:1140,670:810]=255
sm=((h>=120)&(h<=160)&(s>40)&(zone>0)).astype(np.uint8)*255
sm=cv2.morphologyEx(sm,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8));sm=cv2.dilate(sm,np.ones((3,3),np.uint8))
print('strap px',int((sm>0).sum()))
hs=cv2.cvtColor(cl,cv2.COLOR_BGR2HSV); 
alpha=cv2.GaussianBlur(sm,(0,0),1.2)/255.
new=hs.copy(); new[...,0]=177; new[...,1]=np.clip(hs[...,1]*0.6+150,0,255)  # crimson
new[...,2]=np.clip(hs[...,2]*0.95+10,0,255)
newbgr=cv2.cvtColor(new,cv2.COLOR_HSV2BGR).astype(float)
cl=(cl*(1-alpha[...,None])+newbgr*alpha[...,None]).astype(np.uint8)
cv2.imwrite('work/02_clean_full.png',cl)
cv2.imwrite('work/02_clean.jpg',cl[Y0:1655,X0:1242],[cv2.IMWRITE_JPEG_QUALITY,98])
np.save('work/strapmask.npy',sm)
cv2.imwrite('work/_strap_zoom.jpg',cv2.resize(cl[930:1150,640:840],None,fx=3,fy=3))
