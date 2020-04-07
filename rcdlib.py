# Purpose: provides a means of parsing multi-record configuration files and
#	yielding object-oriented access to them
# Public Classes:
#	RcdFile
#		__init__ (filename, rcdClass, keyName)
#		__getitem__ (keyValue)
#		__len__ ()
#		items ()
#		has_key (keyValue)
#		keys ()
#		getFilename ()
#		getConstant (constantName)
#		constantItems ()
#	Rcd
#		__init__ ()
#		__delitem__ (key)
#		__getitem__ (key)
#		__setitem__ (key, value)
#		__len__ ()
#		has_key (key)
#		keys ()
#		items ()
#		add (key, value)
#		getAsList (key)
#		getAsString (key, delimiter)
#		getAsCompiledRegex (key)
# Extended Notes:
# ---------------
# The RcdFile class is designed to support multi-record configuration files.
# By this, we mean that we support configuration files containing separate
# records.  These records must have some key value.  This is analagous to a
# database table and its primary key.

# The beginning of a record is indicated with a [ on a line by itself.
# The end of a record is denoted with a ] on a line by itself.
# Fields are defined as a name = a value.  The value does not require quotes;
#	it is just anything to the right of the first equals sign on the line.
# Both field names and values are stripped to have neither leading nor
#	trailing whitespace.
# Constants may be defined outside the scope of a record by using the same
#	name = value notation.  A constant may then be cited in future lines
#	using ${name} notation.  It is possible to use $$ notation to say
#	"no, I really want a $ here -- don't evaluate the constant".  For
#	example, "xyz$${ABC}pqr" evaluates to simply "xyz${ABC}pqr"; it does
#	not try to find a value for a constant named ABC.
# The # sign indicates that the rest of the line is a comment and should be
#	ignored.
# The \ is a line continuation character.  It will join the next line to the
#	value for the current line using a single space character.
# Any fieldname, even if not specified in a given record, has a value of the
#	empty string '' by default.
# A field may have multiple values by simply defining multiple field = value
#	lines for it in a single record.

# As an example, consider the following lines (ignoring the leading # and
# space on each) to define two constants and two records, each of which has
# two fields:

# SSE = Scientific Software Engineer	# here's a constant
# PI = Principal Investigator		# and another
#
# [					# and the first record
# email = nnn
# title = ${PI} - Software Group
# ]
#
# [					# and the second record
# email = mmm
# title = ${SSE} III			# multi-valued field on multiple lines
# title = Meeting Coordinator
# ]

# Using the RcdFile and Rcd classes to parse this file would involve, for
# example:
#	people = RcdFile ('example.txt', Rcd, 'email')
#	print people['mmm']['title']
#				===> Scientific Software Engineer III

import string
import types
import re

###--- Global Variables ---###

# regular expression used to find a constant cited in a line as ${...}

variable_re = re.compile('\\${([^}]+)}')
###--- Exception Information ---###

error = 'rcdlib.error'		# exception raised in this module

# messages passed along when the exception is raised

NO_EQUALS = 'Missing an expected equals sign (=) on line %d'
BAD_CONSTANT = 'Unknown constant "%s" cited on line %d'
NON_UNIQUE = 'Encountered a duplicated key "%s" above line %d'
MISSING_KEY = 'Encountered a record with no key "%s" above line %d'
BAD_MARKUP = 'File did not terminate as expected.  Check all [, ], and \\'
PROGRAMMER_ERROR = 'Programmer error.  The program is in a bad state...'
EXTRA_OPEN = 'Encountered an extra open bracket ([) on line %d'
EXTRA_CLOSE = 'Encountered an extra closing bracket ([) on line %d'

###--- Public Classes ---###

