from socketIO_client import SocketIO, LoggingNamespace
from ServerHelper import ServerHelper
import logging
import threading
import json


class ControlServerInbound(threading.Thread):
    
    def __init__(self, controlQueue, shutdownEvent, eventWaiting, serverURL, robotID):
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        self.serverURL = serverURL
        self.robotID = robotID
        self.controlQueue = controlQueue
        self.shutdownEvent = shutdownEvent
        self.eventWaiting = eventWaiting
        self.controlHostPort = None
        self.commandSocket = None
        super(ControlServerInbound, self).__init__()
    
    def run(self):
        self.__controlServerSetup()
        self.__listenAndWait()
    
    def __getControlHostPort(self):
        logging.debug("Getting control host port from server")
        url = 'https://{}/get_control_host_port/{}'.format(self.serverURL, self.robotID)
        response = ServerHelper.getWithRetry(url)
        self.controlHostPort = json.loads(response)
    
    def __controlServerSetup(self):
        self.__getControlHostPort()
        logging.debug("Connecting to control socket.io port: {}".format(self.controlHostPort))
        self.commandSocket = SocketIO(self.controlHostPort['host'], self.controlHostPort['port'], LoggingNamespace)
        logging.debug("Finished using socket io to connect to control host port: {}".format(self.controlHostPort))
        
        self.commandSocket.on('command_to_robot', self._handleCommand)
        self.commandSocket.on('disconnect', self._handleCommandDisconnect)
        self.commandSocket.on('connect', self._sendRobotID)
        self.commandSocket.on('reconnect', self._sendRobotID)
    
    def __listenAndWait(self):
        while not self.shutdownEvent.is_set():
            self.commandSocket.wait(seconds=1)
    
    def _handleCommandDisconnect(self):
        logging.debug("Command Socket Disconnected")
    
    def _sendRobotID(self):
        self.commandSocket.emit('identify_robot_id', self.robotID)
    
    def _handleCommand(self, *args):
        #Send it upstream and notify the main thread there is work to do
        logging.debug("Received Command: {} from: {}".format(args[0]['command'],args[0]['user']))
        self.controlQueue.put(*args)
        self.eventWaiting.set()