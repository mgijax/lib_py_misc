# Name: SimpleVocab.py
# Purpose: provides classes for easily accessing simple (non-DAG) vocabularies
#	from the VOC_* tables in the MGI database.
# Notes: By default, this module uses the db module's sql() function for
#	database access.  The db module provides functions to override its
#	default settings for server, database, user, and password.  You may
#	change any of these before instantiating your SimpleVocab objects.
#	Or, you may use the set_sqlFunction() function to choose a different
#	database-access function like wi_db.sql() for the web interface.
#	(This follows the convention established by accessionlib.py)
# Example:
#	How to show each term defined for the PhenoSlim vocabulary..
#		import SimpleVocab
#		phenoslim = SimpleVocab.PhenoSlimVocab()
#		for term in phenoSlim.getTerms():
#			print term.getTerm()

import db
import string

###--- Global Constants ---###

error = 'SimpleVocab.error'	# exception raised by this module

# values passed along when 'error' is raised as an exception:

NO_VOCAB = 'Could not find unique vocabulary named "%s"'
NOT_SIMPLE = 'Vocabulary "%s" is not a simple vocabulary.'

###--- Function used to execute SQL commands ---###

sql = db.sql		# by default, use the db library's sql() function

def set_sqlFunction (
	fn		# function; what function to use to execute SQL
	):
	# Purpose: change the function used to execute SQL statements from
	#	its default value to 'fn'
	# Returns: nothing
	# Assumes: 'fn' has the same inputs and outputs as db.sql()
	# Effects: updates the global 'sql'
	# Throws: nothing

	global sql
	sql = fn
	return

###--- Classes ---###

class Term:
	# IS: one term in a simple vocabulary
	# HAS: the term itself, and its associated database key, abbreviation,
	#	note, synonyms, and accession ID
	# DOES: provides accessor methods for the five public attributes--
	#	term, abbreviation, note, synonyms, and accession ID

	def __init__ (self,
		_Term_key,	# integer; unique database key of the term
		term,		# string; the term itself
		abbreviation,	# string; abbreviation for the term
		note = None,	# string; note associated with the term
		synonyms = [],	# list of strings; synonyms for the term
		accID = None	# string; accession ID for the term
		):
		# Purpose: constructor
		# Returns: nothing
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		self._Term_key = _Term_key
		self.term = term
		self.abbreviation = abbreviation
		self.note = note
		self.synonyms = synonyms
		self.accID = accID
		return

	def getKey (self):
		# Purpose: accessor method for the term key
		# Returns: string
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self._Term_key

	def getTerm (self):
		# Purpose: accessor method for the term itself
		# Returns: string
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.term

	def getAccID (self):
		# Purpose: accessor method for the term's accession ID
		# Returns: string or None
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.accID

	def getAbbreviation (self):
		# Purpose: accessor method for the term's abbreviation
		# Returns: string
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.abbreviation

	def getNote (self):
		# Purpose: accessor method for the term's associated note
		# Returns: string or None (if no associated note)
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.note

	def getSynonyms (self):
		# Purpose: accessor method for the term's associated synonyms
		# Returns: list of strings (may be an empty list)
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.synonyms

