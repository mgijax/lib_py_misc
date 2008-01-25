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

import ignoreDeprecation
import os
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
ERR_UNKNOWN_KEYS = 'Uknown configuration options: %s'

###--- Regular Expressions for Parsing Configuration Files ---###

# pick out a format specification:
re_format = regex.compile ('#format: *\(.*\)', regex.casefold)

# pick out comments and blank lines:
re_comment = regex.compile ('\(#.*\)'		# comment
			'\|'			# or
			'\(^[ \t]*$\)')		# blank line

# parse a tab or space-delimited line:
re_tabbed = regex.compile ('\([^\t\n ]*\)'	# parameter name
			'''[\t ]*['"]?'''	# spacing, optional quote
			'''\([^'"\n]*\)'''	# parameter value
			'''['"]?''')		# optional quote

# parse a Bourne shell-formatted line:
re_shell = regex.compile ('\([^\t =]*\)'	# parameter name
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
			'''\([^\t\n ]+\)'''	# parameter name
			'''[\t ]*['"]?'''	# spacing, optional quote
			'''\([^'"\n]*\)'''	# parameter value
			'''['"]?''')		# optional quote

# find one parameter name embedded within another parameter value:
re_parm = regex.compile ('\${\([^}]+\)}')	# format like ${MYPARM}

###--- Other Global Variables ---###

MEMORY = {}	# maps from (filename, findFile) key to a Configuration
		# object, so we can remember the object once we build it for
		# a given configuration file, and just return it rather than
		# rereading the file and rebuilding the object if we're asked
		# for it again

###--- Functions ---###

def get_Configuration (
	filename,	# string; name of the configuration file to read
	findFile = 0	# boolean (0/1); should we traverse up the directory
			# tree to find 'filename'?
	):
	# Purpose: This is a wrapper over the constructor for the
	#	Configuration class.  It uses the global MEMORY to remember
	#	Configuration objects that we've already constructed, so we
	#	can return them directly without rebuilding them.
	# Returns: Configuration object
	# Assumes: nothing
	# Effects: if this is the first time we ask for the (filename,
	#	findFile) combination, then we read and parse that 'filename',
	#	construct a Configuration object, and remember it in the
	#	global MEMORY
	# Throws: propagates all exceptions raised by Configuration.__init__()

	global MEMORY

	# if we've already encountered this request, then simply return the
	# Configuration object that we constructed last time

	key = (filename, findFile)
	if MEMORY.has_key (key):
		return MEMORY[key]

	# Otherwise, read and parse the file, create the Configuration object,
	# remember it for next time, and return it

	config = Configuration (filename, findFile)
	MEMORY[key] = config
	return config

def find_path (
	s = 'Configuration'	# string pathname for which we're looking
	):
	# Purpose: find an absolute path to the "nearest" instance of 's',
	#	first looking at the directory in which the current script
	#	lives and then going up parent-by-parent to the root of this
	#	directory hierarchy.
	# Returns: absolute path to 's' or None if we can't find it
	# Assumes: nothing
	# Effects: nothing
	# Throws: nothing
	# Notes: If you specify an absolute path for 's', we do not go up the
	#	directory hierarchy -- it either exists or it doesn't.

	if os.path.isabs (s):
		# If we are passed an absolute path, then it either exists or
		# it doesn't.  We don't do any further examination.

		if os.path.exists (s):
			return s
		return None

	# Otherwise, we have a relative path -- this should be relative to
	# where the script resides, which we can get from the way it was
	# called in argv[0]

	script_path, script_name = os.path.split (sys.argv[0])

	# if the 'script_path' is empty, that means that the 'script_name'
	# was found using the user's PATH environment variable.  So, we need
	# to track down where it was found.

	if not script_path:
		PATH = string.split (os.environ['PATH'], ':')
		for dir in PATH:
			if os.path.exists (os.path.join (dir, script_name)):
				script_path = dir
				break
		else:
			raise error, 'Cannot find %s in your PATH' % \
				script_name

	pieces = []	# initial set of pieces of the path to find 's',
			# before any clean-up takes place

	# if the 'script_path' is not absolute, then it is relative to the
	# current working directory...

	if not os.path.isabs (script_path):
		pieces = string.split (os.getcwd(), os.sep)

	# now consider the path to the script and the relative path given for
	# the config file in 's'

	pieces = pieces \
		+ string.split (script_path, os.sep) \
		+ string.split (s, os.sep)

	# Now, go through all the 'pieces' of the path and handle any
	# '.' and '..' directories that we find.  We will build a set of
	# 'new_pieces' which will be the final components of our path.

	new_pieces = []	
	for item in pieces:
		if item == os.curdir:			# ignore a .
			pass
		elif item == os.pardir:			# go up a level for ..
			if len(new_pieces) > 0:
				del new_pieces[-1]
		else:					# append anything else
			new_pieces.append (item)

	pieces = new_pieces		# replace initial set with cleaned one
	filename = pieces[-1:]		# the actual filename as a list

	# now walk up the directory tree looking for the file each step of
	# the way

	i = len(pieces) - 1
	while i >= 0:
		path = os.sep + string.join (pieces[:i] + filename, os.sep)
		if os.path.exists (path):
			return path
		i = i - 1
	return None

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
		#	4. propagates error from find_path if we cannot find
		#		the script in the user's PATH

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

                # if the provided config file uses a global config to define
                # shared knowledge, open the file and read in the parms,
                # giving precedence to the parms found in original config 

                if self.options.has_key ('GLOBAL_CONFIG') and os.path.exists (self['GLOBAL_CONFIG']):
                    globalConfig = get_Configuration(self['GLOBAL_CONFIG'])
                    self.merge(globalConfig)
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

	def getUnresolvedValue(self, key):
		# Purpose: Get a single value, but dont validate its inned variables.
		# Returns: a single unresolved value from the dictionary.
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing
		# Notes: This method does not resolve any parameter names
		#	which are embedded within other parameter values.
		#	See self.__getitem__() for that functionality.
		return self.options[key]


	def getUnresolvedMapping(self):
		# Purpose: Return the internal dictionary
		# Returns: self.options
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing
		# Notes: none
		
		return self.options


	def getResolvedMapping(self):
		# Purpose: Return the internal dictionary
		# Returns: self.options
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing
		# Notes: none
		
		temp = {}
		
		for key in self.keys():
			temp[key] = self.resolve(key)
		
		return temp



	def check_keys (self,
		desired_keys	# list of strings; each string is one key that
				# should be defined in the config file
		):
		# Purpose: check that all the 'desired_keys' are, in fact,
		#	defined
		# Returns: nothing
		# Assumes: nothing
		# Effects: nothing
		# Throws: error.ERR_UNKNOWN_KEYS if we encounter one or more
		#	'desired_keys' which are not defined in this object
		# Notes: This method would often be used by a script to see
		#	that all its needed config parameters are defined
		#	before it begins its real work.

		unknown = []
		for key in desired_keys:
			if not self.has_key(key):
				unknown.append (key)
		if unknown:
			raise error, ERR_UNKNOWN_KEYS % \
				string.join (unknown, ', ')
		return

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

	###--- Convienance Methods ---###
	def merge(self, config):
		# Purpose: Merge to configuration files together, giving preference to values
		#	   stored in the current object.
		# Returns: nothing
		# Assumes: nothing
		# Effects: Adds all of the values that are not in the present object, into the present object.
		# Throws:
		
		for key in config.keys():
			if not self.has_key(key):
                		self[key] = config.getUnresolvedValue(key)

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

