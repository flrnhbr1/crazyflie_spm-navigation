import yaml
import numpy as np
import matplotlib.pyplot as plt

window_size = 5

with open('motion_weighted_MA_weights--quadr_except-psi.yaml') as f:
    loaded_dict = yaml.safe_load(f)
    unf_x = loaded_dict.get('unfiltered_x')
    unf_y = loaded_dict.get('unfiltered_y')
    unf_z = loaded_dict.get('unfiltered_z')
    unf_psi = loaded_dict.get('unfiltered_psi')
    fil_x = loaded_dict.get('filtered_x')
    fil_y = loaded_dict.get('filtered_y')
    fil_z = loaded_dict.get('filtered_z')
    fil_psi = loaded_dict.get('filtered_psi')

    w_fil_x = loaded_dict.get('w_filtered_x')
    w_fil_y = loaded_dict.get('w_filtered_y')
    w_fil_z = loaded_dict.get('w_filtered_z')
    w_fil_psi = loaded_dict.get('w_filtered_psi')

    unfiltered_x = np.array(unf_x)
    unfiltered_y = np.array(unf_y)
    unfiltered_z = np.array(unf_z)
    unfiltered_psi = np.array(unf_psi)

    filtered_x = np.array(fil_x)
    filtered_y = np.array(fil_y)
    filtered_z = np.array(fil_z)
    filtered_psi = np.array(fil_psi)

    w_filtered_x = np.array(w_fil_x)
    w_filtered_y = np.array(w_fil_y)
    w_filtered_z = np.array(w_fil_z)
    w_filtered_psi = np.array(w_fil_psi)


print("Plotting data loaded")

# append filtered data for shifting
for i in range(window_size-1):
    filtered_x = np.insert(filtered_x, 0, filtered_x[0])
    filtered_y = np.insert(filtered_y, 0, filtered_y[0])
    filtered_z = np.insert(filtered_z, 0, filtered_z[0])
    filtered_psi = np.insert(filtered_psi, 0, filtered_psi[0])

    w_filtered_x = np.insert(w_filtered_x, 0, w_filtered_x[0])
    w_filtered_y = np.insert(w_filtered_y, 0, w_filtered_y[0])
    w_filtered_z = np.insert(w_filtered_z, 0, w_filtered_z[0])
    w_filtered_psi = np.insert(w_filtered_psi, 0, w_filtered_psi[0])

# plot
fig = plt.figure(figsize=(20, 10))

fig.add_subplot(2, 2, 1, title="Translation in x")
plt.plot(unfiltered_x, label="Measured distance")
plt.plot(filtered_x, label="Executed motion")
plt.plot(w_filtered_x, label="WMA motion")

plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
plt.ylabel('Distance [cm]')

fig.add_subplot(2, 2, 2, title="Translation in y")
plt.plot(unfiltered_y, label="Measured distance")
plt.plot(filtered_y, label="Executed motion")
plt.plot(w_filtered_y, label="WMA motion")

plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
plt.ylabel('Distance [cm]')

fig.add_subplot(2, 2, 3, title="Translation in z")
plt.plot(unfiltered_z, label="Measured distance")
plt.plot(filtered_z, label="Executed motion")
plt.plot(w_filtered_z, label="WMA motion")

plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
plt.ylabel('Distance [cm]')

fig.add_subplot(2, 2, 4, title="Yaw rotation")
plt.plot(unfiltered_psi, label="Measured offset")
plt.plot(filtered_psi, label="Executed alignment")
plt.plot(w_filtered_psi, label="WMA motion")

plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
plt.ylabel('Offset [rad]')

plt.show()