class RcdFile:
        # IS: an OO representation of a file containing the definitions for
        #	zero or more Rcd objects
        # HAS: a filename, a set of Rcd objects, and a set of constants
        # DOES: parses a file and builds Rcd objects, then provides accessor
        #	methods to retrieve them on demand
        # Implementation:  We can think of the parsing file parsing as having
        #	three states -- IN_RCD, OUT_RCD, IN_FIELD.  We take different
        #	actions based on which state we're in.  This is all document
        #	in the __init__ function's code below.

        def __init__ (self,
                filename,	# string filename to read and parse
                rcdClass,	# Python class to instantiate for each Rcd
                keyName		# string name of the data member which should
                                # be unique for each Rcd object (akin to
                                # a database record's primary key)
                ):
                # Purpose: constructor -- reads given 'filename' and builds a
                #	set of 'rcdClass' objects to be retrieved by 'keyName'
                # Returns: nothing
                # Assumes: nothing
                # Effects: reads 'filename'
                # Throws: IOError if we cannot read 'filename';
                #	'error' if there are problems parsing the file's
                #	contents

                # These constants are used to remember what state we are in
                # when we're parsing the file

                IN_RCD = 0	# currently in an Rcd record
                OUT_RCD = 1	# currently outside an Rcd record

                self.rcds = {}			# the set of Rcd objects
                self.constants = {}		# set of constants
                self.filename = filename	# name of the file to read

                fp = open (filename, 'r')	# open the file for reading

                state = OUT_RCD		# initially, we're outside an Rcd def

                name, value, lineCt = readAndParseLine (fp)

                # name=None and value=None signals the end of the file, so keep going until then

                while name or value:

                        if state == IN_RCD:

                                # we're currently inside the definition for an
                                # Rcd object.  If we've hit the closing marker
                                # then we need to add the object to our set.

                                if name == ']':

                                        # raise errors if the Rcd object is
                                        # missing a key or if it has the same
                                        # key as one we've already saved.

                                        #print('IN_RCD keyName: ', keyName)
                                        #print('IN_RCD rcd: ', rcd[keyName])

                                        # 04/07/2020 lec
                                        # TR13204/python 3
                                        # bug here...commented out
                                        #if keyName not in rcd:
                                        #        raise error(MISSING_KEY % (keyName, lineCt))

                                        #print('IN_RCD rcd: ', rcd[keyName])
                                        key = rcd[keyName]
                                        #print('IN_RCD key: ', key)
                                        if key in self.rcds:
                                                raise error(NON_UNIQUE % (key, lineCt))

                                        # otherwise, save it in our set.

                                        #print('IN_RCD ]: self.rcds[key] ', key, rcd)
                                        self.rcds[key] = rcd
                                        #print(self.rcds)

                                        # having just finished an Rcd def,
                                        # we're now back outside -- go on to
                                        # the next line

                                        state = OUT_RCD

                                elif name == '[':
                                        raise error(EXTRA_OPEN % lineCt)

                                # this line defines an attribute for the
                                # current Rcd object.

                                else:
                                        rcd.add (name, substitute (value.strip(), self.constants, lineCt))

                        elif state == OUT_RCD:

                                #print('OUT_RCD')

                                # We're outside the definition of an Rcd
                                # object, so we need to look for a marker
                                # signalling the start of a new object.

                                if name == '[':
                                        state = IN_RCD
                                        rcd = rcdClass()

                                # Otherwise, this line defines a constant
                                # to be added to our set of constants.

                                else:
                                        self.constants[name] = substitute (value.strip(), self.constants, lineCt)

                        else:
                                # This should never occur, but let's trap it
                                # just to be sure.

                                raise error(PROGRAMMER_ERROR)

                        #print('init: ', value)
                        name, value, lineCt = readAndParseLine (fp, lineCt)

                # If we run out of lines and we're still inside an Rcd object
                # definition, then there was a problem somewhere.

                if state != OUT_RCD:
                        raise error(BAD_MARKUP)
                fp.close()
                return

        def __getitem__ (self,
                keyValue	# string key value for the Rcd object you
                                #	wish to retrieve
                ):
                # Purpose: get the Rcd object keyed by 'keyValue'
                # Returns: either an Rcd object, or None if we have no object
                #	for the given 'keyValue'
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                if keyValue in self.rcds:
                        return self.rcds[keyValue]
                return None

        def __len__ (self):
                # Purpose: get the number of Rcd objects defined in 'self'
                # Returns: integer
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                return len(self.rcds)

        def has_key (self,
                keyValue		# string key value for an Rcd object
                ):
                # Purpose: see if 'keyValue' is defined as an Rcd object
                #	in 'self'
                # Returns: boolean (0/1)
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                return keyValue in self.rcds

        def keys (self):
                # Purpose: get a list of key values for Rcd objects defined
                #	in 'self'
                # Returns: list of string
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                return list(self.rcds.keys())

        def getFilename (self):
                # Purpose: get the name of the file which we read to create
                #	this 'RcdFile' object
                # Returns: string
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                return self.filename

        def getConstant (self,
                name		# string name of the constant whose value you
                                #	wish to retrieve
                ):
                # Purpose: get the value associated with the constant 'name'
                #	in the file we read
                # Returns: string or None if 'name' was not defined in the
                #	file
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                if name in self.constants:
                        return self.constants[name]
                return None

        def items (self):
                # Purpose: get the set of all keys and Rcd objects in 'self'
                # Returns: list of two-item tuples.  Each tuple contains a
                #	key value and its associated Rcd object.
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                return list(self.rcds.items())

        def constantItems (self):
                # Purpose: get the set of all named constants and their values
                #	which were defined in the file we read
                # Returns: list of two-item tuples.  Each tuple contains a
                #	constant's name and its value.
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                return list(self.constants.items())

