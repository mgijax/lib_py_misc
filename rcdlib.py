# Name: rcdlib.py
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
#	using ${name} notation.
# The # sign indicates that the rest of the line is a comment and should be
#	ignored.
# The \ is a line continuation character.  It will join the next line to the
#	value for the current line using a single space character.
# Any fieldname, even if not specified in a given record, has a value of the
#	empty string  '' by default.
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
# title = ${SSE} III
# ]

# Using the RcdFile and Rcd classes to parse this file would involve, for
# example:
#	people = RcdFile ('example.txt', Rcd, 'email')
#	print people['mmm']['title']
#				===> Scientific Software Engineer III

import string
import regex
import types

###--- Global Variables ---###

# regular expression used to find a constant cited in a line as ${...}

variable_re = regex.compile ('\${\([^}]+\)}')

###--- Exception Information ---###

error = 'rcdlib.error'		# exception raised in this module

# messages passed along when the exception is raised

NO_EQUALS = 'Line %d is missing an expected equals sign (=)'
BAD_CONSTANT = 'Unknown constant "%s" cited on line %d'
NON_UNIQUE = 'Encountered a duplicated key "%s" above line %d'
MISSING_KEY = 'Encountered a record with no key "%s" above line %d'
BAD_MARKUP = 'File did not terminate as expected.  Check all [, ], and \\'
PROGRAMMER_ERROR = 'Programmer error.  The program is in a bad state...'

###--- State indicators ---###

# These are used to remember what state we are in when we're parsing the file

