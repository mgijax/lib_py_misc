# mgi_utils.py
# a module for miscellaneous MGI tasks

import os
import string
import types
import time
import ignoreDeprecation
import sys
import tempfile
from signal import signal, alarm, SIGALRM
import runCommand
from types import *
import symbolsort

###--- Exception Information ---###
error = 'mgi_utils.error'          # standard exception raised by the module

# messages passed along when an exception is raised
# mkdirs error
IS_FILE = '"%s": Already exists as a file'

###--- Functions ---###

def mkdirs(path,                        # string, the path to make
             permissions = '0775'):     # string, octal abs permissions mode

        # Purpose: create all intermediate directories in 'path' needed to
        #               contain the leaf directory.  Set mode to 'permissions'
        # Returns: 'path' if any directories are created.
        #               'None' if path already exists
        # Assumes: 'permissions' is a valid permissions mode
        # Effects: creates directories
        #          applies 'permissions' to all directories created
        # Throws: 'error' if Unix mkdir fails or path exists as a file
        # Example 1 :
        #       path = '/home/sc/this/is/a/test'
        #       results = mkdirs.mkdirs(path, '2755')
        #       if results == None:
        #               print 'Path %s already exists' %s path
        #       else:
        #               print 'Directories created'
        # Example 2: default permissions are used
        #       results = mkdirs.mkdirs(path)


        # if 'path' not absolute, create relative to current working dir
        if not os.path.isabs(path):
                path = os.path.join(os.getcwd(), path)

        # if 'path' exists but is a file raise 'error'
        if os.path.isfile(path):
                raise error(IS_FILE % path)

        # if 'path' exists return None
        if os.path.isdir(path):
                return None

        # else split 'path' into existing and non-existing sections
        else:
                # after loop dirsToCreate = all dirs in path that do not exist
                dirsToCreate = []

                # after loop head = all dirs in path that exist
                head = path

                # while the leaf dir of head does not exist
                while not os.path.isdir(head):
                        # split the leaf dir from head
                        (head, leaf) = os.path.split(head)

                        # prepend 'leaf' to dirsToCreate
                        dirsToCreate.insert(0, leaf)

        # create directories relative to head for each dir in dirsToCreate
        # with mode 'permissions'
        for dir in dirsToCreate:
                head = os.path.join(head, dir)
                cmd = 'mkdir -m %s -p %s' % (permissions, head)
                (stdout, stderr, exitCode) = runCommand.runCommand(cmd)
                if exitCode or stderr:
                       raise error(stderr)

        return head

def olddebug(object):
        sys.stderr.write(
                os.path.basename(sys.argv[0]) + ': ' + str(object) + '\n' 
                )


def AlarmClock(sig, stack):
        olddebug('TIMED OUT, environ = ' + str(os.environ))
        errors(None, 'time_out')
        os._exit(-1)


def show_count(obj):
        """Returns a string indicating number of matching items.
        #
        # Requires:
        #       obj - An integer or any object that has a __len__ method.
        #
        # Note:
        #       Used in summary and detail screens.
        """
        if type(obj) is int:
                count = obj
        else:
                try:
                        count = len(obj)
                except:
                        count = 0

        s = '%d matching item' % count
        # Add an 's' on to the end when necessary.
        if count != 1: s = s + 's'

        # TR136 change:
        if count != 0:
                s = s + ' displayed'

        return s


def plural(n, singular, plural=None):
        '''
        # INPUTS:  n - integer. 
        #          singular, plural - string
        # RETURNS: string
        # EXCEPTIONS: none
        # ASSUMES: input parameters are of expected type
        # MODIFIES: nothing
        # EFFECTS: none
        # COMMENTS: Returns a string that is in the plural form
        #  or the singular form depending on the value of n.
        #  e.g. we would want to write "1 assay" instead of "1 assays"
        '''     

        if plural is None:
                plural = singular + 's'
        if n == 1:
                str = singular
        else:
                str = plural
        return  str


def pc(count):
        """Prints a string indicating number of matching items.
        #
        # Note:
        #       This function is here only for backward compatability.  Do not
        #       use for any new software.  Use showcount() instead.
        """

        print(show_count(count))


