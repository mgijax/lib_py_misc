# table.py

"""
Support for generating WWW reports.

INTRODUCTION

This module provides a class (Table) for generating output in a table format.
It allows HTML withing the table (to some extent), and provides a lot of
control over the output formats.

This is a newer implementation of table.py.  It does not use HTMLgen.py now.

There is also a module called MGItable.py that contains subclasses of the
Table class in this module.  For long-term code, you should probably use that.


USING THE TABLE CLASS

1. Begin by writing "import table".  You could do "from table import Table"
   but Table might cause problems in your namespace (eg, HTMLgen.Table).
2. Create an instance of the Table class, with an optional title.
3. Set the heading attribute to a list of strings.
4. Set the body attribute to a list of lists, with each (inner) list containing
   strings or objects that have __repr__ methods that return strings.
5. Set attributes to control the appearance of the table.  See the Table class
   itself for a complete list of available attributes, along with their default
   values.
6. Call the instance as a function to get a string representation of the table.
   There are four options for output formats currently supported -- `netscape',
   `pre', `text' and `auto'.  `auto' tries to figure out the best format for you
   automagically.

	or

6. Use the write method to write the table to a file.  The default file is
   sys.stdout.

A Simple Example:

	import table

	#Build your list using your favorite method.
	body = [['1','Rick'], ['2','John'], ['3', 'Lori']]
	#Build your heading using your favorite method.
	heading = ['foo', 'bar']

	t = table.Table('My First Table')
	t.heading = heading
	t.body = body
	t.sep = '  ' #Use 2 spaces instead of just one.
	t.write('auto') #Automatically determine best output format

Attributes can also be set at instantiation time (and changed later, if
desired).

Example:

	#This example is equivalent to the one above.
	import table

	body = [['1','Rick'], ['2','John'], ['3', 'Lori']]
	heading = ['foo', 'bar']

	t = table.Table(
		'My First Table',
		heading=heading,
		body=body,
		sep='  ',
		)
	t.write() #Same as passing `auto'


IT SLICES, IT DICES...

Here are some examples of things you can do and how to do them.

1.  Tab-delimited text

	import table

	body = [['1','Rick'], ['2','John'], ['3', 'Lori']]
	heading = ['foo', 'bar']

	t = table.Table('My First Table')
	t.heading = heading
	t.body = body
	t.sep = '\t'
	t.pad = 0 #Don't pad the cells with blanks
	t.write( 'text' )

2.  Tab-delimited text, stripping all HTML from the results

	import table

	body = [['1','Rick'], ['2','John'], ['3', 'Lori']]
	heading = ['foo', 'bar']

	t = table.Table('My First Table')
	t.heading = heading
	t.body = body
	t.sep = '\t'
	t.pad = 0
	t.filter = 1 #Strip anything that looks like an HTML tag.
	t.write( 'text' )

3.  The Table class will convert everything to string for you.  This means you
    can give it integers, strings, floating-point, etc.  Anything will work as
    long as it has a repr method.  The Python value None will be converted to
    an empty string, rather than the string 'None'.

4.  The Table class has an attribute `group' that will group the cells in your
    table, intelligently eliminating duplicates.

5.  You can sort your table by any combination of column numbers, headings,
    with any combination of (optional) comparison functions.  Of course, doing
    this on huge tables in Python will take forever...

More examples will be added as time permits and as features are added.


METHODS AVAILABLE OUTSIDE THE CLASS

__len__():
	Returns the number of rows in the table.

read(): *Not implemented yet*
	Reads a table from a file.

reverse():
	Reverses the rows of the table.

sort(arg=None, html=0):
	Sorts by given key(s) with optional comparison function(s).

sql(): *Not implemented yet*
	Performs a query or list of queries.

write(format='auto', outfile=sys.stdout):
	Writes a table to a file.


FUNCTIONS

There are a few functions that are public, for convenience.

browser_is_netscape():
	Returns non-zero if browser is Netscape.

filter_html( string ):
	Strips HTML tags from a string.

escape( string ):
	Replace special characters '&', '<' and '>' by SGML entities.

unescape( string ):
	Opposite of escape().

def hlen( string ):
	Returns length of a string after stripping HTML and unescaping.


THINGS TO DO

1. Add colspan support for __text method.
2. Implement group method and attribute.
3. Add sort attribute.  Right now it is just a method.
4. Implement read method (and attribute?).
5. Implement sql method.
6. Speed up cell_width attribute for 'pre' and 'text'
7. Right now, headings can only be plain text.  Perhaps they should handle
   HTML?  There are many issues that must be settled before doing this.  For
   example, Macintoshes seem to totally screw up column alignments when <I>
   tags are used in preformatted text, so <I> tags should not be used w/
   preformatted text (in the body, too.)
8. We could add a new class, FastTable, that does not make a copy of the
   entire table, and any modifications to it (sort, break, etc.) would
   permanently affect the table (instead of a copy of the table).
"""

