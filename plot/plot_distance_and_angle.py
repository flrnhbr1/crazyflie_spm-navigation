import math
import yaml
import numpy as np
import matplotlib.pyplot as plt
distance_set = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]
distance_measured = [None, 20.481, 30.054, 40.300, 50.641, 60.697, 70.774, 81.249, 90.882, 101.421, 111.198, 121.210,
                     131.418, 142.302, 152.105, 164.234, 174.596, 185.567, 196.613, 210.405]

angle_set = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
angle_measured = [-0.952, 11.293, 22.046, 28.188, 39.251, 49.273, 58.632, 69.457, None, None]

fig = plt.figure(figsize=(20, 10))

fig.add_subplot(1, 2, 1, title="Distance in x-direction")
plt.plot(distance_set, 'o', label="Distance")
plt.plot(distance_set, linestyle=':', marker='o', color="tab:blue")
plt.plot(distance_measured, 'o', label="Measurement")
plt.plot(distance_measured, linestyle=':', marker='o', color="tab:orange")
plt.legend()
plt.grid()
plt.ylabel('Distance [cm]')
plt.xticks(np.arange(0, 0, 10))
plt.yticks(np.arange(0, 220, 10))

fig.add_subplot(1, 2, 2, title="Yaw angle")
plt.plot(angle_set, 'o', label="Angle")
plt.plot(angle_set, linestyle=':', marker='o', color="tab:blue")
plt.plot(angle_measured, 'o', label="Measurement")
plt.plot(angle_measured, linestyle=':', marker='o', color="tab:orange")
plt.legend()
plt.grid()
plt.ylabel('Angle [°]')
plt.xticks(np.arange(0, 0, 10))
plt.yticks(np.arange(0, 100, 10))

plt.show()
