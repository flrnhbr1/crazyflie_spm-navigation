import math
import yaml
import numpy as np
import matplotlib.pyplot as plt

# read data
with open("timing_data/Log_fullTiming_Raw.yaml") as f:
    loaded_dict = yaml.safe_load(f)
    cam = loaded_dict.get('camera')
    det = loaded_dict.get('detection')
    est = loaded_dict.get('estimation')
    cal = loaded_dict.get('calculation')
    exe = loaded_dict.get('execution')

    camera_time_raw = np.array(cam)
    detection_time_raw = np.array(det)
    estimation_time_raw = np.array(est)
    calculation_time_raw = np.array(cal)
    execution_time_raw = np.array(exe)

with open("timing_data/Log_fullTiming_Jpeg.yaml") as f:
    loaded_dict = yaml.safe_load(f)
    cam = loaded_dict.get('camera')
    det = loaded_dict.get('detection')
    est = loaded_dict.get('estimation')
    cal = loaded_dict.get('calculation')
    exe = loaded_dict.get('execution')

    camera_time_jpg = np.array(cam)
    detection_time_jpg = np.array(det)
    estimation_time_jpg = np.array(est)
    calculation_time_jpg = np.array(cal)
    execution_time_jpg = np.array(exe)

print("Plotting data loaded")

avg_cam_raw = np.average(camera_time_raw)
avg_det_raw = np.average(detection_time_raw)
avg_est_raw = np.average(estimation_time_raw)
avg_cal_raw = np.average(calculation_time_raw)
avg_exe_raw = np.average(execution_time_raw)
full_time_raw = camera_time_raw + detection_time_raw + estimation_time_raw + calculation_time_raw + execution_time_raw
avg_full_raw = np.average(full_time_raw)

avg_cam_jpg = np.average(camera_time_jpg)
avg_det_jpg = np.average(detection_time_jpg)
avg_est_jpg = np.average(estimation_time_jpg)
avg_cal_jpg = np.average(calculation_time_jpg)
avg_exe_jpg = np.average(execution_time_jpg)
full_time_jpg = camera_time_jpg + detection_time_jpg + estimation_time_jpg + calculation_time_jpg + execution_time_jpg
avg_full_jpg = np.average(full_time_jpg)

fig = plt.figure(figsize=(20, 10), num='Timing data')

fig.add_subplot(2, 3, 1, title="RTT image acquisition")
plt.plot(camera_time_raw, label="raw data")
plt.plot(camera_time_jpg, label="jpg data")
plt.axhline(avg_cam_raw, linestyle=':', label="average raw data")
plt.axhline(avg_cam_jpg, linestyle=':', label="average jpg data", color='tab:orange')
plt.legend()
plt.grid()
# plt.xlabel('Samples [n]')
plt.ylabel('Time [s]')

fig.add_subplot(2, 3, 2, title="SPM detection")
plt.plot(detection_time_raw, label="raw data")
plt.plot(detection_time_jpg, label="jpg data")
plt.axhline(avg_det_raw, linestyle=':', label="average raw data")
plt.axhline(avg_det_jpg, linestyle=':', label="average jpg data", color='tab:orange')
plt.legend()
plt.grid()
# plt.xlabel('Samples [n]')
# plt.ylabel('Time [s]')

fig.add_subplot(2, 3, 3, title="Pose estimation")
plt.plot(estimation_time_raw, label="raw data")
plt.plot(estimation_time_jpg, label="jpg data")
plt.axhline(avg_est_raw, linestyle=':', label="average raw data")
plt.axhline(avg_est_jpg, linestyle=':', label="average jpg data", color='tab:orange')
plt.legend()
plt.grid()
# plt.xlabel('Samples [n]')
# plt.ylabel('Time [s]')

fig.add_subplot(2, 3, 4, title="Trajectory calculation")
plt.plot(calculation_time_raw, label="raw data")
plt.plot(calculation_time_jpg, label="jpg data")
plt.axhline(avg_cal_raw, linestyle=':', label="average raw data")
plt.axhline(avg_cal_jpg, linestyle=':', label="average jpg data", color='tab:orange')
plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
plt.ylabel('Time [s]')

fig.add_subplot(2, 3, 5, title="Trajectory execution")
plt.plot(execution_time_raw, label="raw data")
plt.plot(execution_time_jpg, label="jpg data")
plt.axhline(avg_exe_raw, linestyle=':', label="average raw data")
plt.axhline(avg_exe_jpg, linestyle=':', label="average jpg data", color='tab:orange')
plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
# plt.ylabel('Time [s]')

fig.add_subplot(2, 3, 6, title="Full time")
plt.plot(full_time_raw, label="raw data")
plt.plot(full_time_jpg, label="jpg data")
plt.axhline(avg_full_raw, linestyle=':', label="average raw data")
plt.axhline(avg_full_jpg, linestyle=':', label="average jpg data", color='tab:orange')
plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
# plt.ylabel('Time [s]')

plt.show()


