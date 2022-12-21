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

# set constants
LOW_BAT = 3.5  # if the cf reaches this battery voltage level, it should land
TAKEOFF_HEIGHT = 0.5
URI = uri_helper.uri_from_env(default='radio://0/100/2M/E7E7E7E701')


def get_cf_data():
    """
    fetches logging information from the crazyflie
    :return: battery level and current yaw, pitch, roll values
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
    :return: the received data in a bytearray
    """

    data = bytearray()
    while len(data) < size:
        data.extend(client_socket.recv(size - len(data)))
    return data


def detect_marker(img):
    """
    function detects square planar marker from an image
    :param img: image with marker
    :return: id and corner coordinates of markers
    """

    # define aruco dictionary and parameters (parameters are default)
    ar_dic = aruco.Dictionary_get(aruco.DICT_ARUCO_ORIGINAL)  # (aruco.DICT_6X6_1000)
    ar_par = aruco.DetectorParameters_create()

    # detect aruco markers
    (corners, ids, rejected) = aruco.detectMarkers(img, ar_dic, parameters=ar_par)

    return ids, corners


def estimate_marker_pose(corners):
    """
    Estimates the pose of a square planar marker
    :param corners: corner coordinates of the marker
    :return: rotation and translation vector of the marker + euler angles of the marker
    """

    # estimate translation and rotation vector of marker
    r_vec, t_vec, _ = aruco.estimatePoseSingleMarkers(corners, marker_size, matrix, distortion)
    # transform rotation vector to euler angles
    eul_angles = rotation_vector_to_euler_angles(r_vec)

    return t_vec, r_vec, eul_angles


def rotation_vector_to_euler_angles(r_vec):
    """
    Transforms the rotation vector to the euler angles
    :param r_vec: rotation vector of the marker
    :return: euler angles [alpha, beta, gamma]
             alpha: rotation around the left/right axis
             beta:  rotation around the up/down axis
             gamma: rotation around the forward/backward axis
    """
    r_matrix, _ = cv2.Rodrigues(r_vec)
    sy = math.sqrt(r_matrix[0, 0] * r_matrix[0, 0] + r_matrix[1, 0] * r_matrix[1, 0])

    singular = sy < 1e-6

    if not singular:
        x = math.atan2(r_matrix[2, 1], r_matrix[2, 2])
        y = math.atan2(-r_matrix[2, 0], sy)
        z = math.atan2(r_matrix[1, 0], r_matrix[0, 0])
    else:
        x = math.atan2(-r_matrix[1, 2], r_matrix[1, 1])
        y = math.atan2(-r_matrix[2, 0], sy)
        z = 0

    if x <= 0:
        x += math.pi

    else:
        x -= math.pi

    return np.array([x, y, z])


def print_marker_info_on_image(img, corners, marker_id, mtrx, dist, t_vec, r_vec, eul_angles):
    """
    function to print a rectangle, axis and text to the marker
    :param eul_angles:
    :param img: input image with marker
    :param corners: corner coordinates of the marker
    :param marker_id: id of the marker
    :param mtrx: camera calibration matrix
    :param dist: camera calibration distortion coefficients
    :param r_vec: rotation vector of the marker
    :param t_vec: translation vector marker
    :return: image with printed info
    """

    # convert to colored image
    img = cv2.cvtColor(img, cv2.COLOR_BayerBG2BGRA)

    font = cv2.FONT_HERSHEY_SIMPLEX
    # save corners in array
    pts = np.array([[int(corners[0, 0]), int(corners[0, 1])], [int(corners[1, 0]), int(corners[1, 1])],
                    [int(corners[2, 0]), int(corners[2, 1])], [int(corners[3, 0]), int(corners[3, 1])]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    # print polygon over marker
    cv2.polylines(img, [pts], True, (255, 0, 0), 3)
    # print translation vector and euler angles
    cv2.putText(img, "marker id = " + str(marker_id), (10, 10), font, 0.4, (255, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, "t_vec= " + str(t_vec[0, 0]) + " -->[tx ty tz]", (10, 30), font, 0.4, (255, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, "eul_angles= " + str(eul_angles) + " -->[a b y]", (10, 50), font, 0.4, (255, 0, 0), 2, cv2.LINE_AA)
    # print axis to marker
    cv2.drawFrameAxes(img, mtrx, dist, r_vec, t_vec, 10, 5)

    return img


def fetch_image():
    """
    function to fetch image from the AI deck
    :return: saves the captured image in the global variable 'image'
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

            # set global variable
            image = img_gray


class SPM:
    """
    class for square planar markers objects
    """

    def __init__(self, id, corner, tvec, rvec, yaw_angle):
        # constructor
        self.id = id
        self.corners = corner
        self.t_vec = tvec
        self.r_vec = rvec
        self.current_yaw = yaw_angle


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
        self.v_bat, self.psi, self.theta, self.phi = get_cf_data()
        self.scf = scf
        self.mc = MotionCommander(scf)

    def decks_attached(self):
        """
        function checks if AI and flow deck are attached
        :return:    True if both decks are attached
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
        :return: battery voltage in V
        """

        # check current battery voltage of cf
        voltage, _, _, _ = get_cf_data()
        time.sleep(0.02)
        self.v_bat = voltage
        return voltage

    def get_yaw(self):
        """
        fetches battery level from crazyflie
        :return: yaw angle in degrees
        """

        # returns current yaw
        _, yaw, _, _ = get_cf_data()
        time.sleep(0.02)
        self.psi = yaw
        return yaw

    def takeoff(self, height):
        """
        lets the crazyflie takeoff
        :param height: height to which the crazyflie should takeoff
        :return: -
        """

        self.mc.take_off(height=height, velocity=0.1)

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

        self.mc.land(velocity=0.1)

    def turn(self, degrees):
        """
        crazyflie turns around
        :param degrees: amount of degrees to turn
                        if degrees > 0 --> turn right
                        if degrees < 0 --> turn left

        :return: -
        """
        if degrees > 0:
            self.mc.turn_right(abs(degrees), rate=45)

        if degrees < 0:
            self.mc.turn_left(abs(degrees), rate=45)

    def move(self, x, y, z):
        """
        crazyflie moves in straight line
        :param x: forward/backward
        :param y: left/right
        :param z: up/down
        :return: -
        """

        self.mc.move_distance(x, y, z, velocity=0.1)

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

    # starting the main functionality
    with SyncCrazyflie(URI, cf) as scf:
        crazyflie = CF(scf)
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

        # All checks done
        # Now start the crazyflie!
        print("All initial checks done!")
        print("crazyflie taking off!")
        # crazyflie.takeoff(TAKEOFF_HEIGHT)
        time.sleep(1)

        image = None

        # flag to stop the image-thread
        stop_thread_flag = False
        t1 = threading.Thread(target=fetch_image)
        t1.start()
        time.sleep(1)

        while image is not None:
            for t in range(0, 361):
                # crazyflie.turn(t)
                time.sleep(0.1)
                image_to_print = image
                marker_ids, marker_corners = detect_marker(image)
                for i, c in enumerate(marker_corners):
                    trans_vec, rot_vec, euler_angles = estimate_marker_pose(c)
                    image_to_print = print_marker_info_on_image(image, c[0], marker_ids[i], matrix,
                                                                distortion, trans_vec, rot_vec, euler_angles)
                cv2.imshow('spm detection', image_to_print)
                cv2.waitKey(1)

        # crazyflie.stop()
        # crazyflie.land()
        client_socket.close()
        stop_thread_flag = True
        t1.join()