IN_RCD = 0	# currently in an Rcd record
OUT_RCD = 1	# currently outside an Rcd record
IN_FIELD = 2	# currently inside a multi-line field in an Rcd record

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
		filename,	# string; filename to read and parse
		rcdClass,	# Python class to instantiate for each Rcd
		keyName		# string; name of the data member which should
				#	be unique for each Rcd object (akin to
				#	a database record's primary key)
		):
		# Purpose: constructor -- reads given 'filename' and builds a
		#	set of 'rcdClass' objects to be retrieved by 'keyName'
		# Returns: nothing
		# Assumes: nothing
		# Effects: reads 'filename'
		# Throws: IOError if we cannot read 'filename';
		#	'error' if there are problems parsing the file's
		#	contents

		self.rcds = {}			# the set of Rcd objects
		self.constants = {}		# set of constants
		self.filename = filename	# name of the file to read

		fp = open (filename, 'r')
		lines = fp.readlines()
		fp.close()

		state = OUT_RCD		# initially, we're outside an Rcd def
		lineNum = 0		# no lines examined yet

		for line in lines:
			lineNum = lineNum + 1

			# trim off anything following a comment delimiter

			commentPos = string.find (line, '#')
			if commentPos != -1:
				line = line[:commentPos]

			# strip all leading and trailing whitespace, and skip
			# the line if it is then empty

			line = string.strip (line)
			if not line:
				continue

			# otherwise, our actions are dictated by what state
			# we're currently in

			if state == IN_RCD:

				# we're currently inside the definition for an
				# Rcd object.  If we've hit the closing marker
				# then we need to add the object to our set.

				if line == ']':

					# raise errors if the Rcd object is
					# missing a key or if it has the same
					# key as one we've already saved.

					if not rcd.has_key(keyName):
						raise error, MISSING_KEY % \
							(keyName, lineNum)
					key = rcd[keyName]
					if self.rcds.has_key (key):
						raise error, NON_UNIQUE % \
							(key, lineNum)

					# otherwise, save it in our set.

					self.rcds[key] = rcd

					# having just finished an Rcd def,
					# we're now back outside -- go on to
					# the next line

					state = OUT_RCD
					continue

				# if we didn't find a closing marker, then we
				# need to look at this line as defining an
				# attribute for the current Rcd object.

				name, value = splitLine(line, lineNum)
				if value and value[-1] == '\\':

					# if we end with a line continuation
					# character (\), then change to the
					# IN_FIELD state

					state = IN_FIELD
					value = string.rstrip(value[:-1]) + \
						' '
				else:
					# otherwise, we have a single-line
					# attribute to add

					rcd.add (name, substitute (value,
						self.constants, lineNum))

			elif state == OUT_RCD:

				# We're outside the definition of an Rcd
				# object, so we need to look for a marker
				# signalling the start of a new object.

				if line == '[':
					state = IN_RCD
					rcd = rcdClass()
					continue

				# Otherwise, this line must define a constant
				# to be added to our set of constants.

				name, value = splitLine(line, lineNum)
				self.constants[name] = substitute (value,
					self.constants, lineNum)

			elif state == IN_FIELD:

				# The current line is the continuation of the
				# previous line.  Look at the end to see if it
				# is continued further onto the next line.

				if line[-1] == '\\':
					line = string.rstrip(line[:-1]) + ' '
					value = value + line
				else:
					# If not, then this line concludes the
					# attribute's definition, so add it
					# and go back to the normal IN_RCD
					# state.

					state = IN_RCD
					value = value + line
					rcd.add (name, substitute (value,
						self.constants, lineNum))
			else:
				# This should never occur, but let's trap it
				# just to be sure.

				raise error, PROGRAMMER_ERROR

		# If we run out of lines and we're still inside an Rcd object
		# definition, then there was a problem somewhere.

		if state != OUT_RCD:
			raise error, BAD_MARKUP
		return

	def __getitem__ (self,
		keyValue	# string; key value for the Rcd object you
				#	wish to retrieve
		):
		# Purpose: get the Rcd object keyed by 'keyValue'
		# Returns: either an Rcd object, or None if we have no object
		#	for the given 'keyValue'
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		if self.rcds.has_key (keyValue):
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
		keyValue		# string; key value for an Rcd object
		):
		# Purpose: see if 'keyValue' is defined as an Rcd object
		#	in 'self'
		# Returns: boolean (0/1)
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.rcds.has_key (key)

	def keys (self):
		# Purpose: get a list of key values for Rcd objects defined
		#	in 'self'
		# Returns: list of strings
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.rcds.keys()

	def getFilename (self):
		# Purpose: get the name of the file which we read to create
		#	this 'RcdFile' object
		# Returns: string
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.filename

	def getConstant (self,
		name		# string; name of the constant whose value you
				#	wish to retrieve
		):
		# Purpose: get the value associated with the constant 'name'
		#	in the file we read
		# Returns: string, or None if 'name' was not defined in the
		#	file
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		if self.constants.has_key (name):
			return self.constants[name]
		return None

	def items (self):
		# Purpose: get the set of all keys and Rcd objects in 'self'
		# Returns: list of two-item tuples.  Each tuple contains a
		#	key value and its associated Rcd object.
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.rcds.items()

	def constantItems (self):
		# Purpose: get the set of all named constants and their values
		#	which were defined in the file we read
		# Returns: list of two-item tuples.  Each tuple contains a
		#	constant's name and its value.
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.constants.items()

