

import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import numpy as np


plt.style.use('fivethirtyeight')

x_values = []
y_values = []
z_values = []
q_values = []
w_values = []

# index = count()
# pos gives coordinates (x, y, z, q)
pos = ( 0, 0, 1, 0)
# get x from pad
# get y from pad
# drone à 1m d'altitude

TEMPO = 0.25 # sec
t = 0 * TEMPO # init

TIMES  = [0, 20, 40, 60, 80]
CHANGE = 0

def takeoff(t, pos):
    pass

def move_spirale(t, pos):
    return (np.cos(t)*10, np.sin(t)*10, pos[2]+t, 0)

def move_cos(t, pos):
    return (np.cos(t), pos[1]+1, pos[2], 0)

def move_sin(t, pos):
    return (pos[0]+1, np.sin(t), pos[2], 0)


def animate(i):
    global t, pos
    # q = 0 # unused # random.randint(0, 10)
    # w = 0 # unused # random.randint(0, 10)
    print(pos)
    if t < 10 :
        pos = move_spirale(t, pos)
    elif t >= 10 and t < 20 :
        pos = move_sin(t, pos)
    elif t >= 20 and t < 40:
        pos = move_cos(t, pos)
    else:
        print("Waiting for new pos")
        time.sleep(1)
    x_values.append(pos[0])
    y_values.append(pos[1])
    z_values.append(pos[2])
    q_values.append(pos[3]) # unsued

    col=['b', 'y', 'g', 'r']

    ax.plot3D(x_values, y_values, z_values, c=col[int(t%4)], linestyle='-', linewidth=1)

    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')

    time.sleep(.05)
    t += TEMPO

fig = plt.figure(figsize=(10, 10))
ax = plt.axes(projection='3d')    
ani = FuncAnimation(plt.gcf(), animate, 10)


plt.tight_layout()
plt.show()