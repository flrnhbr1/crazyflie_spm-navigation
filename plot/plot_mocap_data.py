import csv
import matplotlib.pyplot as plt
import numpy as np

filename = open('/Users/florianhuber/Documents/Uni/Bachelor_Thesis/optitrack_logs/spm_nav_002ed.csv')

# creating dictreader object
file = csv.DictReader(filename)

# creating empty lists
spm_pos_x = []
spm_pos_y = []
spm_pos_z = []
cf_pos_x = []
cf_pos_y = []
cf_pos_z = []
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
    t.append(col['time'])

# convert to float values
cf_pos_x = np.array(cf_pos_x, float)
cf_pos_y = np.array(cf_pos_y, float)
cf_pos_z = np.array(cf_pos_z, float)
spm_pos_x = np.array(spm_pos_x, float)
spm_pos_y = np.array(spm_pos_y, float)
spm_pos_z = np.array(spm_pos_z, float)
t = np.array(t, float)
# plot motion data
fig = plt.figure(figsize=(20, 10), num='MoCap data')

fig.add_subplot(2, 2, 1, title="cf")
plt.plot(t, cf_pos_x,  label="x")
plt.plot(t, cf_pos_y,  label="y")
plt.plot(t, cf_pos_z,  label="z")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [m]')

fig.add_subplot(2, 2, 2, title="spm")
plt.plot(t, spm_pos_x,  label="x")
plt.plot(t, spm_pos_y,  label="y")
plt.plot(t, spm_pos_z,  label="z")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [m]')

fig.add_subplot(2, 2, 3, title="diff")
plt.plot(t, cf_pos_x-spm_pos_x,  label="x")
plt.plot(t, cf_pos_y-spm_pos_y,  label="y")
plt.plot(t, cf_pos_z-spm_pos_z,  label="z")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [m]')

plt.show()


