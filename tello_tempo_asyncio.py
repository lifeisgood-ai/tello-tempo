#!/usr/bin/env python
# coding: utf-8

# # Tello Tempo

# ## Import de bibliothèques

# In[1]:



# In[2]:


# from djitellopy import Tello
# import tellopy
# import cv2 as cv 
# import socket, time
from time import sleep
import datetime
import os
# from threading import Thread
# import numpy as np

import pytz # timezone for timestamp
import datetime


import asyncio
from tello_asyncio import Tello
import random

def on_drone_state(drone, state):
    print(f'acceleration: {state.acceleration}, velocity: {state.velocity}')


async def move_f(tello, timeout):
    # inc = random.randint(0, 5)
    if timeout > 0:
        await asyncio.sleep(timeout)
    # print("Moving forward")
    await tello.move_forward(100)
    # print("... moving should stop")

async def move_b(tello, timeout):
    # inc = random.randint(0, 5)
    # print("waiting for ", 1+inc, " secs")
    if timeout > 0:
        await asyncio.sleep(timeout)
    # print("Moving back")
    await tello.move_back(100)
    # print("... back should stop")

# async def stop(tello):
#     # inc = random.randint(0, 5)
#     # print("waiting for ", 1+inc, " secs")
#     print("Stopping")
#     await tello.stop()
#     # await asyncio.sleep(1 + inc)
#     # await asyncio.sleep(2)
#     print("... stop should stop any movement and hover")

async def battery_level(tello):
    # print(f"Battery level is {tello.get_battery()}%")
    print(f"Battery level is {await tello.query_battery()}%")

async def main():
    # tello = Tello(on_state=on_drone_state)
    tello = Tello()


    # tello = Tello()
    # tello.connect(False)
    await tello.connect()
    await battery_level(tello)
    await tello.set_speed(50)
    await tello.takeoff()
    await asyncio.gather( move_f(tello, 2), move_b(tello, 7))

    print('#### land')
    await tello.land()
    await battery_level(tello)

    # await count()
    # await count_back()


if __name__ == "__main__":
    import time
    s = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")

    

# In[2]:


# Tello??


# ### Useful custom functions

# In[3]:


def get_timestamp():
    tz = pytz.timezone('Europe/Paris')
    currentDT = datetime.datetime.now(tz)
    TIMESTAMP = currentDT.strftime("%Y%m%d_%H%M%S")
    return TIMESTAMP


# In[4]:



# In[ ]:



# In[9]:


def difference(list1, list2):
    zip_object = zip(list1, list2)
    difference=[]
    for list1_i, list2_i in zip_object:
        difference.append(list2_i-list1_i)
    return difference


# # Utilisation  de `Tellopy`

# * Décollage et attérissage 

# In[10]:




# tello= Tello () 
# tello.connect() # Connexion


# # In[27]:


# battery_level(tello)


# In[12]:


# tello.takeoff() # Décollage 
# # tello.streamon() # Activation de la caméra

# time.sleep(1) # Tempo de 2s 
# frame_read = tello.get_frame_read() # Capture d'impage
# img_name = f"view_{get_timestamp()}.png"
# print(img_name)
# cv.imwrite("testnew.png", frame_read.frame) # Stockage en local 
# time.sleep(1)
# tello.streamoff()
# tello.land()   # Attérissage


def videoRecorder():
    height, width,_= frame_read.frame.shape
    video_name = f"video_{get_timestamp()}.avi"

    video = cv.VideoWriter(video_name, cv.VideoWriter_fourcc(*'XVID'), 30, (width,height))
    
    while KeepRecording:
        video.write(frame_read.frame)
        time.sleep(1/30)
    video.release()


def patrol():
    """
    Dessine un arc de cercle et se retourne
    Espae nécessaire environ 1.5m
    """
    print("### curvy path")
    tello.curve_xyz_speed(25, -25, 0, 150, 25, 0, 50)
    # tello.rotate_clockwise(180)
    print('#### Wait')
    time.sleep(1)
    print("### stop")

    tello.stop()
    print("### curvy path back")

    tello.curve_xyz_speed(-25, 25, 0, -150, -25, 0, 50)

    print('#### Wait')
    time.sleep(1)

# tello = Tello()
# tello.connect(False)


# NUM_PATROL = 4

# # afficher niveau de batterie
# battery_level(tello)

# tello.takeoff()
# print('#### up 80')

# tello.move_up(50)

# for k in range(NUM_PATROL):
#     patrol()
# print('#### f 30')
# tello.move_forward(30)
# print('#### r 30')
# tello.move_right(30)
# print('#### b 30')
# tello.move_back(30)
# print('#### l 30')
# tello.move_left(30)
# print('#### stop')
# tello.stop()

# tello.curve_xyz_speed(50, -50, 0, 0, 100, 0, 50)
# tello.curve_xyz_speed(50, -50, 0, 0, 100, 0, 50)

# print('#### land')
# tello.land()
# battery_level(tello)
# tello.stop()





def move_spirale(t, pos):
    return [np.cos(t)*10, np.sin(t)*10, pos[2]+t, 0]


# In[37]:


def spirale(tello):
    TEMPO=0.05
    t=0
    pos=[20, 20, 0, 0]
    speed=50
    PADDING=10

    next_pos = pos
    for k in range(5):
        t+=1
        pos_ = move_spirale(t, next_pos)
        next_pos = difference(next_pos, pos_)
        if next_pos[0] > 0:
            next_pos[0]+=PADDING
        else:
            next_pos[0]-=PADDING
        if next_pos[1] > 0:
            next_pos[1]+=PADDING
        else:
            next_pos[1]-=PADDING
        print(t, next_pos)        
        print('before move')

        tello.go_xyz_speed(int(next_pos[0]), int(next_pos[1]), int(next_pos[2])+PADDING, speed)
        print('move done')
#         time.sleep(TEMPO)
