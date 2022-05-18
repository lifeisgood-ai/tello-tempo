#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
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

    # tello_handler.init_drone()

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

        # Create the drone
        self.drone = djitellopy.Tello()
        self.init_drone()
        self.init_controls()

        self.img_width = 640*2
        self.img_height = 480*2

        self.track_cmd = ""
        self.INTERRUPT = False
        self.TIMEOUT_FINGERS = 0.5  # seconds before validating a count of fingers
        self.MOVE_DISTANCE  = 50

        self.INIT_STATE = 0
        self.state = self.INIT_STATE
        self.state_validation = self.INIT_STATE

        self.cb = 0

        # Declare modules
        self.tello_bridge = TelloBridge()
        self.tello_sound = TelloSound(self.tello_bridge)
        self.tello_dance = TelloDance(self.drone, self.tello_bridge)
        self.hand_detector = HandDetector()

        # Event and Thread to handle th_counter timeout of finger detection
        self.evt_restart_timer = Event()
        self.evt_stop_counter = Event()
        self.evt_validate_state = Event()

        self.evt_restart_timer.clear()
        self.evt_stop_counter.clear()
        self.evt_validate_state.clear()

        # Declare thread and events
        self.timeout_thread = TelloThread(target=self.th_counter,
                                          args=(self.evt_restart_timer,
                                                self.evt_validate_state,
                                                self.evt_stop_counter,))

        #self.dance_thread = TelloThread(target=self.tello_dance.swing1  , args=("default1",))
        self.dance_thread = TelloThread(target=self.tello_dance.dance_now)

        # self.sound_thread = TelloThread(target=self.tello_sound.go_for_music)
        self.sound_thread = self.create_thread(self.tello_sound.go_for_music, "default1")

        self.threads_list = [self.timeout_thread, self.dance_thread, self.sound_thread]

    def create_thread(self, func, *args):
        return TelloThread(target=func, args=(args,))

    def change_state(self, state):
        """
        Handles the command to be launched when there is a valid change in state

        0: state defaults to 0, nothing to do
        other values: change accordingly, no limit in number
        100: sound volume is handled in handdetector class

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
                self.tello_sound.play_music(name="audio/daddys_car.mp3")

            elif self.state == 2:
                # stop music/dance
                print("stopping music/dance")
                self.tello_sound.stop_music()

            elif self.state == 3:
                # change music/dance
                self.sound_thread =  self.create_thread(self.tello_sound.go_for_music, "default1")
                self.dance_thread = self.create_thread(self.tello_dance.dance_now)
                self.dance_thread.start()
                self.sound_thread.start()
                #self.tello_dance.swing()

            elif self.state == 4:
                #self.tello_dance.stop()
                self.tello_sound.stop_music()
                self.dance_thread.kill()
                self.dance_thread.join()
                self.sound_thread.kill()
                self.sound_thread.join()
                self.drone.send_rc_control(0, 0, 0, 0)

            elif self.state == 5:
                if not self.drone.is_flying:
                    self.drone.takeoff()
                #self.change_state(1)
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
            cv.putText(image, str(self.state), (500*2, 375*2), cv.FONT_HERSHEY_PLAIN, 10, (255, 0, 0), 25)

            cv.imshow('Tello Gesture Recognition', image)

            previous_state = state

    def check_change(self, state):
        """
        Resets counter's timer and updates the value of the state to be validated `state_validation`

        Args:
            state: int value to check

        Returns: void

        """
        self.state_validation = state
        self.evt_restart_timer.set()

    def th_counter(self, evt_restart_timer, evt_validate_state, evt_stop_counter):
        """
        Timer that sends events on timeout reached and is restarted/stopped on receiving the corresponding event

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
        self.stop_threads_listeners()
        print("Wait for 2 seconds...")
        time.sleep(2)
        print("RIP...")
        catch_interrupting()

    def stop_threads_listeners(self):
        """
        Stop all threads declared and listeners as well
        To be tested

        Returns:

        """
        for th in self.threads_list:
            th.kill()
            th.join()

        self.key_listener.join()

    def stall(self):
        """
        Appears to be useful ... :-|
        Returns:
        """
        self.drone.send_rc_control(0, 0, 0, 0)

    def battery_level(self):
        print(f"Battery level is {self.drone.get_battery()}%")

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
        if self.keydown:
            return
        try:
            self.keydown = True
            keyname = str(keyname).strip('\'')
            if keyname == 'Key.esc':
                exit(0)
            if keyname in self.controls:
                key_handler = self.controls[keyname]
                if isinstance(key_handler, str):
                    getattr(self.drone, key_handler)(self.speed)
                else:
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
        if keyname in self.controls:
            key_handler = self.controls[keyname]
            print('... released')

    def init_controls(self):
        """Define keys and add listener"""
        self.controls = {
            # 'w': 'forward',
            # 's': 'backward',
            # 'a': 'left',
            # 'd': 'right',
            # 'Key.space': 'up',
            # 'Key.shift': 'down',
            # # 'Key.shift_r': 'down',
            # 'r': 'counter_clockwise',
            # 'e': 'clockwise',
            'i': lambda: self.drone.flip_forward(),
            'k': lambda: self.drone.flip_back(),
            'j': lambda: self.drone.flip_left(),
            'l': lambda: self.drone.flip_right(),
            # # arrow keys for fast turns and altitude adjustments
            # 'Key.left': lambda: self.drone.counter_clockwise(),
            # 'Key.right': lambda: self.drone.clockwise(),
            #
            # 'p': lambda: print("hello"),
            # 't': lambda: self.toggle_tracking(),
            # 'y': lambda: self.toggle_recording(),
            # 'z': lambda: self.toggle_zoom(),
            'Key.enter': lambda: self.tello_dance.draw_spirale(),

            # validated buttons
            'b': lambda: self.change_state(1),
            'n': lambda: self.change_state(2),
            'q': lambda: self.interrupt_all(),
            'Key.tab': lambda: self.drone.takeoff(),
            'Key.backspace': lambda: self.drone.land(),
            'c': lambda: self.change_state(3),
            'v': lambda: self.change_state(4),
            'Key.up': lambda: self.drone.move_up(self.MOVE_DISTANCE),
            'Key.down': lambda: self.drone.move_down(self.MOVE_DISTANCE),
            'Key.left': lambda: self.drone.move_left(self.MOVE_DISTANCE),
            'Key.right': lambda: self.drone.move_right(self.MOVE_DISTANCE),
            'x': lambda: self.stall()

        }
        self.key_listener = keyboard.Listener(on_press=self.on_press,
                                              on_release=self.on_release)
        self.key_listener.start()
        # self.key_listener.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--camera', type=int, default=1, help="Set to 1 to use drone camera (and drone) or webcam (0)")
    config = parser.parse_args()

    status = config.camera
    main(status)
