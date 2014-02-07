import sys

__progress = 0.0


def setProgress(p):
    global __progress
    __progress = p


def __updateProgress__(dp):
    global __progress
    __progress += dp
    print "\b\b\b\b\b\b\b\b%6.2f%%" % __progress,
    sys.stdout.flush()

updateProgress = __updateProgress__
