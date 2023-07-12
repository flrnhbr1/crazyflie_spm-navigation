import csv
import yaml
import math
import matplotlib.pyplot as plt
import numpy as np


# load visual data
# read data
with open("./filter_data/Log_2SPM_Test4.yaml") as f:
    loaded_dict = yaml.safe_load(f)
    unf_x = loaded_dict.get('unfiltered_x')
    unf_y = loaded_dict.get('unfiltered_y')
    unf_z = loaded_dict.get('unfiltered_z')
    unf_psi = loaded_dict.get('unfiltered_psi')
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
filename = open('./optitrack_logs/2SPM_Test4_ed.csv')

# creating dictreader object
file = csv.DictReader(filename)
# creating empty lists
spm0_pos_x = []
spm0_pos_y = []
spm0_pos_z = []
spm0_rot_psi = []

spm1_pos_x = []
spm1_pos_y = []
spm1_pos_z = []
spm1_rot_psi = []

cf_pos_x = []
cf_pos_y = []
cf_pos_z = []
cf_rot_psi = []

time_mocap = []

# iterating over each row and append
# values to empty list
for col in file:
    spm0_pos_y.append((col['spm0_posX']))
    spm0_pos_z.append((col['spm0_posY']))
    spm0_pos_x.append((col['spm0_posZ']))
    spm0_rot_psi.append(col['spm0_rotY'])

    spm1_pos_y.append((col['spm1_posX']))
    spm1_pos_z.append((col['spm1_posY']))
    spm1_pos_x.append((col['spm1_posZ']))
    spm1_rot_psi.append(col['spm1_rotY'])

    cf_pos_y.append(col['cf_posX'])
    cf_pos_z.append(col['cf_posY'])
    cf_pos_x.append(col['cf_posZ'])
    cf_rot_psi.append(col['cf_rotY'])

    time_mocap.append(col['time'])

# convert to float values
cf_pos_x = np.array(cf_pos_x, float)
cf_pos_y = np.array(cf_pos_y, float)
cf_pos_z = np.array(cf_pos_z, float)
cf_rot_psi = np.array(cf_rot_psi, float)

spm0_pos_x = np.array(spm0_pos_x, float)
spm0_pos_y = np.array(spm0_pos_y, float)
spm0_pos_z = np.array(spm0_pos_z, float)
spm0_rot_psi = np.array(spm0_rot_psi, float)

spm1_pos_x = np.array(spm1_pos_x, float)
spm1_pos_y = np.array(spm1_pos_y, float)
spm1_pos_z = np.array(spm1_pos_z, float)
spm1_rot_psi = np.array(spm1_rot_psi, float)

time_mocap = np.array(time_mocap, float)

# apply correction of rigid body center to camera and spm center
cf_pos_x -= 3
cf_pos_z -= 0.85
spm0_pos_x += 0.25
spm1_pos_x += 0.25

# find shift to sync signals

# ## for 2SPM_Test2
# peak_visual_SPM0 = 1689069570.686413 - start_time
# peak_mocap_SPM0 = 17.216667
#
# peak_visual_SPM1 = 1689069590.6834261 - start_time
# peak_mocap_SPM1 = 36.900000
#
#
# shift = peak_mocap_SPM0 - peak_visual_SPM0
# time_visual += shift
#
# signal_begin_SPM0 = 0
# sync_begin_SPM0 = 73
# spm0_rot_psi -= 45
#
# signal_begin_SPM1 = 103
# sync_begin_SPM1 = 161
# #spm1_rot_psi -= 45


# ## for 2SPM_Test3
# peak_visual_SPM0 = 1689075722.568583 - start_time
# peak_mocap_SPM0 = 24.650000
#
# shift = peak_mocap_SPM0 - peak_visual_SPM0
# time_visual += shift
#
# signal_begin_SPM0 = 0
# sync_begin_SPM0 = 106
# spm0_rot_psi -= 45
#
# signal_begin_SPM1 = 146
# sync_begin_SPM1 = 207
# #spm1_rot_psi -= 45


## for 2SPM_Test4
peak_visual_SPM0 = 1689076493.813345 - start_time
peak_mocap_SPM0 = 17.333333

