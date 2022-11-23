#include "pmsis.h"
#include "bsp/bsp.h"
#include "bsp/camera.h"
#include "bsp/camera/himax.h"

#include "gaplib/ImgIO.h"

#define WIDTH    324
#ifdef QVGA_MODE
#define HEIGHT   244
#else
#define HEIGHT   324
#endif
#define BUFF_SIZE (WIDTH*HEIGHT)

PI_L2 unsigned char *buff;

static struct pi_device camera;
static volatile int done;

static void handle_transfer_end(void *arg)
{
    done = 1;
}

static int open_camera(struct pi_device *device)
{
    printf("Opening Himax camera\n");
    struct pi_himax_conf cam_conf;
    pi_himax_conf_init(&cam_conf);

#if defined(QVGA_MODE)
    cam_conf.format = PI_CAMERA_QVGA;
#endif

    pi_open_from_conf(device, &cam_conf);
    if (pi_camera_open(device))
        return -1;
    pi_camera_control(device, PI_CAMERA_CMD_START, 0);
    uint8_t set_value=3;
    uint8_t reg_value;
    pi_camera_reg_set(device, IMG_ORIENTATION, &set_value);
    pi_time_wait_us(1000000);
    pi_camera_reg_get(device, IMG_ORIENTATION, &reg_value);
    if (set_value!=reg_value)
    {
        printf("Failed to rotate camera image\n");
        return -1;
    }

    pi_camera_control(device, PI_CAMERA_CMD_AEG_INIT, 0);

    return 0;
}


int test_camera()
{
    //Set Cluster Frequency to max
    pi_freq_set(PI_FREQ_DOMAIN_CL, 50000000);
    pi_freq_set(PI_FREQ_DOMAIN_FC, 50000000);
    printf("Entering main controller\n");

#ifdef ASYNC_CAPTURE
    printf("Testing async camera capture\n");

#else
    printf("Testing normal camera capture\n");
#endif

    // Open the Himax camera
    if (open_camera(&camera))
    {
        printf("Failed to open camera\n");
        pmsis_exit(-1);
    }


    // Rotate camera orientation
    uint8_t set_value;
    uint8_t reg_value;

#ifdef QVGA_MODE
    set_value=1;
    pi_camera_reg_set(&camera, QVGA_WIN_EN, &set_value);
    pi_camera_reg_get(&camera, QVGA_WIN_EN, &reg_value);
    printf("qvga window enabled %d\n",reg_value);
#endif

#ifndef ASYNC_CAPTURE
    set_value=0;                                                                                                                                                                   
    pi_camera_reg_set(&camera, VSYNC_HSYNC_PIXEL_SHIFT_EN, &set_value);
    pi_camera_reg_get(&camera, VSYNC_HSYNC_PIXEL_SHIFT_EN, &reg_value);
    printf("vsync hsync pixel shift enabled %d\n",reg_value);
#endif

    // Reserve buffer space for image
    buff = pmsis_l2_malloc(BUFF_SIZE);
    if (buff == NULL){ return -1;}
    printf("Initialized buffer\n");

#ifdef ASYNC_CAPTURE
    // Start up async capture task
    done = 0;
    pi_task_t task;
    pi_camera_capture_async(&camera, buff, BUFF_SIZE, pi_task_callback(&task, handle_transfer_end, NULL));
#endif

    // Start the camera
    pi_camera_control(&camera, PI_CAMERA_CMD_START, 0);
#ifdef ASYNC_CAPTURE
    while(!done){pi_yield();}
#else
    pi_camera_capture(&camera, buff, BUFF_SIZE);
#endif

    // Stop the camera and immediately close it
    pi_camera_control(&camera, PI_CAMERA_CMD_STOP, 0);
    pi_camera_close(&camera);

    uint32_t time_before = pi_time_get_us();

    WriteImageToFile("../../../img_captured.ppm", WIDTH, HEIGHT, sizeof(uint8_t), buff, GRAY_SCALE_IO );

    pmsis_exit(0);
}

int main(void)
{
    printf("\n\t*** Image capture ***\n\n");
    return pmsis_kickoff((void *) test_camera);
}
