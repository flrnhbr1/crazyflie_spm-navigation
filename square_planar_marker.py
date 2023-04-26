"""
Created on  22.12.2022

@author: Florian Huber
"""

import cv2.aruco as aruco
import cv2
import math
import numpy as np

# define aruco dictionary and parameters (parameters are default)
AR_DIC = aruco.Dictionary_get(aruco.DICT_ARUCO_ORIGINAL)
AR_PAR = aruco.DetectorParameters_create()


def detect_marker(img):
    """
    function detects square planar marker from an image
    :param img: image with marker
    :return: int array[]: ids,
             double array[[]]: corners
             id and corner coordinates of markers
    """

    # detect aruco markers
    (corners, ids, rejected) = aruco.detectMarkers(img, AR_DIC, parameters=AR_PAR)

    return ids, corners


def estimate_marker_pose(corners, mark_size, mtrx, dist):
    """
    Estimates the pose of a square planar marker
    :param corners: corner coordinates of the marker
    :param mark_size: size of the marker
    :param mtrx: camera calibration matrix
    :param dist: camera calibration distortion coefficients
    :return: double array[]: t_vec,
             double array[]: r_vec,
             double array[]: eul_angles,
             translation and rotation vector of the marker + euler angles of the marker
    """

    # estimate translation and rotation vector of marker
    r_vec, t_vec, _ = aruco.estimatePoseSingleMarkers(corners, mark_size, mtrx, dist)
    # transform rotation vector to euler angles
    eul_angles = transform_r_vec_to_euler_angles(r_vec)

    return t_vec, r_vec, eul_angles


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


def transform_r_vec_to_euler_angles(r_vec):
    """
    Transforms the rotation vector to the euler angles
    :param r_vec: rotation vector of the marker
    :return: double array[]: euler angles,
             [alpha, beta, gamma]
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