peak_visual_SPM1 = 1689076514.428053 - start_time
peak_mocap_SPM1 = 37.933333


shift = peak_mocap_SPM0 - peak_visual_SPM0
time_visual += shift

signal_begin_SPM0 = 0
sync_begin_SPM0 = 67
spm0_rot_psi -= 45
unfiltered_y[0:70] -= 7

signal_begin_SPM1 = 97
sync_begin_SPM1 = 157
#spm1_rot_psi -= 45

# resample mocap data
time_mocap_resampled = []

spm0_pos_x_resampled = []
spm0_pos_y_resampled = []
spm0_pos_z_resampled = []
spm0_rot_psi_resampled = []

spm1_pos_x_resampled = []
spm1_pos_y_resampled = []
spm1_pos_z_resampled = []
spm1_rot_psi_resampled = []

cf_pos_x_resampled = []
cf_pos_y_resampled = []
cf_pos_z_resampled = []
cf_rot_psi_resampled = []

for v in time_visual:
    for m in range(1, len(time_mocap) - 1):
        if time_mocap[m - 1] <= v <= time_mocap[m + 1]:
            time_mocap_resampled.append(v)

            spm0_pos_x_resampled.append(spm0_pos_x[m])
            spm0_pos_y_resampled.append(spm0_pos_y[m])
            spm0_pos_z_resampled.append(spm0_pos_z[m])
            spm0_rot_psi_resampled.append(spm0_rot_psi[m])

            spm1_pos_x_resampled.append(spm1_pos_x[m])
            spm1_pos_y_resampled.append(spm1_pos_y[m])
            spm1_pos_z_resampled.append(spm1_pos_z[m])
            spm1_rot_psi_resampled.append(spm1_rot_psi[m])

            cf_pos_x_resampled.append(cf_pos_x[m])
            cf_pos_y_resampled.append(cf_pos_y[m])
            cf_pos_z_resampled.append(cf_pos_z[m])
            cf_rot_psi_resampled.append(cf_rot_psi[m])

            break
time_mocap_resampled = np.array(time_mocap_resampled, float)

spm0_pos_x_resampled = np.array(spm0_pos_x_resampled, float)
spm0_pos_y_resampled = np.array(spm0_pos_y_resampled, float)
spm0_pos_z_resampled = np.array(spm0_pos_z_resampled, float)
spm0_rot_psi_resampled = np.array(spm0_rot_psi_resampled, float)

spm1_pos_x_resampled = np.array(spm1_pos_x_resampled, float)
spm1_pos_y_resampled = np.array(spm1_pos_y_resampled, float)
spm1_pos_z_resampled = np.array(spm1_pos_z_resampled, float)
spm1_rot_psi_resampled = np.array(spm1_rot_psi_resampled, float)

cf_pos_x_resampled = np.array(cf_pos_x_resampled, float)
cf_pos_y_resampled = np.array(cf_pos_y_resampled, float)
cf_pos_z_resampled = np.array(cf_pos_z_resampled, float)
cf_rot_psi_resampled = np.array(cf_rot_psi_resampled, float)


# plot
fig1 = plt.figure(figsize=(20, 10), num='Visual vs MoCap data SPM0')

fig1.add_subplot(2, 2, 1, title="Signals in x-direction")
plt.plot(time_mocap_resampled[signal_begin_SPM0:sync_begin_SPM0],
         cf_pos_x_resampled[signal_begin_SPM0:sync_begin_SPM0] - spm0_pos_x_resampled[signal_begin_SPM0:sync_begin_SPM0],
         label="Motion capture signal")
plt.plot(time_visual[signal_begin_SPM0:sync_begin_SPM0], unfiltered_x[signal_begin_SPM0:sync_begin_SPM0], label="Visual signal")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [cm]')

fig1.add_subplot(2, 2, 2, title="Signals in y-direction")
plt.plot(time_mocap_resampled[signal_begin_SPM0:sync_begin_SPM0],
         spm0_pos_y_resampled[signal_begin_SPM0:sync_begin_SPM0] - cf_pos_y_resampled[signal_begin_SPM0:sync_begin_SPM0],
         label="Motion capture signal")
