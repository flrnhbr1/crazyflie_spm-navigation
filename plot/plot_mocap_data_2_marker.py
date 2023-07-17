import csv
import matplotlib.pyplot as plt
import numpy as np

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

t = []

# iterating over each row and append
# values to empty list
for col in file:
    spm0_pos_x.append((col['spm0_posX']))
    spm0_pos_y.append((col['spm0_posY']))
    spm0_pos_z.append((col['spm0_posZ']))
    spm0_rot_psi.append(col['spm0_rotY'])

    spm1_pos_x.append((col['spm1_posX']))
    spm1_pos_y.append((col['spm1_posY']))
    spm1_pos_z.append((col['spm1_posZ']))
    spm1_rot_psi.append(col['spm1_rotY'])

    cf_pos_x.append(col['cf_posX'])
    cf_pos_y.append(col['cf_posY'])
    cf_pos_z.append(col['cf_posZ'])
    cf_rot_psi.append(col['cf_rotY'])

    t.append(col['time'])

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

fig.add_subplot(2, 2, 2, title="spm0")
plt.plot(t, spm0_pos_x,  label="x")
plt.plot(t, spm0_pos_y,  label="y")
plt.plot(t, spm0_pos_z,  label="z")
plt.plot(t, spm0_rot_psi,  label="psi")

plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [m]')

fig.add_subplot(2, 2, 3, title="spm1")
plt.plot(t, spm1_pos_x,  label="x")
plt.plot(t, spm1_pos_y,  label="y")
plt.plot(t, spm1_pos_z,  label="z")
plt.plot(t, spm1_rot_psi,  label="psi")

plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [m]')

# plot motion data
fig2 = plt.figure(figsize=(20, 10), num='data')

fig2.add_subplot(2, 1, 1)
plt.plot(t, cf_pos_z,  label="x")
plt.plot(t, cf_pos_x,  label="y")
plt.plot(t, cf_pos_y,  label="z")
#plt.plot(t, cf_rot_psi,  label="psi")
plt.legend()
plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Distance [cm]')

plt.show()


