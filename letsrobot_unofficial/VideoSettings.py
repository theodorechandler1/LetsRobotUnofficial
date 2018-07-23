

class VideoSettings(object):
    
    def __init__(self):
        self.cameraID = None
        self.cameraDeviceNumber = 0
        self.audioDeviceNumber = 1
        self.audioChannels = 1
        self.audioEnabled = True
        self.videoEnabled = True
        self.kbps = 1024
        self.xres = 768
        self.yres = 432
        self.rotation = ''
        self.streamKey = 'hello'
        self.serverURL = 'letsrobot.tv'
        self.serverPort = 8022
        self.apiServer = 'api.letsrobot.tv'
        self.allowServerOverride = True #Allows the server to override settings 
    
    def getVideoCommand(self, videoHostRelay, videoPort):
        videoCommandLine = 'ffmpeg -f v4l2 -framerate 25 -video_size {xres}x{yres} -r 25 -i /dev/video{video_device_number} {rotation_option} -f mpegts -codec:v mpeg1video -b:v {kbps}k -bf 0 -muxdelay 0.001 http://{video_host}:{video_port}/{stream_key}/{xres}/{yres}/'.format( \
            video_device_number=self.cameraDeviceNumber, rotation_option=self.rotation, kbps=self.kbps, video_host=videoHostRelay, video_port=videoPort, xres=self.xres, yres=self.yres, stream_key=self.streamKey)
        return videoCommandLine
    
    def getAudioCommand(self, audioHostRelay, audioPort):
        audioCommandLine = 'ffmpeg -f alsa -ar 44100 -ac {audio_channels} -i hw:{audio_device_number} -f mpegts -codec:a mp2 -b:a 32k -muxdelay 0.001 http://{audio_host}:{audio_port}/{stream_key}/640/480/'.format( \
            audio_channels=self.audioChannels, audio_device_number=self.audioDeviceNumber, audio_host=audioHostRelay, audio_port=audioPort, stream_key=self.streamKey)
        return audioCommandLine

    def setRotationOption(self, rotate):
        if(rotate == True):
            self.rotation = "-vf transpose=2,transpose=2"
        else:
            self.rotation = ""