class Rcd:
        # IS: one record, containing a set of fields and values
        # HAS: a set of fields and values.  Each value may be either a string
        #	or a list of string.
        # DOES: provides accessor and mutator methods for dealing with
        #	individual fields and their values, provides access to the
        #	full set of fields and values, compiles individual values into
        #	compiled regular expressions when requested
        # Implementation: The first time we define a value for a field, it is
        #	a string.  If we come across more definitions, then we convert
        #	it into a list.

        def __init__ (self):
                # Purpose: constructor -- makes an empty record
                # Returns: nothing
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                self.values = {}	# maps field names to values
                self.regex = {}		# as the user requests field values
                                        #	compiled as regexes, we keep
                                        #	a set of them here so that we
                                        #	don't need to recompile them
                                        #	if he/she requests one again
                return

        def __delitem__ (self,
                key			# string fieldname to remove
                ):
                # Purpose: remove the fieldname 'key' and its associated value
                #	if it exists in 'self'
                # Returns: nothing
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                if key in self.values:
                        del self.values[key]
                return

        def __getitem__ (self,
                key			# string fieldname to retrieve
                ):
                # Purpose: retrieves the value associated with 'key'
                # Returns: either a string or a list of string (if 'key' has
                #	multiple values defined)
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing
                # Notes: If 'key' has no value defined, then we return None

                if key in self.values:
                        return self.values[key]
                return None

        def __setitem__ (self,
                key,		# string fieldname to define
                value		# string value to set for the given 'key'
                ):
                # Purpose: set the value for 'key' to be 'value', overwriting
                #	any existing value
                # Returns: nothing
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing
                # Notes: see add() if you don't want to replace old values

                self.values[key] = value
                return

        def __len__ (self):
                # Purpose: get the number of fields defined in 'self'
                # Returns: integer
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                return len(self.values)

        def has_key (self,
                key		# string fieldname to look up
                ):
                # Purpose: see if 'key' is defined as a field in 'self'
                # Returns: boolean (0/1)
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                return key in self.values

        def keys (self):
                # Purpose: get a list of fieldnames defined in 'self'
                # Returns: list of string
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                return list(self.values.keys())

        def items (self):
                # Purpose: get the set of all fieldnames and their values
                #	which are defined in 'self'
                # Returns: list of two-item tuples.  Each tuple contains a
                #	fieldname and its associated value (which is either a
                #	string or a list of string)
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing

                return list(self.values.items())

        def add (self,
                key,		# string fieldname to define
                value		# string value to set for the given 'key'
                ):
                # Purpose: set the value for 'key' to be 'value'; if 'key'
                #	already has a value, then we add this as a new
                #	value to a list of values.
                # Returns: nothing
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing
                # Notes: see __setitem__() if you want to replace old values

                if key not in self.values:
                        self.values[key] = value
                elif type(self.values[key]) == bytes:
                        self.values[key] = [ self.values[key], value ]
                else:
                        self.values[key].append (value)
                return

        def getAsList (self,
                key		# string fieldname to retrieve
                ):
                # Purpose: get the value associated with 'key' and return it
                #	as a list
                # Returns: list of string
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing
                # Notes: If 'key' is not defined, they you will get back an
                #	empty list.

                item = self[key]
                if type(item) == bytes:
                        return [ item ]
                elif item == None:
                        return []
                return item		# item already is a list

        def getAsString (self,
                key,		# string fieldname to retrieve
                delimiter = ','	# string used to join multiple values
                ):
                # Purpose: get the value associated with 'key' and return it
                #	as a string
                # Returns: string
                # Assumes: nothing
                # Effects: nothing
                # Throws: nothing
                # Notes: If 'key' is not defined, you'll get back an empty
                #	string.  If 'key' has multiple values, they'll be
                #	joined together into a single string using 'delimiter'

                item = self[key]
                if type(item) == list:
                        return str.join (delimiter, item)
                elif item == None:
                        return ''
                return item

        def getAsCompiledRegex (self,
                key			# string fieldname to retrieve
                ):
                # Purpose: compile the value of 'key' into a compiled regular
                #	expression and return it
                # Returns: a regular expression object or a list of them, if
                #	'key' has multiple values; or None if 'key' is not
                #	defined
                # Assumes: the value(s) for 'key' are valid regexes
                # Effects: nothing
                # Throws: propagates regex.error if one of the values does not
                #	compile properly into a regular expression object
                # Notes: We maintain a set of regular expressions we have
                #	compiled so that we don't need to recompile them if
                #	the user requests one for 'key' again.  If 'key' is
                #	not defined, this function returns None.

                if key not in self.regex:
                        item = self[key]
                        if type(item) == bytes:
                                self.regex[key] = regex.compile (item)
                        elif item == None:
                                self.regex[key] = None
                        else:
                                self.regex[key] = []
                                for i in item:
                                        self.regex[key].append (
                                                regex.compile (i))
                return self.regex[key]