def vali_date(date):
#
#       Validates that a date is separated into 3 parts by '/'.
#       Couldn't care less what is actually between those '/'s.
#       
        #
        #       Split on 'and' first in case from a field doing a between.
        #
        dates = string.splitfields(string.lower(date),'and')
        for index in range(len(dates)):
                date_parts = string.splitfields(dates[index],'/')
                if len(date_parts) != 3:
                        return(0)
        #
        #       Return 'true'(1) if everything ok.
        #
        return(1)


def sepa_date(date):
#
#       Separates dates that have been connected by 'and' (ie. between
#       m1/d1/y1 and m2/d2/y2).  Also strips off any leading or trailing
#       blanks.
#
        dates = string.splitfields(string.lower(date),'and')
        for i in range(len(dates)):
                dates[i] = string.strip(dates[i])
        return(dates)


def formu_date(field_name, operator, date):
#
#       Formulates where clause portion for query by date.
#       Requires the name of the fields in the database being compared to,
#       including (ie m.modification_date, for a table with defined alias m)
#       Also requires the operator being used, and the date (date must be
#       in format: m1/d1/y1 and m2/d2/y2 if using between operator)
#

        comparison = 'convert(datetime, convert(char(12),' + field_name + ',1))'

        if string.lower(operator) == 'between':
                dates = sepa_date(date)
                if len(dates) != 2:
                        return None     
                date = '"' + dates[0] + '"' + ' ' + 'and' + ' ' + '"' \
                        + dates[1] + '"'
        else:
                date = '"' + string.strip(date) + '"'

        comparison = comparison + ' ' + operator + ' ' + date
        return(comparison)


class Tee:
        """A file-like object that behaves like the Unix 'tee' command.
        #
        # This class allows yo to create a "file-like" object with multiple
        # file descriptors for logging purposes.  Just as the 'tee' command, 
        # this also writes to sys.stderr.
        #
        # Note:
        #       Make sure you use the close() method before your program exits.
        #       If you do not use the close() method, the buffer might not be
        #       flushed.
        #
        # Example (Writes to sys.stderr and 'junk.log'):
        #
        #       #!./python
        #
        #       from mgi_utils import Tee
        #
        #       tee = Tee('junk.log')
        #       tee.write('Here's some junk.\n')
        #       tee.write('Here's some more junk.\n')
        #       tee.close()
        #
        # Example (Logs sql to sys.stderr and 'junk.log'):
        #
        #       #!./python
        #
        #       
        #   import mgi_utils
        #
        #       tee = mgi_utils.Tee('junk.log')
        #       db.set_sqlLogFD(tee)
        #       results = db.sql('select count(*) from MRK_Marker',     'auto')
        #       tee.write('%s row(s) returned.\n' % len(results))
        #       tee.close()
        #
        # Implementor's note:
        #       One obvious thing this *should* do is close files automatically
        #       in the destructor (__del__).  Unfortunately, Python seems to
        #       have strange behaviour in the destructor and we cannot count on
        #       it getting called properly.
        #
        """

        def __init__(self, path, mode='w'):
                """Construct a Tee object.
                #
                # Requires:
                #       path -- A string representing the file path.
                #       mode -- 'w' or 'a'.  The default ('w') is to write over
                #               the file if it already exists.  Append ('a')
                #               mode adds the output to the end of the file.
                """
                self.fd = open(path, mode)

        def write(self, s):
                """Writes a string (s).
                #
                # Requires:
                #       s -- A string.
                #
                """
                # Always write to sys.stderr.
                sys.stderr.write(s)

                if self.fd is not sys.stderr:
                        self.fd.write(s)

        def close(self):
                """Closes file unless it is a tty(-like) device."""
                if not self.fd.isatty():
                        self.fd.close()


def value(object):
        if object is None:
                return 'null'
        else:
                return str(object)


def strval(object):
        if object is None:
                return 'null'
        else:
                return '"' + str(object) + '"'


def prstar(object):
        if object is None:
                return '*'
        else:
                return str(object)


