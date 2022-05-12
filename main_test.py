# -*- coding: utf-8 -*-
"""
Created on Tue May 10 19:29:31 2022

@author: mouha
"""

import tello_hand_detector as htm 
import cv2
wCam, hCam = 640, 480
cap = cv2.VideoCapture(0)

detector = htm.HandDetector(detectionCon=0.75)
 
tipIds = [4, 8, 12, 16, 20]
pTime = 0

while True:
    success, img = cap.read()
    #img = detector.findPosition(img)
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)
    output_process_vol = detector.process_volume(img,lmList)
    
    list_status=[]
    if output_process_vol != None:
        status, img = output_process_vol
        list_status.append(status)
        final_statut = list_status[-1]
        #print("La liste  des statuts est :{}".format(final_statut))
        
    

     
    cv2.imshow("Image", img)
    cv2.waitKey(1)