"""
Created on 23.11.2022

@author: Florian Huber
"""

import logging
import math
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
MAX_MARKER_ID = 0

# define destination vector marker <--> crazyflie
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
            log_data = entry[1]
            vbat = log_data.get('pm.vbat')
            yaw = log_data.get('stabilizer.yaw')
            pitch = log_data.get('stabilizer.pitch')
            roll = log_data.get('stabilizer.roll')
            time.sleep(0.02)
            return vbat, yaw, pitch, roll


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

        self.mc.move_distance(x, y, z, velocity=0.15)


if __name__ == "__main__":

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
    battery_level = []
    time_stamp = []

    # starting the main functionality

    # connect to crazyflie
    with SyncCrazyflie(URI, cf) as sync_cf:
        try:
            crazyflie = CF(sync_cf)
            print("crazyflie initialized!")
            time.sleep(2)

            # check battery level
            v_bat = crazyflie.get_battery_level()
            if v_bat < LOW_BAT:
                print("lowbat")

            print("Battery-level OK [Voltage = " + str(round(v_bat, 2)) + "V]")

            # All checks done

            # Now start the crazyflie!
            print("All initial checks passed!")
            print("----> crazyflie taking off!")
            crazyflie.takeoff(TAKEOFF_HEIGHT)
            time.sleep(1)


            start_time = time.time()
            while v_bat > LOW_BAT:

                v_bat = crazyflie.get_battery_level()
                battery_level.append(v_bat)
                print("Battery-level OK [Voltage = " + str(round(v_bat, 2)) + "V]")
                elapsed_time = time.time() - start_time  # timer for loop iteration
                time_stamp.append(elapsed_time)
                time.sleep(1)
                # print time, that current loop-iteration took
                # print("RTT:" + str(time.time() - start_time))

            crazyflie.stop()  # stop any motion
            aligned = True
            time.sleep(2)  # wait 2 seconds
            crazyflie.back(0.4)  # backup before searching for next marker


        except KeyboardInterrupt:
            print("Error: Application was stopped!")
            print("----> crazyflie is landing")
            crazyflie.land()  # land
            stop_thread_flag = True  # terminate image thread
            time.sleep(2)  # wait

        finally:
            # when all markers are processed --> land
            print("----> crazyflie is landing")
            crazyflie.land()  # land
            time.sleep(2)  # wait



            data = {'battery': np.asarray(battery_level).tolist(),
                    'time': np.asarray(time_stamp).tolist(),
                    }
            t = datetime.datetime.now()
            filename = "Log_" + str(t.year) + "-" + str(t.month) + "-" + str(t.day) + "T" + str(t.hour) + "-" + \
                       str(t.minute) + "-" + str(t.second)

            path = "../plot/battery_data/" + filename + ".yaml"

            print("Save data...")
            print(time)
            print("--")
            print(battery_level)

            with open(path, "w") as f:
                yaml.dump(data, f)

            print("Log saved!")


