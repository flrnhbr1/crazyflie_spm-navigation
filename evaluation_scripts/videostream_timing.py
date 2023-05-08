import argparse
import datetime
import sys
import time
import socket, os, struct, time
import numpy as np
import matplotlib.pyplot as plt
import yaml

# Args for setting IP/port of AI-deck. Default settings are for when
# AI-deck is in AP mode.
parser = argparse.ArgumentParser(description='Connect to AI-deck JPEG streamer example')
parser.add_argument("-n", default="192.168.4.1", metavar="ip", help="AI-deck IP")
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
        data.extend(client_socket.recv(size - len(data)))
    return data


import cv2

start = time.time()
count = 0
counter = 0
counter2 = 0

time_log = []
while counter <= 2000:
    # First get the info
    start_time = time.time()
    packetInfoRaw = rx_bytes(4)
    [length, routing, function] = struct.unpack('<HBB', packetInfoRaw)
    # print("Length is {}".format(length))
    # print("Route is 0x{:02X}->0x{:02X}".format(routing & 0xF, routing >> 4))
    # print("Function is 0x{:02X}".format(function))

    imgHeader = rx_bytes(length - 2)
    # print(imgHeader)
    # print("Length of data is {}".format(len(imgHeader)))
    [magic, width, height, depth, format, size] = struct.unpack('<BHHBBI', imgHeader)

    if magic == 0xBC:
        # print("Magic is good")
        # print("Resolution is {}x{} with depth of {} byte(s)".format(width, height, depth))
        # print("Image format is {}".format(format))
        # print("Image size is {} bytes".format(size))

        # Now we start rx the image, this will be split up in packages of some size
        imgStream = bytearray()

        while len(imgStream) < size:
            packetInfoRaw = rx_bytes(4)
            [length, dst, src] = struct.unpack('<HBB', packetInfoRaw)
            # print("Chunk size is {} ({:02X}->{:02X})".format(length, src, dst))
            chunk = rx_bytes(length - 2)
            imgStream.extend(chunk)

        # count = count + 1
        # meanTimePerImage = (time.time() - start) / count
        # print("{}".format(meanTimePerImage))
        # print("{}".format(1 / meanTimePerImage))

        if format == 0:
            bayer_img = np.frombuffer(imgStream, dtype=np.uint8)
            bayer_img.shape = (244, 324)
            #color_img = cv2.cvtColor(bayer_img, cv2.COLOR_BayerBG2BGRA)
            #cv2.imshow('Raw', bayer_img)
            #cv2.imshow('Color', color_img)

            #cv2.waitKey(1)
        else:
            with open("../functionality_tests/img.jpeg", "wb") as f:
                f.write(imgStream)
            nparr = np.frombuffer(imgStream, np.uint8)
            decoded = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
            # cv2.imshow('JPEG', decoded)
        elapsed_time = time.time() - start_time
        if elapsed_time > 0.01 and counter2 > 3:
            time_log.append(elapsed_time)
            counter += 1
        print(str(counter) + " | Elapsed time: " + str(elapsed_time))
        #print(" --> Average time: " + str(np.average(time_log)))
        print("---")
        counter2 += 1
        #cv2.imshow('RAW', bayer_img)

    if cv2.waitKey(1) == ord('q'):
        print("broke loop")
        client_socket.close()
        sys.exit(1)
print(time_log)

data = {'RTT': np.asarray(time_log).tolist()}

t = datetime.datetime.now()
filename = "Log_" + str(t.year) + "-" + str(t.month) + "-" + str(t.day) + "T" + str(t.hour) + "-" + \
           str(t.minute) + "-" + str(t.second)

path = "../plot/timing_data/" + filename + ".yaml"
print("Save data...")

with open(path, "w") as f:
    yaml.dump(data, f)

print("Log saved!")