plt.plot(time_visual[signal_begin_SPM0:sync_begin_SPM0], unfiltered_y[signal_begin_SPM0:sync_begin_SPM0], label="Visual signal")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [cm]')

fig1.add_subplot(2, 2, 3, title="Signals in z-direction")
plt.plot(time_mocap_resampled[signal_begin_SPM0:sync_begin_SPM0],
         cf_pos_z_resampled[signal_begin_SPM0:sync_begin_SPM0] - spm0_pos_z_resampled[signal_begin_SPM0:sync_begin_SPM0],
         label="Motion capture signal")
plt.plot(time_visual[signal_begin_SPM0:sync_begin_SPM0], unfiltered_z[signal_begin_SPM0:sync_begin_SPM0], label="Visual signal")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [cm]')

fig1.add_subplot(2, 2, 4, title="Signals in yaw-angle")
plt.plot(time_mocap_resampled[signal_begin_SPM0:sync_begin_SPM0],
         cf_rot_psi_resampled[signal_begin_SPM0:sync_begin_SPM0] - spm0_rot_psi_resampled[signal_begin_SPM0:sync_begin_SPM0],
         label="Motion capture signal")
plt.plot(time_visual[signal_begin_SPM0:sync_begin_SPM0], unfiltered_psi[signal_begin_SPM0:sync_begin_SPM0] * 180 / math.pi, label="Visual signal")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Angle [°]')


# plot
fig2 = plt.figure(figsize=(20, 10), num='Visual vs MoCap data SPM1')

fig2.add_subplot(2, 2, 1, title="Signals in x-direction")
plt.plot(time_mocap_resampled[signal_begin_SPM1:sync_begin_SPM1],
         cf_pos_x_resampled[signal_begin_SPM1:sync_begin_SPM1] - spm1_pos_x_resampled[signal_begin_SPM1:sync_begin_SPM1],
         label="Motion capture signal")
plt.plot(time_visual[signal_begin_SPM1:sync_begin_SPM1], unfiltered_x[signal_begin_SPM1:sync_begin_SPM1], label="Visual signal")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [cm]')

fig2.add_subplot(2, 2, 2, title="Signals in y-direction")
plt.plot(time_mocap_resampled[signal_begin_SPM1:sync_begin_SPM1],
         spm1_pos_y_resampled[signal_begin_SPM1:sync_begin_SPM1] - cf_pos_y_resampled[signal_begin_SPM1:sync_begin_SPM1],
         label="Motion capture signal")
plt.plot(time_visual[signal_begin_SPM1:sync_begin_SPM1], unfiltered_y[signal_begin_SPM1:sync_begin_SPM1], label="Visual signal")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [cm]')

fig2.add_subplot(2, 2, 3, title="Signals in z-direction")
plt.plot(time_mocap_resampled[signal_begin_SPM1:sync_begin_SPM1],
         cf_pos_z_resampled[signal_begin_SPM1:sync_begin_SPM1] - spm1_pos_z_resampled[signal_begin_SPM1:sync_begin_SPM1],
         label="Motion capture signal")
plt.plot(time_visual[signal_begin_SPM1:sync_begin_SPM1], unfiltered_z[signal_begin_SPM1:sync_begin_SPM1], label="Visual signal")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [cm]')

fig2.add_subplot(2, 2, 4, title="Signals in yaw angle")
plt.plot(time_mocap_resampled[signal_begin_SPM1:sync_begin_SPM1],
         cf_rot_psi_resampled[signal_begin_SPM1:sync_begin_SPM1] - spm1_rot_psi_resampled[signal_begin_SPM1:sync_begin_SPM1],
         label="Motion capture signal")
plt.plot(time_visual[signal_begin_SPM1:sync_begin_SPM1], unfiltered_psi[signal_begin_SPM1:sync_begin_SPM1] * 180 / math.pi, label="Visual signal")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Angle [°]')




fig3 = plt.figure(figsize=(20, 10), num='Deviation of Visual and MoCap data SPM0')

fig3.add_subplot(2, 2, 1, title="Absolute deviation in x-direction")
plt.plot(time_visual[signal_begin_SPM0:sync_begin_SPM0],
         abs(unfiltered_x[signal_begin_SPM0:sync_begin_SPM0] - (cf_pos_x_resampled[signal_begin_SPM0:sync_begin_SPM0]-spm0_pos_x_resampled[signal_begin_SPM0:sync_begin_SPM0])))