###--- Private Functions ---###

def readAndParseLine (
        fp,		# file pointer from which to read
        lineCt = 0	# integer; counter of lines read so far
        ):
        # Purpose: read the next logical line and return a (name, value) tuple
        # Returns: three-item tuple containing...
        #	(name, value, lineCt) if the next logical line defines a pair
        #	(delim, None, lineCt) if the next logical line contains a
        #		record delimiter (either '[' or ']')
        #	(None, None, lineCt) if no logical lines left.
        #	In each case, the lineCt returned has been updated according
        #	to the actual number of lines read from the file so far.
        # Assumes: nothing
        # Effects: reads one or more lines from 'fp'
        # Throws: IOError if we have problems reading from 'fp'
        # Notes: This function looks for the next logical line by stripping
        #	out comments and combining lines joined by a line continuation
        #	character (\).

        name = None
        value = None

        line = fp.readline()
        lineCt = lineCt + 1

        while line:

                # trim off anything following a comment delimiter

                commentPos = line.find ('#')
                if commentPos != -1:
                        line = line[:commentPos]

                # trim off any leading and trailing whitespace

                line = line.strip()

                # if 'name' has a value, then we know that we're on a
                # continued line.  Otherwise, it's a new line.

                if name:
                        # if the line we just read is also continued, then
                        # just add it to the current value (minus the slash)

                        if line[-1] == '\\':
                                value = '%s %s' % (value, line[:-1].rstrip())

                        # otherwise, add it to the value and return.
                        else:
                                value = '%s %s' % (value, line)
                                return name, value, lineCt
                else:
                        # if we read a line with just a square bracket, then
                        # return it

                        if line in [ '[', ']' ]:
                                return line, value, lineCt

                        # otherwise, try to split the line on the first equals
                        # sign.  if we can, then we have the name and value.

                        eqPos = line.find ('=')
                        if eqPos != -1:
                                name = line[:eqPos].rstrip()
                                value = line[eqPos+1:].rstrip()

                                # if the value isn't marked as a continued
                                # line, then we can return.  Otherwise, trim
                                # off the slash.

                                if value[-1:] != '\\':
                                        return name, value, lineCt
                                value = line[:-1].rstrip()

                        # check that we don't have a blank line.  if we don't,
                        # then we know that we should have a line with an
                        # equals sign on it.

                        elif line:
                                raise error(NO_EQUALS % lineCt)

                line = fp.readline()
                lineCt = lineCt + 1

        return None, None, lineCt	# we reached the end of the file

def substitute (
        s,		# string the string on which to perform substitution
        dict,		# dictionary; maps string names to string values
        lineNum		# integer; what line number is 's' in the input?
        ):
        # Purpose: goes through 's' looking for names of constants cited using
        #	${...} notation, replaces them with their values as defined in
        #	'dict' and returns the resulting string
        # Returns: string
        # Assumes: nothing
        # Effects: nothing
        # Throws: 'error' if a name is cited in ${} which does not appear as
        #	a key in 'dict'
        # Notes: We also handle the case of $${...} notation, so for example
        #		substitute ('tuvw$${ABC}', { 'ABC' : 'xyz' }, 1)
        #	would return:
        #		'tuvw${ABC}'
        # Example: As an example using a single $ sign, consider:
        #		substitute ('tuvw${ABC}', { 'ABC' : 'xyz' }, 1)
        #	would return:
        #		'tuvwxyz'

        # Regular expressions are slow, so let's use string operations to
        # help locate a $ sign.  If there's not one, bail out here.  If there
        # is one, then apply the regex at that point.

        pos = s.find ('$')		# position where we found $
        if pos == -1:
                return s

        re_match = variable_re.search(s,pos)	# pos. where we found ${...}

        t = ''			# new string we're building
        last = 0		# We copied up to this position the last time
                                # we copied characters into 't'.
        while re_match:
                pos,end = re_match.span()

                # if we found part of a $${name} entry, then just chop off the
                # first dollar sign and keep the rest of the string

                if s[pos-1] == '$':
                        t = t + s[last:pos-1] + s[pos:end]

                # otherwise, add up to the beginning of the ${name}, look up
                # the value for that constant's name, and add it.

                else:
                        t = t + s[last:pos]
                        name = re_match.group(1)
                        if name not in dict:
                                raise error(BAD_CONSTANT % (name, lineNum))
                        t = t + dict[name]

                # remember the last character position matched by the regex
                # and go look for the next occurrence

                last = end
                re_match = variable_re.search (s, last)

        return t + s[last:]
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