class SimpleVocab:
	# IS: a simple vocabulary, stored in the VOC_* tables in the database
	# HAS: a name and an ordered set of Terms
	# DOES: loads the vocabulary from the database and provides accessor
	#	methods for the name and the Terms
	# Notes: We do not provide an accessor method for the _Vocab_key
	#	attribute, as we would like it to be considered private.

	def __init__ (self,
		vocabName,		# string; name of the vocabulary
		termClass = Term	# class to instantiate for each Term
		):
		# Purpose: constructor
		# Returns: nothing
		# Assumes: nothing
		# Effects: connects to the database and reads the vocabulary
		# Throws: raises 'error' if no match is found for 'vocabName'
		#	or if the database does not list 'vocabName' as a
		#	simple vocabulary.  propagates any exceptions raised
		#	by the call to 'sql()'.

		# look up 'vocabName' in the database to find its key and to
		# verify that it is a simple vocabulary

		result = sql ('''
			select _Vocab_key, isSimple
			from VOC_Vocab
			where name = "%s"''' % vocabName, 'auto')

		if len(result) != 1:				# error checks
			raise error, NO_VOCAB % vocabName
		if not result[0]['isSimple']:
			raise error, NOT_SIMPLE % vocabName

		# initialize the vocabulary's attributes

		self._Vocab_key = result[0]['_Vocab_key']
		self.name = vocabName
		self.terms = []

		# In an OO-sense, it might be more "correct" to have each Term
		# look up its own attributes using its key.  For the sake of
		# efficiency, though, we look up all the notes, synonyms, and
		# accession IDs here in one batch and cache them for use in
		# the Term-creation step later on.

		[ note_rows, synonym_rows, accID_rows ] = sql ( [

			'''select tx._Term_key, tx.note, tx.sequenceNum
			from VOC_Term vt, VOC_Text tx
			where vt._Term_key = tx._Term_key
				and vt._Vocab_key = %s
			order by tx._Term_key, tx.sequenceNum''' % \
				self._Vocab_key,

			'''select vs._Term_key, vs.synonym
			from VOC_Term vt, VOC_Synonym vs
			where vt._Term_key = vs._Term_key
				and vt._Vocab_key = %s''' % self._Vocab_key,

			'''select vtv._Term_key, vtv.accID
			from VOC_Term_View vtv
			where vtv._Vocab_key = %s''' % self._Vocab_key,

			], 'auto')

		note_cache = {}		# maps _Term_key to string note
		synonym_cache = {}	# maps _Term_key to list of synonyms
		accID_cache = {}	# maps _Term_key to string accID

		# Initially, the notes are stored in 256-byte chunks.  So,
		# we first collect the chunks in a list and then convert
		# the list to a string after we've collected them all.

		for row in note_rows:
			_Term_key = row['_Term_key']
			if not note_cache.has_key (_Term_key):
				note_cache[_Term_key] = []
			note_cache[_Term_key].append (row['note'])
		for (key, value) in note_cache.items():
			note_cache[key] = string.join (value, '')

		# Simply collect all the synonyms for each term

		for row in synonym_rows:
			_Term_key = row['_Term_key']
			if not synonym_cache.has_key (_Term_key):
				synonym_cache[_Term_key] = []
			synonym_cache.append (row['synonym'])

		# collect the accession ID for each term
		# (we do it in a separate query in case some terms do not
		# have accession IDs)

		for row in accID_rows:
			accID_cache[row['_Term_key']] = row['accID']

		# now get the term attributes and build Term objects

		results = sql ('''
			select _Term_key, term, abbreviation, sequenceNum
			from VOC_Term
			where _Vocab_key = %s
			order by sequenceNum''' % self._Vocab_key, 'auto')

		for row in results:
			_Term_key = row['_Term_key']

			# look up note, if one exists

			if note_cache.has_key (_Term_key):
				note = note_cache[_Term_key]
			else:
				note = None

			# look up synonyms, if any exist

			if synonym_cache.has_key (_Term_key):
				synonyms = synonym_cache[_Term_key]
			else:
				synonyms = []

			# look up accession ID, if one exists

			if accID_cache.has_key (_Term_key):
				accID = accID_cache[_Term_key]
			else:
				accID = None

			# instantiate an object of the given 'termClass' class
			# and add it to self.terms

			self.terms.append (termClass (
						_Term_key,
						row['term'],
						row['abbreviation'],
						note,
						synonyms,
						accID))
		return

	def __len__ (self):
		# Purpose: get the number of terms contained in the vocabulary
		# Returns: integer
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return len (self.terms)

	def getName (self):
		# Purpose: accessor method for the vocabulary's name
		# Returns: string
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.name

	def getTerms (self):
		# Purpose: accessor method for the vocabulary's set of Terms
		# Returns: list of Term objects (may be an empty list)
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.terms[:]

