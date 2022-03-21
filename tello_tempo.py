#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import configargparse
import os, sys
import cv2 as cv

# from gestures.tello_gesture_controller import TelloGestureController
# from utils import cvfpscalc
from collections import deque

from djitellopy import Tello
# from gestures import *

import tellopy
import time
import datetime
import os
from threading import Thread

from tello_thread import TelloThread
import librosa 

import threading

import platform
PLATFORM=platform.system()
P_WINDOWS = 'Windows'
P_LINUX   = 'Linux'
P_DARWIN  = 'Darwin'


import numpy as np
import math

if PLATFORM == P_WINDOWS:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from djitellopy import Tello
import mediapipe as mp

from subprocess import call
# call(["amixer", "-D", "pulse", "sset", "Master", "0%"])
battery_status=-1

class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon
 
        self.mpHands = mp.solutions.hands
        #self.hands = self.mpHands.Hands(self.mode, self.maxHands,
                                        #self.detectionCon, self.trackCon)
        self.hands = self.mpHands.Hands()
        
        self.mpDraw = mp.solutions.drawing_utils
 
    def findHands(self, img, draw=True):
        imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        # print(results.multi_hand_landmarks)
 
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms,
                                               self.mpHands.HAND_CONNECTIONS)
        return img
    
    def findPosition(self, img, handNo=0, draw=True):
 
        lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                # print(id, lm)
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                print(id, cx, cy)
                lmList.append([id, cx, cy])
                if draw:
                    cv.circle(img, (cx, cy), 15, (255, 0, 255), cv.FILLED)
        return lmList
                    

class CvFpsCalc(object):
    def __init__(self, buffer_len=1):
        self._start_tick = cv.getTickCount()
        self._freq = 1000.0 / cv.getTickFrequency()
        self._difftimes = deque(maxlen=buffer_len)

    def get(self):
        current_tick = cv.getTickCount()
        different_time = (current_tick - self._start_tick) * self._freq
        self._start_tick = current_tick

        self._difftimes.append(different_time)

        fps = 1000.0 / (sum(self._difftimes) / len(self._difftimes))
        fps_rounded = round(fps, 2)

        return fps_rounded


# def get_args():
#     print('## Reading configuration ##')
#     parser = configargparse.ArgParser(default_config_files=['config.txt'])

#     parser.add('-c', '--my-config', required=False, is_config_file=True, help='config file path')
#     parser.add("--device", type=int)
#     parser.add("--width", help='cap width', type=int)
#     parser.add("--height", help='cap height', type=int)
#     parser.add("--is_keyboard", help='To use Keyboard control by default', type=bool)
#     parser.add('--use_static_image_mode', action='store_true', help='True if running on photos')
#     parser.add("--min_detection_confidence",
#                help='min_detection_confidence',
#                type=float)
#     parser.add("--min_tracking_confidence",
#                help='min_tracking_confidence',
#                type=float)
#     parser.add("--buffer_len",
#                help='Length of gesture buffer',
#                type=int)

#     args = parser.parse_args()

#     return args


def select_mode(key, mode):
    number = -1
    if 48 <= key <= 57:  # 0 ~ 9
        number = key - 48
    if key == 110:  # n
        mode = 0
    if key == 107:  # k
        mode = 1
    if key == 104:  # h
        mode = 2
    return number, mode


def tello_battery(tello):
    global battery_status
    try:
        battery_status = tello.get_battery()
    except:
        battery_status = -1
    return