__author__ = 'Glenn T. Colby   gtc@informatics.jax.org'

# Imports
# =======

import cgi
import regsub
import string
import os
import sys
import regex


# Regular Expressions
# ===================

tag_pattern = regex.compile( '<[^>]*>' )


# Functions
# =========

def browser_is_netscape():
	"""Returns non-zero if browser is Netscape."""

	if os.environ.has_key('HTTP_USER_AGENT'):
		return regex.match('Mozilla', os.environ['HTTP_USER_AGENT']) + 1
	else:
		return 0


def filter_html( s ):
	"""Strips HTML tags from a string."""

	if string.find (s, '<') == -1:		# short-circuit to avoid slow
		return s			# gsub call, if possible
	return gsub( '<[^>]*>', '', s )


def filter_text( s ):
	"""Recursive function that strips text from a string, leaving HTML tags.

	This is the opposite of filter_html.

	This might be useful if you are trying to do word-wrapping with
	preformatted text that contains markup.
	"""

	tag_start =  tag_pattern.search( s )
	if tag_start != -1:
		s = s[tag_start:]
		tag_length = tag_pattern.match( s )
		return s[:tag_length] + filter_text( s[tag_length:] )
	else:
		return ''


def escape( s ):
	"""Replace special characters '&', '<' and '>' by SGML entities."""

	return cgi.escape( s )


def unescape(s):
	"""Opposite of escape()."""

	if string.find (s, '&') == -1:		# short-circuit to avoid slow
		return s			# gsub call, if possible
	s = gsub("&amp;", "&", s)
	s = gsub("&lt;", "<", s)
	s = gsub("&gt;", ">", s)
	return s


def hstrip(s):
	"""Filters, then unescapes."""

	return unescape(filter_html(s))


def hlen(s):
	"""Returns length of a string after stripping HTML and unescaping.

	This is to determine the length of a string as it will be displayed by
	the browser.
	"""

	return len(hstrip(s))


def filter_index( i, s ):
	"""Returns index for a given char s[i] after filtering HTML."""

	return len(filter_html(s[:i]))


def HTML_index( index, s ):
	"""Returns the `real' index of a char that has a given filter_index.

	This could be done much more efficiently...

	Used by __wrap() method.
	"""

	l = []
	for i in range(len(s)):
		l.append( s[:i] )
	l = map( filter_html, l )
	l = map( len, l )
	for i in range(len(l)-1, 0, -1):
		if index == l[i]:
			break
	return i


def hsplit( s, width ):
	"""Inserts newlines at appropriate places for preformatted text.

	Used by __wrap method.
	"""

	f = filter_html(s)
	if width >= len(f):
		return s
	i = width
	if ' ' in f[:i]:
		while i:
			if f[i-1] == ' ':
				break
			i = i - 1
	first_line = s[:HTML_index(i,s)] \
		+ filter_text(s[HTML_index(i,s):])
	second_line = hsplit(
		filter_text(s[:HTML_index(i,s)]) + s[HTML_index(i,s):],
		width
		)
	return first_line + '\n' + second_line


