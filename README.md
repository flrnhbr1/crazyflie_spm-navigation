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