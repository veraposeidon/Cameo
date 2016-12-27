# coding=utf-8
import cv2
import numpy
import time


class CaptureManager(object):
    def __init__(self, capture, previewWindowManager=None, shouldMirrorPreview=False):
        self.previewWindowManager = previewWindowManager
        self.shouldMirrorPreview = shouldMirrorPreview

        self._capture = capture
        self._channel = 0
        self._enteredFrame = False
        self._frame = None
        self._imageFilename = None
        self._videoFilename = None
        self._videoEncoding = None
        self._videoWriter = None

        # starttime 不能初始化为None,否则无法赋值
        # self._startTime = None
        self._startTime = time.time()

        self._frameElapsed = long(0)
        self._fpsEstimate = None

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        if self._channel != value:
            self._channel = value
            self._frame = None

    @property
    def frame(self):
        if self._enteredFrame and self._frame is None:
            _, self._frame = self._capture.retrieve()
        return self._frame

    @property
    def is_writingimage(self):
        return self._imageFilename is not None

    @property
    def is_writingvideo(self):
        return self._videoFilename is not None

    def enterframe(self):
        """获取下一帧"""

        # 但是首先检查没有之前的帧存在
        assert not self._enteredFrame, \
            'previous enterFrame() had no matching exitFrame()'

        if self._capture is not None:
            self._enteredFrame = self._capture.grab()

    def exitframe(self):
        """画窗口，写文件，释放帧"""

        # Check whether any grabbed frame is retrievable
        # The getter may retrieve and cache the frame
        if self.frame is None:
            self._enteredFrame = False
            return

        if self._frameElapsed == 0:
            self._startTime == time.time()
        else:
            timeElapsed = time.time() - self._startTime
            self._fpsEstimate = self._frameElapsed / timeElapsed

        self._frameElapsed += 1

        # Draw to the Window,if any.
        if self.previewWindowManager is not None:
            if self.shouldMirrorPreview:
                mirrored_frame = numpy.fliplr(self._frame).copy()
                self.previewWindowManager.show(mirrored_frame)
            else:
                self.previewWindowManager.show(self._frame)

        # Write to the image file, if any.
        if self.is_writingimage:
            cv2.imwrite(self._imageFilename, self._frame)
            self._imageFilename = None

        # write to the Video file,if any
        self._writevideoframe()

        # release the Frame
        self._frame = None
        self._enteredFrame = False

    def writeimage(self, filename):
        """Write the next frame to an image file"""
        self._imageFilename = filename

    def start_writinvideo(self, filename, encoding=cv2.VideoWriter_fourcc('I', '4', '2',
                                                                          '0')):  # cv2.VideoWriter_fourcc('I', '4', '2', '0')
        """Start Writing existed frame to a video file"""
        self._videoFilename = filename
        self._videoEncoding = encoding

    def stop_writingvideo(self):
        """stop Writing exited frames to a video file"""
        self._videoFilename = None
        self._videoEncoding = None
        self._videoWriter = None

    def _writevideoframe(self):
        if not self.is_writingvideo:
            return
        if self._videoWriter is None:
            fps = self._capture.get(cv2.CAP_PROP_FPS)
            if fps == 0.0:
                # FPS未知，进行估计
                if self._frameElapsed < 20:
                    # wait until more frame elapse so that the estimate is more stable.
                    return
                else:
                    fps = self._fpsEstimate
                    # print fps
            size = (int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            self._videoWriter = cv2.VideoWriter(self._videoFilename, self._videoEncoding, fps, size)

        self._videoWriter.write(self._frame)


class WindowsManager(object):
    def __init__(self, window_name, keypress_callback=None):
        self.keypressCallback = keypress_callback
        self._window_name = window_name
        self._isWindowCreated = False

    @property
    def is_window_created(self):
        return self._isWindowCreated

    def create_window(self):
        cv2.namedWindow(self._window_name)
        self._isWindowCreated = True

    def show(self, frame):
        cv2.imshow(self._window_name, frame)

    def destroy_window(self):
        cv2.destroyWindow(self._window_name)
        self._isWindowCreated = False

    def process_events(self):
        keycode = cv2.waitKey(1)
        if self.keypressCallback is not None and keycode != -1:
            keycode &= 0xFF
            self.keypressCallback(keycode)
