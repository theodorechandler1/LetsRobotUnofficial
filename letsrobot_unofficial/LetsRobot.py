from .ChatServerInbound import ChatServerInbound
from .ControlServerInbound import ControlServerInbound
from .VideoServerOutbound import VideoServerOutbound
from .VideoSettings import VideoSettings
import logging

try:
    from queue import Queue
except ImportError:
    #Backwards compatable for python 2.x
    from Queue import Queue
import threading

class LetsRobot(object):
    """
    LetsRobot is designed to be an easy to use module to allow users to quickly add robots to letsrobot.tv
    
    
    Registered Chat Handler Functions will be passed a dictionary with the following key:value pairs
        name : String Name of the user who sent the message
        message : String Message the user sent. Generally (but not always) prefixed by "[RobotName]" where RobotName is the name of the robot
        robot_id : String ID of the robot from which the chat message was sent from
        room : String Username of the owner of the room or "global" if in global chat
        non_global : Boolean False if in global chat room. True otherwise
        username_color : String HEX color code of the users username_color
        anonymous : Boolean. False if user is logged in. True if the user has no account
        _id : String Unique identifier for the message. Unsure of its use
    
    Registered Control Handler Functions will be passed a dictionary with the following key:value pairs
        command : String value indicating the current command the robot is requested to perform
        robot_id : String ID of the robot which is being controlled
        key_position : String Unknown?
        user : String User requesting the command be performed. Will become inaccurate when multiple people are voting on the same command
        anonymous : Boolean. False if the user is logged in. True if the user has no account
    
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())
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
        chatServer.daemon = True
        chatServer.name = "ChatServer Thread ID: {}".format(robotID)
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
        controlServer.daemon = True
        controlServer.name = "ControlServer Thread ID: {}".format(robotID)
        controlServer.start()
        self.threadList.add(controlServer)
    
    def addVideoOutput(self, cameraID, videoSettings = VideoSettings()):
        self.logger.debug("Adding camera ")
        if(videoSettings.cameraID is None):
            videoSettings.cameraID = cameraID
        videoServer = VideoServerOutbound(self.eventShutdown, videoSettings)
        videoServer.daemon = True
        videoServer.name = "VideoServer Thread ID {}".format(cameraID)
        videoServer.start()
        self.threadList.add(videoServer)
        pass
    
    def wait(self, timeout=1):
        '''Wait for server events and when events are received call the requested functions
            
        Keyword arguments:
            timeout -- Sets the amount of time to wait before returning control back
        
        NOTE: If you are having trouble with Ctrl+C or other exceptions not happening until wait has returned then you are encountering this bug
        https://stackoverflow.com/questions/51083939/why-can-pythons-event-wait-be-interrupted-by-signals-on-some-systems-but-not
        https://bugs.python.org/issue34004
        No known fix is known at this time. A workaround is to set the wait timeout to a low number
        '''
        if timeout is None: #Warning, waiting indefiently can cause issues as exceptions are not always passed while waiting depending on your platform
            self.eventWaiting.wait()
        else: #Wait for however long the user requested or until an event is ready
            self.eventWaiting.wait(timeout)
        while (not self.chatQueue.empty()) or (not self.controlQueue.empty()):
            if not self.chatQueue.empty():
                self.__callChatEvent__(self.chatQueue.get())
            if not self.controlQueue.empty():
                self.__callControlEvent__(self.controlQueue.get())
        self.eventWaiting.clear() #Due to not being an atomic action there is a chance that an event might be set and then cleared without being handled
        #This is an acceptable tradeoff as during control many events will be fired in quick sucession. Limiting the time an event will sit before being processed
    
    def exit(self):
        '''Allows the threads to shutdown gracefully
        
        '''
        waitTime = 1
        self.logger.debug("Setting shutdown event")
        self.eventShutdown.set()
        for t in self.threadList:
            
            self.logger.debug("Waiting for thread %s to shutdown or %s seconds to pass" % (t.name, waitTime))
            t.join(1) 
    
    def __callChatEvent__(self, *args):
        """Internal method. Calls each registered function on chatEvent
        """
        for chatHandler in self.chatHandlers:
            chatHandler(*args)
    
    def __callControlEvent__(self, *args):
        """Internal method. Calls each registered function on controlEvent
        """
        for controlHandler in self.controlHandlers:
            controlHandler(*args)
    