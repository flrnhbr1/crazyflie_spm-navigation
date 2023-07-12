import math
import yaml
import numpy as np
import matplotlib.pyplot as plt

# read data
with open("timing_data/Log_fullTiming_2SPM_Test4.yaml") as f:
    loaded_dict = yaml.safe_load(f)
    cam = loaded_dict.get('camera')
    det = loaded_dict.get('detection')
    est = loaded_dict.get('estimation')
    cal = loaded_dict.get('calculation')
    exe = loaded_dict.get('execution')

    camRaw = []
    for c in range(1,len(cam)):
        if cam[c - 1] != cam[c]:
            camRaw.append(cam[c])

    camera_time_raw = np.array(camRaw)
    camera_time_raw = camera_time_raw[0:89]

    detection_time_raw = np.array(det)
    estimation_time_raw = np.array(est)
    calculation_time_raw = np.array(cal)
    execution_time_raw = np.array(exe)


print("Plotting data loaded")

avg_cam_raw = np.average(camera_time_raw)
avg_det_raw = np.average(detection_time_raw)
avg_est_raw = np.average(estimation_time_raw)
avg_cal_raw = np.average(calculation_time_raw)
avg_exe_raw = np.average(execution_time_raw)
full_time_raw = camera_time_raw + detection_time_raw + estimation_time_raw + calculation_time_raw + execution_time_raw
avg_full_raw = np.average(full_time_raw)


fig = plt.figure(figsize=(20, 10), num='Timing data')

fig.add_subplot(2, 3, 1, title="Image acquisition")
plt.plot(camera_time_raw)
# plt.plot(camera_time_jpg, label="jpg data")
plt.axhline(avg_cam_raw, linestyle=':', label="average raw data")
# plt.axhline(avg_cam_jpg, linestyle=':', label="average jpg data", color='tab:orange')
plt.legend()
plt.grid()
# plt.xlabel('Samples [n]')
plt.ylabel('Time [s]')

fig.add_subplot(2, 3, 2, title="SPM detection")
plt.plot(detection_time_raw)
# plt.plot(detection_time_jpg, label="jpg data")
plt.axhline(avg_det_raw, linestyle=':', label="average raw data")
# plt.axhline(avg_det_jpg, linestyle=':', label="average jpg data", color='tab:orange')
plt.legend()
plt.grid()
# plt.xlabel('Samples [n]')
# plt.ylabel('Time [s]')

fig.add_subplot(2, 3, 3, title="Pose estimation")
plt.plot(estimation_time_raw)
# plt.plot(estimation_time_jpg, label="jpg data")
plt.axhline(avg_est_raw, linestyle=':', label="average raw data")
# plt.axhline(avg_est_jpg, linestyle=':', label="average jpg data", color='tab:orange')
plt.legend()
plt.grid()
# plt.xlabel('Samples [n]')
# plt.ylabel('Time [s]')

fig.add_subplot(2, 3, 4, title="Trajectory calculation")
plt.plot(calculation_time_raw)
# plt.plot(calculation_time_jpg, label="jpg data")
plt.axhline(avg_cal_raw, linestyle=':', label="average raw data")
# plt.axhline(avg_cal_jpg, linestyle=':', label="average jpg data", color='tab:orange')
plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
plt.ylabel('Time [s]')

fig.add_subplot(2, 3, 5, title="Trajectory execution")
plt.plot(execution_time_raw)
# plt.plot(execution_time_jpg, label="jpg data")
plt.axhline(avg_exe_raw, linestyle=':', label="average raw data")
# plt.axhline(avg_exe_jpg, linestyle=':', label="average jpg data", color='tab:orange')
plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
# plt.ylabel('Time [s]')

fig.add_subplot(2, 3, 6, title="Full cycle")
plt.plot(full_time_raw)
# plt.plot(full_time_jpg, label="jpg data")
plt.axhline(avg_full_raw, linestyle=':', label="average raw data")
# plt.axhline(avg_full_jpg, linestyle=':', label="average jpg data", color='tab:orange')
plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
# plt.ylabel('Time [s]')

print("acq: " + str(avg_cam_raw))
print("det: " + str(avg_det_raw))
print("est: " + str(avg_est_raw))
print("cal: " + str(avg_cal_raw))
print("exe: " + str(avg_exe_raw))
print("full: " + str(avg_full_raw))

fig2 = plt.figure(figsize=(20, 10), num='tim')

fig2.add_subplot(2, 1, 1, title="Time of subtasks")
plt.plot(camera_time_raw, label="Image acquisition")
plt.plot(detection_time_raw, label="SPM detection")
plt.plot(estimation_time_raw, label="Pose estimation")
plt.plot(calculation_time_raw, label="Trajectory calculation")
plt.plot(execution_time_raw, label="Trajectory execution")
plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
plt.ylabel('Time [s]')

fig2.add_subplot(2, 1, 2, title="Time of full task")
plt.plot(full_time_raw, label="Image acquisition")
plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
plt.ylabel('Time [s]')


plt.show()

for i in full_time_raw:
    print(round(i, 4))


