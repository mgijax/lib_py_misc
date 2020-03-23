# Name: log.py
# Purpose: provides a quick-and-dirty module for logging debugging messages

import time
import sys

_startTime = time.time()     # time the module was imported, in ms
_active = False              # write logs (True) or not (False)

def on():
    # Turn on logging.
    global _active
    _active = True

def off():
    # Turn on logging.
    global _active
    _active = False

def write(message):
    # write the given message out to the log (if logging is on).
    if _active:
        sys.stderr.write('%6.2f sec : ' % ((time.time() - _startTime) / 1000.0))
        sys.stderr.write(message)
        sys.stderr.write('\n')
        sys.stderr.flush()