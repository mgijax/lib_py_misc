#!/usr/local/bin/python

# Name: Configuration.py
# Purpose: provide a uniform means for accessing files of configuration
#	parameters in different formats
# On Import: several regular expressions (see below) are compiled
# Notes: This file may be either imported as a python library or executed as a
#	script to convert from one config file type to another.
#
#	When reading a configuration file, the default format is tab-
#	delimited.  If you'd prefer, your configuration file may be written
#	as Bourne shell or C-shell variable declarations.  To override the
#	default expectation (tab-delimited), just make sure that the first
#	line of your configuration file is one of the following:
#		#format: csh
#		#format: sh
#		#format: tab
#
#	When using this file as a python module, it looks for a special
#	LIBDIRS configurtion option.  Its value should be a colon-delimited
#	list of directory names in which one expects to find Python libraries.
#	If a LIBDIRS configuration option is found, we add those directories
#	to the PYTHONPATH.
#
#	To use this file as a python module, check out the following code
#	examples:
#		# import the module
#		import Configuration
#
#		# read a config file named 'conf' in the current directory
#		c = Configuration.Configuration ('conf')
#
#		# read a config file named 'conf' which is located either in
#		# the current directory or in one of its parent directories:
#		c = Configuration.Configuration ('conf', 1)
#
#		# look up the value of parameter 'foo' or raise a KeyError
#		# exception if it is not defined:
#		s = c['foo']
#		s = c.get('foo')
#
#		# look up the value of parameter 'foo' or return None if it is
#		# not defined:
#		s = c.lookup('foo')
#
#	When invoking this file as a script, you will need to specify two
#	parameters -- the name of the configuration file and the desired
#	output format.  It then reads the configuration file and writes its
#	contents to stdout in that format.  As examples consider:
#
#		# You're working in a Bourne shell script and you want to
#		# define the configuration options in the file 'config':
#		`Configuration.py config sh`
#
#		# You're working in a C-shell script and you want to define
#		# the configuration options in the file 'config':
#		`Configuration.py config csh`
#
#		# At this point, you can use typical shell notation
#		# to reference the configuration options -- to use the value
#		# of a configuration option named BOB, use $BOB
#
#	When invoked as a script, this module does not traverse up the
#	directory tree to find your specified configuration file.  You must
#	supply to correct path yourself.

import os	# standard Python libraries
import sys
import types
import regex
import string

# if we invoked this module as a script (rather than importing it), then we
# need to define a usage statement:

if __name__ == '__main__':
	USAGE = '''Usage: %s <config filename> <filetype to output>
	The filetype may be csh, sh, or tab.  Output is to stdout.
	Or, this module may be imported as a Python library.
''' % sys.argv[0]

###--- Exception-Related Global Variables ---###

error = 'Configuration.error'		# exception raised by this module

# exception values when 'error' is raised by this module:

ERR_MISSING = 'Cannot find specified config file'
ERR_UNRECOGNIZED = 'Unrecognized format in config file'

###--- Regular Expressions for Parsing Configuration Files ---###

# pick out a format specification:
re_format = regex.compile ('#format: *\(.*\)', regex.casefold)

# pick out comments and blank lines:
re_comment = regex.compile ('\(#.*\)'		# comment
			'\|'			# or
			'\(^[ \t]*$\)')		# blank line

# parse a tab or space-delimited line:
re_tabbed = regex.compile ('\([^\t ]*\)'	# parameter name
			'''[\t ]+['"]?'''	# spacing, optional quote
			'''\([^'"\n]*\)'''	# parameter value
			'''['"]?''')		# optional quote

# parse a Bourne shell-formatted line:
re_shell = regex.compile ('\([^\t ]*\)'		# parameter name
			'''[\t ]*=[\t ]*'''	# spacing, =, spacing
			'''['"]?'''		# optional quote
			'''\([^'"\n]*\)'''	# parameter value
			'''['"]?''')		# optional quote

# parse a C-shell-formatted line using 'set':
re_cshell1 = regex.compile ('set[\t ]+'		# set keyword, spacing
			'''\([^\t ]*\)'''	# parameter name
			'''[\t ]*=[\t ]*'''	# spacing, =, spacing
			'''['"]?'''		# optional quote
			'''\([^'"\n]*\)'''	# parameter value
			'''['"]?''')		# optional quote

# parse a C-shell-formatted line using 'setenv':
re_cshell2 = regex.compile ('setenv[\t ]+'	# setenv keyword, spacing
			'''\([^\t ]*\)'''	# parameter name
			'''[\t ]*['"]?'''	# spacing, optional quote
			'''\([^'"\n]*\)'''	# parameter value
			'''['"]?''')		# optional quote