plt.ylim(0, 40)
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Deviation [cm]')

fig3.add_subplot(2, 2, 2, title="Absolute deviation in y-direction")
plt.plot(time_visual[signal_begin_SPM0:sync_begin_SPM0],
         abs(unfiltered_y[signal_begin_SPM0:sync_begin_SPM0] - (spm0_pos_y_resampled[signal_begin_SPM0:sync_begin_SPM0]-cf_pos_y_resampled[signal_begin_SPM0:sync_begin_SPM0])))
plt.ylim(0, 40)
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Deviation [cm]')

fig3.add_subplot(2, 2, 3, title="Absolute deviation in z-direction")
plt.plot(time_visual[signal_begin_SPM0:sync_begin_SPM0],
         abs(unfiltered_z[signal_begin_SPM0:sync_begin_SPM0] - (cf_pos_z_resampled[signal_begin_SPM0:sync_begin_SPM0]-spm0_pos_z_resampled[signal_begin_SPM0:sync_begin_SPM0])))
plt.ylim(0, 40)
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Deviation [cm]')

fig3.add_subplot(2, 2, 4, title="Absolute deviation in yaw angle")
plt.plot(time_visual[signal_begin_SPM0:sync_begin_SPM0],
         abs(unfiltered_psi[signal_begin_SPM0:sync_begin_SPM0]* 180 / math.pi - (cf_rot_psi_resampled[signal_begin_SPM0:sync_begin_SPM0]-spm0_rot_psi_resampled[signal_begin_SPM0:sync_begin_SPM0])))
plt.ylim(0, 40)
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Deviation [°]')



fig4 = plt.figure(figsize=(20, 10), num='Deviation of Visual and MoCap data SPM1')

fig4.add_subplot(2, 2, 1, title="Absolute deviation in x-direction")
plt.plot(time_visual[signal_begin_SPM1:sync_begin_SPM1],
         abs(unfiltered_x[signal_begin_SPM1:sync_begin_SPM1] - (cf_pos_x_resampled[signal_begin_SPM1:sync_begin_SPM1]-spm1_pos_x_resampled[signal_begin_SPM1:sync_begin_SPM1])))
plt.ylim(0, 40)
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Deviation [cm]')

fig4.add_subplot(2, 2, 2, title="Absolute deviation in y-direction")
plt.plot(time_visual[signal_begin_SPM1:sync_begin_SPM1],
         abs(unfiltered_y[signal_begin_SPM1:sync_begin_SPM1] - (spm1_pos_y_resampled[signal_begin_SPM1:sync_begin_SPM1]-cf_pos_y_resampled[signal_begin_SPM1:sync_begin_SPM1])))
plt.ylim(0, 40)
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Deviation [cm]')

fig4.add_subplot(2, 2, 3, title="Absolute deviation in z-direction")
plt.plot(time_visual[signal_begin_SPM1:sync_begin_SPM1],
         abs(unfiltered_z[signal_begin_SPM1:sync_begin_SPM1] - (cf_pos_z_resampled[signal_begin_SPM1:sync_begin_SPM1]-spm1_pos_z_resampled[signal_begin_SPM1:sync_begin_SPM1])))
plt.ylim(0, 40)
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Deviation [cm]')

fig4.add_subplot(2, 2, 4, title="Absolute deviation in yaw angle")
plt.plot(time_visual[signal_begin_SPM1:sync_begin_SPM1],
         abs(unfiltered_psi[signal_begin_SPM1:sync_begin_SPM1]* 180 / math.pi - (cf_rot_psi_resampled[signal_begin_SPM1:sync_begin_SPM1]-spm1_rot_psi_resampled[signal_begin_SPM1:sync_begin_SPM1])))
plt.ylim(0, 40)
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Deviation [°]')

print("Distance SPM center:" + str(abs(spm0_pos_y[0]-spm1_pos_y[0])))
print("Distance cf:" + str(abs(spm0_pos_x_resampled[0]-cf_pos_x_resampled[0])))

plt.show()
