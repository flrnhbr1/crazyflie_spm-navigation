import math
import yaml
import numpy as np
import matplotlib.pyplot as plt

# read data
with open("battery_data/Log_2023-7-5T13-40-12withAI.yaml") as f:
    loaded_dict = yaml.safe_load(f)
    bat = loaded_dict.get('battery')
    tim = loaded_dict.get('time')

    battery_AI = np.array(bat)
    time_AI = np.array(tim)

with open("battery_data/Log_2023-7-5T14-56-28withAI.yaml") as f:
    loaded_dict = yaml.safe_load(f)
    bat = loaded_dict.get('battery')
    tim = loaded_dict.get('time')

    battery_noAI = np.array(bat)
    time_noAI = np.array(tim)

# averaging --> noise suppression
window_size = 3
weights = []
for a in range(-1, window_size-1):
    weights.append(2**a)

avg_battery_AI = []
i = 0
while i < len(battery_AI) - window_size + 1:
    # Calculate the moving average of current window
    window_average_AI = np.average(battery_AI[i:i + window_size], weights=weights)
    avg_battery_AI.append(window_average_AI)
    i += 1

avg_battery_noAI = []
i = 0
while i < len(battery_noAI) - window_size + 1:
    # Calculate the moving average of current window
    window_average_noAI = np.average(battery_noAI[i:i + window_size], weights=weights)
    avg_battery_noAI.append(window_average_noAI)
    i += 1


# change to percent
max_AI = avg_battery_AI[0]
min_AI = avg_battery_AI[len(avg_battery_AI)-1]
max_noAI = avg_battery_noAI[0]
min_noAI = avg_battery_noAI[len(avg_battery_noAI)-1]

battery_percent_AI = []
battery_percent_noAI = []

for i in avg_battery_AI:
    percentage = ((i-min_AI) / (max_AI-min_AI))*100
    battery_percent_AI.append(percentage)

for i in avg_battery_noAI:
    percentage = ((i-min_noAI) / (max_noAI-min_noAI))*100
    battery_percent_noAI.append(percentage)

time_AI = time_AI[0:len(time_AI)-2]

print("Plotting data loaded")

fig = plt.figure(figsize=(20, 10), num='Battery data')
fig.add_subplot(2, 1, 1, title="Battery voltage over time")
plt.plot(time_AI, avg_battery_AI)

plt.grid()
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')

# fig.add_subplot(2, 1, 2, title="Battery percentage over time")
# plt.plot(time_AI, battery_percent_AI, label="with AI deck")
# plt.plot(time_AI, battery_percent_noAI, label="without AI deck")
#
# plt.legend()
# plt.grid()
# plt.xlabel('Time [s]')
# plt.ylabel('Battery Level [%]')



plt.show()

print(np.array(avg_battery_AI, float))
print(np.array(time_AI, float))
