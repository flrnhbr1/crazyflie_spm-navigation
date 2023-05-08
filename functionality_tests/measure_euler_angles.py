import argparse
import math
import socket
import struct
import time

import cv2
import cv2.aruco as aruco
import numpy as np
import yaml

import square_planar_marker as spm

CAMERA_OFFSET = 0

# Args for setting IP/port of AI-deck. Default settings are for when
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

# load calibration-data for markers
with open(
        '/Users/florianhuber/Documents/Uni/Bachelor_Thesis/crazyflie_spm-navigation/calibrate_camera/calibration.yaml') as f:
    loadeddict = yaml.safe_load(f)
    mtx = loadeddict.get('camera_matrix')
    dist = loadeddict.get('dist_coeff')
    matrix = np.array(mtx)
    distortion = np.array(dist)
    marker_size = 20  # size in cm
imgdata = None
data_buffer = bytearray()


def rotation_vector_to_euler_angles(r):
    r_matrix, _ = cv2.Rodrigues(r)
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


def estimate_marker_pose(img, id, corners):
    """
    Estimates the pose of a square planar marker
    :param img: image with the marker
    :param id: id of the marker to be estimated
    :param corners: corner coordinates of the marker
    :return:
    """
    # estimate translation and rotation vector of marker
    r_vec, t_vec, _ = aruco.estimatePoseSingleMarkers(corners, marker_size, matrix, distortion)
    # transform rotation vector to rotation matrix
    print(t_vec[0, 0])
    euler_angles = rotation_vector_to_euler_angles(r_vec)
    # pose_matrix = cv2.hconcat((r_matrix, t_vec))
    # _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_matrix)

    img = print_marker_details(img, corners[0], id, matrix, distortion, r_vec, t_vec, euler_angles, 1)
    # img = print_marker_position(img, corners[0])
    return img, euler_angles


def print_markerinfo_on_image(img, corners, distance, id):
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
    cv2.putText(img, text_id, (int(corners[1, 0]), int(corners[1, 1]) - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0),
                2, cv2.LINE_AA)
    return img


