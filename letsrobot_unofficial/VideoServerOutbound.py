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
        self.streamSettings = None
        pass
    
    def run(self):
        videoProcess = None
        audioProcess = None
        try:
            self.__setupAppServerSocketIO()
            self.__identifyRobotToAppServer()
            self.__getRobotID()
            self.streamSettings = self.__getVideoSettings()
            self.appServerSocketIO.on('robot_settings_changed', self.__onVideoSettingsChanged)
            count = 0
            while not self.shutdownEvent.is_set():
                self.appServerSocketIO.wait(seconds=1)
                self.appServerSocketIO.emit('send_video_status', {'send_video_process_exists': True, 'ffmpeg_process_exists': True, 'camera_id':self.videoSettings.cameraID})
                if((self.videoSettings.videoEnabled == True) and (videoProcess is not None)):
                    out, err = videoProcess.communicate()
                    self.logger.debug("Video process output begin")
                    self.logger.debug(out)
                    self.logger.debug(err)
                    self.logger.debug("Video process output end")
                if((self.videoSettings.audioEnabled == True) and (audioProcess is not None)):
                    out, err = audioProcess.communicate()
                    self.logger.debug(out)
                    self.logger.debug(err)
                
                if(self.videoSettings.videoEnabled == True and (videoProcess is None or videoProcess.poll() != None)):
                    self.logger.debug("Video process is not running. Attempting to (re)start")
                    time.sleep(5)
                    videoProcess = self.__startVideoCaptureLinux()
                if(self.videoSettings.audioEnabled == True and (audioProcess is None or audioProcess.poll() != None)):
                    self.logger.debug("Audio process is not running. Attempting to (re)start")
                    time.sleep(5)
                    audioProcess = self.__startAudioCaptureLinux()
                if((count % 60) == 0):
                    self.__identifyRobotToAppServer()
                count += 1
        except Exception as e:
            logging.exception("VideoServerOutbound encountered an error")
            raise e
        finally:
            if videoProcess is not None:
                videoProcess.kill()
            if audioProcess is not None:
                audioProcess.kill()
    
    
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
        return result
    
    def __identifyRobotToAppServer(self):
        self.logger.debug("Sending robot id %s to appServerSocketIO" % (self.robotID))
        self.appServerSocketIO.emit('identify_robot_id', self.robotID)
    
    def __onVideoSettingsChanged(self, *args):
        self.logger.debug("Video settings changed")
        self.__getVideoSettings()
        #TODO: Actually Change the settings
        pass
    
    def __startVideoCaptureLinux(self):
        videoCommandLine = self.videoSettings.getVideoCommand(self.__getWebsocketRelayHost(), self.__getVideoPort())
        self.logger.debug("Starting ffmpeg video with command %s" % (videoCommandLine))
        return subprocess.Popen(shlex.split(videoCommandLine), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    def __startAudioCaptureLinux(self):
        audioCommandLine = self.videoSettings.getAudioCommand(self.__getWebsocketRelayHost(), self.__getAudioPort())
        self.logger.debug("Starting ffmpeg audio with command %s" % (audioCommandLine))
        return subprocess.Popen(shlex.split(audioCommandLine), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        