# find one parameter name embedded within another parameter value:
re_parm = regex.compile ('\${\([^}]+\)}')	# format like ${MYPARM}

###--- Functions ---###

def find_path (
	s = 'Configuration',	# string pathname for which we're looking
	max = 10		# number of parent directory levels to search
	):
	# Purpose: find a relative path to the "nearest" instance of 's', up
	#       to 'max' parent directories away
	# Returns: relative path to 's'
	# Assumes: nothing
	# Effects: nothing
	# Throws: nothing
	# Notes: This is a recursive function.  If 's' exists, we simply
	#       return it.  If not, and if 'max' is zero, then we've searched
	#       far enough, and we just return None.  Otherwise, look in the
	#       parent directory of 's'.

	if os.path.exists (s):
		return s
	elif max == 0:
		return None
	else:
		return find_path (os.path.join (os.pardir, s), max - 1)

###--- Classes ---###

class Configuration:
	# IS:	a set of parameters from a configuration file
	# HAS:	zero or more parameter names, each with an associated string
	#	value
	# DOES:	reads a configuration file, looks up the value corresponding
	#	to a parameter name, converts parameter list into a variety
	#	of file formats.

	def __init__ (self,
		filename,		# string; name of configuration file,
					# or the path to that file
		findFile = 0		# boolean 0/1; should we traverse up
					# the directory tree to find
					# 'filename'?
		):
		# Purpose: instantiate the object and load the config file
		# Returns: nothing
		# Assumes: nothing
		# Effects: reads from the file system to initialize 'self'
		# Throws:
		#	1. IOError - if we can't open 'filename'
		#	2. error, ERR_MISSING - if we can't find 'filename'
		#	3. error, ERR_UNRECOGNIZED - if the config file has
		#		a first line which specifies an unrecognized
		#		format (not tab, sh, or csh)

		self.options = {}	# options[parm name] = string value

		# if we need to traverse up the directory tree to find the
		# given filename, then do so.  If we don't find it, then raise
		# an exception.

		if findFile == 1:
			filename = find_path (filename)
			if filename is None:
				raise error, ERR_MISSING

		# load the configuration file and proceed to parse it.

		fp = open (filename, 'r')
		lines = fp.readlines()
		fp.close ()

		if len(lines) == 0:		# no config options
			return

		regexes = [ re_tabbed ]		# assume default 'tab' format

		# check for other formats, as specified in the first line:

		if re_format.match(lines[0]) != -1:
			format = re_format.group(1)
			if format == 'tab':		# tab-delimited
				pass
			elif format == 'sh':		# Bourne shell
				regexes = [ re_shell ]

			# if C shell, we need to look for set & setenv parms

			elif format == 'csh':
				regexes = [ re_cshell1, re_cshell2 ]
			else:
				raise error, ERR_UNRECOGNIZED
			del lines[0]

		# parse the remaining lines in the file, ignoring comments and
		# blank lines:

		for line in lines:
			if re_comment.match (line) != -1:
				continue
			for re in regexes:
				if re.match (line) != -1:
					field, value = re.group (1,2)
					self.options [field] = value
					break

		# if we had a LIBDIRS configuration option, then we need to
		# add the colon-delimited list of directories to the
		# PYTHONPATH of the currently executing process:

		if self.options.has_key ('LIBDIRS'):
			libdirs = string.split (self['LIBDIRS'], ':')
			libdirs.reverse()
			for libdir in libdirs:
				if libdir not in sys.path:
					sys.path.insert (0, libdir)
		return

	###--- Dictionary-Compatible Methods ---###

	def __getitem__ (self,
		key		# string; parameter name
		):
		# Purpose: get the value associated with 'key', in a
		#	dictionary-style manner
		# Returns: string; parameter value for 'key'
		# Assumes: nothing
		# Effects: nothing
		# Throws: KeyError if 'key' is not a valid parameter name

		return self.resolve(key)

	def __len__ (self):
		# Purpose: get the number of parameters in self
		# Returns: integer number of parms
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return len(self.options)

	def __setitem__ (self,
		key,		# string; parameter name
		value		# string; parameter value
		):
		# Purpose: set the 'value' associated with  'key', in a
		#	dictionary-style manner
		# Returns: nothing
		# Assumes: nothing
		# Effects: updates self.options to reflect the new value
		#	associated with 'key', overwriting any existing one
		# Throws: nothing

		self.options[key] = value
		return

	def has_key (self,
		key		# string; parameter name
		):
		# Purpose: test to see if 'key' is a valid parameter name
		# Returns: boolean; 0 if no 'key' parameter, or 1 if it exists
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.options.has_key (key)

	def items (self):
		# Purpose: get the whole set of parameter names and values
		# Returns: a list of tuples, each containing two strings:
		#	(parameter name, parameter value)
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing
		# Notes: This function resolves any parameter names embedded
		#	within other parameter values.  If you want the raw
		#	values as read from the configuration file, see the
		#	self.rawItems() method instead.

		list = []
		for name in self.keys():
			list.append ( (name, self[name]) )
		return list

	def keys (self):
		# Purpose: get a list of parameter names
		# Returns: list of strings, each of which is a parameter name
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.options.keys()

	###--- Other Data Access Methods ---###

	def get (self,
		key		# string; parameter name
		):
		# Purpose: get the value associated with 'key', wrapper for
		#	__getitem__
		# Returns: string; parameter value associated with 'key'
		# Assumes: nothing
		# Effects: nothing
		# Throws: propagates KeyError if 'key' is not a known
		#	parameter name

		return self[key]

	def lookup (self,
		key		# string; parameter name
		):
		# Purpose: get the value associated with 'key', or None if
		#	'key' is not a known parameter name
		# Returns: string or None; see Purpose
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		if self.has_key (key):
			return self[key]
		return None

	###--- Conversion Routines ---###

	def asCsh (self):
		# Purpose: build a C-shell version of the configuration
		#	parameters and values
		# Returns: a list of strings, used to set the configuration
		#	options for C-shell scripts
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return map (lambda (field, value): 'setenv %s "%s"' % \
			(field, value), self.items())

	def asSh (self):
		# Purpose: build a Bourne shell version of the configuration
		#	parameters and values
		# Returns: a list of strings, used to set the configuration
		#	options for Bourne shell scripts
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		lines = []
		for (field, value) in self.items():
			lines.append ('%s="%s"' % (field, value))
			lines.append ('export %s' % field)
		return lines

	def asTab (self):
		# Purpose: build a tab-delimited version of the configuration
		#	parameters and values
		# Returns: a list of strings, with the parameter name
		#	followed by a tab and the parameter value
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return map (lambda (field, value): '%s\t%s' % (field, value),
			self.items())

	def write (self,
		file=sys.stdout,	# file pointer; file to write to
		format='tab'		# string; 'tab', 'csh', or 'sh'
		):
		# Purpose: write the configuration parameters out to a file
		#	in a given format, with a header line specifying the
		#	format
		# Returns: nothing
		# Assumes: nothing
		# Effects: writes one or more lines to 'file'
		# Throws:
		#	1. IOError if we cannot write to 'file'
		#	2. error, ERR_UNRECOGNIZED - if 'format' is unknown

		if format == 'tab':
			lines = self.asTab()
		elif format == 'sh':
			lines = self.asSh()
		elif format == 'csh':
			lines = self.asCsh()
		else:
			raise error, ERR_UNRECOGNIZED

		file.write ('#format: %s\n' % format)
		for line in lines:
			file.write ('%s\n' % line)
		return

	###--- Private Methods ---###

	def rawItems (self):
		# Purpose: get the whole set of parameter names and values
		# Returns: a list of tuples, each containing two strings:
		#	(parameter name, parameter value)
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing
		# Notes: This method does not resolve any parameter names
		#	which are embedded within other parameter values.
		#	See self.items() for that functionality.

		return self.options.items()

	def resolve (self,
		key,		# string; parameter name
		steps = 100	# integer; maximum recursive levels allowed
		):
		# Purpose: return the value of the parameter named 'key',
		#	with any embedded parameter references ( ${PARM} )
		#	having been resolved if we can do it in under the
		#	given number of 'steps'
		# Returns: string
		# Assumes: nothing
		# Effects: nothing
		# Throws: raises a KeyError if 'key' is not one of the
		#	parameter names.  raises 'error' if 'steps' reaches
		#	zero.
		# Notes: Mainly, we use 'steps' to prevent an infinite loop if
		#	we have two parameters that reference each other, like
		#		A	"My ${B} value"
		#		B	"My ${A} value"
		#	or one references itself like
		#		A	"My ${A} value"

		if steps == 0:
			raise error, 'Could not resolve parameter.'
		s = self.options[key]
		while re_parm.search (s) != -1:
			start, stop = re_parm.regs[0]
			parm = re_parm.group(1)
			s = s[:start] + self.resolve(parm, steps-1) + s[stop:]
		return s

###--- Main Program ---###

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print USAGE
		sys.exit(0)

	# read the specified Configuration file, and write the values to
	# stdout with the specified format.  If exceptions occur, just let
	# them happen and the script will exit with a non-zero return code.

	c = Configuration (sys.argv[1])
	c.write (sys.stdout, sys.argv[2])