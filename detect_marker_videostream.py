#!/usr/bin/env python3

import argparse
import time
import socket,struct, time
import numpy as np
import yaml
import cv2
import cv2.aruco as aruco

CAMERA_OFFSET = 2.2 #cm

# Args for setting IP/port of AI-deck. Default settings are for when
# AI-deck is in AP mode.
parser = argparse.ArgumentParser(description='Connect to AI-deck JPEG streamer example')
parser.add_argument("-n",  default="192.168.4.1", metavar="ip", help="AI-deck IP")
parser.add_argument("-p", type=int, default='5000', metavar="port", help="AI-deck port")
parser.add_argument('--save', action='store_true', help="Save streamed images")
args = parser.parse_args()

deck_port = args.p
deck_ip = args.n

print("Connecting to socket on {}:{}...".format(deck_ip, deck_port))
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((deck_ip, deck_port))
print("Socket connected")

imgdata = None
data_buffer = bytearray()

def rx_bytes(size):
  data = bytearray()
  while len(data) < size:
    data.extend(client_socket.recv(size-len(data)))
  return data

def aruco_marker_detection(image):# define aruco dictionary and parameters (parameters are default)
  arDic = aruco.Dictionary_get(aruco.DICT_ARUCO_ORIGINAL) #(aruco.DICT_6X6_1000)
  arPar = aruco.DetectorParameters_create()

  # detect aruco markers
  (corners, ids, rejected) = aruco.detectMarkers(image, arDic, parameters=arPar)

  # return coordinates of all markers and their ids
  if corners is not None:
    return corners, ids

def details_on_image(img, corners, distance, id):
  # save corners in array
  pts = np.array([[int(corners[0, 0]), int(corners[0, 1])], [int(corners[1, 0]), int(corners[1, 1])], [int(corners[2, 0]), int(corners[2, 1])], [int(corners[3, 0]), int(corners[3, 1])]], np.int32)
  pts = pts.reshape((-1, 1, 2))
  # print polygon over aruco marker
  cv2.polylines(img, [pts], True, (255,0,0), 3)
  # print distance between camera and marker on image
  distance = round(distance, 2)
  text_dist = str(distance) + "cm"
  text_id = "ID = " + str(id)
  cv2.putText(img, text_dist, (int(corners[1, 0]), int(corners[1, 1])-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2, cv2.LINE_AA)
  cv2.putText(img, text_id, (int(corners[1, 0]), int(corners[1, 1])-40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2, cv2.LINE_AA)
  return img

def main():
  # load calibration-data for markers
  with open('./calibrate_camera/calibration.yaml') as f:
    loadeddict = yaml.load(f)
    mtx = loadeddict.get('camera_matrix')
    dist = loadeddict.get('dist_coeff')
    matrix = np.array(mtx)
    distortion = np.array(dist)
  markerSize = 20   # size in cm

  start = time.time()
  count = 0
  while(1):
    # First get the info
    packetInfoRaw = rx_bytes(4)
    [length, routing, function] = struct.unpack('<HBB', packetInfoRaw)
    imgHeader = rx_bytes(length - 2)
    [magic, width, height, depth, format, size] = struct.unpack('<BHHBBI', imgHeader)
    if magic == 0xBC:
      # Now we start rx the image, this will be split up in packages of some size
      imgStream = bytearray()

      while len(imgStream) < size:
        packetInfoRaw = rx_bytes(4)
        [length, dst, src] = struct.unpack('<HBB', packetInfoRaw)
        chunk = rx_bytes(length - 2)
        imgStream.extend(chunk)
     
      count = count + 1
      meanTimePerImage = (time.time()-start) / count
      
      img_gray = np.frombuffer(imgStream, dtype=np.uint8)
      img_gray.shape = (244, 324)
      img_color = cv2.cvtColor(img_gray, cv2.COLOR_BayerBG2BGRA)
      corners, ids = aruco_marker_detection(img_gray)
      if corners is not None:
        i=0
        for c in corners:
          r_vec, t_vec, _= aruco.estimatePoseSingleMarkers(c, markerSize, matrix, distortion)
          distance = t_vec[0,0,2] - CAMERA_OFFSET
          img_color = details_on_image(img_color, c[0], distance, ids[i])
          i+=1
      cv2.imshow('Aruco marker detection', img_color)
      cv2.waitKey(1)


if __name__ == "__main__":
    main()


