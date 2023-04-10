"""
Created on 23.11.2022

@author: Florian Huber
"""

import logging

import time
import argparse
import socket
import struct
import numpy as np
import threading

# import cf functions
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.crazyflie.log import LogConfig
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

import cv2

# set constants
LOW_BAT = 3.0  # if the cf reaches this battery voltage level, it should land
TAKEOFF_HEIGHT = 0.5
MAX_MARKER_ID = 3
URI = uri_helper.uri_from_env(default='radio://0/100/2M/E7E7E7E701')


def get_cf_data(scf):
    """
    fetches logging information from the crazyflie
    :param scf: id of SyncCrazyflie
    :return: double: v_bat
             double: yaw
             double: pitch
             double: roll
             battery level and current yaw, pitch, roll values
    """

    # fetch parameter data from cf and extract information
    with SyncLogger(scf, log_stabilizer) as logger:
        # logger.connect()
        for entry in logger:
            data = entry[1]
            vbat = data.get('pm.vbat')
            yaw = data.get('stabilizer.yaw')
            pitch = data.get('stabilizer.pitch')
            roll = data.get('stabilizer.roll')
            time.sleep(0.02)
            return vbat, yaw, pitch, roll


def rx_bytes(size):
    """
    fetches data from the AI deck over wi-fi
    :param size: size of data segment to fetch
    :return: bytearray: data
             the received data in a bytearray
    """

    data = bytearray()
    while len(data) < size:
        data.extend(client_socket.recv(size - len(data)))
    return data


def get_image_from_ai_deck():
    """
    function to fetch image from the AI deck
    :return: -
             saves the captured image in the global variable 'image'
    """
    # Get the info
    while True:
        global image
        global stop_thread_flag
        if stop_thread_flag:
            break
        packet_info_raw = rx_bytes(4)
        [length, _, _] = struct.unpack('<HBB', packet_info_raw)
        img_header = rx_bytes(length - 2)
        [magic, _, _, _, image_format, size] = struct.unpack('<BHHBBI', img_header)
        if magic == 0xBC:
            # Receive the image, this will be split up in packages of some size
            img_stream = bytearray()

            while len(img_stream) < size:
                packet_info_raw = rx_bytes(4)
                [length, _, _] = struct.unpack('<HBB', packet_info_raw)
                chunk = rx_bytes(length - 2)
                img_stream.extend(chunk)

            if image_format == 0:
                # RAW image format streamed
                img_gray = np.frombuffer(img_stream, dtype=np.uint8)
                img_gray.shape = (244, 324)

            else:
                # JPEG encoded image format streamed
                # stores the image temporary in this path
                with open("../wifi_streaming/imgBuffer/img.jpeg", "wb") as im:
                    im.write(img_stream)
                np_arr = np.frombuffer(img_stream, np.uint8)
                img_gray = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

            # set global variable
            image = img_gray


