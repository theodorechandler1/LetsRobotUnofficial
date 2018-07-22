===========
LetsRobotUnofficial
===========

LetsRobotUnoffical is a easy to use interface for connecting your robot to the letsrobot.tv website.
Typical usage often looks like this::

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

For more information visit https://letsrobot.tv
or 