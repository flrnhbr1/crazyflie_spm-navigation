import logging
import sys
import time

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

LOW_BAT = 2.8  # if the cf reaches this battery voltage level, it should land
TAKEOFF_HEIGHT = 1
URI = uri_helper.uri_from_env(default='radio://0/100/2M/E7E7E7E701')


def get_cf_data():
    # fetch parameter data from cf and extract information
    with SyncLogger(scf, log_stabilizer) as logger:
        # logger.connect()
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

        # psi --> yaw
        # theta --> pitch
        # phi --> roll
        self.v_bat, self.psi, self.theta, self.phi = get_cf_data()
        self.scf = scf
        self.mc = MotionCommander(scf)

    def takeoff(self, height):
        # cf takes of "height" meter
        self.mc.take_off(height=height, velocity=0.2)

    def update_and_check_battery_level(self):
        # check current battery voltage of cf
        voltage, _, _, _ = get_cf_data()
        time.sleep(0.02)
        self.v_bat = voltage
        return voltage

    def land(self):
        self.mc.land(velocity=0.2)

    def turn_left(self, degrees):
        self.mc.turn_left(degrees, rate=45.0)


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

    with SyncCrazyflie(URI, cf) as scf:
        crazyflie = CF(scf)
        print("crazyflie initialized!")

        # check if extensions decks are connected
        flow_deck_attached = scf.cf.param.get_value(complete_name='deck.bcFlow2', timeout=5)
        ai_deck_attached = scf.cf.param.get_value(complete_name='deck.bcAI', timeout=5)

        if flow_deck_attached == 0:
            print('No flow deck detected!')
            sys.exit(1)

        if ai_deck_attached == 0:
            print('No ai deck detected!')
            sys.exit(1)

        print("Flow deck and ai deck detected")

        # check battery level
        v_bat = crazyflie.update_and_check_battery_level()
        if v_bat < LOW_BAT:
            print("Battery-level too low [Voltage = " + str(round(v_bat, 2)) + "V]")
            sys.exit(1)

        print("Battery-level OK [Voltage = " + str(round(v_bat, 2)) + "V]")
        # crazyflie.takeoff(TAKEOFF_HEIGHT)
        print("crazyflie taking off!")