class CF:
    """
    class for crazyflie parameters, functions and methods
    """

    def __init__(self, scf):
        """
        constructor for a crazyflie object
        :param scf: id of SyncCrazyflie
        """

        # psi --> yaw
        # theta --> pitch
        # phi --> roll
        self.v_bat, self.psi, self.theta, self.phi = get_cf_data(scf)
        self.scf = scf
        self.mc = MotionCommander(scf)

    def decks_attached(self):
        """
        function checks if AI and flow deck are attached
        :return: boolean: return_code
                 True if both decks are attached
                 False is at least one deck is not detected
        """

        # detects if extension decks are connected
        flow_deck_attached = self.scf.cf.param.get_value(complete_name='deck.bcFlow2', timeout=5)
        ai_deck_attached = self.scf.cf.param.get_value(complete_name='deck.bcAI', timeout=5)
        return_code = True
        if flow_deck_attached == 0:
            print("No flow deck detected!")
            return_code = False

        if ai_deck_attached == 0:
            print("No ai deck detected!")
            return_code = False

        return return_code

    def get_battery_level(self):
        """
        fetches battery level from crazyflie
        :return: double: v_bat
                 battery voltage in V
        """

        # check current battery voltage of cf
        voltage, _, _, _ = get_cf_data(self.scf)
        time.sleep(0.02)
        self.v_bat = voltage
        return voltage

    def get_yaw(self):
        """
        fetches battery level from crazyflie
        :return: double: yaw
                 angle of yaw in degrees
        """

        # returns current yaw
        _, yaw, _, _ = get_cf_data(self.scf)
        time.sleep(0.02)
        self.psi = yaw
        return yaw

    def takeoff(self, height):
        """
        lets the crazyflie takeoff
        :param height: height to which the crazyflie should takeoff
        :return: -
        """

        self.mc.take_off(height=height, velocity=0.5)

    def stop(self):
        """
        cf stops any motion and hovers
        :return: -
        """
        self.mc.stop()

    def land(self):
        """
        crazyflie lands
        :return: -
        """

        self.mc.land(velocity=0.1)

    def turn(self, degrees):
        """
        crazyflie turns around
        :param degrees: amount of degrees to turn
                        if degrees > 0 --> turn right
                        if degrees < 0 --> turn left

        :return: -
        """
        if degrees > 0:
            self.mc.turn_right(abs(degrees), rate=45)

        if degrees < 0:
            self.mc.turn_left(abs(degrees), rate=45)

    def start_turning(self, rate):
        """
        crazyflie starts to turn
        :param rate: degrees/second in which the crazyflie starts to turn
                     if rate > 0 --> turn right
                     if rate < 0 --> turn left

        :return: -
        """
        if rate > 0:
            self.mc.start_turn_right(abs(rate))

        if rate < 0:
            self.mc.start_turn_left(abs(rate))

    def move(self, x, y, z):
        """
        crazyflie moves in straight line
        :param x: forward/backward
        :param y: left/right
        :param z: up/down
        :return: -
        """

        self.mc.move_distance(x, y, z, velocity=0.2)

    def start_moving(self, vel_x, vel_y, vel_z):
        """
        crazyflie moves in straight line
        :param vel_x: velocity forward/backward
        :param vel_y: velocity left/right
        :param vel_z: velocity up/down
        :return: -
        """

        self.mc.start_linear_motion(vel_x, vel_y, vel_z)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Connect to AI-deck JPEG streamer example')
    parser.add_argument("-n", default="192.168.4.1", metavar="ip", help="AI-deck IP")
    parser.add_argument("-p", type=int, default='5000', metavar="port", help="AI-deck port")
    args = parser.parse_args()
    deck_port = args.p
    deck_ip = args.n

    # connect the AI deck
    print("Connecting to socket on {}:{}...".format(deck_ip, deck_port))
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((deck_ip, deck_port))
    print("Socket connected")

    # setup for logging
    logging.basicConfig(level=logging.ERROR)
    log_stabilizer = LogConfig(name="Stabilizer", period_in_ms=12)
    log_stabilizer.add_variable('pm.vbat', 'float')
    log_stabilizer.add_variable('stabilizer.yaw', 'float')
    log_stabilizer.add_variable('stabilizer.pitch', 'float')
    log_stabilizer.add_variable('stabilizer.roll', 'float')

    # initiate low level drivers
    cflib.crtp.init_drivers(enable_debug_driver=False)
    cf = Crazyflie(rw_cache='./cache')

    # starting the main functionality
    with SyncCrazyflie(URI, cf) as sync_cf:
        crazyflie = CF(sync_cf)
        print("crazyflie initialized!")

        image = None
        stop_thread_flag = False
        # start thread for image acquisition
        t1 = threading.Thread(target=get_image_from_ai_deck)
        t1.start()
        time.sleep(1)
        while image is None:
            print("Wait for image!")

        # All checks done
        # Now start the crazyflie!
        print("All initial checks done!")
        print("crazyflie taking off!")
        crazyflie.takeoff(1)
        time.sleep(1)

        voltage = []
        timestamp = []
        start = time.time()
        v_bat = crazyflie.get_battery_level()
        while v_bat > LOW_BAT:
            try:
                v = (crazyflie.get_battery_level())
                print(v)
                voltage.append(v)
                timestamp.append(time.time()-start)

            finally:
                time.sleep(1)

        crazyflie.stop()
        print("crazyflie is landing")
        crazyflie.land()

    print("Calculate moving average")
    moving_averages = []
    i = 0
    window_size = 3
    while i < len(voltage) - window_size + 1:
        # Store elements from j to j+window_size
        # in list to get the current window
        window = voltage[i: i + window_size]

        # Calculate the average of current window
        window_average = round(sum(window) / window_size, 3)

        # Store the average of current
        # window in moving average list
        moving_averages.append(window_average)

        # Shift window to right by one position
        i += 1

    print(moving_averages)
    print("-----")
    print(timestamp)

    stop_thread_flag = True
    time.sleep(5)
    client_socket.close()
