import logging
from app import socketInstance
from flask import request
import time
from threading import Thread,Event


@socketInstance.on('connect')
def connect():
    logging.info('Connecting from user id: {}'.format(request.sid))


@socketInstance.on('disconnect')
def test_disconnect():
    logging.info('Disconnecting from user id: {}'.format(request.sid))



@socketInstance.on('connect',namespace='/camera')
def connectToCamerad():
    logging.info('Connecting to name space ''/camera'' from user id: {}'.format(request.sid))

@socketInstance.on('connect',namespace='/amp')
def connectToAmp():
    logging.info('Connecting to name space ''/amp'' from user id: {}'.format(request.sid))



class Pause():
  def __init__(self,thread_name):
    self.thread_name=thread_name or None
    self.thread_event=Event()
  def pauseExecution(self):
    while not self.thread_event.isSet():
        logging.info('Experiment is paused for user to restart...')
        socketInstance.sleep(2)
        if self.thread_event.isSet():
          break

  
  def startPause(self,socket_event,socket_info,socket_namespace):
      socketInstance.emit(socket_event,socket_info,namespace=socket_namespace)
      self.pauseAgain()
      pauseThread = Thread(name=self.thread_name, target=self.pauseExecution)
      pauseThread.start() 
      pauseThread.join()

  def restart(self):
      self.thread_event.set()
  def pauseAgain(self):
      self.thread_event.clear()

