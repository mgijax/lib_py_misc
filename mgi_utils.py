#
# mgi_utils.py
# a module for miscellaneous MGI tasks
#
# 11/15/2023    lec
#       removed all but 3 that are still used
#
# current functions:
# def prvalue() : used by some reports_db, qcreports_db
# def date()    : used in data loads, reports_db, qreports_db
# def send_Mail() : used by mgihome only
#

import os
import time
import sys
import tempfile
import runCommand

###--- Functions ---###

def prvalue(object):
        if object is None:
                return ''
        else:
                return str(object)

def date( format = '%c' ):
        """
        # Returns the current date and time in a nice format.
        #
        # Requires:
        #       format - an optional string of arguments (see man strftime(3) for instructions).  
        #       The default is '%c' (normal format).
        #
        # Example:
        #
        #       Here's how to print the current month:
        #               print mgi_utils.date( '%B' )
        #
        # Hint:
        #       You can put other characters in the format string, as in
        #               print mgi_utils.date( '<STRONG>%m/%d/%y</STRONG>' )
        """
        try:
                s = time.strftime( format, time.localtime(time.time()) )
        except:
                s = 'Error:  mgi_utils.date( ' + str(format) + ' )'
        return s

###--- Template for generating e-mail file, for send_Mail() ---###

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
        config = None   # dict with key 'SENDMAIL' whose value is full pathname of the sendmail executable.
        ):
        # Purpose: produce and send an e-mail message from 'send_from' to 'send_to' with the given 'subject' and 'message'
        # Returns: integer; 0 if sent okay, non-zero return code from sendmail if some error
        # Assumes: nothing
        # Effects: If 'config' is not None, config.get('SENDMAIL') will be invoked to send the mail. 
        #       If it is None, we default to /usr/lib/sendmail.
        # Throws: Propogates IOError if an error occurs in sending stuff to sendmail.

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

        stdout, stderr, code = runCommand.runCommand ('cat %s | %s -t' % (filename, sendmail))

        # cleanup and exit with the status code

        os.remove (filename)
        return code
# end send_Mail ------------------------------------------

