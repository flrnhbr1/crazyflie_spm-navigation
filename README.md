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
- 
```shell
pip install pyyaml
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


## Important informations

### Marker
The square planar markers (spm), that have to be used must meet the following specifications:
- Marker type: ArUco marker
- Dictionary: Original ArUco
- Marker size: 200mm

The markers can be generated with python 
(see e.g., https://pyimagesearch.com/2020/12/14/generating-aruco-markers-with-opencv-and-python/) 
or with an online generator (e.g., https://chev.me/arucogen/).


### Camera calibration
In order to use the camera of the AI deck properly, the camera must be calibrated first.
There are multiple variants to calibrate the camera, the one I used can be downloaded from 
https://github.com/abakisita/camera_calibration.

After successfully calibrating the camera, the file calibration.yaml 
is saved. This file has to be referenced afterwards in application.py (see below)

    with open('./calibrate_camera/calibration.yaml') as f:
        loaded_dict = yaml.safe_load(f)
        mtx = loaded_dict.get('camera_matrix')
        dis = loaded_dict.get('dist_coeff')
        matrix = np.array(mtx)
        distortion = np.array(dis)
        marker_size = 20  # size in cm
    print("Camera calibration loaded")