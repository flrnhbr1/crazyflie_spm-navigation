# crazyflie_spm-navigation

As first step clone this repository 
```shell
git clone https://github.com/flrnhbr1/crazyflie_spm-navigation.git
```

## Guide for flashing the AI deck
To enable the image-streaming over wi-fi from the AI deck, the crazyflie and the AI deck must be prepared.
Also, the development environment must be set up and the deck must be flashed with the right file.

#### Prepare the crazyflie + AI deck and set up the environment :
https://www.bitcraze.io/documentation/tutorials/getting-started-with-aideck/


#### Flash the image-streaming file

Note: You may have to install this before the following steps:
```shell
sudo apt install build-essential libncurses5-dev
```

Now follow the guide in this link:
https://www.bitcraze.io/documentation/repository/aideck-gap8-examples/master/test-functions/wifi-streamer/

Note: for good performance make sure to set this variable in the wifi-img-streamer.c file:
 ```
static StreamerMode_t streamerMode = JPEG_ENCODING
```
Now application.py can access the image-stream, when the PC is connected to the AI deck wi-fi

## Python requirements for the main application 
 The following python packages must be installed

#### numpy:
```shell
pip install numpy
```
#### yaml:
- Ubuntu 20.04
```shell
pip install yaml
```
- macOS
```shell
pip install pyyaml
```

#### matplotlib for plotting data:
```shell
pip install matplotlib
```

#### opencv for image processing:
```shell
pip install opencv-python
```
#### opencv contrib for aruco markers:
```shell
pip install opencv-contrib-python
```

#### crazyflie-lib-python:
```shell
git clone https://github.com/bitcraze/crazyflie-lib-python.git
cd crazyflie-lib-python
pip install -e .
```
- For detailed install information see: https://github.com/bitcraze/crazyflie-lib-python


## Important information

### Marker
The square planar markers (spm), that have to be used must meet the following specifications:
- Marker type: ArUco marker
- Dictionary: Original ArUco
- Marker size: 200mm

The markers can be generated with python 
(e.g., https://pyimagesearch.com/2020/12/14/generating-aruco-markers-with-opencv-and-python/) 
or with an online generator (e.g., https://chev.me/arucogen/).


## Setup for the application

### Camera calibration
In order to use the camera of the AI deck properly, the camera must be calibrated first.
There are multiple variants to calibrate the camera, the one I used can be downloaded from 
https://github.com/abakisita/camera_calibration.

After successfully calibrating the camera, the file calibration.yaml 
is saved. This file has to be referenced afterwards in application.py (see below)
````python
    with open('./calibrate_camera/calibration.yaml') as f:
        loaded_dict = yaml.safe_load(f)
        mtx = loaded_dict.get('camera_matrix')
        dis = loaded_dict.get('dist_coeff')
        matrix = np.array(mtx)
        distortion = np.array(dis)
        marker_size = 20  # size in cm
    print("Camera calibration loaded")
````

### Set constants

In the head of the python code a few constants must be set when setting up 
a new environment for the crazyflie to fly.

````python
# default height of takeoff
TAKEOFF_HEIGHT = 0.8

# highest used marker id, start from id=0
# marker type must be aruco original dictionary
MAX_MARKER_ID = 1

# define destination vector marker <--> crazyflie
DISTANCE = np.array([0, 0, 75])  # [cm]
````

The ```TAKEOFF_HEIGHT``` is the initial height the crazyflie hovers after
startup.  ```MAX_MARKER_ID``` is the highest ID in th environment. The application
always starts searching at ID=0 and proceeds until the maximum id defined. 
```DISTANCE``` is a array that defines the vector (with respect to the center of the marker),
in which the crazyflie should align in front of every marker. The first value is the translation 
in  left/right, the second value the translation in up/down and the last (here set to 0.75) is 
the translation in forward/backward. In the upper example, the crazyflie will align directly
in front of the center of the marker, with a distance of 0.75m.

### AI deck connection
The first step of the main function, is to open a socket to the AI deck. The following code fragment
shows the default IP address and port number of every AI deck. 
````python
if __name__ == "__main__":
    # Arguments for setting IP/port of AI deck. Default settings are for when
    parser = argparse.ArgumentParser(description='Connect to AI-deck JPEG streamer example')
    parser.add_argument("-n", default="192.168.4.1", metavar="ip", help="AI-deck IP")
    parser.add_argument("-p", type=int, default='5000', metavar="port", help="AI-deck port")
    args = parser.parse_args()
    deck_port = args.p
    deck_ip = args.n
````

So if a new deck is used, this is the default setting.
However, it is possible to change this settings on the AI deck if needed. Be sure to also change it in the python code as well.