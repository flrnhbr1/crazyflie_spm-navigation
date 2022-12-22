"""
Created on 23.11.2022

@author: Florian Huber
"""

import logging
import sys
import time
import argparse
import yaml
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

# import open cv functions
import cv2

# import square planar marker functions
import square_planar_marker as spm

# set constants
LOW_BAT = 3.5  # if the cf reaches this battery voltage level, it should land
TAKEOFF_HEIGHT = 0.5
MAX_MARKER_ID = 5
URI = uri_helper.uri_from_env(default='radio://0/100/2M/E7E7E7E701')


def get_cf_data(scf):
    """
    fetches logging information from the crazyflie
    :param scf: id of SyncCrazyflie
    :return: battery level and current yaw, pitch, roll values
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
    :return: the received data in a bytearray
    """

    data = bytearray()
    while len(data) < size:
        data.extend(client_socket.recv(size - len(data)))
    return data


def get_image_from_ai_deck():
    """
    function to fetch image from the AI deck
    :return: saves the captured image in the global variable 'image'
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
                with open("./wifi_streaming/imgBuffer/img.jpeg", "wb") as im:
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
        :return:    True if both decks are attached
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
        :return: battery voltage in V
        """

        # check current battery voltage of cf
        voltage, _, _, _ = get_cf_data(self.scf)
        time.sleep(0.02)
        self.v_bat = voltage
        return voltage

    def get_yaw(self):
        """
        fetches battery level from crazyflie
        :return: yaw angle in degrees
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

        self.mc.take_off(height=height, velocity=0.1)

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

    def move(self, x, y, z):
        """
        crazyflie moves in straight line
        :param x: forward/backward
        :param y: left/right
        :param z: up/down
        :return: -
        """

        self.mc.move_distance(x, y, z, velocity=0.1)

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
    # Arguments for setting IP/port of AI deck. Default settings are for when
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

    # load calibration-data of camera
    with open('./calibrate_camera/calibration.yaml') as f:
        loaded_dict = yaml.safe_load(f)
        mtx = loaded_dict.get('camera_matrix')
        dis = loaded_dict.get('dist_coeff')
        matrix = np.array(mtx)
        distortion = np.array(dis)
        marker_size = 20  # size in cm
    print("Camera calibration loaded")

    imgdata = None
    data_buffer = bytearray()
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

        # check if extensions decks are connected
        if not crazyflie.decks_attached():
            sys.exit(1)

        print("Flow deck and ai deck connected")

        # check battery level
        v_bat = crazyflie.get_battery_level()
        if v_bat < LOW_BAT:
            print("Battery-level too low [Voltage = " + str(round(v_bat, 2)) + "V]")
            sys.exit(1)

        print("Battery-level OK [Voltage = " + str(round(v_bat, 2)) + "V]")

        # All checks done
        # Now start the crazyflie!
        print("All initial checks done!")
        print("crazyflie taking off!")
        # crazyflie.takeoff(TAKEOFF_HEIGHT)
        time.sleep(1)

        # initialize global variable for image
        image = None

        # marker_geometry is the datastruct for saving the position data of the markers
        # every marker id gets an entry that is has 6 values
        #       e.g., marker id = 3
        #       marker_geometry[3] =   [[t_x t_y t_z]         --> translation vector
        #                               [alpha beta gamma]]   --> euler angles
        marker_geometry = np.zeros([MAX_MARKER_ID, 2, 3])

        # flag to stop the image-thread
        stop_thread_flag = False
        t1 = threading.Thread(target=get_image_from_ai_deck)
        t1.start()
        time.sleep(1)

        while image is not None:
            for t in range(0, 361):
                # crazyflie.turn(t)
                time.sleep(0.1)
                image_to_process = image
                marker_ids, marker_corners = spm.detect_marker(img=image_to_process)
                # convert to colored image for visualization
                image_to_process = cv2.cvtColor(image_to_process, cv2.COLOR_BayerBG2BGRA)
                for i, c in enumerate(marker_corners):
                    trans_vec, rot_vec, euler_angles = spm.estimate_marker_pose(corners=c, mark_size=marker_size,
                                                                                mtrx=matrix, dist=distortion)
                    image_to_process = spm.print_marker_info_on_image(img=image_to_process, corners=c[0],
                                                                      marker_id=marker_ids[i], mtrx=matrix,
                                                                      dist=distortion, t_vec=trans_vec, r_vec=rot_vec,
                                                                      eul_angles=euler_angles, index=i)
                cv2.imshow('spm detection', image_to_process)
                cv2.waitKey(1)

        # crazyflie.stop()
        # crazyflie.land()
        client_socket.close()
        stop_thread_flag = True
        t1.join()
