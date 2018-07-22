from letsrobot_unofficial import LetsRobot
import logging

def chatEvent(args):
    #Handle chat events here

def controlEvent(args):
    #Handle control events here

#To debug the LetsRobot library you can insert the following code before instantiating a LetsRobot instance.
logger = logging.getLogger('letsrobot_unofficial') 
#Note if you want to debug only a certain part of the library you can replace the previous line with one of the following
#logger = logging.getLogger('letsrobot_unofficial.VideoServerOutbound') #For video issues
#logger = logging.getLogger('letsrobot_unofficial.ChatServerInbound') #For chat issues
#logger = logging.getLogger('letsrobot_unofficial.ControlServerInbound') #For control issues
#logger = logging.getLogger('letsrobot_unofficial.LetsRobot') #For issues with interfacing with the other sections
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(streamHandler)
logger.setLevel(logging.DEBUG)

r = LetsRobot()
r.addChatServer("robotIDHere")
r.addControlServer("robotIDHere")
r.addVideoOutput("videoIDHere")
r.addChatHandler(chatEvent)
r.addControlHandler(controlEvent)
while(True):
    r.wait()