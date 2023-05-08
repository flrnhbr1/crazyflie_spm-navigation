import cv2
import numpy as np
# import picture
image = cv2.imread("img_captured.ppm")
cv2.imshow('Image', image)


arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_ARUCO_ORIGINAL)
arucoParams = cv2.aruco.DetectorParameters.create()
(corners, ids, rejected) = cv2.aruco.detectMarkers(image, arucoDict, parameters=arucoParams)

print(corners)
print(ids)

cv2.waitKey(0)
