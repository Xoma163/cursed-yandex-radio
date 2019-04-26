import sys
import time


class Logger:
    def __init__(self):
        self.DEBUG = True
        self.STATUS = True
        self.FEEDBACK = True
        self.ERROR = True

    @staticmethod
    def timestamp():
        return time.strftime('[%d %b %Y %H:%M:%S] ', time.localtime())

    def debug(self, info):
        if self.DEBUG:
            with open('debug.log', 'a') as f:
                if sys.version_info[0] < 3:
                    info = info.encode('utf-8')
                f.write(self.timestamp() + info + '\n')

    def status(self, info):
        if self.STATUS:
            with open('status.log', 'a') as f:
                if sys.version_info[0] < 3:
                    info = info.encode('utf-8')
                f.write(self.timestamp() + info + '\n')

    def feedback(self, info):
        if self.FEEDBACK:
            with open('feedback.log', 'a') as f:
                if sys.version_info[0] < 3:
                    info = info.encode('utf-8')
                f.write(self.timestamp() + info + '\n')

    def error(self, info):
        if self.ERROR:
            with open('error.log', 'a') as f:
                if sys.version_info[0] < 3:
                    info = info.encode('utf-8')
                f.write(self.timestamp() + info + '\n')
