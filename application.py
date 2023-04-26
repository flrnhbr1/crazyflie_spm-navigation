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
import datetime

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

# import custom exceptions
import custom_exceptions as exceptions

# set constants

# if the cf reaches this battery voltage level, it should land
LOW_BAT = 3.0

# ID of the crazyflie
URI = uri_helper.uri_from_env(default='radio://0/100/2M/E7E7E7E701')

# default height of takeoff
TAKEOFF_HEIGHT = 0.8

# highest used marker id, start from id=0
# marker type must be aruco original dictionary
MAX_MARKER_ID = 2

# define destination vector marker <--> crazyflie
DISTANCE = np.array([0, 0, 75])  # [cm]


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


class MovingAverageFilter:
    """
    class for moving average filter for trajectory paths
    """

    def __init__(self, wind_size):
        """
        constructor for a moving average lowpass filter
        :param wind_size: size of the filter window of the moving average filter
        """
        self.wind_size = wind_size
        self.data_x = []
        self.data_y = []
        self.data_z = []
        self.data_psi = []
        self.weights = []

        # define weights
        for a in range(wind_size, 0, -1):
            self.weights.append(1 / a)

    def append(self, t_vec, eul_angles):
        """
        function for appending the filter data
        :param t_vec: translation vector marker
        :param eul_angles: euler angles of the marker
        :return: -
        """
        self.data_y.append(t_vec[0, 0, 0])
        self.data_z.append(t_vec[0, 0, 1])
        self.data_x.append(t_vec[0, 0, 2])
        self.data_psi.append(eul_angles[1])

    def get_moving_average(self):
        """
        function to get the moving average filtered values
        :return:    double array[]: t_vec (filtered),
                    double: psi_angle (filtered yaw angle)
        """

        t_vec = [0, 0, 0]
        length = len(self.data_x)
        t_vec[2] = np.average(self.data_x[length - self.wind_size:length])
        t_vec[0] = np.average(self.data_y[length - self.wind_size:length])
        t_vec[1] = np.average(self.data_z[length - self.wind_size:length])
        psi = np.average(self.data_psi[length - self.wind_size:length])

        return t_vec, psi

    def get_weighted_moving_average(self):
        """
        function to get the weighted moving average values for linear and unweighted for angular motion
        :return:    double array[]: t_vec (filtered),
                    double: psi_angle (filtered yaw angle)
        """

        t_vec = [0, 0, 0]
        length = len(self.data_x)
        t_vec[2] = np.average(self.data_x[length - self.wind_size:length], weights=self.weights)
        t_vec[0] = np.average(self.data_y[length - self.wind_size:length], weights=self.weights)
        t_vec[1] = np.average(self.data_z[length - self.wind_size:length], weights=self.weights)
        psi = np.average(self.data_psi[length - self.wind_size:length])

        return t_vec, psi


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

    def takeoff(self, height):
        """
        lets the crazyflie takeoff
        :param height: height to which the crazyflie should takeoff
        :return: -
        """

        self.mc.take_off(height=height, velocity=1)

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

        self.mc.move_distance(x, y, z, velocity=0.25)


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
    print("Camera calibration loaded")
    marker_size = 20  # size in cm

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

    # initiate filter for noise filtering
    window_size = 7  # window size of the moving average filter
    motion_filter = MovingAverageFilter(window_size)

    # starting the main functionality

    # connect to crazyflie
    with SyncCrazyflie(URI, cf) as sync_cf:
        try:
            crazyflie = CF(sync_cf)
            print("crazyflie initialized!")

            # check if extensions decks are connected
            if not crazyflie.decks_attached():
                raise exceptions.DeckException

            print("Flow deck and ai deck connected")

            # check battery level
            v_bat = crazyflie.get_battery_level()
            if v_bat < LOW_BAT:
                raise exceptions.BatteryException(v_bat, False)

            print("Battery-level OK [Voltage = " + str(round(v_bat, 2)) + "V]")

            # initialize global variable for image
            image = None
            # initialize flag to stop the image-thread
            stop_thread_flag = False
            # start thread for image acquisition
            t1 = threading.Thread(target=get_image_from_ai_deck)
            t1.start()
            time.sleep(1)

            c = 0  # counter for image waiting
            while image is None:
                print("Wait for image!")
                time.sleep(2)
                c += 1
                if c > 3:  # if image can not be detected more than 3 times --> raise exception
                    raise exceptions.ImageFetchException
            print("Image Thread started")

            # All checks done

            # Now start the crazyflie!
            print("All initial checks passed!")
            print("----> crazyflie taking off!")
            crazyflie.takeoff(TAKEOFF_HEIGHT)
            time.sleep(1)

            # perform for all defined markers
            for m in range(0, MAX_MARKER_ID + 1):

                # check battery level
                v_bat = crazyflie.get_battery_level()
                if v_bat < LOW_BAT:
                    raise exceptions.BatteryException(v_bat, True)

                print("Battery-level OK [Voltage = " + str(round(v_bat, 2)) + "V]")

                # set aligned variable to False
                aligned = False

                # start turning to find marker with id == m
                crazyflie.start_turning(-45)

                # initialize timer
                start_time = time.time()
                elapsed_time = 0

                # search for marker while turning around for 10 seconds
                # if the desired marker is not found before the timeout --> go to next marker
                marker_found = False
                while not marker_found and elapsed_time < 10:
                    print("Search for marker with id=" + str(m))
                    marker_ids, marker_corners = spm.detect_marker(image)
                    cv2.imshow('spm detection', image)
                    cv2.waitKey(1)
                    elapsed_time = time.time() - start_time
                    # if marker is found exit searching loop and let the crazyflie hover
                    if marker_ids is not None and m in marker_ids:
                        crazyflie.stop()  # stop the searching motion
                        crazyflie.turn(-10)  # turn 10 degrees further to get the marker fully into the frame
                        print("Marker found")
                        marker_found = True

                # detect markers again in current image
                # first make sure the marker is found, because sometimes in between the first and second search,
                # the marker gets out of the image frame
                marker_ids = None
                while marker_ids is None:
                    marker_ids, marker_corners = spm.detect_marker(image)

                # now perform control-loop for marker with id == m
                for c, i in enumerate(marker_ids):  # if multiple markers are in frame, iterate over them

                    if i == m:  # if the desired marker is found
                        # counter for entering the controlling, first 'window_size' values must be appended,
                        # to perform filtering
                        filter_count = 0

                        mag_goal = 1  # set to 1, to enter the loop
                        # initialize timeout
                        start_time = time.time()
                        elapsed_time = 0

                        # control loop -- approach marker until distance to goal is > 5cm
                        while mag_goal > 0.1 and elapsed_time < 5:
                            marker_ids, marker_corners = spm.detect_marker(image)  # detect markers in image
                            if marker_ids is not None:  # if there is a marker
                                for d, j in enumerate(
                                        marker_ids):  # if multiple markers are in frame, iterate over them
                                    if j == m:  # if the desired marker is found

                                        start_time = time.time()  # marker found --> reset timeout

                                        # estimate pose of the marker
                                        trans_vec, rot_vec, euler_angles = spm.estimate_marker_pose(marker_corners[d],
                                                                                                    marker_size, matrix,
                                                                                                    distortion)
                                        # append measured values to moving average filter
                                        motion_filter.append(trans_vec, euler_angles)

                                        # show image
                                        cv2.imshow('spm detection', image)
                                        cv2.waitKey(1)

                                        # get filtered signal and execute trajectory
                                        if filter_count > window_size:  # if enough data is available
                                            # get lowpass-filtered data
                                            linear_motion, yaw_motion = motion_filter.get_weighted_moving_average()

                                            # subtract vectors to get the trajectory to the destination coordinates
                                            # divide by 100 to get from cm to m
                                            goal = (linear_motion - DISTANCE) / 100

                                            # calculate distance to marker,
                                            mag_goal = math.sqrt(goal[0] ** 2 + goal[1] ** 2 + goal[2] ** 2)

                                            # trajectory is 1/25 of the vector towards the destination coordinates
                                            trajectory = goal / 25

                                            # fly towards the marker
                                            crazyflie.move(trajectory[2], -trajectory[0], -trajectory[1])

                                            # align towards the marker, 1/8 of the measured yaw-angle
                                            # also convert from rad to degrees
                                            crazyflie.turn(yaw_motion * 180 / (math.pi * 8))

                            elapsed_time = time.time() - start_time  # timer for loop iteration

                            filter_count += 1  # increment, to fill the filter with data before fetching filtered data

                            # print time, that current loop-iteration took
                            # print("RTT:" + str(time.time() - start_time))

                        crazyflie.stop()  # stop any motion
                        aligned = True
                        print("----> Aligned to marker with id=" + str(m))
                        time.sleep(2)  # wait 2 seconds
                        crazyflie.back(0.3)  # backup before searching for next marker
                        break  # break loop --> go to next marker

                if not aligned:
                    print("Could not align to marker with id=" + str(m) + "!")


        except exceptions.DeckException:
            print("Error: At least one deck not detected")

        except exceptions.ImageFetchException:
            print("Error: Image can not be fetched from AI deck")

        except exceptions.BatteryException as e:
            print("Error: Battery-level too low [Voltage = " + str(round(e.battery_level, 2)) + "V]")
            if e.cf_takeoff:  # if crazyflie already took off --> land
                print("----> crazyflie is landing")
                crazyflie.land()  # land
                stop_thread_flag = True  # terminate image thread
                t1.join()  # join image thread
                time.sleep(2)  # wait
                client_socket.close()  # close WiFi socket

        except KeyboardInterrupt:
            print("Error: Application was stopped!")
            print("----> crazyflie is landing")
            crazyflie.land()  # land
            stop_thread_flag = True  # terminate image thread
            t1.join()  # join image thread
            time.sleep(2)  # wait
            client_socket.close()  # close WiFi socket

        else:
            # when all markers are processed --> land
            print("----> crazyflie is landing")
            crazyflie.land()  # land
            stop_thread_flag = True  # terminate image thread
            t1.join()  # join image thread
            time.sleep(2)  # wait
            client_socket.close()  # close WiFi socket

            # save motion data for analyzing
            moving_averages_x = []
            moving_averages_y = []
            moving_averages_z = []
            moving_averages_psi = []

            w_moving_averages_x = []
            w_moving_averages_y = []
            w_moving_averages_z = []
            w_moving_averages_psi = []

            i = 0
            while i < len(motion_filter.data_x) - window_size + 1:
                # Calculate the moving average of current window
                window_average_x = np.average(motion_filter.data_x[i:i + window_size])
                window_average_y = np.average(motion_filter.data_y[i:i + window_size])
                window_average_z = np.average(motion_filter.data_z[i:i + window_size])
                window_average_psi = np.average(motion_filter.data_psi[i:i + window_size])

                # Calculate the weighted moving average of current window

                w_window_average_x = np.average(motion_filter.data_x[i:i + window_size], weights=motion_filter.weights)
                w_window_average_y = np.average(motion_filter.data_y[i:i + window_size], weights=motion_filter.weights)
                w_window_average_z = np.average(motion_filter.data_z[i:i + window_size], weights=motion_filter.weights)
                w_window_average_psi = np.average(motion_filter.data_psi[i:i + window_size],
                                                  weights=motion_filter.weights)

                # Store the average of current
                # window in moving average list
                moving_averages_x.append(window_average_x)
                moving_averages_y.append(window_average_y)
                moving_averages_z.append(window_average_z)
                moving_averages_psi.append(window_average_psi)

                w_moving_averages_x.append(w_window_average_x)
                w_moving_averages_y.append(w_window_average_y)
                w_moving_averages_z.append(w_window_average_z)
                w_moving_averages_psi.append(w_window_average_psi)

                # Shift window to right by one position
                i += 1

            data = {'unfiltered_x': np.asarray(motion_filter.data_x).tolist(),
                    'filtered_x': np.asarray(moving_averages_x).tolist(),
                    'w_filtered_x': np.asarray(w_moving_averages_x).tolist(),

                    'unfiltered_y': np.asarray(motion_filter.data_y).tolist(),
                    'filtered_y': np.asarray(moving_averages_y).tolist(),
                    'w_filtered_y': np.asarray(w_moving_averages_y).tolist(),

                    'unfiltered_z': np.asarray(motion_filter.data_z).tolist(),
                    'filtered_z': np.asarray(moving_averages_z).tolist(),
                    'w_filtered_z': np.asarray(w_moving_averages_z).tolist(),

                    'unfiltered_psi': np.asarray(motion_filter.data_psi).tolist(),
                    'filtered_psi': np.asarray(moving_averages_psi).tolist(),
                    'w_filtered_psi': np.asarray(w_moving_averages_psi).tolist(),

                    }
            t = datetime.datetime.now()
            filename = "Log_" + str(t.year) + "-" + str(t.month) + "-" + str(t.day) + "T" + str(t.hour) + "-" + \
                       str(t.minute) + "-" + str(t.second)

            path = "plot/" + filename + ".yaml"
            print("Save data...")

            with open(path, "w") as f:
                yaml.dump(data, f)

            print("Log saved!")

        finally:
            print("Application ended!")
