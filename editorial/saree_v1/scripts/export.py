import cv2,numpy as np,os
rng=np.random.default_rng(3)
o=cv2.imread('work/01_crop.jpg')
def fixspecks(x):
    m=np.zeros(x.shape[:2],np.uint8)
    for (x0,y0,x1,y1) in [(305,815,340,885),(436,738,462,756)]:
        r=x[y0:y1,x0:x1].astype(int); teal=((r[...,1]>r[...,2]+6)&(r[...,0]>r[...,2]+4)&(r.sum(-1)<420))|(r.sum(-1)<110)
        m[y0:y1,x0:x1][teal]=255
    m=cv2.dilate(m,np.ones((5,5),np.uint8)); return cv2.inpaint(x,m,4,cv2.INPAINT_TELEA)
FACE=(565,335,740,545)
def lab(img,b): x0,y0,x1,y1=b; return cv2.cvtColor(img[y0:y1,x0:x1].astype(np.float32)/255,cv2.COLOR_BGR2Lab).reshape(-1,3).mean(0)
rows=[]
for mood in ['heritage','studio']:
    fin=cv2.imread(f'work/06_final_{mood}.png'); fin=fixspecks(fin) if mood=='studio' else fin
    d=lab(fin,FACE)-lab(o,FACE); print(mood,'face dL,da,db =',np.round(d,2),'| mean L*',round(lab(fin,FACE)[0],1))
    # face-crop & full side-by-side
    fc=lambda im:cv2.resize(im[FACE[1]:FACE[3],FACE[0]:FACE[2]],None,fx=2.4,fy=2.4,interpolation=cv2.INTER_CUBIC)
    cv2.imwrite(f'della_saree_{mood}_v1_facecheck.jpg',np.hstack([fc(o),fc(fin)]),[cv2.IMWRITE_JPEG_QUALITY,93])
    sbs=np.hstack([o,np.full((o.shape[0],20,3),255,np.uint8),fin]); cv2.imwrite(f'della_saree_{mood}_v1_before_after.jpg',sbs,[cv2.IMWRITE_JPEG_QUALITY,92])
    # exports: 2x full-res (max allowed), under-2MB, 1080x1350
    big=cv2.resize(fin,None,fx=2,fy=2,interpolation=cv2.INTER_LANCZOS4)
    big=np.clip(big.astype(np.float32)+rng.normal(0,1.2,big.shape[:2])[...,None],0,255).astype(np.uint8)
    cv2.imwrite(f'della_saree_{mood}_v1.jpg',big,[cv2.IMWRITE_JPEG_QUALITY,95,cv2.IMWRITE_JPEG_OPTIMIZE,1])
    web=cv2.resize(fin,(1080,1350),interpolation=cv2.INTER_LANCZOS4); cv2.imwrite(f'della_saree_{mood}_v1_1080x1350.jpg',web,[cv2.IMWRITE_JPEG_QUALITY,95])
    for q in range(92,60,-4):
        cv2.imwrite(f'della_saree_{mood}_v1_under2MB.jpg',big,[cv2.IMWRITE_JPEG_QUALITY,q])
        if os.path.getsize(f'della_saree_{mood}_v1_under2MB.jpg')<2e6: print(' under2MB q',q); break
