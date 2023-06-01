import logging
import sys
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.crazyflie.log import LogConfig

URI = uri_helper.uri_from_env(default='radio://0/100/2M/E7E7E7E701')

DEFAULT_HEIGHT = 0.5


def get_cf_data():
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


def take_off_simple(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        time.sleep(1)
        #mc.stop()


def get_battery_level():
    """
    fetches battery level from crazyflie
    :return: double: v_bat
             battery voltage in V
    """

    # check current battery voltage of cf
    voltage, _, _, _ = get_cf_data()
    time.sleep(0.02)
    return voltage


if __name__ == '__main__':

    # setup for logging
    logging.basicConfig(level=logging.ERROR)
    log_stabilizer = LogConfig(name="Stabilizer", period_in_ms=12)
    log_stabilizer.add_variable('pm.vbat', 'float')
    log_stabilizer.add_variable('stabilizer.yaw', 'float')
    log_stabilizer.add_variable('stabilizer.pitch', 'float')
    log_stabilizer.add_variable('stabilizer.roll', 'float')
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:

        flow_deck_attached = int(scf.cf.param.get_value(complete_name='deck.bcFlow2', timeout=5))
        ai_deck_attached = int(scf.cf.param.get_value(complete_name='deck.bcAI', timeout=5))

        if flow_deck_attached == 0:
            print('No flow deck detected!')
            sys.exit(1)

        if ai_deck_attached == 0:
            print('No ai deck detected!')
            sys.exit(1)

        print("Both decks detected :)")

        take_off_simple(scf)

        print("TAKEOFF")