def lsort(list, field, html, func = cmp):
	"""Sorts a list by a field using optional comparison function.

	list - A sequence (a list, dictionary, tuple, etc.).  If you pass a
		tuple, you'll get a tuple back.
	field - An index or dictionary key.
	html - A 0|1 flag indicating whether or not to strip HTML and unescape
		SGML entities prior to the comparison.
	func - The comparison function to use when sorting.

	Note:  Leaves other columns in correct order.  This is important.

	This function was inspired by an example in the Programming Python book
	on p. 499.  If there is a problem that's probably a good place to start.
	"""

	# return operand type
	result = list[:0]
	for j in range(len(list)):
		i = 0
		if html:
			for y in result:
				if func( hstrip(list[j][field]),
					hstrip(y[field]) ) < 0: break
				i = i + 1
		else:
			for y in result:
				if func( list[j][field], y[field] ) < 0: break
				i = i + 1
		result = result[:i] + list[j:j+1] + result[i:]
	return result


# Aliases
# =======
ljust = string.ljust
center = string.center
rjust = string.rjust
join = string.joinfields
strip = string.strip
gsub = regsub.gsub
StringType = type('s')
ListType = type([])
TupleType = type((0,1))
IntType = type(0)
FunctionType = type(escape)
FileType = type(sys.stdout)


