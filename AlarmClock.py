
# Name: AlarmClock.py
# Purpose: provides an easy mechanism for scheduling the execution of a
#       certain function at some point in the future; this would be very
#       useful when dealing with setting a timeout for some operations.
# On Import: instantiates 'alarmClock', an object for use only within this
#       module
# Notes:
#       Interaction with this module should occur through the three public
#       functions -- set, clear, and reset.
#
#       At present, only one alarm may be set at a time.  This is due to the
#       fact that signal.alarm() will only handle one scheduled SIGALRM at
#       a time.  In the future, it might be good to code an event queue which
#       would allow us to schedule multiple alarms, but it doesn't seem to be
#       a real need at this point.

import signal

###--- Public Global Variables ---###

error = 'AlarmClock.error'      # exception to be raised w/in this module
timeUp = 'AlarmClock.timeUp'    # exception to be raised when the alarm sounds

###--- Public Functions ---###

def set (sec,           # integer; how many secs ahead do you want the alarm?
        fn = None       # function; what function to call when the alarm
                        #       sounds.  if None, the 'timeUp' exception is
                        #       raised when the alarm sounds.
        ):
        # Purpose: set an alarm to sound 'sec' seconds in the future.  If the
        #       caller defines 'fn', then we invoke that function when the
        #       alarm sounds.  If 'fn' is None, then we raise the 'timeUp'
        #       exception.
        # Returns: nothing
        # Assumes: nothing
        # Effects: alters the global 'alarmClock'
        # Throws: 1. 'timeUp' if the alarm sounds and 'fn' is None;
        #       2. 'error' if we try to 'set' an alarm while another is
        #       already pending.
        # Notes: Remember that signal handling functions should accept exactly
        #       two parameters -- an integer signal number and a stack frame.
        #       So, 'fn' should accept two parameters whether you do anything
        #       with them or not.
        global alarmClock

        alarmClock.setAlarm (sec, fn)
        return

def clear ():
        # Purpose: clear any alarm that may currently be set
        # Returns: nothing
        # Assumes: nothing
        # Effects: alters the global 'alarmClock'
        # Throws: nothing
        global alarmClock

        alarmClock.clearAlarm()
        return

def reset (sec,         # integer; how many secs ahead do you want the alarm?
        fn = None       # function; what function to call when the alarm
                        #       sounds.  if None, the 'timeUp' exception is
                        #       raised when the alarm sounds.
        ):
        # Purpose: clears any currently pending alarm and sets a new one for
        #       the given parameters
        # Returns: nothing
        # Assumes: nothing
        # Effects: alters the global 'alarmClock'
        # Throws: propagates 'timeUp' and 'error' exceptions from the 'set()'
        #       function above
        global alarmClock

        alarmClock.clearAlarm()
        alarmClock.setAlarm (sec, fn)
        return

def alreadySet ():
        # Purpose: test to see if there's already an alarm set to occur
        # Returns: boolean (0/1).  1 if an alarm is pending, 0 if no alarm
        #       is currently scheduled.
        # Assumes: nothing
        # Effects: nothing
        # Throws: nothing

        return alarmClock.isPending()

###--- Private Class ---###

