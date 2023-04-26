import time
import logging

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.crazyflie.log import LogConfig
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

# URI to the Crazyflie to connect to
uri = 'radio://0/100/2M/E7E7E7E701'


def simple_connect():
    print("Yeah, I'm connected! :D")
    time.sleep(3)
    print("Now I will disconnect :'(")


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


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    log_stabilizer = LogConfig(name="Stabilizer", period_in_ms=12)
    log_stabilizer.add_variable('pm.vbat', 'float')
    log_stabilizer.add_variable('stabilizer.yaw', 'float')
    log_stabilizer.add_variable('stabilizer.pitch', 'float')
    log_stabilizer.add_variable('stabilizer.roll', 'float')

    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    scf = SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache'))
    init(scf)
    simple_connect()
