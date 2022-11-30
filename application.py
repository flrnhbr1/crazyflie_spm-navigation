import logging
import sys
import time
from threading import Event

# importing cf functions
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.crazyflie.log import LogConfig
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

# importing open cv functions
import cv2
import cv2.aruco as aruco

LOW_BAT = 2.8
URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E702')


def get_data():
    with SyncLogger(scf, log_stabilizer) as logger:
        for entry in logger:
            data = entry[1]
            v_bat = data.get('pm.vbat')
            yaw = data.get('stabilizer.yaw')
            pitch = data.get('stabilizer.pitch')
            roll = data.get('stabilizer.roll')
            time.sleep(0.02)
    return v_bat, yaw, pitch, roll


class SPM:
    """
    class for square planar markers parameters, functions and methods
    """

    def __init__(self, id):
        # constructor
        self.id = id
        self.t_vec = None
        self.r_vec = None
        self.current_yaw = None

    def save_position(self, t_vec, r_vec, current_yaw):
        # save positioning data
        self.t_vec = t_vec
        self.r_vec = r_vec
        self.current_yaw = current_yaw


class CF:
    """
    class for crazyflie parameters, functions and methods
    """

    def __init__(self, scf):
        # constructor
        self.scf = scf
        self.mc = MotionCommander(scf)
        self.battery_voltage = None

    def takeoff(self, height):
        # cf takes of "height" meter
        print()  # remove

    def check_battery(self):
        # check current battery voltage of cf
        print()


if __name__ == "__main__":
    # setup for logging
    logging.basicConfig(level=logging.ERROR)
    log_stabilizer = LogConfig(name="Stabilizer", period_in_ms=12)
    log_stabilizer.add_variable('pm.vbat', float)
    log_stabilizer.add_variable('stabilizer.yaw', float)
    log_stabilizer.add_variable('stabilizer.pitch', float)
    log_stabilizer.add_variable('stabilizer.roll', float)

    # initiate low level drivers
    cflib.crtp.init_drivers()
    scf = SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache'))
    crazyflie = CF(scf)
