import math
import yaml
import numpy as np
import matplotlib.pyplot as plt

# read data
with open("timing_data/Log_RAW_long.yaml") as f:
    loaded_dict = yaml.safe_load(f)
    rtt = loaded_dict.get('RTT')
    rtt_raw = np.array(rtt)

with open("timing_data/Log_JPG_long.yaml") as f:
    loaded_dict = yaml.safe_load(f)
    rtt = loaded_dict.get('RTT')
    rtt_jpg = np.array(rtt)

print("Plotting data loaded")

avg_raw = np.average(rtt_raw)
avg_jpg = np.average(rtt_jpg)

fig = plt.figure(figsize=(20, 10), num='Timing data')
fig.add_subplot(2, 1, 1, title="RTT image acquisition")
plt.plot(rtt_raw, label="raw data")
plt.plot(rtt_jpg, label="jpg data")
plt.axhline(avg_raw, linestyle=':', label="average raw data")
plt.axhline(avg_jpg, linestyle=':', label="average jpg data", color='tab:orange')
plt.text(len(rtt_raw)+0.005*len(rtt_raw), avg_raw+0.000005*len(rtt_raw), str(round(avg_raw, 3)),
         color="tab:blue", fontsize=12)
plt.text(len(rtt_jpg)+0.005*len(rtt_jpg), avg_jpg-0.000015*len(rtt_jpg), str(round(avg_jpg, 3)),
         color="tab:orange", fontsize=12)


plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
plt.ylabel('Time [s]')

plt.show()
