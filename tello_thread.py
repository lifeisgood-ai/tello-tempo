#!/usr/bin/env python
# -*- coding: utf-8 -*-

 # good ref here : https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
 
import sys
import trace
from threading import Thread, Event
import time

class TelloThread(Thread):
  def __init__(self, *args, **keywords):
    Thread.__init__(self, *args, **keywords)
    self.killed = False

  def start(self):
    self.__run_backup = self.run
    self.run = self.__run     
    Thread.start(self)
 
  def __run(self):
    sys.settrace(self.globaltrace)
    self.__run_backup()
    self.run = self.__run_backup
 
  def globaltrace(self, frame, event, arg):
    if event == 'call':
      return self.localtrace
    else:
      return None
 
  def localtrace(self, frame, event, arg):
    if self.killed:
      if event == 'line':
        raise SystemExit()
    return self.localtrace
 
  def kill(self):
    print("Ask to kill thread_id", self.ident)
    self.killed = True


 
def func():
  while True:
    print('thread running func')
    time.sleep(1)

def bbar(status):
  print(status)
  while True:
    print('thread running bbar')
    time.sleep(2)
 
if __name__ == "__main__":
  status= 111
  t1 = TelloThread(target = func)
  t2 = TelloThread(target = bbar, args=(status,))
  t1.start()
  t2.start()
  print("wait 2 sec")
  time.sleep(2)
  print(threading.get_ident())
  print(threading.get_native_id()) # process id
  t1.kill()
  t1.join()
  t2.kill()
  t2.join()

  if not t1.is_alive():
    print('thread t1 killed')