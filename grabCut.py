__author__ = 'FiksII'
import cv2
import numpy as np

def grabCutFast1(image,rect,coeff):
    image_rect=image[rect[1]:rect[1]+rect[3],rect[0]:rect[0]+rect[2]]
    rectangle=(0,0,image_rect.shape[0]-1,image_rect.shape[1]-1)

    mask=np.zeros(image.shape)

    image_rectrgb=cv2.cvtColor(image_rect,cv2.COLOR_GRAY2RGB)
    mask_rect= np.zeros(image_rect.shape[:2],np.uint8)
    bgdmodel = np.zeros((1,65),np.float64)
    fgdmodel = np.zeros((1,65),np.float64)

    cv2.grabCut(image_rectrgb,mask_rect,rectangle,bgdmodel,fgdmodel,1,cv2.GC_INIT_WITH_RECT)
    mask_rect = np.where((mask_rect==2)|(mask_rect==0),0,1).astype('uint8')

    mask[rect[1]:rect[1]+rect[3],rect[0]:rect[0]+rect[2]]=mask_rect
    return mask.astype(np.uint8)

def grabCutFast(image,rect,coeff):
    if coeff<1:
        image=cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
        newsize=(int(image.shape[1]*coeff),int(image.shape[0]*coeff))

        image_down=cv2.resize(image,dsize=newsize,interpolation=cv2.INTER_CUBIC)
        rect_down=(int(rect[0]*coeff),int(rect[1]*coeff),int(rect[2]*coeff),int(rect[3]*coeff))

        bgdmodel = np.zeros((1,65),np.float64)
        fgdmodel = np.zeros((1,65),np.float64)
        mask = np.zeros(image_down.shape[:2],np.uint8)
        cv2.grabCut(image_down,mask,rect_down,bgdmodel,fgdmodel,1,cv2.GC_INIT_WITH_RECT)
        mask_down = np.where((mask==2)|(mask==0),0,1).astype('uint8')
        mask = cv2.resize(mask_down,(image.shape[1],image.shape[0]),interpolation=cv2.INTER_CUBIC)
        return mask
    else:
        image=cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
        bgdmodel = np.zeros((1,65),np.float64)
        fgdmodel = np.zeros((1,65),np.float64)
        mask = np.zeros(image.shape[:2],np.uint8)
        rect=tuple(rect)
        cv2.grabCut(image,mask,rect,bgdmodel,fgdmodel,1,cv2.GC_INIT_WITH_RECT)
        mask = np.where((mask==2)|(mask==0),0,1).astype('uint8')
        return mask
