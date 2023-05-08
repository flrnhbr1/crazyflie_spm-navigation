from gettext import translation
import cv2
import cv2.aruco as aruco
import numpy as np
import yaml

# get calibration-data
with open('../calibrate_camera/calibration.yaml') as f:
    loadeddict = yaml.load(f)
    mtx = loadeddict.get('camera_matrix')
    dist = loadeddict.get('dist_coeff')
    matrix = np.array(mtx)
    distortion = np.array(dist)

# get image 
image = cv2.imread("./images/20cm.ppm")
image_tilted = cv2.imread("./images/20cm_tilted.ppm")


# define aruco settings
arDic = aruco.Dictionary.get(aruco.DICT_6X6_1000)
arPar = aruco.DetectorParameters.create()
markerSize = 3.75   # size in cm


# read aruco tag
(corners, ids, rejected) = aruco.detectMarkers(image, arDic, parameters=arPar)

# print tag coordinates
print("\n\n --- Marker ID: ", ids)
r_vec, t_vec, _= aruco.estimatePoseSingleMarkers(corners, markerSize, matrix, distortion)
#print("Distance camera <-> arUco tag: ", t_vec[0,0,2])
print(t_vec)
print(r_vec)
print(corners)


(corners, ids, rejected) = aruco.detectMarkers(image_tilted, arDic, parameters=arPar)

# print tag coordinates
print("\n\n --- Marker ID: ", ids)
r_vec, t_vec, _= aruco.estimatePoseSingleMarkers(corners, markerSize, matrix, distortion)
#print("Distance camera <-> arUco tag: ", t_vec[0,0,2])
print(t_vec)
print(r_vec)
print(corners)
