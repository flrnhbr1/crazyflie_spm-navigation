import logging
import sys
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

URI = uri_helper.uri_from_env(default='radio://0/100/2M/E7E7E7E701')

DEFAULT_HEIGHT = 0.5

logging.basicConfig(level=logging.ERROR)


def take_off_simple(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        time.sleep(1)
        mc.stop()


if __name__ == '__main__':
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