def print_marker_info_on_image(img, corners, id, mtrx, dist, rot_vec, trans_vec, eul):
    """
    function to print a rectangle, axis and text to the marker
    :param eul:
    :param img: input image with marker
    :param corners: corner coordinates of the marker
    :param id: id of the marker
    :param mtrx:
    :param dist:
    :param rot_vec:
    :param trans_vec:
    :return: image with printed info
    """

    # save corners in array
    pts = np.array([[int(corners[0, 0]), int(corners[0, 1])], [int(corners[1, 0]), int(corners[1, 1])],
                    [int(corners[2, 0]), int(corners[2, 1])], [int(corners[3, 0]), int(corners[3, 1])]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    # print polygon over aruco marker
    cv2.polylines(img, [pts], True, (255, 0, 0), 3)
    # print rounded distance between camera and marker on image
    text_dist = str(round(trans_vec[0, 0, 2], 2)) + "cm"
    text_id = "ID = " + str(id)
    cv2.putText(img, str(trans_vec), (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, str(eul), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 2, cv2.LINE_AA)
    # print axis to marker
    cv2.drawFrameAxes(img, mtrx, dist, rot_vec, trans_vec, 10, 5)

    return img


def print_marker_details(img, corners, marker_id, mtrx, dist, t_vec, r_vec, eul_angles, index):
    """
    function to print a rectangle, axis and text to the marker
    :param img: input image with marker
    :param corners: corner coordinates of the marker
    :param marker_id: id of the marker
    :param mtrx: camera calibration matrix
    :param dist: camera calibration distortion coefficients
    :param r_vec: rotation vector of the marker
    :param t_vec: translation vector marker
    :param eul_angles: euler angles of the marker
    :param index: index of the marker regarding the number of all detected markers
    :return: image: img,
             image with printed info
    """

    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (50, 160, 200)

    # save corners in array
    pts = np.array([[int(corners[0, 0]), int(corners[0, 1])], [int(corners[1, 0]), int(corners[1, 1])],
                    [int(corners[2, 0]), int(corners[2, 1])], [int(corners[3, 0]), int(corners[3, 1])]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    # print polygon over marker
    cv2.polylines(img, [pts], True, color, 2)

    # define text properties
    str_id = "marker id = " + str(marker_id)
    pos_id = (10, ((4 * index + 1) * 10))
    str_t_vec = "t_vec= " + str(np.round(t_vec[0, 0], decimals=3)) + " -->[tx ty tz]"
    pos_t_vec = (10, ((4 * index + 2) * 10))
    str_eul = "eul_angles= " + str(np.round(eul_angles, decimals=3)) + " -->[a b y]"
    pos_eul = (10, ((4 * index + 3) * 10))
    # print translation vector and euler angles
    cv2.putText(img, str_id, pos_id, font, 0.3, color, 1, cv2.LINE_AA)
    cv2.putText(img, str_t_vec, pos_t_vec, font, 0.3, color, 1, cv2.LINE_AA)
    cv2.putText(img, str_eul, pos_eul, font, 0.3, color, 1, cv2.LINE_AA)
    # print axis to marker
    cv2.drawFrameAxes(img, mtrx, dist, r_vec, t_vec, 10, 5)

    return img


def print_marker_position(img, corners):
    """
    function to print a rectangle, axis and text to the marker
    :param img: input image with marker
    :param corners: corner coordinates of the marker

    :return: image: img,
             image with rectangle around marker
    """

    color = (50, 160, 200)

    # save corners in array
    pts = np.array([[int(corners[0, 0]) - 10, int(corners[0, 1]) - 10],
                    [int(corners[1, 0]) + 10, int(corners[1, 1]) - 10],
                    [int(corners[2, 0]) + 10, int(corners[2, 1]) + 15],
                    [int(corners[3, 0]) - 10, int(corners[3, 1]) + 10]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    # print polygon over marker
    cv2.polylines(img, [pts], True, color, 2)
    return img


def main():
    start = time.time()
    count = 0

    while 1:
        # Get the info
        packet_info_raw = rx_bytes(4)
        [length, routing, function] = struct.unpack('<HBB', packet_info_raw)
        img_header = rx_bytes(length - 2)
        [magic, width, height, depth, format, size] = struct.unpack('<BHHBBI', img_header)
        if magic == 0xBC:
            # Receive the image, this will be split up in packages of some size
            img_stream = bytearray()

            while len(img_stream) < size:
                packet_info_raw = rx_bytes(4)
                [length, dst, src] = struct.unpack('<HBB', packet_info_raw)
                chunk = rx_bytes(length - 2)
                img_stream.extend(chunk)

            count = count + 1
            mean_time_per_image = (time.time() - start) / count

            if format == 0:
                # RAW image format streamed
                img_gray = np.frombuffer(img_stream, dtype=np.uint8)
                img_gray.shape = (244, 324)

            else:
                # JPEG encoded image format streamed
                # stores the image temporary in the path
                with open("/Users/florianhuber/Documents/Uni/Bachelor_Thesis/crazyflie_spm-navigation/wifi_streaming"
                          "/imgBuffer/img.jpeg", "wb") as f:
                    f.write(img_stream)
                np_arr = np.frombuffer(img_stream, np.uint8)
                img_gray = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

            # img_color is only used for showing on screen
            euler = None
            img_color = cv2.cvtColor(img_gray, cv2.COLOR_BayerBG2BGRA)
            marker_ids = None
            while marker_ids is None:
                marker_ids, marker_corners = spm.detect_marker(img_gray)
                cv2.imshow('spm detection', img_gray)
                img_color = cv2.cvtColor(img_gray, cv2.COLOR_BayerBG2BGRA)
            for c, i in enumerate(marker_ids):
                # estimate pose of marker with desired id
                trans_vec, rot_vec, euler_angles = spm.estimate_marker_pose(marker_corners[c], marker_size,
                                                                            matrix, distortion)
                img_color = spm.print_marker_details(img_color, c, 3, matrix, distortion, trans_vec, rot_vec,
                                                     euler_angles, 0)

            cv2.imshow('spm detection', img_color)
            print(euler)
            cv2.waitKey(1)


if __name__ == "__main__":
    main()
