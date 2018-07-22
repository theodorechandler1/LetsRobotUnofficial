# LetsRobotUnofficial


LetsRobotUnoffical is a easy to use interface for connecting your robot to the letsrobot.tv website.
A minimal example looks like:

```python
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
```

For more information including how to get a robot id and video id visit https://letsrobot.tv
or for additional examples and documentation visit https://github.com/theodorechandler1/LetsRobotUnofficial