class AlarmClock:
        # IS:   an alarm clock, allowing one function call to be scheduled a
        #       certain number of seconds in the future
        # HAS:  a function and a number of seconds to elapse before that
        #       function should be invoked (precisely one of each)
        # DOES: provides methods for setting and clearing alarms
        #
        # Notes: This class is intended to be a singleton -- if you
        #       instantiate more than one AlarmClock object, the behavior of
        #       each is not guaranteed.

        def __init__ (self):
                # Purpose: instantiates the object
                # Returns: nothing
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                # currently scheduled alarm, as a number of seconds:
                self.alarmTime = None

                # the default signal handler for SIGALRM, because we only
                # want to catch that signal when we are expecting an alarm.
                # Otherwise, we want the signal to go to the default handler:
                self.signalHandler = signal.getsignal (signal.SIGALRM)

                # the function the user desires to call when the alarm sounds.
                # By default, we will invoke a method to raise the 'timeUp'
                # exception:
                self.userFunction = self.raiseException
                return

        def clearAlarm (self):
                # Purpose: clears any currently set alarm, and lets any
                #       SIGALRM signals go to the default handler
                # Returns: nothing
                # Assumes: nothing
                # Effects: changes the current handler for SIGALRM
                # Throws: nothing

                signal.alarm (0)
                self.alarmTime = None
                signal.signal (signal.SIGALRM, self.signalHandler)
                return

        def setAlarm (self,
                sec,            # integer; how many secs ahead do you want
                                # the alarm?
                userFn = None   # function; what function to call when the
                                # alarm sounds.  if None, the 'timeUp'
                                # exception is raised when the alarm sounds.
                ):
                # Purpose: set an alarm 'sec' seconds into the future, at
                #       which time we will invoke the given 'userFn'.  If
                #       'userFn' is None, then we will instead raise the
                #       'timeUp' exception when the alarm sounds.
                # Returns: nothing
                # Assumes: nothing
                # Effects: changes the signal handler for SIGALRM
                # Throws: 'error' if an alarm has already been scheduled and
                #       is still pending

                if self.alarmTime:
                        raise error('An alarm has already been set.')
                self.alarmTime = sec
                self.setCallback (userFn)
                signal.signal (signal.SIGALRM, self.invokeHandler)
                signal.alarm (self.alarmTime)
                return

        def setCallback (self,
                fn              # function to call when the alarm sounds (or
                                # None, see Notes below)
                ):
                # Purpose: to set the function to call when the alarm sounds
                # Returns: nothing
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing
                # Notes: if 'fn' is None, then we set the default alarm
                #       handler -- to raise a 'timeUp' exception when the
                #       alarm sounds.

                if fn:
                        self.userFunction = fn
                else:
                        self.userFunction = self.raiseException
                return

        def invokeHandler (self,
                signal,         # integer; signal number (ignored)
                stack           # None or stack frame (ignored)
                ):
                # Purpose: to be called when an alarm sounds -- clears the
                #       information about that alarm and then invokes the
                #       function set as a callback
                # Returns: whatever the callback function returns
                # Assumes: nothing
                # Effects: whatever the callback function does
                # Throws: propagates any exceptions raised by the callback
                #       function
                # Notes: The 'signal' and 'stack' parameters are standard
                #       for functions / methods that handle signals.  We make
                #       sure to pass them on to the userFunction.

                self.clearAlarm()
                return self.userFunction (signal, stack)

        def raiseException (self,
                signal,         # integer; signal number (ignored)
                stack           # None or stack frame (ignored)
                ):
                # Purpose: serves as a default function to call when an alarm
                #       sounds -- raises the 'timeUp' exception
                # Returns: nothing
                # Assumes: nothing
                # Effects: nothing
                # Throws: 'timeUp' with a value explaining that the determined
                #       number of seconds have expired.
                # Notes: The 'signal' and 'stack' parameters are standard
                #       for functions / methods that handle signals.  For
                #       the purposes of this function, we ignore them.

                raise timeUp('The time (%s sec) has expired.' % \
                        self.alarmTime)
                return

        def isPending (self):
                # Purpose: test to see whether an alarm has been set but has
                #       not yet sounded
                # Returns: boolean (0/1).  If an alarm is still pending then
                #       1, or 0 if no alarms are currently set.
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                if self.alarmTime:
                        return 1
                return 0

###--- Private Global Variables ---###

alarmClock = AlarmClock()       # (private) object for use w/in this module

###--- Self-Testing Code ---###

if __name__ == '__main__':
        def myTest(sig, stack):
                # function to test the ability to call an arbitrary function
                print('PASS - Custom handler called here')
                raise SystemExit
                return

        # try a 2-second alarm with the default handler
        try:
                print('setting 2 second alarm')
                set (2)
                while 1:
                        pass
        except timeUp:
                print('PASS - Default handler invoked, timeUp exception raised')

        # try to set an alarm while we're still waiting for another to sound
        print()
        try:
                print('setting 10 second alarm')
                set (10)
                print('trying to set another')
                set (15)
                print('ERROR - should not get here')
        except error as value:
                print(('PASS - %s' % value))

        # note that the previous alarm is still set, then clear it
        print()
        print('clearing alarm')
        before = alreadySet()
        clear()
        after = alreadySet()
        if (before == 1) and (after == 0):
                print('PASS - alarm cleared')
        else:
                print('ERROR - alarm was not cleared appropriately')

        # set an alarm, then try to reset it using one with a custom handler
        print()
        try:
                print('setting 10-second alarm with default handler')
                set (10)
                print('overriding with 2-second alarm and custom message')
                reset (2, myTest)
                while 1:
                        pass
        except timeUp:
                print('ERROR - should not get here')

###--- end self-test ---###
#
# Warranty Disclaimer and Copyright Notice
# 
#  THE JACKSON LABORATORY MAKES NO REPRESENTATION ABOUT THE SUITABILITY OR 
#  ACCURACY OF THIS SOFTWARE OR DATA FOR ANY PURPOSE, AND MAKES NO WARRANTIES, 
#  EITHER EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY AND FITNESS FOR A 
#  PARTICULAR PURPOSE OR THAT THE USE OF THIS SOFTWARE OR DATA WILL NOT 
#  INFRINGE ANY THIRD PARTY PATENTS, COPYRIGHTS, TRADEMARKS, OR OTHER RIGHTS.  
#  THE SOFTWARE AND DATA ARE PROVIDED "AS IS".
# 
#  This software and data are provided to enhance knowledge and encourage 
#  progress in the scientific community and are to be used only for research 
#  and educational purposes.  Any reproduction or use for commercial purpose 
#  is prohibited without the prior express written permission of the Jackson 
#  Laboratory.
# 
# Copyright (c) 1996, 1999, 2002 by The Jackson Laboratory
# All Rights Reserved
#