###--- Subclasses for the PhenoSlim Vocabulary ---###

class PhenoSlimTerm (Term):
	# IS: a Term of the PhenoSlim vocabulary
	# HAS: see Term, plus an optional definition and example
	# DOES: see Term, plus splits the note into a definition and example
	#	if possible (and provides accessors for those)
	# Implementation:
	#	If the note contains the string '\\nExample:' then this is a
	#	signal that we can split the note into a definition (the
	#	preceding part of the note) and an example (the following part
	#	of the note).  Otherwise, the definition and example will be
	#	None.

	def __init__ (self,
		_Term_key,	# integer; unique database key of the term
		term,		# string; the term itself
		abbreviation,	# string; abbreviation for the term
		note = None,	# string; note associated with the term
		synonyms = [],	# list of strings; synonyms for the term
		accID = None	# string; accession ID for the term
		):
		# Purpose: constructor
		# Returns: nothing
		# Assumes: nothing
		# Effects: splits 'note' into a definition and an example,
		#	if possible.  See PhenoSlimTerm's Implementation
		#	section.
		# Throws: nothing

		# invoke superclass constructor

		Term.__init__ (self, _Term_key, term, abbreviation, note,
			synonyms, accID)

		# break out the definition and example, if we can

		splitPos = string.find (note, '\\nExample:')
		if splitPos == -1:
			splitPos = string.find (note, '\012Example:')

		if splitPos == -1:
			self.definition = None
			self.example = None
		else:
			self.definition = string.strip(note[:splitPos])
			self.example = string.strip(note[splitPos+10:])
		return

	def getDefinition (self):
		# Purpose: accessor method for the term's definition
		# Returns: string or None
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.definition

	def getExample (self):
		# Purpose: accessor method for the term's example
		# Returns: string or None
		# Assumes: nothing
		# Effects: nothing
		# Throws: nothing

		return self.example

class PhenoSlimVocab (SimpleVocab):
	# IS: a SimpleVocab for the PhenoSlim vocabulary
	# HAS: a name and an ordered list of PhenoSlimTerms
	# DOES: see SimpleVocab
	# Notes: This class provides nothing interesting logically, but serves
	#	as a convenience for code wanting to access the PhenoSlim
	#	vocabulary.

	def __init__ (self):
		# Purpose: constructor
		# Returns: nothing
		# Assumes: nothing
		# Effects: Invokes the superclass constructor to read the
		#	PhenoSlim vocabulary from the database and construct
		#	appropriate objects.
		# Throws: propagates exceptions from SimpleVocab.__init__()

		SimpleVocab.__init__ (self, 'PhenoSlim', PhenoSlimTerm)
		return

###--- Functions ---###

def getSelectionList (
	vocab,				# SimpleVocab object
	size = 5,			# integer; number of terms to show
	fieldname = "phenoslim",	# string; name of HTML field
	url = None,			# string; URL for 'browse' link
	andBox = 0,			# boolean; to show a choice box
					# for allowing an AND/OR selection
	):
	# Purpose: build and return a list of strings for an HTML select box
	#	build from the given 'vocab'
	# Returns: list of HTML strings
	# Assumes: nothing
	# Effects: nothing
	# Throws: nothing

	output = []
	if url:
		output.append ('(<I>You can</I> <a href="%s">' % url \
			+ 'browse the Classification Definitions</a>)<dd>')
	if andBox :
		output.append ('<SELECT NAME="phenoslimAnd">\r\n'\
			       '  <OPTION>ALL\r\n'\
			       '  <OPTION>ANY\r\n'\
			       '</SELECT>\r\n')
	output.append ('<SELECT SIZE=%d MULTIPLE NAME="%s">' % \
		(size, fieldname))
	output.append ('<OPTION VALUE="" SELECTED> ANY')

	terms = vocab.getTerms()
	for term in terms:
		output.append ('<OPTION VALUE=%d> %s' % (term.getKey(),
			term.getTerm()))
	output.append ('</SELECT>')
	return output

