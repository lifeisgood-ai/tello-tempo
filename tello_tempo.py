#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import configargparse
import os, sys, time

import platform
import djitellopy
from tello_sound import TelloSound
from tello_thread import TelloThread
from tello_dance import TelloDance
from tello_hand_detector import HandDetector
from threading import Thread, Event
from tello_bridge import TelloBridge

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
    #b=0
    # tello_sound = TelloSound(b)
    # tello_sound.load_libro()
    # tello_sound.go()

    #sys.exit(0)
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

        self.keydown = False
        self.speed = 50

        self.drone = djitellopy.Tello()
        self.init_drone()
        self.init_controls()

        self.img_width = 640
        self.img_height = 480

        self.track_cmd = ""
        # self.tracker = Tracker(self.vid_stream.height,
        #                       self.vid_stream.width,
        #                       green_lower, green_upper)
        self.INTERRUPT = False
        self.TIMEOUT_FINGERS = 0.5  # seconds before validating a count of fingers

        self.INIT_STATE = 0
        self.state = self.INIT_STATE
        self.state_validation = self.INIT_STATE

        self.cb = 0

        self.tello_bridge = TelloBridge()
        self.tello_sound = TelloSound(self.tello_bridge)
        self.tello_dance = TelloDance(self.drone, self.tello_bridge)

        self.hand_detector = HandDetector()


        # Event and Thread to handle timeout of finger detection
        self.evt_restart_timer = Event()
        self.evt_stop_counter = Event()
        self.evt_validate_state = Event()

        self.evt_restart_timer.clear()
        self.evt_stop_counter.clear()
        self.evt_validate_state.clear()

        self.timeout_thread = TelloThread(target=self.th_counter,
                                          args=(self.evt_restart_timer,
                                                self.evt_validate_state,
                                                self.evt_stop_counter,))

        self.dance_thread = TelloThread(target=self.tello_dance.swing1  ,
                                        args=("daddy",))

        self.sound_thread = TelloThread(target=self.tello_sound.go)

    def change_state(self, state):
        """

        Args:
            state: the int value returned by detection of fingers or with keybord call

        Returns:
            void
        """
        if self.state == state:
            pass
        else:
            print("State changed...")
            self.state = state
            if self.state == 0:
                print('Do nothing state 0')
                pass
            elif self.state == 1:
                # start music/dance
                print("playing music/dance")
                self.tello_sound.play_music()

            elif self.state == 2:
                # stop music/dance
                print("stopping music/dance")
                self.tello_sound.stop_music()

            elif self.state == 3:
                # change music/dance
                self.dance_thread.start()
                self.sound_thread.start()
                #self.tello_dance.swing()

            elif self.state == 4:
                #self.tello_dance.stop()
                self.dance_thread.kill()
                self.dance_thread.join()
                self.sound_thread.kill()
                self.sound_thread.join()
                self.drone.send_rc_control(0, 0, 0, 0)

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

    def capture(self):
        """
        Handles the cv image frame capture loop

        Returns:

        """
        self.timeout_thread.start()
        state = self.INIT_STATE
        previous_state = self.INIT_STATE

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

            # image = self.preprocess_image(my_frame)
            image = cv.resize(my_frame, (self.img_width, self.img_height))
            image = cv.flip(image, 1)

            image, state = self.hand_detector.process_fingers(image)

            if previous_state != state:
                print(previous_state, '->', state)
                self.evt_stop_counter.set()
                self.check_change(state)

            if self.evt_validate_state.is_set():
                self.evt_validate_state.clear()
                self.change_state(self.state_validation)

            # Process Key (ESC: end)
            key = cv.waitKey(1) & 0xff

            # Battery status and image rendering
            cv.putText(image, "Shape/channels: {}".format(image.shape), (5, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv.putText(image, str(self.state), (500, 375), cv.FONT_HERSHEY_PLAIN, 10, (255, 0, 0), 25)

            cv.imshow('Tello Gesture Recognition', image)

            previous_state = state

    def check_change(self, state):
        """

        Args:
            state: int value to check

        Returns: void

        """
        self.state_validation = state
        self.evt_restart_timer.set()

    def th_counter(self, evt_restart_timer, evt_validate_state, evt_stop_counter):
        """
        Function executer in the thread
        Args:
            evt_restart_timer:
            evt_validate_state:
            evt_stop_counter:

        Returns:

        """
        d = self.TIMEOUT_FINGERS
        while True:
            if evt_restart_timer.is_set():
                evt_restart_timer.clear()
                evt_stop_counter.clear()
                timeout = time.time() + d
                #print(f"Checking {self.checking_state}...")
                while True:
                    if evt_stop_counter.is_set():
                        #print("Timer interrupted")
                        break
                    if time.time() > timeout:
                        #print("Change validated")
                        evt_validate_state.set()
                        break
                    time.sleep(.05)

        time.sleep(.05)

    def preprocess_image(self, frame, scale=100):
        """
        Converts image to B&W, reduces size, flips image
        Args:
            frame:
            scale:

        Returns:

        """
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
        """
        Function to cleanly stop the drone

        Returns:

        """
        self.drone.send_rc_control(0, 0, 0, 0)
        self.stop_drone()
        self.INTERRUPT = True
        print("Killing cv window...")
        try:
            cv.destroyAllWindows()
        except Exception as e:
            print(e)
        self.stop_threads()
        print("Wait for 2 seconds...")
        time.sleep(2)
        print("RIP...")
        catch_interrupting()

    def stop_threads(self):
        """
        Stop all thread declared

        TODO: handle a list of threads instead

        Returns:

        """
        self.timeout_thread.kill()
        self.timeout_thread.join()
        self.tello_thread.kill()
        self.tello_thread.join()

        self.key_listener.join()

    def stall(self):
        """
        Appears to be useful for keyboard control :-|
        Returns:

        """
        self.drone.send_rc_control(0, 0, 0, 0)

    # Drone configuration handling
    def init_drone(self):
        """
        Connect, enable streaming and subscribe to events

        Returns:

        """
        if self.on_tello:
            # self.drone.log.set_level(2)
            print("Connecting to drone")
            self.drone.connect()

            # print("Sending 'command' to drone")
            # self.drone.send_control_command("command")

            print("Stalling drone")
            self.stall()

            print("Activating stream on drone")
            self.drone.streamon()

            #time.sleep(3)
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
            # print('+' + keyname)
            if keyname == 'Key.esc':
                # self.drone.quit()
                exit(0)
            if keyname in self.controls:
                key_handler = self.controls[keyname]
                if isinstance(key_handler, str):
                    # print("press", key_handler)
                    getattr(self.drone, key_handler)(self.speed)
                else:
                    # print("press", key_handler)
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
        # print('-' + keyname)
        if keyname in self.controls:
            key_handler = self.controls[keyname]
            print('... released')
            # if isinstance(key_handler, str):
            # print("release ", key_handler)
            #    getattr(self.drone, key_handler)(0)
            # else:
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
            # 'Key.shift_r': 'down',
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
    #   cstatus = 0
    # beat()
    main(status)
    # hand_detect()
