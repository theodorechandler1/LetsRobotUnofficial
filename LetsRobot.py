from ChatServerInbound import ChatServerInbound
from ControlServerInbound import ControlServerInbound
import logging
from queue import Queue
import threading

class LetsRobot(object):
    """
    LetsRobot is designed to be an easy to use module to allow users to quickly add robots to letsrobot.tv
    
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__).addHandler(logging.NullHandler())
        self.shutdownEventSet = set()
        self.chatHandlers = set()
        self.controlHandlers = set()
        self.chatQueue = Queue()
        self.controlQueue = Queue()
        self.eventWaiting = threading.Event()
        self.eventShutdown = threading.Event()
        self.threadList = set()
        
    def addChatHandler(self, function):
        """Add a function to be called each time a chat event is passed from the server
            
        Keyword arguments:
            function -- function to be called
        """
        self.chatHandlers.add(function)
    
    def removeChatHandler(self, function):
        """Remove a function to be called each time a chat event is passed from the server
            
        Keyword arguments:
            function -- function to be removed
        """
        self.chatHandlers.remove(function)
    
    def addChatServer(self, robotID, chatServerURL= "letsrobot.tv"):
        """Add a robot to listen for chat events on
            
        Keyword arguments:
            robotID -- Robot ID Number passed as a string that we should listen for chat events
            chatServerURL -- URL to retrieve chat events from. Leave this alone for the most part
        """
        chatServer = ChatServerInbound(self.chatQueue, self.eventShutdown, self.eventWaiting, chatServerURL, robotID)
        chatServer.start()
        self.threadList.add(chatServer)
    
    def addControlHandler(self, function):
        """Add a function to be called each time a control event is passed from the server
            
        Keyword arguments:
            function -- function to be called
        """
        self.controlHandlers.add(function)
    
    def removeControlHandler(self, function):
        """Remove a function to be called each time a control event is passed from the server
            
        Keyword arguments:
            function -- function to be removed
        """
        self.controlHandlers.remove(function)
        
    def addControlServer(self, robotID, controlServerURL= "letsrobot.tv"):
        """Add a robot to listen for control events on
            
        Keyword arguments:
            robotID -- Robot ID Number passed as a string that we should listen for control events
            chatServerURL -- URL to retrieve control events from. Leave this alone for the most part
        """
        controlServer = ControlServerInbound(self.controlQueue, self.eventShutdown, self.eventWaiting, controlServerURL, robotID)
        controlServer.start()
        self.threadList.add(controlServer)
    
    def wait(self, timeout=5):
        '''Wait for server events and when events are received call the requested functions
            
        Keyword arguments:
            timeout -- Sets the amount of time to wait before returning control back
        '''
        if timeout is None: #Warning, waiting indefiently causes issues as exceptions are not passed while waiting
            self.eventWaiting.wait()
        else: #Wait for however long the user requested or until an event is ready
            self.eventWaiting.wait(timeout)
        while (not self.chatQueue.empty()) or (not self.controlQueue.empty()):
            if not self.chatQueue.empty():
                self.__callChatEvent__(self.chatQueue.get())
            if not self.controlQueue.empty():
                self.__callControlEvent__(self.controlQueue.get())
        self.eventWaiting.clear()
    
    def exit(self):
        '''Allows the threads to shutdown gracefully
        
        '''
        self.eventShutdown.set()
        for t in self.threadList:
            t.join(5) 
    
    def __callChatEvent__(self, *args):
        for chatHandler in self.chatHandlers:
            chatHandler(*args)
    
    def __callControlEvent__(self, *args):
        for controlHandler in self.controlHandlers:
            controlHandler(*args)
    

if __name__ == '__main__':
    try:
        r = LetsRobot()
        r.start()
    except(KeyboardInterrupt):
        
        print("KeyboardInterrupt, exiting")