def prvalue(object):
        if object is None:
                return ''
        else:
                return str(object)


def date( format = '%c' ):
        """Returns the current date and time in a nice format.
        #
        # Requires:
        #       format - an optional string of arguments (see man strftime(3)
        #               for instructions).  The default is '%c' (normal format).
        #
        # Example:
        #
        #       Here's how to print the current month:
        #
        #               print mgi_utils.date( '%B' )
        #
        # Hint:
        #       You can put other characters in the format string, as in
        #
        #               print mgi_utils.date( '<STRONG>%m/%d/%y</STRONG>' )
        """
        try:
                s = time.strftime( format, time.localtime(time.time()) )
        except:
                s = 'Error:  mgi_utils.date( ' + str(format) + ' )'
        return s

def setAlarm(timeout, alarmclock=AlarmClock):
        # Schedule a UNIX alarm call after timeout seconds
        signal(SIGALRM, alarmclock)
        alarm(timeout)

def addQuotes (list):
        # return a copy of list, with each element in double quotes
        return ['"%s"' % x for x in list]

def joinPaths (*item):
        # Purpose: join all the items passed in into one path, which we return
        # Returns: string; see Purpose
        # Assumes: nothing
        # Effects: nothing
        # Throws: nothing
        # Notes: The same rules which apply to os.path.join() apply here.
        #       The most interesting case is:
        #               a = '/a/b/c'
        #               b = '/d/e/f'
        #               joinPaths (a, b) ==> '/d/e/f'
        #       This is because any full path on the right causes any path on
        #       the left to be ignored.

        s = ''
        for i in item:
                s = os.path.join (s, i)
        return s


###--- Template string for generating e-mail file, for send_Mail() ---###

MAIL_FILE = '''From: %s
To: %s
Subject: %s

%s
'''

def send_Mail (
        send_from,      # e-mail address sending the message
        send_to,        # e-mail address to which to send the message
        subject,        # e-mail subject line
        message,        # text of the e-mail message
        config = None   # dict with key 'SENDMAIL' whose value is full
                        #  pathname of the sendmail executable.
        ):
        # Purpose: produce and send an e-mail message from 'send_from' to
        #       'send_to' with the given 'subject' and 'message'
        # Returns: integer; 0 if sent okay, non-zero return code from sendmail
        #       if some error
        # Assumes: nothing
        # Effects: If 'config' is not None, config.get('SENDMAIL') will
        #       be invoked to send the mail. If it is None, we default
        #       to /usr/lib/sendmail.
        # Throws: Propogates IOError if an error occurs in sending stuff
        #       to sendmail.

        # provide a default for sendmail and allow the config file to override

        sendmail = '/usr/lib/sendmail'
        if (config != None and 'SENDMAIL' in config):
                sendmail = config['SENDMAIL']

        # build a unique temporary filename

        tempfile.template = 'mailfile.'
        filename = tempfile.mktemp()

        # write the file

        fp = open (filename, 'w')
        fp.write (MAIL_FILE % (send_from, send_to, subject, message))
        fp.close()

        # pipe the file into sendmail

        stdout, stderr, code = runCommand.runCommand ('cat %s | %s -t' % \
                (filename, sendmail))

        # cleanup and exit with the status code

        os.remove (filename)
        return code
# end send_Mail ------------------------------------------

def askUserForOneChar (
        question,               # string; a message posing a question.
        okAnswers = 'yn'        # string; acceptable single char answers
        ):
        # Purpose: Ask user the 'question' and keep asking til
        #          we get a single char answer in 'okAnswers'.
        # Returns: string: the answer or None if EOF
        # Assumes: nothing
        # Effects: Uses raw_input, trapping EOFError. Keeps asking til the
        #           user gives an "okAnswer'.
        # Throws : nothing

        ans = ""
        while (ans == ""):
                try:
                        ans = input( question + " [%s] " % okAnswers)
                except EOFError :
                        ans = None
                        break

                if (len(ans) != 1 or ans not in okAnswers):
                        ans = ""
        return ans
# end askUserForOneChar() ----------------------------------

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