def hand_detect():
    ### PARAMETRES DE LA CAMERA
    width= 640
    height= 480

    ########### CONNEXION A TELLO ET ACTIVATION DE LA CAMERA 
    if ON_TELLO:
        tello =  Tello()
        tello.connect()
        tello.streamon()
    else:
        cam = cv.VideoCapture(0)

     
    #### initialisation du temps de départ et de fin
    pTime = 0
    cTime = 0

    # INSTANTIATION DE L'objet DETECTEUR DE MAINS
    detector= handDetector(detectionCon= 0.7)

    if PLATFORM == P_WINDOWS:
        #ACCES AU VOLUME DE L'ORDINATEUR
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        # volume.GetMute()
        # volume.GetMasterVolumeLevel()

        # Récupération du volume minimum et maximum
        volRange = volume.GetVolumeRange() 
        minVol = volRange[0]
        maxVol = volRange[1]
    else:
        minVol = 0
        maxVol = 200
    volBar = 400
    volPer = 0
    vol = 0

    while True:  # BOUCLE INFINIE
        
        # CApture de l'image en temps réel
        if ON_TELLO:
            frame_read = tello.get_frame_read()
            my_frame= frame_read.frame
        else:
            result, my_frame = cam.read()

        img = cv.resize(my_frame,(width, height))
        
        # Detection de la main et des 21 features avec les positions en X et Y de chaque feature
        img= detector.findHands(img)
        lmList=  detector.findPosition(img, draw=  False)
      
        
        
        if len(lmList) != 0:
            # print(lmList[4], lmList[8])
            x1, y1 = lmList[4][1], lmList[4][2] # Coordonnées X et Y du feature 4
            x2, y2 = lmList[8][1], lmList[8][2] # Coordonnées X et  Y du feature 8 
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2 # Coordonnées du milieu entre 4 et 8 
            
            
            cv.circle(img, (x1, y1), 15, (255, 0, 255), cv.FILLED)
            cv.circle(img, (x2, y2), 15, (255, 0, 255), cv.FILLED)
            cv.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv.circle(img, (cx, cy), 15, (255, 0, 255), cv.FILLED)
            
            length = math.hypot(x2 - x1, y2 - y1) # Calcul de la distance entre les doigts
            
            # Corrélation entre le volume et la distance entre les doigts
            vol = np.interp(length, [50, 300], [minVol, maxVol])
            volBar = np.interp(length, [50, 300], [400, 150])
            volPer = np.interp(length, [50, 300], [0, 100])
            print(int(length), vol)
            if PLATFORM == P_WINDOWS:
                volume.SetMasterVolumeLevel(vol, None)
            else:
                call(["amixer", "-D", "pulse", "sset", "Master", f"{vol}%"])

            # Passage de la couleur en vert lorsque la distannce est minime
            if length < 50:
                cv.circle(img, (cx, cy), 15, (0, 255, 0), cv.FILLED)
     
        cv.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
        cv.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv.FILLED)
        cv.putText(img, f'{int(volPer)} %', (40, 450), cv.FONT_HERSHEY_COMPLEX,
                    1, (255, 0, 0), 3)
     
        # Calcul de la fréquence de rafraichissement de l'image
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

            
        # Affichage de la fréquence de rafraichissement
        cv.putText(img, str(int(fps)), (40, 50), cv.FONT_HERSHEY_PLAIN, 3,
                        (255, 0, 255), 3)

        cv.imshow("Image", img)
        cv.waitKey(1)

def preprocess_image(frame, scale=100):
    # image = cv.resize(my_frame,(width, height))
    image = frame
    image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    image = cv.flip(image, 1)
    scale_percent = scale # percent of original size
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)

    image = cv.resize(image, dim, interpolation = cv.INTER_AREA)
    return image