def getPhenoslimTable (
	vocab			# PhenoSlimVocab object
	):
	# Purpose: build and return a list of HTML strings which represent
	#	a three-column table (term, definition, example) of the
	#	phenoslim vocabulary
	# Returns: list of strings
	# Assumes: nothing
	# Effects: nothing
	# Throws: nothing

	template = '''<TR><TD><A NAME="%s"></A><B>%s</B></TD>
		<TD>%s</TD><TD>%s</TD></TR>'''
	output = [ '<TABLE BORDER=1 WIDTH="100%">',
		'<TR bgcolor="e0e0e0"><TH width="30%">Term</TH>',
		'	<TH width="45%">Definition</TH>',
		'	<TH width="25%">Example</TH></TR>',
		]
	terms = vocab.getTerms()
	for term in terms:
		output.append (template % (term.getKey(), term.getTerm(),
			term.getDefinition(), term.getExample()))
	output.append ('</TABLE>')
	output.append ('(%d terms)' % len(terms))

	return output

def getPhenoslimTabDelim (
	vocab,			# PhenoSlimVocab object
	headings = [		# four-item list of string column headings
		'Acc ID',
		'Phenotype Classification Term',
		'Definition',
		'Examples' ],
	):
	# Purpose: build and return a list of strings which represent
	#	a four-column tab-delimited table (accID, term, definition,
	#	example) of the given 'vocab'
	# Returns: list of strings
	# Assumes: nothing
	# Effects: nothing
	# Throws: nothing
	# Notes: lines returned do not end with line-break characters

	template = '%s\t%s\t%s\t%s'
	output = []

	# add headings, if specified:
	if headings:
		output.append (template % tuple(headings))
		output.append (template % tuple(map (lambda x: '-' * len(x),
							headings)))
	# add term info:
	terms = vocab.getTerms()
	for term in terms:
		output.append (template % (term.getAccID(), term.getTerm(),
			term.getDefinition(), term.getExample()))
	return output

def getPhenoslimText (
	vocab,			# PhenoSlimVocab object
	headings = [		# four-item list of string column headings
		'Acc ID',
		'Phenotype Classification Term',
		'Definition',
		'Examples' ],
	spacing = 5		# integer; number of spaces between columns
	):
	# Purpose: build and return a list of strings which represent
	#	a four-column table (accID, term, definition, example) of the
	#	given 'vocab'; columns are separated with 'spacing'
	#	space characters
	# Returns: list of strings
	# Assumes: nothing
	# Effects: nothing
	# Throws: nothing
	# Notes: lines returned do not end with line-break characters

	# first, we need to collect the data for each row, then determine the
	# maximum width of each, so that we know how much the smaller values
	# will need to be padded

	data = []
	terms = vocab.getTerms()
	for term in terms:
		data.append ( (term.getAccID(), term.getTerm(),
			str(term.getDefinition()), str(term.getExample()) ) )
	
	width = []
	width.append (max (map (lambda term: len(term[0]), data)))
	width.append (max (map (lambda term: len(term[1]), data)))
	width.append (max (map (lambda term: len(term[2]), data)))

	if headings:
		for i in [ 0, 1, 2 ]:
			width[i] = max (width[i], len(headings[i]))

	# now we construct the output

	spaces = spacing * ' '
	template = '%%s%s%%s%s%%s%s%%s' % (spaces, spaces, spaces)
	output = []

	# add headings, if specified:
	if headings:
		output.append(template % (string.ljust(headings[0], width[0]),
					string.ljust(headings[1], width[1]),
					string.ljust(headings[2], width[2]),
					headings[3]))
		lines = map (lambda x: '-' * len(x), headings)
		output.append(template % (string.ljust(lines[0], width[0]),
					string.ljust(lines[1], width[1]),
					string.ljust(lines[2], width[2]),
					lines[3]))
	# add term info:
	for (accID, term, definition, example) in data:
		output.append (template % (string.ljust (accID, width[0]),
				string.ljust (term, width[1]),
				string.ljust (definition, width[2]),
				example))
	return output

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
