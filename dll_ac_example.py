# -*- coding: utf-8 -*-

# import required modules
import numpy as np
import matplotlib.pyplot as plt
from nl5_dll import NL5_dll

# create NL5 instance
nl5 = NL5_dll(path='C:/NL5/nl5_dll')

if nl5.get_license():
    print(f'Using license: {nl5.get_error()}')
else:
    print('License not valid, run in demo mode.')
print(f'NL5 version is: {nl5.get_info()}')

# open simulation file
nl5.open('dll_example.nl5')

# initialize
R = np.logspace(-2, 1, 50)
Z = np.zeros((50, 100))

for k in range(50):
    # set R1 value
    nl5.set_value('R1.R', R[k])

    # simulate AC
    nl5.simulate_ac()

    # read data
    for i in range(100):
        freq, mag, phase = nl5.get_ac_data_at('V(out)', i)
        Z[k, i] = 20.0 * np.log10(mag)

# close document
nl5.close()
print(f'NL5 Status: {nl5.get_error()}')

# plot a 3D Surface
X = np.linspace(1, 100, 100)
Y = np.linspace(1, 50, 50)
Y, X = np.meshgrid(X, Y)

# formatting the figure
fig = plt.figure(figsize=(5, 5))
ax = fig.add_subplot(111, projection='3d')
ax.set_zlim(-60, 20)
mycmap = plt.get_cmap('jet')
plt.gca().invert_xaxis()

# plotting the surface
surf = ax.plot_surface(X, Y, Z, cmap=mycmap)

# adding the colorbar
cb = plt.colorbar(surf)

ax.view_init(45, 15)

plt.show()
