import cv2
import numpy as np


arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_1000)
arucoParams = cv2.aruco.DetectorParameters.create()
count = 1
while(count < 73):
    image = cv2.imread(f"./images/{count}.png")
    (corners, ids, rejected) = cv2.aruco.detectMarkers(image, arucoDict, parameters=arucoParams)
    print(str(count) + ": " + str(ids.size))
    count+=1