class Rcd:
	# IS: one record, containing a set of fields and values
	# HAS: a set of fields and values.  Each value may be either a string
	#	or a list of strings.
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
		key			# string; fieldname to remove
		):
		# Purpose: remove the fieldname 'key' and its associated value
		#	if it exists in 'self'
		# Returns: nothing
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		if self.values.has_key (key):
			del self.values[key]
		return

	def __getitem__ (self,
		key			# string; fieldname to retrieve
		):
		# Purpose: retrieves the value associated with 'key'
		# Returns: either a string or a list of strings (if 'key' has
		#	multiple values defined)
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing
		# Notes: If 'key' has no value defined, then we return an
		#	empty string -- ''

		if self.values.has_key (key):
			return self.values[key]
		return ''

	def __setitem__ (self,
		key,		# string; fieldname to define
		value		# string; value to set for the given 'key'
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
		key		# string; fieldname to look up
		):
		# Purpose: see if 'key' is defined as a field in 'self'
		# Returns: boolean (0/1)
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.values.has_key (key)

	def keys (self):
		# Purpose: get a list of fieldnames defined in 'self'
		# Returns: list of strings
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.values.keys()

	def items (self):
		# Purpose: get the set of all fieldnames and their values
		#	which are defined in 'self'
		# Returns: list of two-item tuples.  Each tuple contains a
		#	fieldname and its associated value (which is either a
		#	string or a list of strings)
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.values.items()

	def add (self,
		key,		# string; fieldname to define
		value		# string; value to set for the given 'key'
		):
		# Purpose: set the value for 'key' to be 'value'; if 'key'
		#	already has a value, then we add this as a new
		#	value to a list of values.
		# Returns: nothing
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing
		# Notes: see __setitem__() if you want to replace old values

		if not self.values.has_key (key):
			self.values[key] = value
		elif type(self.values[key]) == types.StringType:
			self.values[key] = [ self.values[key], value ]
		else:
			self.values[key].append (value)
		return

	def getAsList (self,
		key		# string; fieldname to retrieve
		):
		# Purpose: get the value associated with 'key' and return it
		#	as a list
		# Returns: list of strings
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing
		# Notes: If 'key' is not defined, they you will get back a
		#	list containing an empty string -- ['']

		item = self[key]
		if type(item) == types.StringType:
			return [ item ]
		return item

	def getAsString (self,
		key,		# string; fieldname to retrieve
		delimiter = ','	# string; used to join multiple values
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
		if type(item) == types.ListType:
			return string.join (item, delimiter)
		return item

	def getAsCompiledRegex (self,
		key			# string; fieldname to retrieve
		):
		# Purpose: compile the value of 'key' into a compiled regular
		#	expression and return it
		# Returns: a regular expression object or a list of them, if
		#	'key' has multiple values
		# Assumes: the value(s) for 'key' are valid regexes
		# Effects: nothing
		# Throws: propagates regex.error if one of the values does not
		#	compile properly into a regular expression object
		# Notes: We maintain a set of regular expressions we have
		#	compiled so that we don't need to recompile them if
		#	the user requests one for 'key' again.

		if not self.regex.has_key (key):
			item = self[key]
			if type(item) == types.StringType:
				self.regex[key] = regex.compile (item)
			else:
				self.regex[key] = []
				for i in item:
					self.regex[key].append (
						regex.compile (i))
		return self.regex[key]

###--- Private Functions ---###

def splitLine (
	s,		# string; a line of input
	lineNum		# integer; what line number is 's' in the input?
	):
	# Purpose: breaks input line 's' into a name, value pair based on the
	#	position of an equals sign (=)
	# Returns: a tuple of two strings -- the name and the value
	# Assumes: 's' has no leading or trailing whitespace
	# Effects: nothing
	# Throws: 'error' if 's' does not contain an equals sign
	# Notes: Neither item returned will have leading or trailing
	#	whitespace.

	eqPos = string.find (s, '=')
	if eqPos == -1:
		raise error, NO_EQUALS % lineNum
	name = string.rstrip(s[:eqPos])
	value = string.lstrip(s[eqPos+1:])
	return name, value

def substitute (
	s,		# string; a line of input
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
	#		'tuvw${xyz}'
	# Example: As an example using a single $ sign, consider:
	#		substitute ('tuvw${ABC}', { 'ABC' : 'xyz' }, 1)
	#	would return:
	#		'tuvwxyz'

	# Regular expressions are slow, so let's use string operations to
	# help locate a $ sign.  If there's not one, bail out here.  If there
	# is one, then apply the regex at that point.

	pos = string.find (s, '$')		# position where we found $
	if pos == -1:
		return s
	pos = variable_re.search (s, pos)	# pos. where we found ${...}

	t = ''			# new string we're building
	last = 0		# We copied up to this position the last time
				#	we copied characters into 't'.
	while pos != -1:

		# Copy characters up to where the ${...} starts to 't', and
		# ensure that the constant named in ${...} is in 'dict'.

		t = t + s[last:pos]
		name = variable_re.group(1)
		if not dict.has_key (name):
			raise error, BAD_CONSTANT % (name, lineNum)

		# Check for the case where we had two $ signs.  If there were
		# two, the constant's value needs to go in {}.

		if s[pos-1] == '$':
			t = '%s{%s}' % (t, dict[name])
		else:
			t = t + dict[name]

		# remember the last character matched by the regex and go
		# look for the next occurrence

		last = variable_re.regs[0][1]
		pos = variable_re.search (s, last)

	return t + s[last:]