class Table:
	"""Construct a Table with Python lists.

	Instantiate with a string argument for the table's name (caption).
	Set object.heading to a list of strings representing the column
	headings.  Set object.body to a list of lists representing rows.

	KEYWORD PARAMETERS

	Defaults in (parenthesis).  Keyword parameters may be set as attributes
	of the instantiated table object as well.

	Keyword Parameters Available to `netscape', `pre' and `text' formats.

		body -- a list of lists in row major order containing strings
			or objects to populate the body of the table.
			( [['&nbsp;']*3] )
		caption_align -- 'top'|'bottom'  specifies the location of the
			table title ('top')
		cell_align -- 'left'|'right'|'center'  text alignment for all
			other cells. ('left')
		column1_align -- 'left'|'right'|'center'  text alignment of the
			first column. ('left')
		escape -- 1|0  flag to determine if special characters '&', '<'
			and '>' should be replaced by SGML entities.  (0)
		filter -- 1|0  flag to determine if HTML tags, or at least what
			appear to be HTML tags, should be filtered out.  (0)
		group -- 1|0 flag to determine if table columns should be
			grouped.  See __group method for full description.  (0)
		heading --  list of strings, the length of which determine the
			number of columns.  ( None )
		heading_align -- 'center'|'left'|'right'
                        horizontally align text in the header row ('center')
		unescape -- 1|0  flag to determine if SGML entities
			representing special characters '&', '<' and '>' should
			be replaced by the characters themselves.  This is the
			inverse of escape.  (0)

	Keyword Parameters Available to 'netscape' format only.

		blank -- string to output in place of a blank cell
		border -- the width in pixels of the bevel effect around the
			table (2)
		cell_line_breaks -- 1|0  flag to determine if newline char in
			body text will be converted to <br> symbols; 1 they
			will, 0 they won't.  (1)
		cell_valign --  'middle' |'top'|'bottom'  vertically align
			text in all cells.  This does not appear to work
			in Netscape for Digital Unix.  ('middle')
		cell_padding -- the distance between cell text and the cell
			boundary (4)
		cell_spacing -- the width of the cell borders themselves.  (1)
		colspan -- a list specifying the number of columns spanned by
			that heading index. e.g. t.colspan = [2,2] will place 2
			headings spanning 2 columns each (assuming the body has
			4 columns).
		colors -- a list of color codes for netscape to cycle through
			when displaying rows.  e.g.- [ '#ffffff', '#eeeeee' ]
		heading_nobreak -- 1|0 flag to determine if spaces in heading
			should be replaced by '&nbsp;'.  This only applies if
			the browser is Netscape.  (0)
		heading_valign --  'middle' |'top'|'bottom'  vertically align
			text in the header row.  This does not appear to work
			in Netscape for Digital Unix.  ('middle')
		width -- the width of the entire table wrt the current window
			width.  ('100%')

	Keyword Parameters Available to 'text' and 'pre' formats only.

		cell_width -- Integer or list of integers specifying the width
			of the cells in each column.  ( None )
		line_spacing -- Integer specifying how many newlines should
			appear at the end of each row.  A 1 means singlespaced,
			a 2 means doublespaced, etc.  ( 1 )
		pad -- 1|0 flag to determine if table cells should be padded
			with spaces. (1)
		sep -- String used to separate columns. ( ' ' )
	"""

	def __init__(self, tabletitle='', **kw):
		"""Arg1 is a string title for the table caption, optional
		keyword arguments follow.
		"""

		# Specify the default values
		self.blank = ''			# string output for blank cell
		self.body = [['&nbsp;']*3]
		self.border = 2
		self.caption_align = 'top'
		self.cell_padding = 1
		self.cell_spacing = 1
		#Cell width is used by __text method, but is too slow.
		#self.cell_width = None
		self.column1_align = 'left'
		self.cell_align = 'left'
		self.cell_valign = 'top'
		self.cell_line_breaks = 1
		self.colspan = None
		self.colors = [ '#ffffff' ]	# white rows only by default
		self.escape = 0
		self.filter = 0
		self.group = 0
		self.heading = None
		self.heading_align = 'center'
		self.heading_nobreak = 0
		self.heading_valign = 'top'
		self.line_spacing = 1
		self.oneRowColor = 0		# index in self.colors of the
						# color to use when we only
						# have one body row
		self.pad = 1
		self.sep = ' '
		self.tabletitle = tabletitle
		self.unescape = 0
		self.width = '100%'

		# Now overlay the keyword arguments from caller
		for k in kw.keys():
			if k == 'body': #Must repr the body
				self.body = kw['body']
			elif self.__dict__.has_key(k):
				self.__dict__[k] = kw[k]
			else:
				print `k`, "not a valid parameter for class."


	def __str(self, obj):
		"""Converts an object to string (same as str except None -> ''.

		This is necessary in case the object is None.  str would
		convert None to 'None', which we don't want to print.
		"""
		if obj is None:
			return ''
		else:
			return str(obj)


	def __setattr__(self, name, value):
		self.__dict__[name] = value

		# Converting everything in body to string.
		if name == 'body':
			self.__copy = []
			for i in range(len(value)):
				self.__copy.append(map(self.__str, value[i]))


	def fixBlank (self, s):
		# Purpose: returns 's' if it is non-blank, or a defined
		#	string (self.blank) to substitute for a blank 's'
		# Returns: string
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		if s == '':
			return self.blank
		return s

	def isNewLogicalRow (self,
		oldRow,
		newRow
		):
		# Purpose: determine if 'newRow' is a new logical row when
		#	considering 'oldRow'
		# Returns: boolean (0/1); 1 if 'newRow' is indeed a new
		#	logical row
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing
		# Notes: A new logical row is one which should get a distinct
		#	color (if available) from the previous row.  It
		#	indicates that this row is a different logical object,
		#	not just a continuation of the previous row.

		return 1		# always consider as a new row

	def __netscape(self):
		"""Generates an HTML Table object using Netscape-style tags."""

		s = ''
 
		s = s + '<TABLE border=%s ' % self.border \
			+ 'cellpadding=%s ' % self.cell_padding \
			+ 'cellspacing=%s ' % self.cell_spacing \
			+ 'width="%s">\n' % self.width
		if self.tabletitle:
			s = s + '<CAPTION align=%s>' % self.caption_align \
				+ '<STRONG>%s</STRONG>' % self.tabletitle \
				+ '</CAPTION>\n'

		if self.cell_line_breaks:
			# process cell contents to insert breaks for \n
			for i in range(len(self.body)):
				for j in range(len(self.body[i])):
					self.body[i][j] = gsub('\n', '<br>',
						strip(self.body[i][j]))

		# Convert spaces in heading to &nbsp; (Netscape only).
		if self.heading_nobreak and browser_is_netscape():
			for i in range(len(self.heading)):
				self.heading[i] = gsub( ' ', '&nbsp;',
					self.heading[i] )

		# Initialize colspan property to 1 for each
		# heading column if user doesn't provide it.
		if self.heading:
			if not self.colspan:
				if type(self.heading[0]) == ListType:
					self.colspan = [1]*len(self.heading[0])
				else:
					self.colspan = [1]*len(self.heading)

		# Construct heading spec
		#  can handle multi-row headings. colspan is a list specifying
		#  how many columns the i-th element should span. Spanning only
		#  applies to the first or only heading line.
		if self.heading:
			prefix = '<TR Align=%s' % self.heading_align \
				+ ' VALIGN=%s> ' % self.heading_valign
			postfix = '</TR>\n'
			middle = ''
			if type(self.heading[0]) == ListType:
				for i in range(len(self.heading[0])):
					middle = middle + '<TH ColSpan=%s>' % \
						self.colspan[i] \
						+ str(self.heading[0][i]) \
						+'</TH>'
				s = s + prefix + middle + postfix
				for i in range(len(self.heading[1])):
					middle = middle + '<TH>' \
						+ str(self.heading[i]) +'</TH>'
				for heading_row in self.heading[1:]:
					for i in range(len(self.heading[1])):
						middle = middle + '<TH>' \
							+ heading_row[i] \
							+'</TH>'
					s = s + prefix + middle + postfix
			else:
				for i in range(len(self.heading)):
					middle = middle \
						+ '<TH ColSpan=%s>' % \
							self.colspan[i] \
						+ str(self.heading[i]) +'</TH>'
				s = s + prefix + middle + postfix

		# find out if there's more than one "logical row" so we know
		# what to do about swapping colors.  (If there are fewer than
		# two logical rows, then we start with self.oneRowColor.)

		logical_rows = 0
		lastRow = []
		for row in self.body:
			if self.isNewLogicalRow (lastRow, row):
				logical_rows = logical_rows + 1
				if logical_rows >= 2:
					break
			lastRow = row

		# construct the rows themselves
		num_colors = len(self.colors)
		if logical_rows <= 1:
			i = self.oneRowColor - 1
		else:
			i = -1
		lastRow = []
		for row in self.body:
			if self.isNewLogicalRow (lastRow, row):
				i = i + 1
			color = self.colors[i % num_colors]

			prefix = '<TR VALIGN=%s BGCOLOR="%s"> ' % \
				(self.cell_valign, color) \
				+ '<TD Align=%s>' % self.column1_align
			postfix = '</TD> </TR>\n'
			infix = '</TD> <TD Align='+self.cell_align+'>'
			s = s + prefix + \
				string.join(
					map (self.fixBlank, row),
					infix) + \
				postfix
			lastRow = row

		#close table
		s = s + '</TABLE><P>\n'

		return s

	def __wrap(self):

		if type(self.cell_width) == IntType:
			widths = []
			for i in range(len(self.body[0])):
				widths.append(self.cell_width)
			self.cell_width = widths

		for i in range(len(self.body)):
			for j in range(len(self.body[i])):
				if self.cell_width[j]:
					self.body[i][j]=hsplit(self.body[i][j],
						self.cell_width[j])


	def __text(self, pre=0):
		"""Generates a Table in text format.

		pre -- 1|0 flag to determine if output is preformatted or
			plain text.  Preformatted text is intended for display
			by an HTML browser.
		"""

		s = ''

		if pre:
			s = s + '<PRE>\n'

		# Figure out which heading_align function to use.
		if self.heading_align == 'right':
			heading_align = rjust
		elif self.heading_align == 'center':
			heading_align = center
		else:
			heading_align = ljust

		# Figure out which cell_align function to use.
		if self.cell_align == 'right':
			cell_align = rjust
		elif self.cell_align == 'center':
			cell_align = center
		else:
			cell_align = ljust

		# Figure out which column1_align function to use.
		if self.column1_align == 'right':
			column1_align = rjust
		elif self.column1_align == 'center':
			column1_align = center
		else:
			column1_align = ljust

		if not self.cell_line_breaks:
			for i in range(len(self.body)):
			    for j in range(len(self.body[i])):
				# only call the slow gsub() function if we
				# determine that we really need to:

				if string.find (self.body[i][j], '\n') != -1:
					self.body[i][j] = gsub('\n', ' ',	
						self.body[i][j])

		#Fix column widths if necessary.
		#This is commented out because it is too slow.  It ends up
		#making an *additional* copy of the entire table.
		#if self.cell_width:
		#	self.__wrap()

		# Build list of column widths iff padding cells with spaces.
		if self.pad:
			self.__widths = [0]*len(self.body[0])
			#self.__widths = [0]*255 # max number of columns (Yuck!)
			if self.heading:
				for i in range( len( self.heading ) ):
					if pre:
						self.__widths[i] = len(
							filter_html(
								self.heading[i])
								)
					else:
						self.__widths[i] = len(
							self.heading[i])
			for row in self.body:
				for i in range( len( row ) ):
					if pre:
						self.__widths[i] = max(
							self.__widths[i],
							hlen(row[i]))
					else:
						self.__widths[i] = max(
							self.__widths[i],
							len(row[i]))

		# Determine width of table, to be used later.
		table_width = 0
		if self.pad:
			for i in range( len( self.body[0] ) ):
				table_width = table_width + self.__widths[i] \
					+ len(self.sep)
			table_width = table_width \
				- len(self.sep)

		# Center the title (caption).
		if self.tabletitle and self.caption_align == 'top':
			s = s + center( self.tabletitle, table_width ) + 2*'\n'

		# Dump column headings into table.
		if self.heading:
			if self.pad:
				l = []
				for i in range(len(self.heading)):
					cell = self.heading[i]
					if pre:
						offset = len(cell) - hlen(cell)
					else:
						offset = 0
					heading = heading_align(cell,
						self.__widths[i] + offset)
					l.append( heading )
			else:
				l = self.heading
			s = s + join( l, self.sep ) + 2*'\n'

		# Dump cells into table.
		for row in self.body:
			if self.pad:
				l = []
				for i in range(len(row)):
					cell = row[i]
					if pre:
						offset = len(row[i]) \
							- hlen(row[i])
					else:
						offset = 0
					if i == 0:
						r = column1_align( row[i],
							self.__widths[i] \
							+ offset )
					else:
						r = cell_align( row[i],
							self.__widths[i] \
							+ offset )
					l.append( r )
			else:
				l = row
			s = s + join( l, self.sep ) + self.line_spacing*'\n'

		# Center the title (caption).
		if self.tabletitle and self.caption_align == 'bottom':
			s = s + '\n' + center( self.tabletitle, table_width ) \
				+ '\n'

		if pre:
			s = s + '</PRE>\n'
		return s


	def __escape_html(self):
		"""Converts everythin in the table to string and escapes it.

		**WARNING:** the body attribute will be edited to conform to
		html. If you don't want your data changed make a copy of this
		list and use that with the table object.
		"""

		for i in range(len(self.body)):
			self.body[i] = map( str, self.body[i] )
			self.body[i] = map( escape, self.body[i] )


	def __unescape_html(self):
		"""Converts everythin in the table to string and unescapes it.

		**WARNING:** the body attribute will be edited to conform to
		html. If you don't want your data changed make a copy of this
		list and use that with the table object.
		"""

		for i in range(len(self.body)):
			self.body[i] = map( str, self.body[i] )
			self.body[i] = map( unescape, self.body[i] )


	def __filter_html(self):
		"""Strips anything that looks like HTML from the table.

		**WARNING:** the body attribute will be edited to conform to
		html. If you don't want your data changed make a copy of this
		list and use that with the table object.
		"""

		for i in range(len(self.body)):
			self.body[i] = map( str, self.body[i] )
			self.body[i] = map( filter_html, self.body[i] )


	def __len__(self):
		"""Returns the number of rows in the table."""

		return len(self.body)


	def __group(self):
		"""Groups results by given column(s).

		This will modify (a copy of) the table so that duplicate cells
		are not printed, as shown below:

		c1	c2	c3
		a	b	c
			d	e
			f	g
		b	d	h
				i
		c	s	j
		"""

		for i in range( len(self.body)-1, 0, -1 ):
			for j in range( len(self.body[i]) ):
				if self.body[i][j] == self.body[i-1][j]:
					self.body[i][j] = ''
				else:
					break


	def read(self, file=sys.stdin):
		"""Reads a table from a file.

		Not implemented yet.  (Duh...)  This method will probably open
		a file that contains tab-delimited text and build self.body.
		Seems useful.

		Perhaps some regex support as well?

		Maybe pass a function as an argument that will process a string
		and return a list?
		"""
		pass


	def reverse(self):
		"""Reverses the rows of the table."""
		self.__copy.reverse()


	def sort(self, arg=None, html=0):
		"""Sorts by given key(s) with optional comparison function(s).

		arg -- Sort key(s), function(s).  Read below for description.
		html -- 1|0 flag indicating whether HTML should be stripped out
			and escape sequences converted back to text prior to
			comparison.

		This function allows any combination of sort keys and
		comparison functions by allowing arg to be

			- a key (string or integer).  If key is a string, sort
				will determine the index of the string based
				on the contents of self.header.
			- a comparison function that compares two strings,
				returning -1, 0 or 1.
			- a tuple containing a key and a comparison function.
			- a list of keys or tuples (as described above).

		Example:

		Python 1.4 (Jan  2 1997) [C]
		Copyright 1991-1995 Stichting Mathematisch Centrum, Amsterdam
		>>> import table
		>>> t = table.Table()
		>>> t.body = [
		...	['Ren1', 2, 3],
		...	['Ren12', 6, 2],
		...	['Ren2', 7, 1],
		...	[4, 5, 6],
		...	]
		>>> t.heading = ['Column 1', 'Column 2', 'Column 3']
		>>> t.write() #Print table before sorting.
		Column 1 Column 2 Column 3
 
		Ren1     2        3       
		Ren12    6        2       
		Ren2     7        1       
		4        5        6       
		>>> t.sort('Column 3') # Same as t.sort(2)
		>>> t.write()
		Column 1 Column 2 Column 3
 
		Ren2     7        1       
		Ren12    6        2       
		Ren1     2        3       
		4        5        6       
		>>> t.sort() # Sort all the columns left to right, ASCII
		>>> t.write()
		Column 1 Column 2 Column 3
 
		4        5        6       
		Ren1     2        3       
		Ren12    6        2       
		Ren2     7        1
		>>> from mgi_utils import byNumeric # A comparison function
		>>> t.sort( (0, byNumeric) ) # Will sort marker symbols right.
		>>> t.write()
		Column 1 Column 2 Column 3
 
		4        5        6       
		Ren1     2        3       
		Ren2     7        1       
		Ren12    6        2       
		"""

		#Build a list of tuples of form [(int, function), ....]
		try:
			if arg == None:
				arg = []
				for i in range(len(self.__copy[0])):
					arg.append( (i, None) )
			elif type(arg) == IntType:
				arg = [ (arg, None) ]
			elif type(arg) == StringType:
				key = arg
				i = self.heading.index(arg)
				arg = [ (i, None) ]
			elif type(arg) == TupleType:
				if type(arg[0]) == StringType:
					key = arg[0]
					arg = (self.heading.index(arg[0]),
						arg[1])
				elif type(arg[0]) != IntType:
					key = arg[0]
					raise TypeError
				arg = [ arg ]
			elif type(arg) == ListType:
				for i in range(len(arg)):
					a = arg[i]
					if type(a) == IntType:
						a = (a, None)
					elif type(a) == StringType:
						key = a
						i = self.heading.index(a)
						a = (i, None)
					elif type(a) == TupleType:
						if type(a[0]) == StringType:
							key = a[0]
							a = (self.heading.index(
								a[0]), a[1])
					arg[i] = a
			elif type(arg) == type(escape):
				func = arg
				arg = []
				for i in range(len(self.__copy[0])):
					arg.append( (i, func) )
			else:
				print 'TypeError:', str(arg), str(type(arg))
				return
				
		except ValueError:
			print 'ValueError:', str(key)
			return
		except TypeError:
			print 'TypeError:', str(key), str(type(key))
			return

		arg.reverse()
		for t in arg:
			key = t[0]
			func = t[1]
			if func == None:
				self.__copy = lsort(self.__copy, key, html)
			else:
				self.__copy = lsort(self.__copy, key, html,
					func)


	def sql(self):
		"""Performs a query or list of queries.

		Not sure how this will work yet.  Perhaps set an attribute
		containing a list of results, each of which is an instance of
		the Table class?  How do we handle errors?  Perhaps just dump
		them to stderr?

		Not implemented yet.  (Duh...)

		This might be a good test for Geoff's new sybasemodule.
		"""
		pass


	def write(self, format='auto', outfile=sys.stdout):
		"""Writes a table to a file.

		format -- 'netscape', 'pre', 'text', or 'auto'. ('auto')
		outfile -- Can be a filename or file descriptor. (sys.stdout)
		"""
		if type(outfile) == FileType:
			fd = outfile
		else:
			fd = open( outfile, 'w' )

		fd.write( self(format) )

		if fd is not sys.stdout and type(outfile) == FileType:
			fd.close()


	def __call__(self, format='auto'):
		"""Returns a string representation of table in given format.

		format -- 'netscape', 'pre', 'text', or 'auto'. ('auto')

		This should probably be changed to __repr__(self), with
		format being an attribute instead of a parameter.  Maybe after
		the May release...
		"""

		#Get the original copy of the body.
		self.body = self.__copy[:]

		#Process the body, if necessary.
		if self.escape:
			self.__escape_html()
		if self.filter:
			self.__filter_html()
		if self.unescape:
			self.__unescape_html()
		if self.group:
			self.__group()

		# Decide what format to use.
		if format == 'auto':
			if os.environ.has_key('REMOTE_ADDR'):
				if browser_is_netscape():
					format = 'netscape'
				else:
					format = 'pre'
			else:
				format = 'text'

		#Generate the table.
		if format == 'netscape':
			s = self.__netscape()
		elif format == 'text':
			s = self.__text(pre=0)
		elif format == 'pre':
			s = self.__text(pre=1)
		else:
			print `format`, "not a valid parameter for method."
			return

		return s

