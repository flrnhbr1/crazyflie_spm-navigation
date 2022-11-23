APP = image_capture
APP_SRCS += image_capture.c $(GAP_LIB_PATH)/img_io/ImgIO.c
APP_INC  += . $(GAP_LIB_PATH)/include

APP_CFLAGS += -O3 -g


PMSIS_OS ?= pulp_os

# this flag enables asynchronous image capturing
# keep in mind that you should always have a buffer enqueued
# if recording an image stream to avoid missing data (meaning you need 2)
APP_CFLAGS += -DASYNC_CAPTURE
# configures camera in QVGA format (324x244)
# the extra 4 is from padding for the RGB camera (but also present on the grey one)
APP_CFLAGS += -DQVGA_MODE

clean::
	rm -rf img_raw.ppm img_color.ppm img_gray.ppm img_inverted.ppm

include $(RULES_DIR)/pmsis_rules.mk
