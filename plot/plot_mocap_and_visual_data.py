import csv
import yaml
import math
import matplotlib.pyplot as plt
import numpy as np


# load visual data
# read data
with open("filter_data/Log_2023-6-1T10-58-29.yaml") as f:
    loaded_dict = yaml.safe_load(f)
    unf_x = loaded_dict.get('w_filtered_x')
    unf_y = loaded_dict.get('w_filtered_y')
    unf_z = loaded_dict.get('w_filtered_z')
    unf_psi = loaded_dict.get('filtered_psi')
    time_vis = loaded_dict.get('time')

unfiltered_x = np.array(unf_x)
unfiltered_y = np.array(unf_y)
unfiltered_z = np.array(unf_z)
unfiltered_psi = np.array(unf_psi)

# make start time for visual data == 0
start_time = time_vis[0]
for i in range(len(time_vis)):
    time_vis[i] -= start_time

time_visual = np.array(time_vis)

# load mocap data
filename = open('/Users/florianhuber/Documents/Uni/Bachelor_Thesis/crazyflie_spm-navigation/plot/'
                'optitrack_logs/Take 2023-06-01_10-58-29_ed.csv')
# creating dictreader object
file = csv.DictReader(filename)
# creating empty lists
spm_pos_x = []
spm_pos_y = []
spm_pos_z = []
spm_rot_psi = []
cf_pos_x = []
cf_pos_y = []
cf_pos_z = []
cf_rot_psi = []
time_mocap = []

# iterating over each row and append values to empty list
for col in file:
    spm_pos_y.append(col['spm_pos_x'])  # coordinate systems are unequal
    spm_pos_z.append(col['spm_pos_y'])
    spm_pos_x.append(col['spm_pos_z'])
    spm_rot_psi.append(col['spm_rot_y'])
    cf_pos_y.append(col['cf_pos_x'])
    cf_pos_z.append(col['cf_pos_y'])
    cf_pos_x.append(col['cf_pos_z'])
    cf_rot_psi.append(col['cf_rot_y'])
    time_mocap.append(col['time'])
# convert to float values
cf_pos_x = np.array(cf_pos_x, float)
cf_pos_y = np.array(cf_pos_y, float)
cf_pos_z = np.array(cf_pos_z, float)
spm_pos_x = np.array(spm_pos_x, float)
spm_pos_y = np.array(spm_pos_y, float)
spm_pos_z = np.array(spm_pos_z, float)
cf_rot_psi = np.array(cf_rot_psi, float)
spm_rot_psi = np.array(spm_rot_psi, float)
time_mocap = np.array(time_mocap, float)

# find shift to sync signals
peak_visual = 1685609896.565727 - start_time
peak_mocap = 27.033333
shift = peak_mocap - peak_visual
time_visual += shift
signal_begin = 8
sync_begin = 107-10  # -window size+3

# resample mocap data
time_mocap_resampled = []
signal_mocap_x_resampled = []
signal_mocap_y_resampled = []
signal_mocap_z_resampled = []
signal_mocap_psi_resampled = []

for v in time_visual:
    for m in range(1, len(time_mocap) - 1):
        if time_mocap[m - 1] <= v <= time_mocap[m + 1]:
            time_mocap_resampled.append(v)
            signal_mocap_x_resampled.append(cf_pos_x[m] - spm_pos_x[m])
            signal_mocap_y_resampled.append(spm_pos_y[m] - cf_pos_y[m])
            signal_mocap_z_resampled.append(cf_pos_z[m] - spm_pos_z[m])
            signal_mocap_psi_resampled.append(cf_rot_psi[m] - spm_rot_psi[m])
            break
time_mocap_resampled = np.array(time_mocap_resampled, float)
signal_mocap_x_resampled = np.array(signal_mocap_x_resampled, float)
signal_mocap_y_resampled = np.array(signal_mocap_y_resampled, float)
signal_mocap_z_resampled = np.array(signal_mocap_z_resampled, float)
signal_mocap_psi_resampled = np.array(signal_mocap_psi_resampled, float)


