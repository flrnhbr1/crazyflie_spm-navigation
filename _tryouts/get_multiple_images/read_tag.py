import cv2
import cv2.aruco as aruco
i = 0
while(i <=46):
    file_path = "./images/{}.ppm".format(i)
    image = cv2.imread(file_path)
    arDic = aruco.Dictionary.get(aruco.DICT_6X6_1000)
    arPar = aruco.DetectorParameters.create()

    (corners, ids, rejected) = aruco.detectMarkers(image, arDic, parameters=arPar)
    #print(i)
    #print (len(ids))
    #print()
    if len(ids) < 20:
        print ("false")
    i += 1