
import platform
PLATFORM = platform.system()
P_WINDOWS = 'Windows'
P_LINUX = 'Linux'
P_DARWIN = 'Darwin'
if PLATFORM == P_WINDOWS:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from subprocess import call
# call(["amixer", "-D", "pulse", "sset", "Master", "0%"])

import mediapipe as mp
import cv2 as cv
import numpy as np
import math
import time

class HandDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        # self.hands = self.mpHands.Hands(self.mode, self.maxHands,
        # self.detectionCon, self.trackCon)
        self.hands = self.mpHands.Hands()
        self.mpDraw = mp.solutions.drawing_utils
        self.init_sound_parameters()

        # self.state [0..]
        # 100 reglage volume
        # 1 doigt 1 ...
        self.hand_state = 0

    def init_sound_parameters(self):
        if PLATFORM == P_WINDOWS:
            # ACCES AU VOLUME DE L'ORDINATEUR
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = cast(interface, POINTER(IAudioEndpointVolume))
            # self.volume.GetMute()
            # self.volume.GetMasterVolumeLevel()

            # Récupération du volume minimum et maximum
            volRange = self.volume.GetVolumeRange()
            self.minVol = volRange[0]
            self.maxVol = volRange[1]
        else:
            self.minVol = 0
            self.maxVol = 200
        self.volBar = 400
        self.volPer = 0
        self.vol = 0

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

    def process_volume(self, img):
        pTime = 0
        cTime = 0

        # Detection de la main et des 21 features avec les positions en X et Y de chaque feature
        img = self.findHands(img)
        lmList = self.findPosition(img, draw=False)

        if len(lmList) != 0:
            # print(lmList[4], lmList[8])
            x1, y1 = lmList[4][1], lmList[4][2]  # Coordonnées X et Y du feature 4
            x2, y2 = lmList[8][1], lmList[8][2]  # Coordonnées X et  Y du feature 8
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # Coordonnées du milieu entre 4 et 8
            # compute real angle
            angle= 40
            if angle < 30:
                self.hand_state=100
                cv.circle(img, (x1, y1), 15, (255, 0, 255), cv.FILLED)
                cv.circle(img, (x2, y2), 15, (255, 0, 255), cv.FILLED)
                cv.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                cv.circle(img, (cx, cy), 15, (255, 0, 255), cv.FILLED)

                length = math.hypot(x2 - x1, y2 - y1)  # Calcul de la distance entre les doigts

                # Corrélation entre le volume et la distance entre les doigts
                self.vol = np.interp(length, [50, 300], [self.minVol, self.maxVol])
                self.volBar = np.interp(length, [50, 300], [400, 150])
                self.volPer = np.interp(length, [50, 300], [0, 100])
                print(int(length), self.vol)
                if PLATFORM == P_WINDOWS:
                    self.volume.SetMasterVolumeLevel(self.vol, None)
                else:
                    call(["amixer", "-D", "pulse", "sset", "Master", f"{self.vol}%"])

                # Passage de la couleur en vert lorsque la distannce est minime
                if length < 50:
                    cv.circle(img, (cx, cy), 15, (0, 255, 0), cv.FILLED)

        cv.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
        cv.rectangle(img, (50, int(self.volBar)), (85, 400), (255, 0, 0), cv.FILLED)
        cv.putText(img, f'{int(self.volPer)} %', (40, 450), cv.FONT_HERSHEY_COMPLEX,
                    1, (255, 0, 0), 3)

        # Calcul de la fréquence de rafraichissement de l'image
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        return img


