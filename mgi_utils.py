'''
# mgi_utils.py - A module for miscellaneous MGI tasks
# 
# (not web-interface specific, but may be for processing/generating html)
'''

import os
import string
import time
import regex
import cgi
import urllib
import sys
from signal import signal, alarm, SIGALRM


# Aliases
#########
url_unescape = urllib.unquote	# For backward compatability


# Functions
###########

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
	#	obj - An integer or any object that has a __len__ method.
	#
	# Note:
	#	Used in summary and detail screens.
	"""
	if type(obj) is type(0):
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
	#	   singular, plural - string
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
	return 	str


def pc(count):
	"""Prints a string indicating number of matching items.
	#
	# Note:
	# 	This function is here only for backward compatability.  Do not
	#	use for any new software.  Use showcount() instead.
	"""

	print show_count(count)


def mgiCopyright():
	"""Returns a string representation of the copyright for web pages."""

	s = '''\
<HR>
<SMALL><H3>WARRANTY DISCLAIMER AND COPYRIGHT NOTICE</H3>
THE JACKSON LABORATORY MAKES NO REPRESENTATION ABOUT THE SUITABILITY OR
ACCURACY OF THIS SOFTWARE OR DATA FOR ANY PURPOSE, AND MAKES NO WARRANTIES,
EITHER EXPRESS OR IMPLIED, INCLUDING THE WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE OR THAT THE USE OF THIS SOFTWARE OR DATA
WILL NOT INFRINGE ANY THIRD PARTY PATENTS, COPYRIGHTS, TRADEMARKS OF OTHER
RIGHTS.  IT IS PROVIDED "AS IS."
<P>
This software and data are provided as a service to the scientific community
to be used only for research and educational purposes.  Any commercial
reproduction is prohibited without the prior written permission of The
Jackson Laboratory.
<P>
</SMALL>
Copyright &#169 1996 The Jackson Laboratory
<BR>
All Rights Reserved
<BR>
'''
	return s


def mgiRetrieve():
	"""Returns a string representation of the retrieve button for forms."""

	s = '''\
<HR>
<INPUT TYPE=submit VALUE="Retrieve"> <INPUT TYPE=reset VALUE="Reset Form">
<HR>
'''
	return s


def mgiMaxReturn():
	"""Returns a string representation of the maxreturn section of forms."""

	s = '''\
<b>Max number of items returned:</b>
<INPUT TYPE="radio" NAME="*limit" VALUE="10">10
<INPUT TYPE="radio" NAME="*limit" VALUE="100" CHECKED>100
<INPUT TYPE="radio" NAME="*limit" VALUE="500">500
<INPUT TYPE="radio" NAME="*limit" VALUE="0">No limit
<BR>
'''
	return s


def vali_date(date):
#
#	Validates that a date is separated into 3 parts by '/'.
#	Couldn't care less what is actually between those '/'s.
#	
	#
	#	Split on 'and' first in case from a field doing a between.
	#
	dates = string.splitfields(string.lower(date),'and')
	for index in range(len(dates)):
		date_parts = string.splitfields(dates[index],'/')
		if len(date_parts) != 3:
			return(0)
	#
	#	Return 'true'(1) if everything ok.
	#
	return(1)


def sepa_date(date):
#
#	Separates dates that have been connected by 'and' (ie. between
#	m1/d1/y1 and m2/d2/y2).  Also strips off any leading or trailing
#	blanks.
#
	dates = string.splitfields(string.lower(date),'and')
	for i in range(len(dates)):
		dates[i] = string.strip(dates[i])
	return(dates)


def formu_date(field_name, operator, date):
#
#	Formulates where clause portion for query by date.
#	Requires the name of the fields in the database being compared to,
#	including (ie m.modification_date, for a table with defined alias m)
#	Also requires the operator being used, and the date (date must be
#	in format: m1/d1/y1 and m2/d2/y2 if using between operator)
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
	#	Make sure you use the close() method before your program exits.
	#	If you do not use the close() method, the buffer might not be
	#	flushed.
	#
	# Example (Writes to sys.stderr and 'junk.log'):
	#
	#	#!/usr/local/bin/python
	#
	#	from mgi_utils import Tee
	#
	#	tee = Tee('junk.log')
	#	tee.write('Here's some junk.\n')
	#	tee.write('Here's some more junk.\n')
	#	tee.close()
	#
	# Example (Logs sql to sys.stderr and 'junk.log'):
	#
	#	#!/usr/local/bin/python
	#
	#	
	#   import db 
	#   import mgi_utils
	#
	#	tee = mgi_utils.Tee('junk.log')
	#	db.set_sqlLogFD(tee)
	#	results = db.sql('select count(*) from MRK_Marker',	'auto')
	#	tee.write('%s row(s) returned.\n' % len(results))
	#	tee.close()
	#
	# Implementor's note:
	#	One obvious thing this *should* do is close files automatically
	#	in the destructor (__del__).  Unfortunately, Python seems to
	#	have strange behaviour in the destructor and we cannot count on
	#	it getting called properly.
	#
	"""

	def __init__(self, path, mode='w'):
		"""Construct a Tee object.
		#
		# Requires:
		#	path -- A string representing the file path.
		#	mode -- 'w' or 'a'.  The default ('w') is to write over
		#		the file if it already exists.  Append ('a')
		#		mode adds the output to the end of the file.
		"""
		self.fd = open(path, mode)

	def write(self, s):
		"""Writes a string (s).
		#
		# Requires:
		#	s -- A string.
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


def get_fields(content = None):
	"""Processes fields from an HTML form.
	#
	# Requires:
	#	content -- A string containing form content.  A value of None
	#		(default) means to read from sys.stdin.
	#
	# Effects:
	#	- Reads from sys.stdin
	#	
	# Note:
	#	This needs work big-time.
	#
	"""
	fields = {}
	operators = {}
	types = {}
	negates = {}

	# Note -- httpd 1.3 does not close stdin
	# read exactly CONTENT_LENGTH bytes or the script will hang
	if content is None:
		length = string.atoi(os.environ['CONTENT_LENGTH'])
		content = sys.stdin.read(length)

	tokens = string.splitfields(content, '&')
	for i in range(0, len(tokens)):
		mapping = string.splitfields(string.joinfields(
			string.splitfields(string.strip(tokens[i]), '+'), ' '),
			'=')
		mapping[1] = string.strip(url_unescape(mapping[1]))
		if mapping[1] == '':
			continue
		mapping = url_unescape(mapping[0]), mapping[1]
		type = string.splitfields(mapping[0], ':')
		if len(type) == 1:
			fields[type[0]] = mapping[1]
		elif type[0] == 'op':
			operators[type[1]] = mapping[1]
		elif type[0] == 'not':
#
#	Grabs all of fields that have a "checked" NOT operator.
#
			negates[type[1]] = mapping[1]
		elif type[0] == 'list':
			key = type[1]
			if fields.has_key(key) == 0:
				fields[key] = []
			fields[key].append(mapping[1])
		else:
			fields[type[1]] = mapping[1]
			types[type[1]] = type[0]
	for key in fields.keys():
		if types.has_key(key) and operators.has_key(key):
			operator = operators[key]
			if string.lower(operator) == 'is null':
				del fields[key]
				continue
			if key == 'symbol':
				l = string.split(fields[key], ',')
				for i in range(len(l)):
					l[i] = string.strip(l[i])

				if operator == 'begins':
					for i in range(len(l)):
						l[i] = l[i] + '%'
				elif operator == 'ends':
					for i in range(len(l)):
						l[i] = '%' + l[i]
				elif operator == 'contains':
					for i in range(len(l)):
						l[i] = '%' + l[i] + '%'
				elif string.lower(operator) == 'is null':
					del fields[key]
					continue
				else:
					fields[key] = l
					continue
				fields[key] = l
				operators[key] = 'like'
			elif types[key] == 'text':
				if operator == 'begins':
					fields[key] = fields[key] + '%'
				elif operator == 'ends':
					fields[key] = '%' + fields[key]
				elif operator == 'contains':
					fields[key] = '%' + fields[key] + '%'
				elif string.lower(operator) == 'is null':
					del fields[key]
					continue
				else:
					continue
				operators[key] = 'like'
#
#	Where NOT has been used alter the operator accordingly.
#
	for key in negates.keys():
		if operators.has_key(key):
			operator = operators[key]
			if operator == '=':
				operators[key] = '!' + operators[key]
			elif operator == 'like':
				operators[key] = 'not' + ' ' + operators[key]
			elif string.lower(operator) == 'is null':
				operators[key] = 'is not null'
	result =  fields, operators, types
	#olddebug(result)
	return result


def print_field(label, value):
	sys.stdout.write('<B>%s</B>\t' % label)
	if value is None:
		print  'NULL'
	else:
		print str(value)
	print '<BR>'


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


def escape(html):
	"""Escapes '&', '<' and '>' characters as SGML entities.
	#
	# Note:
	#	This was repaired in 10/97 to escape the '&' properly.  It was
	#	not being done before that.
	"""
	if html is not None and type(html) is type(''):
		html = cgi.escape(html)
	else:
		html = ''
	return html


def date( format = '%c' ):
	"""Returns the current date and time in a nice format.
	#
	# Requires:
	#	format - an optional string of arguments (see man strftime(3)
	#		for instructions).  The default is '%c' (normal format).
	#
	# Example:
	#
	#	Here's how to print the current month:
	#
	#		print mgi_utils.date( '%B' )
	#
	# Hint:
	#	You can put other characters in the format string, as in
	#
	#		print mgi_utils.date( '<STRONG>%m/%d/%y</STRONG>' )
	"""
	try:
		s = time.strftime( format, time.localtime(time.time()) )
	except:
		s = 'Error:  mgi_utils.date( ' + str(format) + ' )'
	return s


def byNumeric( a, b ):
	"""String comparison that compares numeric substrings separately.
	#
	# Requires:
	#       a, b - strings
	#
	# Example:
	#	Here's how to sort a list of marker symbols:
	#
	#		l.sort( mgi_utils.byNumeric )
	#
	# Bugs:
	#	- In some cases, substrings are converted to lower case, which
	#	  can give random results back (see code).
	#	- Also, it's kinda slow.  :-)
	#	- If either of the strings contain numeric substrings that are
	#	  too big for string.atoi to handle, an exception is raised.
	#
	# It's slow because passing any comparison function to the list sort
	# method slows things to a crawl.
	#
	# Note:
	#	Hao has written a new version of this that is being tested.
	"""
 
        def getIndex( s ): # returns the length of the first chunk.
                if s[:1] in map( None, string.digits ):
                        result = regex.search( '[^0-9]', s )
                else:
                        result = regex.search( '[0-9]', s )
		if result < 0: # It's the last chunk in the string.
			result = len( s )
		return result
 
	if type(a) != type('') or type(b) != type(''):
		return cmp(a,b)

        indexA = getIndex( a )
        indexB = getIndex( b )
        DIGITS = map( None, string.digits )
 
	if a == b: # not necessary, but maybe speeds things up!
		result = 0
        elif a[:indexA] == b[:indexB]:
                if len( a ) == indexA:
                        if len( b ) == indexB:
                                result = 0
                        else:
                                result = -1
                elif len( b ) == indexB:
                        result = 1
                else:
                        result = bySymbol( a[indexA:], b[indexB:] )
        elif a[:1] in DIGITS and b[:1] in DIGITS:
                result = cmp( string.atoi(a[:indexA]), string.atoi(b[:indexB]) )
        else:   # This returns can random results (eg. ren1 =? Ren1)
                # OK if data is already in a reasonable order though.
                result = cmp(string.lower(a[:indexA]),string.lower(b[:indexB]))

	return result

# aliases
byFilename = byNumeric
bySymbol = byNumeric

def setAlarm(timeout, alarmclock=AlarmClock):
	# Schedule a UNIX alarm call after timeout seconds
	signal(SIGALRM, alarmclock)
	alarm(timeout)
#
# WARRANTY DISCLAIMER AND COPYRIGHT NOTICE 
#
#    THE JACKSON LABORATORY MAKES NO REPRESENTATION ABOUT THE 
#    SUITABILITY OR ACCURACY OF THIS SOFTWARE OR DATA FOR ANY 
#    PURPOSE, AND MAKES NO WARRANTIES, EITHER EXPRESS OR IMPLIED, 
#    INCLUDING THE WARRANTIES OF MERCHANTABILITY AND FITNESS FOR 
#    A PARTICULAR PURPOSE OR THAT THE USE OF THIS SOFTWARE OR DATA 
#    WILL NOT INFRINGE ANY THIRD PARTY PATENTS, COPYRIGHTS, 
#    TRADEMARKS OF OTHER RIGHTS. IT IS PROVIDED "AS IS." 
#
#    This software and data are provided as a service to the scientific 
#    community to be used only for research and educational purposes. Any
#    commercial reproduction is prohibited without the prior written 
#    permission of The Jackson Laboratory. 
#
#    Copyright © 1996 The Jackson Laboratory All Rights Reserved 
#
