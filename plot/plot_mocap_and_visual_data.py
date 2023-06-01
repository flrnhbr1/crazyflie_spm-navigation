import csv
import yaml
import math
import matplotlib.pyplot as plt
import numpy as np

# load visual data
window_size = 7
# read data
with open("filter_data/Log_2023-6-1T10-58-29.yaml") as f:
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

# make start == 0
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
cf_pos_x = []
cf_pos_y = []
cf_pos_z = []
cf_rot_psi = []
time_mocap = []
# iterating over each row and append
# values to empty list
for col in file:
    spm_pos_y.append((col['spm_pos_x']))  # coordinate systems are unequal
    spm_pos_z.append((col['spm_pos_y']))
    spm_pos_x.append((col['spm_pos_z']))
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
time_mocap = np.array(time_mocap, float)



# find shift to sync signals
peak_visual = 1685609896.565727 - start_time
peak_mocap = 27.033333
shift = peak_mocap - peak_visual


# plot
fig = plt.figure(figsize=(20, 10), num='Visual and MoCap data')
fig.add_subplot(2, 2, 1, title="X")
plt.plot(time_mocap, cf_pos_x - spm_pos_x, label="MoCap")
plt.plot(time_visual+shift, unfiltered_x, label="Visual")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [cm]')

fig.add_subplot(2, 2, 2, title="Y")
plt.plot(time_mocap, spm_pos_y - cf_pos_y, label="MoCap")
plt.plot(time_visual+shift, unfiltered_y, label="Visual")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [cm]')

fig.add_subplot(2, 2, 3, title="Z")
plt.plot(time_mocap, cf_pos_z - spm_pos_z, label="MoCap")
plt.plot(time_visual+shift, unfiltered_z, label="Visual")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [cm]')

plt.show()
