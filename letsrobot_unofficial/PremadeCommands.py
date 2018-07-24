import os
import logging
import tempfile
import uuid
import sys

if sys.platform.startswith('win32'):
    try:
        from win32com.client import Dispatch
    except ImportError:
        pass

class PremadeCommands(object):
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())
        self.voiceOutputNumber = None
        self.tempDir = tempfile.gettempdir()
        self.defaultVoice = "en" #Which voice to use
        self.defaultSpeed = 160 #How fast the text is read
        self.defaultPitch = 50
        pass
    
    
    def say(self, message):
        if sys.platform.startswith('linux'):
            return self.__sayLinux(message)
        elif sys.platform.startswith('win32'):
            return self.__sayWindows(message)
    
    def __sayLinux(self, message):
        if self.voiceOutputNumber is None:
            self.__findAudioHardwareNoLinux__()
        tempFilePath = os.path.join(self.tempDir, "text_" + str(uuid.uuid4()))
        result = 1 #Default to an error result
        with open(tempFilePath, "w") as f:
            f.write(message.encode('utf8'))
            f.close()
            # espeak tts
            command = "espeak -s {} -v {} -p {} -f {} --stdout | aplay -D plughw:{},0 > /dev/null 2>&1".format(self.defaultSpeed, self.defaultVoice, self.defaultPitch, tempFilePath, self.voiceOutputNumber)
            result = os.system(command)
            os.remove(tempFilePath)
        return result
    
    def __sayWindows(self,message):
        pass
    
    def __findAudioHardwareNoLinux__(self):
        for voiceOutputNumber in range(25):
            self.voiceOutputNumber = voiceOutputNumber
            result = self.say(" ")
            if result == 0:
                self.logger.debug("Found hardware number %s" % (self.voiceOutputNumber))
                break