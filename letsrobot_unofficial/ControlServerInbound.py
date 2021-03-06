from socketIO_client import SocketIO, LoggingNamespace
from requests.exceptions import ConnectionError
from .ServerHelper import ServerHelper
import logging
import threading
import json


class ControlServerInbound(threading.Thread):
    
    def __init__(self, controlQueue, shutdownEvent, eventWaiting, serverURL, robotID, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())
        self.serverURL = serverURL
        self.robotID = robotID
        self.controlQueue = controlQueue
        self.shutdownEvent = shutdownEvent
        self.eventWaiting = eventWaiting
        self.controlHostPort = None
        self.commandSocket = None
        self.disconnected = True
        super(ControlServerInbound, self).__init__(*args, **kwargs)
    
    def run(self):
        while not self.shutdownEvent.is_set(): #Retry every time the server fails to connect
            self.__controlServerSetup()
            self.__listenAndWait()
    
    def __getControlHostPort(self):
        url = 'https://{}/get_control_host_port/{}'.format(self.serverURL, self.robotID)
        self.logger.debug("Getting control host port from url: %s" % (url))
        response = ServerHelper.getWithRetry(url)
        self.controlHostPort = json.loads(response)
    
    def __controlServerSetup(self):
        self.__getControlHostPort()
        self.logger.debug("Connecting to control socket.io port: {}".format(self.controlHostPort))
        self.commandSocket = SocketIO(self.controlHostPort['host'], self.controlHostPort['port'], LoggingNamespace)
        self.logger.debug("Finished using socket io to connect to control host port: {}".format(self.controlHostPort))
        
        self.commandSocket.on('command_to_robot', self._handleCommand)
        self.commandSocket.on('disconnect', self._handleCommandDisconnect)
        self.commandSocket.on('connect', self._sendRobotID)
        self.commandSocket.on('reconnect', self._sendRobotID)
        self.disconnected = False
    
    def __listenAndWait(self):
        while(not self.shutdownEvent.is_set() and (self.disconnected == False)):
            self.commandSocket.wait(seconds=1)
                
    def _handleCommandDisconnect(self):
        self.logger.debug("Command Socket Disconnected")
        self.disconnected = True
    
    def _sendRobotID(self):
        self.commandSocket.emit('identify_robot_id', self.robotID)
        self.commandSocket.emit('libVer', {'library' : 'letsrobot_unofficial', 'version' : '0.0.1'})
    
    def _handleCommand(self, *args):
        #Send it upstream and notify the main thread there is work to do
        self.logger.debug("Received Command: {} from: {}".format(args[0]['command'],args[0]['user']))
        self.controlQueue.put(*args)
        self.eventWaiting.set()