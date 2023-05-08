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

# import open cv functions
import cv2


def rx_bytes(size):
    """
    fetches data from the AI deck over wi-fi
    :param size: size of data segment to fetch
    :return: bytearray: data
             the received data in a bytearray
    """

    data = bytearray()
    while len(data) < size:
        data.extend(client_socket.recv(size - len(data)))
    return data


def get_image_from_ai_deck():
    """
    function to fetch image from the AI deck
    :return: -
             saves the captured image in the global variable 'image'
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
        [magic, _, _, _, image_format, size] = struct.unpack('<BHHBBI', img_header)
        if magic == 0xBC:
            # Receive the image, this will be split up in packages of some size
            img_stream = bytearray()

            while len(img_stream) < size:
                packet_info_raw = rx_bytes(4)
                [length, _, _] = struct.unpack('<HBB', packet_info_raw)
                chunk = rx_bytes(length - 2)
                img_stream.extend(chunk)

            if image_format == 0:
                # RAW image format streamed
                img_gray = np.frombuffer(img_stream, dtype=np.uint8)
                img_gray.shape = (244, 324)

            else:
                # JPEG encoded image format streamed
                # stores the image temporary in this path
                with open("../wifi_streaming/imgBuffer/img.jpeg", "wb") as im:
                    im.write(img_stream)
                np_arr = np.frombuffer(img_stream, np.uint8)
                img_gray = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

            image = img_gray


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

    image = None
    stop_thread_flag = False

    #cv2.namedWindow("img", cv2.WINDOW_NORMAL)

    t1 = threading.Thread(target=get_image_from_ai_deck)
    t1.start()
    # set global variable
    if image is not None:
        cv2.imshow('img', image)
        cv2.waitKey(1)
