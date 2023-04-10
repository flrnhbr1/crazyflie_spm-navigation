"""
Created on 23.11.2022

@author: Florian Huber
"""

import logging
import math
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
LOW_BAT = 3.0  # if the cf reaches this battery voltage level, it should land
URI = uri_helper.uri_from_env(default='radio://0/100/2M/E7E7E7E701')

# default height of takeoff
TAKEOFF_HEIGHT = 0.8
# highest used marker id, start from id=0
# marker type must be aruco original dictionary
MAX_MARKER_ID = 0
# define distance crazyflie <--> marker (when moving to marker)
DISTANCE = np.array([0, 0, 100])  # [cm]


def get_cf_data(scf):
    """
    fetches logging information from the crazyflie
    :param scf: id of SyncCrazyflie
    :return: double: v_bat,
             double: yaw,
             double: pitch,
             double: roll,
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
                with open("./wifi_streaming/imgBuffer/img.jpeg", "wb") as im:
                    im.write(img_stream)
                np_arr = np.frombuffer(img_stream, np.uint8)
                img_gray = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

            # set global variable
            image = img_gray


class LowPassFilter:
    """
    class for moving average filter for the trajectory paths
    """

    def __init__(self):
        """
        constructor for a moving average lowpass filter
        """

        self.data_x = []
        self.data_y = []
        self.data_z = []
        self.data_psi = []

    def append(self, t_vec, eul_angles):
        """
        function for appending the filter data
        :param t_vec: translation vector marker
        :param eul_angles: euler angles of the marker
        :return: -
        """
        self.data_x.append(t_vec[0, 0, 0])
        self.data_y.append(t_vec[0, 0, 1])
        self.data_z.append(t_vec[0, 0, 2])
        self.data_psi.append(eul_angles[1])

    def get_filtered(self, window_size):
        """
        function to get the filtered values
        :param window_size: size of the filter window of the moving average filter
        :return:    double array[]: t_vec (filtered),
                    double: psi_angle (filtered yaw angle)
        """

        t_vec = [0, 0, 0]
        length = len(self.data_x)
        t_vec[0] = np.sum(self.data_x[length - window_size:length]) / window_size
        t_vec[1] = np.sum(self.data_y[length - window_size:length]) / window_size
        t_vec[2] = np.sum(self.data_z[length - window_size:length]) / window_size
        psi_angle = np.sum(self.data_psi[length - window_size:length]) / window_size

        return t_vec, psi_angle


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

        self.mc.land(velocity=0.5)

    def turn(self, degrees):
        """
        crazyflie turns around
        :param degrees: amount of degrees to turn
                        positive degrees --> turn right,
                        negative degrees --> turn left

        :return: -
        """
        r = 30  # rate to turn (degrees/second)
        if degrees > 0:
            self.mc.turn_right(abs(degrees), rate=r)

        if degrees < 0:
            self.mc.turn_left(abs(degrees), rate=r)
        time.sleep((abs(degrees) / r))  # wait for turning

    def start_turning(self, rate):
        """
        crazyflie starts to turn
        :param rate: degrees/second in which the crazyflie starts to turn
                     positive degrees --> turn right,
                     negative degrees --> turn left

        :return: -
        """
        if rate > 0:
            self.mc.start_turn_right(abs(rate))

        if rate < 0:
            self.mc.start_turn_left(abs(rate))

    def back(self, dist_b):
        """
        crazyflie moves backwards
        :param dist_b: distance
        :return: -
        """

        self.mc.back(dist_b, velocity=0.5)

    def move(self, x, y, z):
        """
        crazyflie moves in straight line
        :param x: forward/backward
        :param y: left/right
        :param z: up/down
        :return: -
        """

        self.mc.move_distance(x, y, z, velocity=0.3)

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

        # initialize global variable for image
        image = None
        # initialize flag to stop the image-thread
        stop_thread_flag = False
        # start thread for image acquisition
        t1 = threading.Thread(target=get_image_from_ai_deck)
        t1.start()
        time.sleep(1)
        while image is None:
            print("Wait for image!")
        print("Image Thread started")

        # All checks done
        # Now start the crazyflie!
        print("All initial checks done!")
        print("crazyflie taking off!")
        crazyflie.takeoff(TAKEOFF_HEIGHT)
        time.sleep(1)

        # perform for all defined markers
        for m in range(0, MAX_MARKER_ID + 1):

            # check battery level
            v_bat = crazyflie.get_battery_level()
            if v_bat < LOW_BAT:
                print("Battery-level too low [Voltage = " + str(round(v_bat, 2)) + "V]")
                break

            # initiate low pass filter for noise filtering
            traj_filter = LowPassFilter()

            marker_found = False

            # start turning to find marker with id m
            crazyflie.start_turning(-45)
            start_time = time.time()
            elapsed_time = 0
            while not marker_found:
                print("Search for marker with id=" + str(m))
                marker_ids, marker_corners = spm.detect_marker(image)
                cv2.imshow('spm detection', image)
                cv2.waitKey(1)
                elapsed_time = time.time() - start_time
                # if marker is found exit searching loop and let the crazyflie hover
                if marker_ids is not None and m in marker_ids:
                    crazyflie.stop()  # stop the searching motion
                    crazyflie.turn(-10)  # turn 10 degrees further to get the marker stable into the frame
                    print("Marker found")
                    marker_found = True
            # detect markers again in current image
            # first make sure the marker is found, because sometimes in between the first and second search,
            # the marker gets out of the image frame
            marker_ids = None
            while marker_ids is None:
                marker_ids, marker_corners = spm.detect_marker(image)
            for c, i in enumerate(marker_ids):
                if i == m:
                    # estimate pose of marker with desired id
                    trans_vec, rot_vec, euler_angles = spm.estimate_marker_pose(marker_corners[c], marker_size,
                                                                                matrix, distortion)

                    cv2.imshow('spm detection', image)
                    cv2.waitKey(1)

                    # calculate trajectory vector to marker and magnitude of it
                    traj = (trans_vec[0, 0] - DISTANCE) / 100
                    mag_traj = math.sqrt(traj[0] ** 2 + traj[1] ** 2 + traj[2] ** 2)

                    # control loop -- approach marker until distance to goal is > 10cm

                    filter_count = 0
                    window_size = 3
                    while mag_traj > 0.1:
                        start_time = time.time()
                        marker_ids, marker_corners = spm.detect_marker(image)
                        if marker_ids is not None:
                            for d, j in enumerate(marker_ids):
                                if j == m:
                                    # estimate pose of marker with desired id
                                    trans_vec, rot_vec, euler_angles = spm.estimate_marker_pose(marker_corners[d],
                                                                                                marker_size, matrix,
                                                                                                distortion)
                                    # append filter data
                                    traj_filter.append(trans_vec, euler_angles)
                                    cv2.imshow('spm detection', image)
                                    cv2.waitKey(1)
                                    # get filtered signal and execute trajectory
                                    if filter_count > window_size:
                                        traj, psi = traj_filter.get_filtered(window_size)
                                        traj = (traj - DISTANCE) / 100
                                        mag_traj = math.sqrt(traj[0] ** 2 + traj[1] ** 2 + traj[2] ** 2)
                                        direction = traj / (mag_traj * 15)

                                        # fly a bit towards the marker
                                        crazyflie.move(direction[2], -direction[0], -direction[1])
                                        # turn a bit towards the marker
                                        crazyflie.turn(psi * 180 / (math.pi * 8))
                        filter_count += 1

                        # print("RTT:" + str(time.time() - start_time))

                    crazyflie.stop()  # stop any motion
                    time.sleep(2)
                    crazyflie.back(1)  # backup before searching for next marker

                    break
        # when all markers are processed --> land
        # crazyflie.stop()
        print("crazyflie is landing")
        crazyflie.land()
        stop_thread_flag = True
        t1.join()
        time.sleep(2)
        client_socket.close()

        # save motion data for analyzing

        moving_averages_x = []
        moving_averages_y = []
        moving_averages_z = []
        moving_averages_psi = []

        i = 0
        while i < len(traj_filter.data_x) - window_size + 1:
            # Calculate the average of current window
            window_average_x = np.sum(traj_filter.data_x[i:i + window_size]) / window_size
            print("hell:" + str(traj_filter.data_x[i:i + window_size]))
            window_average_y = np.sum(traj_filter.data_y[i:i + window_size]) / window_size
            window_average_z = np.sum(traj_filter.data_z[i:i + window_size]) / window_size
            window_average_psi = np.sum(traj_filter.data_psi[i:i + window_size]) / window_size

            # Store the average of current
            # window in moving average list
            moving_averages_x.append(window_average_x)
            moving_averages_y.append(window_average_y)
            moving_averages_z.append(window_average_z)
            moving_averages_psi.append(window_average_psi)

            # Shift window to right by one position
            i += 1

        data = {'unfiltered_x': np.asarray(traj_filter.data_x).tolist(),
                'filtered_x': np.asarray(moving_averages_x).tolist(),
                'unfiltered_y': np.asarray(traj_filter.data_y).tolist(),
                'filtered_y': np.asarray(moving_averages_y).tolist(),
                'unfiltered_z': np.asarray(traj_filter.data_z).tolist(),
                'filtered_z': np.asarray(moving_averages_z).tolist(),
                'unfiltered_psi': np.asarray(traj_filter.data_psi).tolist(),
                'filtered_psi': np.asarray(moving_averages_psi).tolist()
                }
        with open("plot/motion_data.yaml", "w") as f:
            yaml.dump(data, f)
