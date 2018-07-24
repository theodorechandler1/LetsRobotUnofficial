from socketIO_client import SocketIO, LoggingNamespace
from .ServerHelper import ServerHelper
import logging
import threading
import json
import subprocess
import shlex
import time


class VideoServerOutbound(threading.Thread):
    
    def __init__(self, shutdownEvent, videoSettings, *args, **kwargs):
        super(VideoServerOutbound, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())
        self.shutdownEvent = shutdownEvent
        self.videoSettings = videoSettings #Contains all the relevant information for the video stream
        self.robotID = None
        self.appServerSocketIO = None
        self.requireRestart = False
        
        self.videoProcess = None
        self.audioProcess = None
        pass
    
    def run(self):
        try:
            self.__setupAppServerSocketIO()
            self.__identifyRobotToAppServer()
            self.__getRobotID()
            self.__getVideoSettings()
            self.appServerSocketIO.on('robot_settings_changed', self.__onVideoSettingsChanged)
            count = 0
            while not self.shutdownEvent.is_set():
                self.appServerSocketIO.wait(seconds=1)
                keepAlive = {'send_video_process_exists': True, 'ffmpeg_process_exists': True, 'camera_id':self.videoSettings.cameraID}
                self.logger.debug("Sending keepAlive: send_video_status, %s" % (keepAlive))
                self.appServerSocketIO.emit('send_video_status', keepAlive)
                if((self.videoSettings.videoEnabled == True) and (self.videoProcess is not None)):
                    pass
                    #self.logger.debug("Video process output begin")
                    #self.logger.debug("Video Out: %s" %(self.videoProcess.stdout.readline()))
                    #self.logger.debug("Video Err: %s" %(self.videoProcess.stderr.readline()))
                    #self.logger.debug("Video process output end")
                if((self.videoSettings.audioEnabled == True) and (self.audioProcess is not None)):
                    pass
                    #self.logger.debug("Audio process output begin")
                    #self.logger.debug("Audio Out: %s" %(self.audioProcess.stdout.readline()))
                    #self.logger.debug("Audio Err: %s" %(self.audioProcess.stderr.readline()))
                    #self.logger.debug("Audio process output end")
                
                if(self.videoSettings.videoEnabled == True and (self.videoProcess is None or self.videoProcess.poll() != None)):
                    self.logger.debug("Video process is not running. Attempting to (re)start")
                    time.sleep(5)
                    self.videoProcess = self.__startVideoCaptureLinux()
                if(self.videoSettings.audioEnabled == True and (self.audioProcess is None or self.audioProcess.poll() != None)):
                    self.logger.debug("Audio process is not running. Attempting to (re)start")
                    time.sleep(5)
                    self.audioProcess = self.__startAudioCaptureLinux()
                if((count % 60) == 0):
                    self.__identifyRobotToAppServer()
                count += 1
                
                if(self.requireRestart == True):
                    self.__getVideoSettings()
                    self.__killProcesses()
                    self.requireRestart = False
        except Exception as e:
            logging.exception("VideoServerOutbound encountered an error")
            raise e
        finally:
            self.__killProcesses()
    
    
    def __setupAppServerSocketIO(self):
        self.logger.debug("Setting up socket IO for app server using URL %s:%s" %(self.videoSettings.serverURL, self.videoSettings.serverPort))
        self.appServerSocketIO = SocketIO(self.videoSettings.serverURL, self.videoSettings.serverPort, LoggingNamespace)
    
    def __getVideoPort(self):
        url = 'https://{}/get_video_port/{}'.format(self.videoSettings.serverURL, self.videoSettings.cameraID)
        self.logger.debug("Getting video port from url: %s" % (url))
        response = ServerHelper.getWithRetry(url)
        videoPort = json.loads(response)['mpeg_stream_port']
        self.logger.debug("Received video port %s" % (videoPort))
        return videoPort
    
    def __getAudioPort(self):
        url = 'https://{}/get_audio_port/{}'.format(self.videoSettings.serverURL, self.videoSettings.cameraID)
        self.logger.debug("Getting audio port from url: %s" % (url))
        response = ServerHelper.getWithRetry(url)
        audioPort = json.loads(response)['audio_stream_port']
        self.logger.debug("Received audio port %s" % (audioPort))
        return audioPort
    
    def __getRobotID(self):
        url = 'https://{}/get_robot_id/{}'.format(self.videoSettings.serverURL, self.videoSettings.cameraID)
        self.logger.debug("Getting robot id from url: %s" % (url))
        response = ServerHelper.getWithRetry(url)
        self.robotID = json.loads(response)['robot_id']
        self.logger.debug("Received robot id %s" % (self.robotID))
    
    def __getWebsocketRelayHost(self):
        url = 'https://{}/get_websocket_relay_host/{}'.format(self.videoSettings.serverURL, self.videoSettings.cameraID)
        self.logger.debug("Getting websocket relay from url: %s" % (url))
        response = ServerHelper.getWithRetry(url)
        websocketRelay = json.loads(response)
        self.logger.debug("Received websocket relay %s" % (websocketRelay))
        return websocketRelay['host']
    
    def __getVideoSettings(self):
        url = 'https://{}/api/v1/robots/{}'.format(self.videoSettings.apiServer, self.robotID)
        self.logger.debug("Getting video settings from url: %s" % (url))
        response = ServerHelper.getWithRetry(url)
        result = json.loads(response)
        self.logger.debug("Received video settings %s" % (result))
        if(self.videoSettings.allowServerOverride == True):
            if 'xres' in result:
                self.videoSettings.xres = result['xres']
            else:
                self.logger.warn("Server did not send 'xres' in video settings")
            if 'yres' in result:
                self.videoSettings.yres = result['yres']
            else:
                self.logger.warn("Server did not send 'yres' in video settings.")
        return result
    
    def __identifyRobotToAppServer(self):
        self.logger.debug("Sending robot id %s to appServerSocketIO" % (self.robotID))
        self.appServerSocketIO.emit('identify_robot_id', self.robotID)
    
    def __onVideoSettingsChanged(self, *args):
        self.logger.debug("Video settings changed beginning video/audio restart process")
        self.requireRestart = True
        #TODO: Actually Change the settings
        pass
    
    def __startVideoCaptureLinux(self):
        videoCommandLine = self.videoSettings.getVideoCommand(self.__getWebsocketRelayHost(), self.__getVideoPort())
        self.logger.debug("Starting ffmpeg video with command %s" % (videoCommandLine))
        return subprocess.Popen(shlex.split(videoCommandLine)) #TODO: Find a better way to log output
    
    def __startAudioCaptureLinux(self):
        audioCommandLine = self.videoSettings.getAudioCommand(self.__getWebsocketRelayHost(), self.__getAudioPort())
        self.logger.debug("Starting ffmpeg audio with command %s" % (audioCommandLine))
        return subprocess.Popen(shlex.split(audioCommandLine))#TODO: Find a better way to log output , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    def __killProcesses(self):
        self.logger.debug("Killing processes")
        if self.videoProcess is not None:
            self.logger.debug("Killing video process")
            self.videoProcess.kill()
        if self.audioProcess is not None:
            self.logger.debug("Killing video process")
            self.audioProcess.kill()