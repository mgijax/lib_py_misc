# glimpselib.py

# Support module for glimpse queries.

# Common problems and solutions
# -----------------------------
# - Read the glimpse manual to make sure you are using ALL of the options
#	necessary to perform your query.
# - If you are not getting any results, make sure the index files AND the data
#	files are where they need to be.

import os
import string
import regsub

SP = ' '
indexerror = 'indexerror'		# exception raised if problem occurs
GLIMPSE = '/usr/local/bin/glimpse'	# Default location of glimpse binary

def set_glimpseExe (path):
	# set the path to the glimpse executable
	global GLIMPSE
	GLIMPSE = path
	return

def quote(s):
	"""Adds quotes around a string.

	Useful for multi-word searches.

	This is necessary because glimpse expects one command-line argument
	for the search string.
	"""

	# Strip all quotes first, then quote the whole search string.
	s = regsub.gsub('[\'\"]', '', s)
	return '\'' + s + '\''


def wais_to_glimpse(query):
	"""Converts wais query to glimpse query."""

	query = string.lower(query)
	query = regsub.gsub(' and ', ';', query)
	query = regsub.gsub(' or ', ',', query)
	query = regsub.gsub(' not ', '!', query)
	query = regsub.gsub('*', '#', query)
	query = regsub.gsub('(', '{', query)
	query = regsub.gsub(')', '}', query)
	return query


def search( pattern, directory_name, options='' ):
	"""Performs a glimpse search.

	The '-y' option means to answer yes to any prompts.
	The '-H' names the location of the index files.

	"""
	index_path = os.path.join(directory_name, '.glimpse_index')
	if not os.path.exists(index_path):
		raise indexerror, 'Full text searching not available at this time (Glimpse index files not generated).  Please check back later.'
	command = GLIMPSE + ' -y -H ' + directory_name + SP + options +  SP \
		+ quote( pattern )
	fd = os.popen( command )
	# readlines and return results just as glimpse returns them.
	lines = fd.readlines()

	results = []
	for line in lines:
		results.append( line[:-1] ) # strip of newlines chars.
	return results
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
