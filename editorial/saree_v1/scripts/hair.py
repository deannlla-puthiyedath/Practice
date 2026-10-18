import cv2,numpy as np
o=cv2.imread('work/02_clean.jpg').astype(np.float32); H,W=o.shape[:2]
hsv=cv2.cvtColor(o.astype(np.uint8),cv2.COLOR_BGR2HSV)
box=np.zeros((H,W),np.uint8); box[290:640,500:800]=1
hair=((hsv[...,2]<95)&(box>0)&(cv2.imread('work/alpha.png',0)>60)).astype(np.uint8)
hair=cv2.morphologyEx(hair,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
m=cv2.GaussianBlur(cv2.dilate(hair,np.ones((3,3),np.uint8)).astype(np.float32),(0,0),1.5)[...,None]
araw=cv2.imread('work/alpha.png',0).astype(np.float32)[...,None]/255.
araw[:552,762:]=0
for mood in ['heritage','studio']:
    f=cv2.imread(f'work/06_final_{mood}.png').astype(np.float32)
    if mood=='studio':
        bg=cv2.imread('work/06_final_studio_prehair.png').astype(np.float32); bg=cv2.inpaint(bg.astype(np.uint8),(araw[...,0]>0.02).astype(np.uint8)*255,9,cv2.INPAINT_TELEA).astype(np.float32)          # teal behind
        orig=o*araw+bg*(1-araw)                  # original hair with its own soft edge
    else: orig=o
    out=f*(1-m)+orig*m
    cv2.imwrite(f'work/06_final_{mood}.png',np.clip(out,0,255).astype(np.uint8))
cv2.imwrite('work/hairmask.png',(m[...,0]*255).astype(np.uint8))
