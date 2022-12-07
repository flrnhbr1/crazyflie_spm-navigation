import time
import logging

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

# URI to the Crazyflie to connect to
uri = 'radio://0/100/2M/E7E7E7E701'


def simple_connect():
    print("Yeah, I'm connected! :D")
    time.sleep(3)
    print("Now I will disconnect :'(")


if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        simple_connect()
