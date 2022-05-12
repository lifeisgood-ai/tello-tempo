#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import configargparse
import os, sys, time

import platform
import djitellopy
from  tello_sound import TelloSound
from tello_thread import TelloThread
from tello_dance import TelloDance
from tello_hand_detector import HandDetector

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

import cv2 as cv
from pynput import keyboard

def catch_interrupting():
    print('Interrupted')
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)

def main(status):
    tello_handler = TelloHandler(status)
    tello_handler.init_drone()
    try:
        tello_handler.capture()
        tello_handler.stop_drone()
    except KeyboardInterrupt:
        tello_handler.stop_drone()
        catch_interrupting()

class TelloHandler(object):
    """
    TelloHandler builds keyboard controls on top of TelloPy as well
    as generating images from the video stream and enabling opencv support
    """

    def __init__(self, status):
        self.on_tello = status


        self.prev_flight_data = None
        self.record = False
        self.tracking = False
        self.keydown = False
        self.date_fmt = '%Y-%m-%d_%H%M%S'
        self.speed = 50
        self.drone = djitellopy.Tello()
        self.init_drone()
        self.init_controls()

        # container for processing the packets into frames
        #self.container = av.open(self.drone.get_video_stream())
        #self.vid_stream = self.container.streams.video[0]
        self.out_file = None
        self.out_stream = None
        self.out_name = None
        self.start_time = time.time()

        # tracking a color
        green_lower = (30, 50, 50)
        green_upper = (80, 255, 255)
        #red_lower = (0, 50, 50)
        # red_upper = (20, 255, 255)
        # blue_lower = (110, 50, 50)
        # upper_blue = (130, 255, 255)
        self.img_width= 640
        self.img_height= 480

        self.track_cmd = ""
        # self.tracker = Tracker(self.vid_stream.height,
        #                       self.vid_stream.width,
        #                       green_lower, green_upper)
        self.INTERRUPT = False
        self.DELAY = 2 # secnods
        self.VALID_CHANGE = False
        self.state = 0

        self.tello_sound = TelloSound()
        self.tello_dance = TelloDance(self.drone)
        # self.timeout = TelloThread(target=self.validate_finger_change, args=(self.state, ))
        self.tello_thread = TelloThread()
        self.hand_detector = HandDetector()



    def dance(self):
        self.on_dance = True
        # make movements
        # sync it with music

    def change_state(self, state):
        if self.state == state:
            pass
        else:
            print("State changed...")
            self.state = state
            if self.state == 1:
                # start music/dance
                print("playing music/dance")
                self.tello_sound.play_music()

            elif self.state == 2:
                # stop music/dance
                print("stopping music/dance")
                self.tello_sound.stop_music()

            elif self.state == 3:
                # change music/dance
                self.tello_dance.swing()

            elif self.state == 4:
                self.tello_dance.stop()

            elif self.state == 5:
                if not self.drone.is_flying:
                    self.drone.takeoff()
                self.change_state(1)
                # takeoff - thumb up
                pass
            elif self.state == 100:
                # change volume sound
                pass
            else:
                pass

    # def validate_finger_change(self, state):
    #     print("## validate_finger_change")
    #     timeout = time.time() + self.DELAY
    #
    #     while not self.VALID_CHANGE:
    #         if time.time() > timeout:
    #             self.VALID_CHANGE = True
    #             self.state = state
    #             time.sleep(.1)
    #             print("## Finger change confirmed")
    #
    # def on_finger_change(self, state):
    #     if self.state != state :
    #         print("## Change of state")
    #         self.VALID_CHANGE = False
    #         if self.timeout.is_alive():
    #             self.timeout.kill()
    #             self.timeout.join()
    #         self.timeout = TelloThread(target=self.validate_finger_change, args=(state, ))
    #         self.timeout.start()
    #         #self.validate_finger_change(state)

    # Image handling
    def capture(self):

        if self.on_tello:
            print("Getting image from drone")
            frame_read = self.drone.get_frame_read()
            my_frame = frame_read.frame
        else:
            print("Getting image from webcam")
            self.cam = cv.VideoCapture(0)

        while not self.INTERRUPT:
            # Capture de l'image en temps réel
            if self.on_tello:
                frame_read = self.drone.get_frame_read()
                my_frame = frame_read.frame
            else:
                result, my_frame = self.cam.read()


            #image = self.preprocess_image(my_frame)
            image = cv.resize(my_frame, (self.img_width, self.img_height))
            image = cv.flip(image, 1)

            image, state = self.hand_detector.process_fingers(image)
            # image, state = self.hand_detector.process_finger_counter(image)

            self.change_state(state)
            # self.on_finger_change(state)
            # if self.VALID_CHANGE:
            #     self.change_state(state)
            #    self.VALID_CHANGE=False

            # Process Key (ESC: end)
            key = cv.waitKey(1) & 0xff

            # Battery status and image rendering
            cv.putText(image, "Shape/channels: {}".format(image.shape), (5, 30),
                       cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv.imshow('Tello Gesture Recognition', image)

        #cv.destroyAllWindows()


    def preprocess_image(self, frame, scale=100):
        # image = cv.resize(my_frame,(width, height))
        image = frame
        image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        image = cv.flip(image, 1)
        scale_percent = scale  # percent of original size
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)

        image = cv.resize(image, dim, interpolation=cv.INTER_AREA)
        return image

    def interrupt_all(self):
        self.drone.send_rc_control(0, 0, 0, 0)
        self.stop_drone()
        self.INTERRUPT = True
        print("Killing cv window...")
        try:
            cv.destroyAllWindows()
        except Exception as e:
            print(e)
        print("Wait for 2 seconds...")
        time.sleep(2)
        print("RIP...")
        catch_interrupting()

    def stall(self):
        self.drone.send_rc_control(0, 0, 0, 0)

    # Drone configuraitoon hanlding
    def init_drone(self):
        """Connect, uneable streaming and subscribe to events"""
        if self.on_tello:
            # self.drone.log.set_level(2)
            self.stall()
            self.drone.connect()
            self.drone.streamon()
            # self.drone.subscribe(self.drone.EVENT_FLIGHT_DATA,
            #                      self.flight_data_handler)
            # self.drone.subscribe(self.drone.EVENT_FILE_RECEIVED,
            #                      self.handle_flight_received)

    def stop_drone(self):
        # End of processing
        print("Stopping drone...")
        if self.on_tello:
            if self.drone.is_flying:
                self.drone.land()
            self.drone.stop()

    # Keuborard Handling
    def on_press(self, keyname):
        """handler for keyboard listener"""
        # 'Key.tab': lambda speed: self.drone.takeoff(),
        if self.keydown:
            return
        try:
            self.keydown = True
            keyname = str(keyname).strip('\'')
            #print('+' + keyname)
            if keyname == 'Key.esc':
                #self.drone.quit()
                exit(0)
            if keyname in self.controls:
                key_handler = self.controls[keyname]
                if isinstance(key_handler, str):
                    #print("press", key_handler)
                    getattr(self.drone, key_handler)(self.speed)
                else:
                    #print("press", key_handler)
                    key_handler()
        except AttributeError:
            print('special key {0} pressed'.format(keyname))
        except Exception as e:
            """
            Ugly catch to get any error from drone api
            """
            print(e)


    def on_release(self, keyname):
        """Reset on key up from keyboard listener"""
        self.keydown = False
        keyname = str(keyname).strip('\'')
        #print('-' + keyname)
        if keyname in self.controls:
            key_handler = self.controls[keyname]
            print('... released')
            #if isinstance(key_handler, str):
                #print("release ", key_handler)
            #    getattr(self.drone, key_handler)(0)
            #else:
            #    key_handler()


    def init_controls(self):
        """Define keys and add listener"""
        self.controls = {
            'w': 'forward',
            's': 'backward',
            'a': 'left',
            'd': 'right',
            'Key.space': 'up',
            'Key.shift': 'down',
            #'Key.shift_r': 'down',
            'r': 'counter_clockwise',
            'e': 'clockwise',
            'i': lambda: self.drone.flip_forward(),
            'k': lambda: self.drone.flip_back(),
            'j': lambda: self.drone.flip_left(),
            'l': lambda: self.drone.flip_right(),
            # arrow keys for fast turns and altitude adjustments
            'Key.left': lambda: self.drone.counter_clockwise(),
            'Key.right': lambda: self.drone.clockwise(),

            'p': lambda: print("hello"),
            't': lambda: self.toggle_tracking(),
            'y': lambda: self.toggle_recording(),
            'z': lambda: self.toggle_zoom(),
            'Key.enter': lambda: self.take_picture(),


            # validated buttons
            'b': lambda: self.change_state(1),
            'n': lambda: self.change_state(2),
            'q': lambda: self.interrupt_all(),
            'Key.tab': lambda: self.drone.takeoff(),
            'Key.backspace': lambda: self.drone.land(),
            'c': lambda: self.change_state(3),
            'v': lambda: self.change_state(4),
            'Key.up': lambda: self.drone.move_up(20),
            'Key.down': lambda: self.drone.move_down(20),
            'Key.left': lambda: self.drone.move_left(20),
            'Key.right': lambda: self.drone.move_right(20),
            'x': lambda: self.stall()

        }
        self.key_listener = keyboard.Listener(on_press=self.on_press,
                                              on_release=self.on_release)
        self.key_listener.start()
        # self.key_listener.join()

if __name__ == '__main__':

    # status == 0 => webcam
    # status == 1 => drone
    status = 1
    # beat()
    main(status)
    # hand_detect()