class StripedTable (Table):
	# IS: a Table with rows in alternating colors, by default gray and
	#	white.
	# HAS: see Table
	# DOES: see Table

	def __init__(self, tabletitle='', **kw):

		Table.__init__ (self, tabletitle)

		# update default settings for this type of table

		self.blank = '&nbsp;'
		self.cell_padding = 3
		self.cell_spacing = 0
		self.colors = [ '#dddddd', '#ffffff' ]
		self.oneRowColor = 1

		# Now overlay the keyword arguments from caller
		for k in kw.keys():
			if k == 'body': #Must repr the body
				self.body = kw['body']
			elif self.__dict__.has_key(k):
				self.__dict__[k] = kw[k]
			else:
				print `k`, "not a valid parameter for class."

class MultiRowStripedTable (StripedTable):
	# IS: a StripedTable which handles multiple physical rows per logical
	#	row.  (A row may be continued into the next row by providing
	#	blank cells to the left.)
	# HAS: see Table
	# DOES: see Table

	def isNewLogicalRow (self,
		oldRow,
		newRow
		):
		# Overrides Table.isNewLogicalRow() to handle the case of
		# continued rows.

		if not oldRow:
			return 1
		return newRow[0] not in [ '', ' ', '&nbsp;' ]

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
# Copyright © 1996, 1999, 2002 by The Jackson Laboratory
# All Rights Reserved
#
