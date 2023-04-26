import numpy as np
import matplotlib.pyplot as plt

# try out moving and weighted moving average

wind_size = 7
data = []
for i in range(100):
    if i != 50:
        data.append(0)
    else:
        data.append(1)
result_ma = []
result_wma = []

length = len(data)
weights = []

# define weights
for a in range(wind_size, 0, -1):
    weights.append(1/a)

print(weights)

for d in range(length-wind_size):
    result_ma.append(np.average(data[d:d+wind_size]))
    result_wma.append(np.average(data[d:d+wind_size], weights=weights))

for i in range(wind_size - 1):
    result_ma = np.insert(result_ma, 0, result_ma[0])
    result_wma = np.insert(result_wma, 0, result_wma[0])



fig = plt.figure(figsize=(20, 10))

fig.add_subplot(2, 2, 1, title="Moving Average vs. Weighted Moving Average")
plt.plot(data, label="Impulse")
plt.plot(result_ma, label="Response MA filter")
plt.plot(result_wma, label="Response WMA filter")

plt.legend()
plt.grid()
plt.xlabel('Samples [n]')
plt.ylabel('')

plt.show()