def main():
    ON_TELLO=True
    # init global vars
    global gesture_buffer
    global gesture_id
    global battery_status
    battery_status = 0
    beat_coords = [0, 0, 60, 0]

    ### PARAMETRES DE LA CAMERA
    width= 640
    height= 480

    if ON_TELLO:
        tello =  Tello()
        tello.connect()
        tello.streamon()
    else:
        cam = cv.VideoCapture(0)



    print("********************STARTNING**************************")
    # Argument parsing
    # args = get_args()
    KEYBOARD_CONTROL = 1 #args.is_keyboard
    WRITE_CONTROL = False
    in_flight = False

    # Init Tello Controllers
    # gesture_controller = TelloGestureController(tello)
    # keyboard_controller = TelloKeyboardController(tello)

    # gesture_detector = GestureRecognition(args.use_static_image_mode, args.min_detection_confidence,
    #                                       args.min_tracking_confidence)
    # gesture_buffer = GestureBuffer(buffer_len=args.buffer_len)

    # def tello_control(key, keyboard_controller, gesture_controller):
    #     global gesture_buffer

    #     if KEYBOARD_CONTROL:
    #         keyboard_controller.control(key)
    #     else:
    #         gesture_controller.gesture_control(gesture_buffer)

    # rc a b c d 
    # a left/right
    # b forward/backward
    # c up/down
    # d yaw

    
    if ON_TELLO:
        print(f"Battery level: {tello_battery(tello)}")

        #### Declare control threads ####
        thr_battery = TelloThread(target=tello_battery, args=(tello,))

        tbeat = TelloBeat()
        thr_beat = TelloThread(target=tbeat)    
        # thr_hand_detect = TelloThread(target=hand_detect, args=(tello,))
        # thr_control = TelloThread(target=tello_control, args=(key, keyboard_controller, gesture_controller,))

        #### Start control threads ####
        thr_battery.start()
        thr_beat.start()
        ### do not forget to kill and join at the end.
        # t1.kill()
        # t1.join()
    else:
        tbeat = TelloBeat()
        # thr_beat = TelloThread(target=tbeat)

    # FPS Measurement
    cv_fps_calc = CvFpsCalc(buffer_len=10)

    mode = 0
    number = -1

    # tello.move_down(20)
    print("in loop")
    while True:
        # CApture de l'image en temps réel
        if ON_TELLO:
            frame_read = tello.get_frame_read()
            my_frame= frame_read.frame
        else:
            result, my_frame = cam.read()

        image = preprocess_image(my_frame)
        
        fps = cv_fps_calc.get()

        # Process Key (ESC: end)
        key = cv.waitKey(1) & 0xff
        # print(key)
        if key == 27:  # ESC
            print("ESC pressed")
            break
        elif key == 32:  # Space
            print("SPACE pressed")

            if not in_flight:
                # Take-off drone
                tello.takeoff()
                in_flight = True

            elif in_flight:
                # Land tello
                tello.land()
                in_flight = False
        elif key == ord('s'):
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            tello.send_rc_control(0, 0, 0, 0)  # Stop moving
        elif key == ord('f'):
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            tello.send_rc_control(0, 40, 0, 0)  # forward moving
        elif key == ord('b'):
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            tello.send_rc_control(0, -40, 0, 0)  # back moving
        elif key == ord('l'):
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            tello.send_rc_control(-40, 0, 0, 0)  # left moving
        elif key == ord('r'):
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            tello.send_rc_control(40, 0, 0, 0)  # right moving

        elif key == ord('u'):
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            tello.send_rc_control(0, 0, 100, 0)  # up moving
        elif key == ord('d'):
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            tello.send_rc_control(0, 0, -100, 0)  # down moving
        elif key == ord('g'):
            KEYBOARD_CONTROL = False
        elif key == ord('n'):
            mode = 1
            WRITE_CONTROL = True
            KEYBOARD_CONTROL = True
        elif key == ord('k'):
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            if ON_TELLO:
                print(tello_battery(tello))
        elif key == ord('t'):
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            tbeat.bip()
            c = [beat_coords[i]*-1 for i in range(len(beat_coords))]
            beat_coords = c.copy()
            tello.send_rc_control(beat_coords[0],beat_coords[1],beat_coords[2],beat_coords[3], )  
            print(beat_coords)

        if WRITE_CONTROL:
            number = -1
            if 48 <= key <= 57:  # 0 ~ 9
                number = key - 48

   
         
        # print('Resized Dimensions : ',resized.shape)
         
        # image = cv.imread('smile.png')
        

        # debug_image, gesture_id = gesture_detector.recognize(image, number, mode)
        # gesture_buffer.add_gesture(gesture_id)

        # # Start control thread
        # threading.Thread(target=tello_control, args=(key, keyboard_controller, gesture_controller,)).start()
        # threading.Thread(target=tello_battery, args=(tello,)).start()

        # debug_image = gesture_detector.draw_info(debug_image, fps, mode, number)

        # Battery status and image rendering
        cv.putText(image, "Shape/channels: {}".format(image.shape), (5, 550 - 5),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv.putText(image, "Battery: {}".format(battery_status), (40, 50), cv.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
        cv.imshow('Tello Gesture Recognition', image)

    if ON_TELLO:
        tello.streamoff()

        tello.land()
        tello.end()


        thr_battery.kill()
        thr_battery.join()

        thr_beat.kill()
        thr_beat.join()


    cv.destroyAllWindows()


from tello_sound import TelloBeat

if __name__ == '__main__':
    
    if len( sys.argv ) == 2:
        if sys.argv[1] in [0,1]:
            ON_TELLO = str(sys.argv[1])
        

    # beat()
    main()
    # hand_detect()