from letsrobot_unofficial import LetsRobot
from datetime import datetime


f = open('chatLog.txt', 'a', encoding='utf-8')

def chatEvent(args):
    #Handle chat events here
    print(args)
    message = args['message'].split(']')
    message = message[1:]
    if len(message) > 0:
        message = message[0]
    else:
        message = ""
    f.write(datetime.today().strftime("%m/%d/%y %H:%M:%S") + ' ' + args['name'] + ': ' + args['message'] + "\n")
    f.flush()

try:
    r = LetsRobot()
    r.addChatServer("robotID1")
    r.addChatServer("robotID2")
    while(True):
        r.wait()
except(KeyboardInterrupt):
    print("KeyboardInterrupt Main Thread, exiting")
    
finally:
    r.exit()
    f.close()