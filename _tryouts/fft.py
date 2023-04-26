import math

import yaml
import numpy as np
import matplotlib.pyplot as plt


def plot_motion_data():
    # plot motion data
    fig = plt.figure(figsize=(20, 10), num='Motion data')

    fig.add_subplot(2, 2, 1, title="Translation in x (forward/backward)")
    plt.plot(unfiltered_x, label="Measured signal")
    # plt.plot(filtered_x, label="Signal after MA filter")
    plt.plot(w_filtered_x, label="Filtered signal (WMA)", color="tab:green")

    plt.legend()
    plt.grid()
    plt.xlabel('Samples [n]')
    plt.ylabel('Distance [cm]')

    fig.add_subplot(2, 2, 2, title="Translation in y (left/right)")
    plt.plot(unfiltered_y, label="Measured signal")
    # plt.plot(filtered_y, label="Signal after MA filter")
    plt.plot(w_filtered_y, label="Filtered signal (WMA)", color="tab:green")

    plt.legend()
    plt.grid()
    plt.xlabel('Samples [n]')
    plt.ylabel('Distance [cm]')

    fig.add_subplot(2, 2, 3, title="Translation in z (up/down)")
    plt.plot(unfiltered_z, label="Measured signal")
    # plt.plot(filtered_z, label="Signal after MA filter")
    plt.plot(w_filtered_z, label="Filtered signal (WMA)", color="tab:green")

    plt.legend()
    plt.grid()
    plt.xlabel('Samples [n]')
    plt.ylabel('Distance [cm]')

    fig.add_subplot(2, 2, 4, title="Yaw rotation")
    plt.plot(unfiltered_psi * 180 / math.pi, label="Measured signal")
    plt.plot(filtered_psi * 180 / math.pi, label="Filtered signal (MA)")
    # plt.plot(w_filtered_psi, label="Signal after WMA filter")

    plt.legend()
    plt.grid()
    plt.xlabel('Samples [n]')
    plt.ylabel('Offset [°]')

    plt.show()


def plot_errors():
    # plot errors
    fig2 = plt.figure(figsize=(20, 10), num='Errors')

    fig2.add_subplot(2, 2, 1, title="Translation in x (forward/backward)")
    plt.plot(abs(unfiltered_x - w_filtered_x), 'red', label="Error measured <--> WMA")
    plt.legend()
    plt.grid()
    plt.xlabel('Samples [n]')
    plt.ylabel('Deviation [cm]')

    fig2.add_subplot(2, 2, 2, title="Translation in y (left/right)")
    plt.plot(abs(unfiltered_y - w_filtered_y), 'red', label="Error measured <--> WMA")
    plt.legend()
    plt.grid()
    plt.xlabel('Samples [n]')
    plt.ylabel('Deviation [cm]')

    fig2.add_subplot(2, 2, 3, title="Translation in z (up/down)")
    plt.plot(abs(unfiltered_z - w_filtered_z), 'red', label="Error measured <--> WMA")
    plt.legend()
    plt.grid()
    plt.xlabel('Samples [n]')
    plt.ylabel('Deviation [cm]')

    fig2.add_subplot(2, 2, 4, title="Yaw rotation")
    plt.plot(abs(unfiltered_psi - filtered_psi) * 180 / math.pi, 'red', label="Error measured <--> MA")
    plt.legend()
    plt.grid()
    plt.xlabel('Samples [n]')
    plt.ylabel('Deviation [°]')
    plt.show()


def plot_fft():
    unf_x_fft = np.fft.fft(unfiltered_y)
    wma_x_fft = np.fft.fft(w_filtered_y)

    fig3 = plt.figure(figsize=(20, 10), num='Fourier data')

    fig3.add_subplot(2, 2, 1, title="Translation in x (forward/backward)")
    plt.plot(np.real(unf_x_fft), label="Original")
    plt.plot(np.real(wma_x_fft), label="WMA")

    plt.legend()
    plt.grid()
    plt.xlabel('Samples [n]')
    plt.ylabel('Distance [cm]')
    plt.show()

window_size = 3
# read data
with open("../plot/WMA_weights--quadr.yaml") as f:
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
for i in range(window_size - 1):
    filtered_x = np.insert(filtered_x, 0, filtered_x[0])
    filtered_y = np.insert(filtered_y, 0, filtered_y[0])
    filtered_z = np.insert(filtered_z, 0, filtered_z[0])
    filtered_psi = np.insert(filtered_psi, 0, filtered_psi[0])

    w_filtered_x = np.insert(w_filtered_x, 0, w_filtered_x[0])
    w_filtered_y = np.insert(w_filtered_y, 0, w_filtered_y[0])
    w_filtered_z = np.insert(w_filtered_z, 0, w_filtered_z[0])
    w_filtered_psi = np.insert(w_filtered_psi, 0, w_filtered_psi[0])

plot_fft()