# plot
fig1 = plt.figure(figsize=(20, 10), num='Visual and MoCap data')

fig1.add_subplot(2, 2, 1, title="Signals in x-direction")
plt.plot(time_mocap_resampled[signal_begin:sync_begin],
         signal_mocap_x_resampled[signal_begin:sync_begin], label="Motion capture signal")
plt.plot(time_visual[signal_begin:sync_begin], unfiltered_x[signal_begin:sync_begin], label="Visual signal")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [cm]')

fig1.add_subplot(2, 2, 2, title="Signals in y-direction")
plt.plot(time_mocap_resampled[signal_begin:sync_begin],
         signal_mocap_y_resampled[signal_begin:sync_begin], label="Motion capture signal")
plt.plot(time_visual[signal_begin:sync_begin], unfiltered_y[signal_begin:sync_begin], label="Visual signal")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [cm]')

fig1.add_subplot(2, 2, 3, title="Signals in z-direction")
plt.plot(time_mocap_resampled[signal_begin:sync_begin],
         signal_mocap_z_resampled[signal_begin:sync_begin], label="Motion capture signal")
plt.plot(time_visual[signal_begin:sync_begin], unfiltered_z[signal_begin:sync_begin], label="Visual signal")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [cm]')

fig1.add_subplot(2, 2, 4, title="Signals in yaw-angle")
plt.plot(time_mocap_resampled[signal_begin:sync_begin],
         signal_mocap_psi_resampled[signal_begin:sync_begin], label="Motion capture signal")
plt.plot(time_visual[signal_begin:sync_begin], unfiltered_psi[signal_begin:sync_begin] * 180 / math.pi, label="Visual signal")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Angle [°]')


fig2 = plt.figure(figsize=(20, 10), num='Deviation of Visual and MoCap data')

fig2.add_subplot(2, 2, 1, title="Deviation in x-direction")
plt.plot(time_visual[signal_begin:sync_begin],
         abs(unfiltered_x[signal_begin:sync_begin] - signal_mocap_x_resampled[signal_begin:sync_begin]))
plt.axhline(np.average(abs(unfiltered_x[signal_begin:sync_begin] - signal_mocap_x_resampled[signal_begin:sync_begin])),
            linestyle=':', label="Average deviation")
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Deviation [cm]')

fig2.add_subplot(2, 2, 2, title="Difference in y-direction")
plt.plot(time_visual[signal_begin:sync_begin],
         abs(unfiltered_y[signal_begin:sync_begin] - signal_mocap_y_resampled[signal_begin:sync_begin]))
plt.axhline(np.average(abs(unfiltered_y[signal_begin:sync_begin] - signal_mocap_y_resampled[signal_begin:sync_begin])),
            linestyle=':', label="Average deviation")
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Deviation [cm]')

fig2.add_subplot(2, 2, 3, title="Difference in z-direction")
plt.plot(time_visual[signal_begin:sync_begin],
         abs(unfiltered_z[signal_begin:sync_begin] - signal_mocap_z_resampled[signal_begin:sync_begin]))
plt.axhline(np.average(abs(unfiltered_z[signal_begin:sync_begin] - signal_mocap_z_resampled[signal_begin:sync_begin])),
            linestyle=':', label="Average deviation")
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Deviation [cm]')

fig2.add_subplot(2, 2, 4, title="Difference in yaw-angle")
plt.plot(time_visual[signal_begin:sync_begin],
         abs(unfiltered_psi[signal_begin:sync_begin] - signal_mocap_psi_resampled[signal_begin:sync_begin]))
plt.axhline(np.average(abs(unfiltered_psi[signal_begin:sync_begin] - signal_mocap_psi_resampled[signal_begin:sync_begin])),
            linestyle=':', label="Average deviation")
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Deviation [°]')

plt.show()
