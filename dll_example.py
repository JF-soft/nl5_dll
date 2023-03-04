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
R = np.logspace(-1, 1, 50)
Z = np.zeros((50, 100))

for k in range(50):
    # set R1 value
    nl5.set_value('R1.R', R[k])

    # simulate for 10s
    nl5.start()
    nl5.simulate(10.0)

    # read data
    for i in range(100):
        t = i * 0.1
        d = nl5.get_data('V(out)', t)
        Z[k, i] = d

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
ax.set_zlim(0, 20)
mycmap = plt.get_cmap('jet')
plt.gca().invert_xaxis()

# plotting the surface
surf = ax.plot_surface(X, Y, Z, cmap=mycmap)

# adding the colorbar
cb = plt.colorbar(surf)

plt.show()
