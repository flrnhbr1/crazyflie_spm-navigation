import csv
import matplotlib.pyplot as plt
import numpy as np

filename = open('./optitrack_logs/Take 2023-06-14_14-1-48_ed.csv')

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
spm_rot_psi = []
t = []

# iterating over each row and append
# values to empty list
for col in file:
    spm_pos_x.append((col['spm_pos_x']))
    spm_pos_y.append((col['spm_pos_y']))
    spm_pos_z.append((col['spm_pos_z']))
    cf_pos_x.append(col['cf_pos_x'])
    cf_pos_y.append(col['cf_pos_y'])
    cf_pos_z.append(col['cf_pos_z'])
    cf_rot_psi.append(col['cf_rot_y'])
    spm_rot_psi.append(col['spm_rot_y'])

    t.append(col['time'])

# convert to float values
cf_pos_x = np.array(cf_pos_x, float)
cf_pos_y = np.array(cf_pos_y, float)
cf_pos_z = np.array(cf_pos_z, float)
spm_pos_x = np.array(spm_pos_x, float)
spm_pos_y = np.array(spm_pos_y, float)
spm_pos_z = np.array(spm_pos_z, float)
cf_rot_psi = np.array(cf_rot_psi, float)
spm_rot_psi = np.array(spm_rot_psi, float)
t = np.array(t, float)
# plot motion data
fig = plt.figure(figsize=(20, 10), num='MoCap data')

fig.add_subplot(2, 2, 1, title="cf")
plt.plot(t, cf_pos_x,  label="x")
plt.plot(t, cf_pos_y,  label="y")
plt.plot(t, cf_pos_z,  label="z")
plt.plot(t, cf_rot_psi,  label="psi")

plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [m]')

fig.add_subplot(2, 2, 2, title="spm")
plt.plot(t, spm_pos_x,  label="x")
plt.plot(t, spm_pos_y,  label="y")
plt.plot(t, spm_pos_z,  label="z")
plt.plot(t, spm_rot_psi,  label="psi")

plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [m]')

fig.add_subplot(2, 2, 3, title="diff")
plt.plot(t, cf_pos_x-spm_pos_x,  label="x")
plt.plot(t, cf_pos_y-spm_pos_y,  label="y")
plt.plot(t, cf_pos_z-spm_pos_z,  label="z")
plt.plot(t, cf_rot_psi-spm_rot_psi,  label="psi")

plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [m]')

plt.show()


