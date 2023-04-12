import numpy as np

# try out moving and weighted moving average

wind_size = 5
data = [1, 2, 3, 4, 5, 6, 7]

length = len(data)
weights = []
for i in range(wind_size-1, -1, -1):  # fill weight array [... , 0.125, 0.25, 0.5, 1]
    print(i)
    weights.append(1/2**i)

print(weights)

result = np.average(data)
print(result)
leng = len(data)
result = np.average(data[leng-wind_size:leng], weights=weights)
print(result)
