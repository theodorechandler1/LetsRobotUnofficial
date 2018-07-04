from socketIO_client import SocketIO, LoggingNamespace
from ServerHelper import ServerHelper
import logging
import threading
import json

class ChatServerInbound(threading.Thread):
    """ 
        This class receives messages from the chat server (generally letsrobot.tv) and passes them to a pipe so that the robot can act on them
    """
    def __init__(self, chatQueue, shutdownEvent, eventWaiting, serverURL, robotID):
        self.logger = logging.getLogger(__name__).addHandler(logging.NullHandler())
        self.chatQueue = chatQueue
        self.shutdownEvent = shutdownEvent
        self.eventWaiting = eventWaiting
        self.serverURL = serverURL
        self.robotID = robotID
        self.chatHostPort = None
        self.chatSocket = None
        self.chatConnected = False
        super(ChatServerInbound, self).__init__()
    
    def run(self):
        self.__chatReceiverSetup()
        self.__listenAndWait()
    
    def __listenAndWait(self):
        while not self.shutdownEvent.is_set(): #While we have not been told to shutdown
            self.chatSocket.wait(seconds=1) #Check for chatEvents
    
    def _getChatHostPort(self):
        logging.debug("Getting chat host port from server")
        url = 'https://{}/get_chat_host_port/{}'.format(self.serverURL, self.robotID)
        response = ServerHelper.getWithRetry(url)
        self.chatHostPort = json.loads(response)
        logging.debug("Found chat host port of: {}".format(self.chatHostPort))
    
    def __chatReceiverSetup(self):
        self._getChatHostPort()
        logging.debug("Connecting to chat socket.io port: {}".format(self.chatHostPort))
        self.chatSocket = SocketIO(self.chatHostPort['host'], self.chatHostPort['port'], LoggingNamespace)
        logging.debug('Finished using socket io to connect to chat port: {}'.format(self.chatHostPort))
        
        self.chatSocket.on('chat_message_with_name', self._handleChatMessage)
        self.chatSocket.on('connect', self._sendRobotID)
        self.chatSocket.on('reconnect', self._sendRobotID)
        self.chatSocket.on('disconnect', self._handleChatDisconnect)
        
    def _sendRobotID(self):
        logging.info("Socket connected. Sending robot ID")
        self.chatSocket.emit('identify_robot_id', self.robotID)
        self.chatConnected = True
    
    def _handleChatDisconnect(self):
        logging.info("Chat socket disconnected.")
        self.chatConnected = False
    
    def _handleChatMessage(self, *args):
        #Send it upstream and notify the main thread there is work to do
        logging.debug("User: %s sent: %s" % (args[0]['name'], args[0]['message']))
        self.chatQueue.put(*args)
        self.eventWaiting.set()

