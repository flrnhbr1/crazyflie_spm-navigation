import yaml
import numpy as np
import matplotlib.pyplot as plt

with open('motion_data.yaml') as f:
    loaded_dict = yaml.safe_load(f)
    unf_x = loaded_dict.get('unfiltered_x')
    unf_y = loaded_dict.get('unfiltered_y')
    unf_z = loaded_dict.get('unfiltered_z')
    unf_psi = loaded_dict.get('unfiltered_psi')
    fil_x = loaded_dict.get('filtered_x')
    fil_y = loaded_dict.get('filtered_y')
    fil_z = loaded_dict.get('filtered_z')
    fil_psi = loaded_dict.get('filtered_psi')

    unfiltered_x = np.array(unf_x)
    unfiltered_y = np.array(unf_y)
    unfiltered_z = np.array(unf_z)
    unfiltered_psi = np.array(unf_psi)

    filtered_x = np.array(fil_x)
    filtered_y = np.array(fil_y)
    filtered_z = np.array(fil_z)
    filtered_psi = np.array(fil_psi)


print("Plotting data loaded")

# append filtered data for shifting
for i in range(4):
    filtered_x = np.insert(filtered_x, 0, filtered_x[0])
    filtered_y = np.insert(filtered_y, 0, filtered_y[0])
    filtered_z = np.insert(filtered_z, 0, filtered_z[0])
    filtered_psi = np.insert(filtered_psi, 0, filtered_psi[0])

# plot
fig = plt.figure(figsize=(20, 10))

fig.add_subplot(2, 2, 1, title="Signal x")
plt.plot(unfiltered_x, label="original signal")
plt.plot(filtered_x, label="filtered signal")
plt.legend()
plt.xlabel('time')
plt.ylabel('value')

fig.add_subplot(2, 2, 2, title="Signal y")
plt.plot(unfiltered_y, label="original signal")
plt.plot(filtered_y, label="filtered signal")
plt.legend()
plt.xlabel('time')
plt.ylabel('value')

fig.add_subplot(2, 2, 3, title="Signal z")
plt.plot(unfiltered_z, label="original signal")
plt.plot(filtered_z, label="filtered signal")
plt.legend()
plt.xlabel('time')
plt.ylabel('value')

fig.add_subplot(2, 2, 4, title="Signal psi")
plt.plot(unfiltered_psi, label="original signal")
plt.plot(filtered_psi, label="filtered signal")
plt.legend()
plt.xlabel('time')
plt.ylabel('value')

plt.show()
