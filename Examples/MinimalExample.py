from letsrobot_unofficial import LetsRobot

def chatEvent(args):
    #Handle chat events here

def controlEvent(args):
    #Handle control events here

r = LetsRobot()
r.addChatServer("robotIDHere")
r.addControlServer("robotIDHere")
r.addVideoOutput("videoIDHere")
r.addChatHandler(chatEvent)
r.addControlHandler(controlEvent)
while(True):
    r.wait()