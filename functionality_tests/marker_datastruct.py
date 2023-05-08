import numpy as np
import cv2
import cv2.aruco as aruco
import yaml
import math

MAX_MARKER_ID = 3
FONT = cv2.FONT_HERSHEY_SIMPLEX
COLOR = (180, 180, 20)

# load calibration-data of camera
with open('../calibrate_camera/calibration.yaml') as f:
    loaded_dict = yaml.safe_load(f)
    mtx = loaded_dict.get('camera_matrix')
    dis = loaded_dict.get('dist_coeff')
    matrix = np.array(mtx)
    distortion = np.array(dis)
    marker_size = 20  # size in cm
print("Camera calibration loaded")


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
    eul_angles = transform_r_vec_to_euler_angles(r_vec)

    return t_vec, r_vec, eul_angles


def transform_r_vec_to_euler_angles(r_vec):
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
    # img = cv2.cvtColor(img, cv2.COLOR_BayerBG2BGRA)

    # save corners in array
    pts = np.array([[int(corners[0, 0]), int(corners[0, 1])], [int(corners[1, 0]), int(corners[1, 1])],
                    [int(corners[2, 0]), int(corners[2, 1])], [int(corners[3, 0]), int(corners[3, 1])]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    # print polygon over marker
    cv2.polylines(img, [pts], True, (255, 0, 0), 3)
    # print translation vector and euler angles
    cv2.putText(img, "marker id = " + str(marker_id), (10, 10), FONT, 0.4, COLOR, 2, cv2.LINE_AA)
    cv2.putText(img, "t_vec= " + str(t_vec[0, 0]) + " -->[tx ty tz]", (10, 20), FONT, 0.4, COLOR, 2, cv2.LINE_AA)
    cv2.putText(img, "eul_angles= " + str(eul_angles) + " -->[a b y]", (10, 30), FONT, 0.4, COLOR, 2, cv2.LINE_AA)
    # print axis to marker
    cv2.drawFrameAxes(img, mtrx, dist, r_vec, t_vec, 10, 5)

    return img


marker_geometry = np.zeros([MAX_MARKER_ID, 2, 3])
image_to_process = cv2.imread("./marker.jpeg")

marker_ids, marker_corners = detect_marker(image_to_process)
for i, c in enumerate(marker_corners):
    trans_vec, rot_vec, euler_angles = estimate_marker_pose(c)
    image_to_print = print_marker_info_on_image(image_to_process, c[0], marker_ids[i], matrix,
                                                distortion, trans_vec, rot_vec, euler_angles)
    marker_geometry[i, 0] = trans_vec[0, 0]
    marker_geometry[i, 1] = euler_angles

    cv2.imshow('spm detection', image_to_process)

print(marker_geometry[0])

print(marker_ids[0, 0])
cv2.waitKey(0)
