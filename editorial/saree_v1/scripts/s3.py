import cv2,numpy as np
from rembg import new_session,remove
cl=cv2.imread('work/02_clean.jpg')
try:
    ss=new_session('isnet-general-use'); name='isnet-general-use'
except Exception as e:
    print('ERR',repr(e)[:300]); raise
rgba=remove(cv2.cvtColor(cl,cv2.COLOR_BGR2RGB),session=ss,alpha_matting=True,alpha_matting_foreground_threshold=240,alpha_matting_background_threshold=15,alpha_matting_erode_size=6)
a=rgba[...,3]; cv2.imwrite('work/alpha.png',a); print(name,a.mean())
vis=(cl*(a[...,None]/255.)).astype(np.uint8); cv2.imwrite('work/_cut.jpg',vis)
