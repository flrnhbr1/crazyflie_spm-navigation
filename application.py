import logging
import sys
import time
import argparse
import yaml
import socket
import struct
import numpy as np

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


def rx_bytes(size):
    data = bytearray()
    while len(data) < size:
        data.extend(client_socket.recv(size - len(data)))
    return data


def marker_detection(image):  # define aruco dictionary and parameters (parameters are default)
    ar_dic = aruco.Dictionary_get(aruco.DICT_ARUCO_ORIGINAL)  # (aruco.DICT_6X6_1000)
    ar_par = aruco.DetectorParameters_create()

    # detect aruco markers
    (corners, ids, rejected) = aruco.detectMarkers(image, ar_dic, parameters=ar_par)

    # return coordinates of all markers and their ids
    if corners is not None:
        return corners, ids


def print_marker_info_on_image(img, corners, distance, id):
    # save corners in array
    pts = np.array([[int(corners[0, 0]), int(corners[0, 1])], [int(corners[1, 0]), int(corners[1, 1])],
                    [int(corners[2, 0]), int(corners[2, 1])], [int(corners[3, 0]), int(corners[3, 1])]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    # print polygon over aruco marker
    cv2.polylines(img, [pts], True, (255, 0, 0), 3)
    # print distance between camera and marker on image
    distance = round(distance, 2)
    text_dist = str(distance) + "cm"
    text_id = "ID = " + str(id)
    cv2.putText(img, text_dist, (int(corners[1, 0]), int(corners[1, 1]) - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, text_id, (int(corners[1, 0]), int(corners[1, 1]) - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 0, 0),
                2, cv2.LINE_AA)
    return img


def fetch_image():
    # Get the info
    packet_info_raw = rx_bytes(4)
    [length, _, _] = struct.unpack('<HBB', packet_info_raw)
    img_header = rx_bytes(length - 2)
    [magic, _, _, _, format, size] = struct.unpack('<BHHBBI', img_header)
    if magic == 0xBC:
        # Receive the image, this will be split up in packages of some size
        img_stream = bytearray()

        while len(img_stream) < size:
            packet_info_raw = rx_bytes(4)
            [length, _, _] = struct.unpack('<HBB', packet_info_raw)
            chunk = rx_bytes(length - 2)
            img_stream.extend(chunk)

        if format == 0:
            # RAW image format streamed
            img_gray = np.frombuffer(img_stream, dtype=np.uint8)
            img_gray.shape = (244, 324)

        else:
            # JPEG encoded image format streamed
            # stores the image temporary in this path
            with open("./wifi_streaming/imgBuffer/img.jpeg", "wb") as f:
                f.write(img_stream)
            np_arr = np.frombuffer(img_stream, np.uint8)
            img_gray = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

        # img_color is only used for showing on screen
        img_color = cv2.cvtColor(img_gray, cv2.COLOR_BayerBG2BGRA)
        corners, ids = marker_detection(img_gray)
        if corners is not None:
            i = 0
            for c in corners:
                r_vec, t_vec, _ = aruco.estimatePoseSingleMarkers(c, marker_size, matrix, distortion)
                distance = t_vec[0, 0, 2]
                img_color = print_marker_info_on_image(img_color, c[0], distance, ids[i])
                i += 1
        cv2.imshow('spm detection', img_color)
        cv2.waitKey(1)


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

    def get_battery_level(self):
        # check current battery voltage of cf
        voltage, _, _, _ = get_cf_data()
        time.sleep(0.02)
        self.v_bat = voltage
        return voltage

    def get_yaw(self):
        # returns current yaw
        _, yaw, _, _ = get_cf_data()
        time.sleep(0.02)
        self.psi = yaw
        return yaw

    def takeoff(self, height):
        # cf takes of "height" meter
        self.mc.take_off(height=height, velocity=0.2)

    def land(self):
        self.mc.land(velocity=0.2)

    def turn_left(self, degrees):
        self.mc.turn_left(degrees, rate=22.5)


if __name__ == "__main__":
    # Arguments for setting IP/port of AI-deck. Default settings are for when
    parser = argparse.ArgumentParser(description='Connect to AI-deck JPEG streamer example')
    parser.add_argument("-n", default="192.168.4.1", metavar="ip", help="AI-deck IP")
    parser.add_argument("-p", type=int, default='5000', metavar="port", help="AI-deck port")
    args = parser.parse_args()

    deck_port = args.p
    deck_ip = args.n

    print("Connecting to socket on {}:{}...".format(deck_ip, deck_port))
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((deck_ip, deck_port))
    print("Socket connected")

    # load calibration-data of camera
    with open('./calibrate_camera/calibration.yaml') as f:
        loaded_dict = yaml.safe_load(f)
        mtx = loaded_dict.get('camera_matrix')
        dist = loaded_dict.get('dist_coeff')
        matrix = np.array(mtx)
        distortion = np.array(dist)
        marker_size = 20  # size in cm

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
        v_bat = crazyflie.get_battery_level()
        if v_bat < LOW_BAT:
            print("Battery-level too low [Voltage = " + str(round(v_bat, 2)) + "V]")
            sys.exit(1)

        print("Battery-level OK [Voltage = " + str(round(v_bat, 2)) + "V]")
        crazyflie.takeoff(0.5)
        print("crazyflie taking off!")
        time.sleep(2)
        spm_stack = []
        count = 0
        while count < 100:
            crazyflie.turn_left(3.6)
            fetch_image()
            count += 1

        crazyflie.land()



