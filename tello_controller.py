#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configargparse

import cv2 as cv

# from gestures.tello_gesture_controller import TelloGestureController
# from utils import cvfpscalc
from collections import deque

from djitellopy import Tello
# from gestures import *

import threading

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


def get_args():
    print('## Reading configuration ##')
    parser = configargparse.ArgParser(default_config_files=['config.txt'])

    parser.add('-c', '--my-config', required=False, is_config_file=True, help='config file path')
    parser.add("--device", type=int)
    parser.add("--width", help='cap width', type=int)
    parser.add("--height", help='cap height', type=int)
    parser.add("--is_keyboard", help='To use Keyboard control by default', type=bool)
    parser.add('--use_static_image_mode', action='store_true', help='True if running on photos')
    parser.add("--min_detection_confidence",
               help='min_detection_confidence',
               type=float)
    parser.add("--min_tracking_confidence",
               help='min_tracking_confidence',
               type=float)
    parser.add("--buffer_len",
               help='Length of gesture buffer',
               type=int)

    args = parser.parse_args()

    return args


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
        battery_status = tello.get_battery()[:-2]
    except:
        battery_status = -1

def main():
    # init global vars
    global gesture_buffer
    global gesture_id
    global battery_status

    # Argument parsing
    args = get_args()
    KEYBOARD_CONTROL = args.is_keyboard
    WRITE_CONTROL = False
    in_flight = False

    # Camera preparation
    tello = Tello()
    print("connect")
    tello.connect()
    tello.streamon()

    cap = tello.get_frame_read()

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



    # FPS Measurement
    cv_fps_calc = CvFpsCalc(buffer_len=10)

    mode = 0
    number = -1
    battery_status = -1

    # tello.move_down(20)
    print("in loop")
    while True:
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
        elif key == ord('g'):
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
            tello.send_rc_control(40, 0, 0, 0)  # left moving
        elif key == ord('r'):
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            tello.send_rc_control(-40, 0, 0, 0)  # right moving

        elif key == ord('u'):
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            tello.send_rc_control(0, 0, 10, 0)  # up moving
        elif key == ord('d'):
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            tello.send_rc_control(0, 0, -10, 0)  # down moving
        elif key == ord('g'):
            KEYBOARD_CONTROL = False
        elif key == ord('n'):
            mode = 1
            WRITE_CONTROL = True
            KEYBOARD_CONTROL = True

        if WRITE_CONTROL:
            number = -1
            if 48 <= key <= 57:  # 0 ~ 9
                number = key - 48

        # Camera capture
        image = cap.frame
        image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        scale_percent = 60 # percent of original size
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)

        image = cv.resize(image, dim, interpolation = cv.INTER_AREA)
         
        # print('Resized Dimensions : ',resized.shape)
         
        # image = cv.imread('smile.png')
        

        # debug_image, gesture_id = gesture_detector.recognize(image, number, mode)
        # gesture_buffer.add_gesture(gesture_id)

        # # Start control thread
        # threading.Thread(target=tello_control, args=(key, keyboard_controller, gesture_controller,)).start()
        threading.Thread(target=tello_battery, args=(tello,)).start()

        # debug_image = gesture_detector.draw_info(debug_image, fps, mode, number)

        # Battery status and image rendering
        cv.putText(image, "Battery: {}".format(battery_status), (5, 600 - 5),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv.putText(image, "Shape/channels: {}".format(image.shape), (5, 550 - 5),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv.imshow('Tello Gesture Recognition', image)

    tello.streamoff()

    tello.land()
    tello.end()
    cv.destroyAllWindows()


if __name__ == '__main__':
    main()