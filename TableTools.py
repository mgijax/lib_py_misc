#!/usr/local/bin/python

HELPTEXT = '''
#
# TableTools.py
#
# A collection of command-line oriented tools for processing
# tabular data stored in delimited text files (e.g., TAB-delimited).
# All tools take table inputs and produce table outputs.
# Currently, these tools read and write files; they do not support
# creating pipelines of operations on memory-resident tables.
# (This is a primary area of planned extentions.)
#
# CONTENTS:
#   The main exported classes (which correspond to the supported
#   operations) are:
#
#        TAggregate : Computes aggregate values (such as max or sum)
#               over specified columns, grouped by specified columns.
#        TBucketize: Bucketizes a table of binary associations between 
#               two sets of objects.
#        TDifference : Outputs rows from the first file whose keys do
#               not occur in the second.
#        TFilter  : Generic filtering/reformatting tool. Caller supplies
#               expressions that restrict and/or reformat the rows.
#               NOTE that ALL tools (except FJoin) support filtering
#               and reformatting of their outputs, so TFilter is often
#               not needed.
#        TIntersection : Outputs rows from the first file whose keys 
#               also occur in the second.
#        TJoin: Joins two tables, in the relation sense. Supports equijoin
#               an generic (theta) join. Supports inner and outer joins.
#        TPartition : Writes the rows to separate files, determined by
#               column values.
#        TSort  : Sorts a table. (Provided for completeness. Use GNU sort
#               instead if available.)
#        TUnion : Outputs all of the first table, followed by all rows
#               of the second whose keys do not occur in the first.
#        TXpand  : Converts list-valued attributes (such as produced by
#               the list aggregation operator) into multiple rows of
#               single-valued attributes.
#        FJoin : Efficiently finds the overlapping pairs in two
#               sets of features. (Note that this tool was developed 
#               independently, and doesn't *really* belong here. Oh well...)
#
#   Along with these operator classes, there are a host of supporting
#   classes which you don't need to know about. However, if you do this:
#
#       from TableTools import *
#
#   you'll get them all. The preferred method is to import just the classes
#   you need, or to use qualified names:
#       import TableTools
#       TableTools.TAggregate(...)
#
#   (If this set of tools were split out and made into a Python package,
#    we would have a better organization for the source code. However,
#    the existing MGI installation tools assume a single directory, while
#    packages exist in subdirectories. Until MGI installs can deal with
#    that, we'll cram everything into one .py file.)
#
# USAGE:
#
#   These tools can be invoked from the command line, or from
#   within Python. Command line invocations have the following form:
#       $ TableTools.py <op> <args> [<exprs>]
#   where <op> is one of the following:
#       ta, tb, td, tf, ti, tj, tp, ts, tu, tx, fj
#   Some parameters are common to all operators, and some
#   are specific to the operator. For help on any operator:
#       $ TableTools.py <op> -h
#
#   Example of command line:
#
#       $ TableTools.py ta -1 file1.txt -g1 -acount "?IN[2] > 1" -o out.txt
#
#   This command counts the number of distinct values in column 1 of
#   the file file1.txt, and writes out those whose count is greater than 1 to
#   the file out.txt. 
#
#   You can also (if you wish) create symbolic links to TableTools.py, using
#   the <op>s as the links' names. For example:
#
#       $ ln -s TableTools.py ta
#       $ ta -1 file1.txt -g1 -acount "?IN[2] > 1" -o out.txt
#
#   You can invoke these operators from within Python. Here's the same command:
#
#       from TableTools import TAggregate
#       ...
#       args=[ "-1", "file1.txt", "-g1", "-acount", "?IN[2] > 1", "-o", "out.txt"]
#       TAggregate(args).go()
#
#    For convenience and consistency with the command line operator names, all
#    the operator classes are aliased to the same name as used in the command
#    line, except in all caps. Therefore, we could also do the following:
#       from TableTools import TA
#       ...
#       TA(args).go()
#
'''
# AUTHOR:
#   Joel Richardson, Ph.D.
#   Mouse Genome Informatics
#   The Jackson Laboratory
#   Bar Harbor, Maine 04609
#   jer@informatics.jax.org
# 
# DATE: 
#   April 2006 - Initial version
#   March 2007 - Modified to fit into MGI frameworks.
#   January 2011 - Replaced calls to string module functions with calls 
#               to corresponding methods. Avoid unnecessary usage of map(str, ...).
#
#

#------------------------------------------------------------
import sys
import types
import os
import re
import math
from optparse import OptionParser
import time
from fjoin import FJoin 
#import gff3


#------------------------------------------------------------
NL      = "\n"
TAB     = "\t"
SP      = " "
COLON   = ":"
HASH    = "#"

#------------------------------------------------------------
# Superclass of all the command-line tools in this library.
# (The one exception is fjoin, what was developed independently.)
#
class TableTool:
    def __init__(self, ninputs, noDefaultOut=False ):
        self.parser = None
        self.args = None
        self.options = None
        self.nOutputRows = 0
        self.functionContext = {}
        self.functions = []
        self.isFilter = []
        self.ninputs = ninputs

        self.t1 = TableFileIterator()
        self.t2 = TableFileIterator()

        # Output file
        self.noDefaultOut = noDefaultOut
        if noDefaultOut:
            self.ofd = None
        else:
            self.ofd = sys.stdout

        self.lfd = sys.stderr   # log file

    #---------------------------------------------------------
    def usageString(self):
        return "usage: %prog [options] expression expression ... < input > output"

    #---------------------------------------------------------
    def initArgParser(self):

        self.parser = OptionParser(self.usageString())

        self.parser.add_option("-1","-f","--file1", dest="file1", default=None,
            metavar="FILE",
            help="Specifies file for input table [default=read from stdin]")

        self.parser.add_option("-s", "--separator", dest="sep1", default=TAB,
            metavar="CHAR",
            help="Separator character (default=TAB).")
        #self.parser.add_option("-t", "--format", dest="format1", default="tsv",
            #metavar="FORMAT",
            #help="Either tsv (the default) or gff3.")
        self.parser.add_option("-c", "--comment", dest="com1", default=HASH,
            metavar="CHAR",
            help="Comment character (default=HASH). " + \
                 "Lines beginning with CHAR are skipped.")
        if self.ninputs == 2:
            self.parser.add_option("-2","--file2", dest="file2", default=None,
                metavar="FILE",
                help="Specifies file for table T2 [default=read from stdin]")
            #self.parser.add_option("-T", "--format2", dest="format2", default="tsv",
                #metavar="FORMAT",
                #help="Either tsv (the default) or gff3.")
            self.parser.add_option("-S","--separator2", dest="sep2", default=TAB,
                metavar="CHAR",
                help="Separator character for file 2 (default=TAB).")
            self.parser.add_option("-C","--comment2", dest="com2", default=HASH,
                metavar="CHAR",
                help="Comment character for file 2 (default=HASH). " + \
                     "Lines beginning with CHAR are skipped.")

        if not self.noDefaultOut:
            self.parser.add_option("-o","--out-file", dest="outFile", default=None,
                metavar="FILE",
                help="Specifies output file [default=write to stdout]")

        self.parser.add_option("-l", "--log-file", dest="logFile", default=None,
            metavar="FILE",
            help="Specifies log file [default=write to stderr]")

        self.parser.add_option("--exec-file", dest="execFile", default=None,
            action="store",
            metavar="FILE",
            help="Execs the code in FILE, e.g., for defining functions to " +\
               "use in command line filters and generators.")

        self.parser.add_option("--expr-file", dest="exprFiles", default=[],
            action="append",
            metavar="FILE",
            help="Loads expressions (filters/generators) from FILE." + \
                " Expression loaded from files are evaluated before " + \
                "command line expressions.")

    #---------------------------------------------------------
    # Parses the command line. Options and positional args
    # assigned to self.options and self.args, resp.
    #
    def parseCmdLine(self, argv):
        self.initArgParser()
        (self.options, self.args) = self.parser.parse_args(argv)
        self.validate()

    #---------------------------------------------------------
    # Check options, open files, and generally get set up.
    #
    def validate(self):
        try:
            self.openFiles()
            self.loadExprs(self.options)
            self.processOptions(self.options)
        except:
            self.errorExit()

    #---------------------------------------------------------
    # Subclasses should override to add processing for
    # additional options. 
    #
    def processOptions(self, opts):
        pass

    #---------------------------------------------------------
    #
    def loadExprs(self, opts):
        exprs = []
        for f in self.options.exprFiles:
            efd = open(f,'r')
            line = efd.readline()
            while(line):
                if line[0] not in [NL,HASH]:
                    exprs.append(line.strip())
                line = efd.readline()
            efd.close()

        if len(exprs) > 0:
            self.args = exprs + self.args
        self.compileFunctions(self.args)

        # Create the global context in which expressions
        # will be evaluated.
        s = "import sys\nimport string\nimport re\nimport math\n"
        if self.options.execFile is not None:
            fd=open(self.options.execFile,'r')
            s = s + fd.read()
            fd.close()
        exec(s,self.functionContext)


    #---------------------------------------------------------
    # Compiles positional command line arguments into generator
    # and/or filter functions. A parallel list of booleans
    # indicates whether a function is a filter or a generator.
    #
    def compileFunctions(self, args):
        noGenerators = True
        for arg in args:
            isf = (arg[0] == '?')
            self.functions.append( self.makeFunction( arg ) )
            self.isFilter.append( isf )
            noGenerators = noGenerators and isf

        if noGenerators:
            if self.ninputs==1:
                self.functions.append( \
                    self.makeFunction( "IN[1:]" ) )
                self.isFilter.append( False )
            elif self.ninputs==2:
                self.functions.append( \
                    self.makeFunction( "IN1[1:]+IN2[1:]" ) )
                self.isFilter.append( False )

    #---------------------------------------------------------
    # Given a string expression, returns a callable object that
    # evaluates it. The arguments to the function are IN1 and IN2. 
    #
    def makeFunction(self, expr):
        if expr[0] == '?':
            expr = 'bool(' + expr[1:] + ')'
        if self.ninputs == 1:
            s = "lambda IN: " + expr
        elif self.ninputs == 2:
            s = "lambda IN1, IN2: " + expr
        return (eval(s, self.functionContext), expr)

    #---------------------------------------------------------
    # Open all input and output files.
    #
    def openFiles(self):
        if self.options.file1:
            self.t1.open(self.options.file1)
        if self.ninputs==2 and self.options.file2:
            self.t2.open(self.options.file2)
            self.t2.setCommentChar(self.options.com2)
            self.t2.setSeparatorChar(self.options.sep2)
        if not self.noDefaultOut and self.options.outFile:
            self.ofd = open(self.options.outFile, 'w')
        if self.options.logFile:
            self.lfd = open(self.options.logFile, 'a')
            sys.stderr = self.lfd
        self.t1.setLogFile(self.lfd)
        if self.ninputs==2 and self.options.file2:
            self.t2.setLogFile(self.lfd)

    #---------------------------------------------------------
    def setInputFile(self, file, index = 1):
        if index == 1:
            self.t1.open(file)
        elif index == 2:
            self.t2.open(file)

    def setOutputFile(self, file):
        if type(file) is str:
            self.ofd = open( file, 'w' )
        else:
            self.ofd = file

    def setLogFile(self, file):
        if type(file) is str:
            self.lfd = open( file, 'a' )
        else:
            self.lfd = file

    #---------------------------------------------------------
    def closeFiles(self):
        self.t1.close()
        if(self.t2 is not None):
            self.t2.close()
        if(self.ofd is not None):
            self.ofd.close()

    #---------------------------------------------------------
    # Prints exception info, then dies.
    #
    def errorExit(self, message=None):
        (ex_type, ex_value, traceback) = sys.exc_info()
        self.debug("\nAn error has occurred.")
        if message is not None:
            self.debug(message)
        if ex_type is not None:
            self.debug("\nThe following exception was caught:")
            sys.excepthook(ex_type, ex_value, traceback)
            self.die()

    #---------------------------------------------------------
    # Writes an error message and dies. Exits with -1 status.
    #
    def die(self, error=None):
        if error:
            self.debug(error)
        sys.exit(-1)

    #---------------------------------------------------------
    # Writes a message and a newline to the log file.
    #
    def debug(self, msg):
        self.lfd.write(str(msg))
        self.lfd.write(NL)

    #---------------------------------------------------------
    # Returns a tuple containing the indicated columns
    # from the given row.
    #
    def makeKey(self, row, colIndexes):
        t = []
        for c in colIndexes:
            t.append( row[c] )
        return tuple(t)

    #---------------------------------------------------------
    # Parses a list of integers from val. val may
    # be a string or a list of strings. (If a list,
    # it's joined first.) Column numbers are separated
    # by commas. Returns list of all the
    # integers parsed from the string.
    #
    def parseIntList(self, val):
        if type(val) is list:
            val = ", ".join(val)
        val=re.split("[, ]+", val)
        return list(map(int, [_f for _f in val if _f]))

    #---------------------------------------------------------
    # Evaluates the list of functions to generate zero
    # or one output rows. Each function is evaluated
    # in order. If f is a filter, and it evaluates to
    # False, the function returns, and no row is output.
    # If f is a generator, its value(s) is(are)
    # appended as the next output column(s). (The output
    # row grows as the functions evaluate.)
    #
    # If no filter fails, writes the output row,
    # and increment the row count.
    #
    def generateOutputRow(self, r1, r2=None):
        outrow = [ self.nOutputRows+1 ]
        i=-1
        for (f,fexpr) in self.functions:
            try:
                if self.ninputs==1:
                    x=f(r1)
                else:
                    x=f(r1,r2)
            except:
                self.debug("Error generating output row.")
                self.debug("Input row 1: " + str(r1))
                if(self.ninputs==2):
                    self.debug("Input row 2: " + str(r2))
                self.debug("Function: " + fexpr)
                raise

            i=i+1
            if self.isFilter[i]:
                if x:
                    continue
                else:
                    return None

            # generate output column(s)
            if type(x) is list:
                outrow = outrow + x
            elif type(x) is tuple:
                outrow = outrow + list(x)
            else:
                outrow.append(x)

        # end for-loop
        return outrow
        
    #---------------------------------------------------------
    # Write the row to the output file.
    #
    def writeOutput(self, row, fd=None):
        if fd is None:
            fd = self.ofd
        if fd is self.ofd:
            self.nOutputRows += 1
        row = list(map(str,row))
        fd.write(TAB.join(row) + NL)

#------------------------------------------------------------
# Superclass of all command line tools 
# that take one input table and produce
# one output table.
#
class UnaryTableTool( TableTool ):
    def __init__(self, ndf=False):
        TableTool.__init__(self,1,ndf)

#------------------------------------------------------------
# Superclass of all command line tools 
# that take two input tables and produce
# one output table.
#
class BinaryTableTool( TableTool ):
    def __init__(self, ndf=False):
        TableTool.__init__(self,2, ndf)

#----------------------------------------------------------------------
# Iterator class for returning the rows of a table
# stored in a file or read from stdin. Rows are
# returned as python lists. The 0th list element
# is the integer row number (inserted automatically).
# The remaining elements 1 .. n are the column values.
# By default, column values are converted 
# to numbers if possible, and are otherwise returned 
# as strings (This conversion attempt can be suppressed.)
#
#
class TableFileIterator:

    def __init__(self):

        # if a string matches this, it's not a number
        # (Strings that do match might still not be a
        # number, e.g., "...". This regex is just
        # used as a first test.)
        #
        self.nre = re.compile("[^-+0-9.eE ]")

        # if string matches self.nre and then matches
        # this regex, try conversion to float(), 
        # otherwise int()
        #
        self.fre = re.compile("[.eE]")

        #
        # 
        self.ncols = 0

        #
        self.lfd = sys.stderr

        #
        self.separatorChar       = TAB
        self.commentChar        = HASH

        #
        self.fileName = None
        self.fileDesc = None
        #
        self.currentLine = None
        self.currentLineNum = 0
        #
        self.currentRow = None
        self.currentRowNum = 0

    #--------------------------------------------------
    def getCommentChar(self):
        return self.commentChar

    def setCommentChar(self, c):
        if c is None:
                c = HASH
        self.commentChar = c

    #--------------------------------------------------
    def getSeparatorChar(self):
        return self.separatorChar

    def setSeparatorChar(self, s):
        if s is None:
                s = TAB
        self.separatorChar = s

    #--------------------------------------------------
    def setLogFile(self, lfd):
        self.lfd = lfd

    #--------------------------------------------------
    def open(self, file, rowType="tsv"):
        self.close()

        if type(file) is str:
            if file == "-":
                self.fileName = "<stdin>"
                self.fileDesc = sys.stdin
            else:
                self.fileName = file
                self.fileDesc = open(file,'r')
        #elif type(file) is types.FileType:
        else:
            self.fileName = "<???>"
            self.fileDesc = file

        #
        if rowType == "tsv":
            self.rowFunc = lambda row: row
        elif rowType in ["gff","gff3"]:
            self.rowFunc = lambda row: gff3.Feature(row[1:])
        else:
           raise RuntimeError("Unknown row type specified: " + str(rowType))

        #
        self.currentLineNum = 0
        self.currentLine = None
        #
        self.currentRowNum  = 0
        self.currentRow  = None

    #--------------------------------------------------
    def close(self):
        if self.fileDesc is not None \
        and self.fileDesc is not sys.stdin:
            self.fileDesc.close()
        #
        self.fileDesc = None
        self.fileName = None

    #--------------------------------------------------
    # Returns next row from file, or None if there are
    # no more. Skips comment lines and blank lines.
    # Advances line and row counters.
    #
    def nextRow(self):
        self.currentLine = self.fileDesc.readline()
        while self.currentLine:
            self.currentLineNum += 1
            if self.currentLine == NL \
            or self.currentLine.startswith(self.commentChar):
                self.currentLine = self.fileDesc.readline()
                continue

            self.currentRowNum += 1
            self.currentRow = [self.currentRowNum] \
                + self.currentLine.split(self.separatorChar)
            self.currentRow[-1] = self.currentRow[-1][:-1] # remove newline from last col

            if self.ncols == 0:
                self.ncols = len(self.currentRow) - 1
            elif self.ncols != (len(self.currentRow) - 1):
                self.lfd.write(\
                  "WARNING: wrong number of columns (%d) in line %d. Expected %d. Skipping...\n" % \
                  ((len(self.currentRow)-1), self.currentLineNum, self.ncols))
                self.lfd.write(self.currentLine)
                self.currentLine = self.fileDesc.readline()
                continue
                
            return self.rowFunc(self.currentRow)
        # end while-loop
        return None

    #--------------------------------------------------
    # If reading from a file, stat the file.
    # If reading from stdin or unnamed file descriptor,
    # return None.
    #
    def statFile( self ):
        if self.fileName[0] != "<":
            return os.stat( self.fileName )
        return None

    #--------------------------------------------------
    # If reading from a file, return size of file in
    # bytes. If reading from stdin or unnamed file
    # descriptor, return -1.
    #
    def fileSize(self):
        stat = self.statFile()
        if stat is None:
            return -1
        else:
            return stat.st_size 

    #--------------------------------------------------
    # Returns the current line
    #
    def getCurrentLine(self):
        return self.currentLine

    #--------------------------------------------------
    # Returns the current line number. Line numbers 
    # start at 1.
    #
    def getCurrentLineNum(self):
        return self.currentLineNum

    #--------------------------------------------------
    # Returns the current row.
    #
    def getCurrentRow(self):
        return self.currentRow

    #--------------------------------------------------
    def getNCols(self):
        return self.ncols

    #--------------------------------------------------
    # Returns the current row number.
    #
    def getCurrentRowNum(self):
        return self.currentRowNum

    #--------------------------------------------------
    # Returns the file name this iterator is attached to.
    #
    def getFileName(self):
        return self.fileName

    #--------------------------------------------------
    # Allows self to be interated over in a for loop.
    #
    def __iter__(self):
        return self

    #--------------------------------------------------
    # Returns next row, or throws StopIteration.
    #
    def __next__(self):
        r = self.nextRow()
        if r is None:
            raise StopIteration
        return ( self.currentLineNum, self.currentRowNum, r )

#----------------------------------------------------------------------
# AGGREGATE
#----------------------------------------------------------------------
# Table aggregation filter. In aggregation, the input table
# is logically partitioned by specifying one or more "group-by"
# columns; input rows having the same values in these columns
# belong to the same partition. Each partition generates one
# output row. Each output row contains (at least) the group-by
# values that define its partition. Additional columns may
# be added that contain specified aggregate functions of the
# input rows.
#
# Example: Consider this simple example, showing a table
# of information about students.
# The columns are: student name, gender, year (1-4), GPA.
#       John    M       1       3.5
#       Mary    F       2       3.7
#       Jean    F       1       2.9
#       Joe     M       1       2.6
#       Bill    M       3       3.4
#       Bob     M       3       3.6
#       Alice   F       4       4.0
#       Larry   M       4       3.2
#       
# Suppose we want to know the average GPA broken down by
# year in school and gender. The two columns, year and
# gender, are the group-by columns. Each distinct value
# combination (e.g., "3" and "F") defines a partition
# of the input rows. The GPAs are averaged within each 
# partition. Thus the output would be:
#
#       1       F       2.9
#       1       M       3.05
#       2       F       3.7
#       3       M       3.5
#       4       F       4.0
#       4       M       3.2
#
# Note that the output does NOT include all possible value
# combinations of group by values - only those that occur 
# in the input.
#
# Table aggregation is an algebraic transformation.
# It takes a table as input and produces a table as output.
#
# INPUT/OUTPUT:
#  This is a filter. It reads from stdin and writes to stdout.
#
# FORMAT:
#  Currently supports only tab-delimited files without column
#  headers, comment lines, or anything else (TO BE FIXED SOON).
# 
#  The output table contains each of the group-by columns
#  (in the order specified) followed by one column for each aggregation 
#  specifier (in the order specified). The output contains one row
#  for each partition of the input table induced by the group-by columns.
#
# SPECIFYING COLUMNS
#  Columns are specified by integer position in the table. 
#  The leftmost column in a table is column 1. 
#  Lists of columns are specified by separating the integers
#  with commas, colons, pipes, etc., e.g., "1,2,3". Whitespace 
#  may be used by enclosing the list in quotes, e.g., "1 2 3".
#  
#
# OPTIONS:
#
#  --group-by <column-list>
#  -g  <column-list>
#       Specifies the columns used to group the computation.
#       Each distinct value combination in the
#       input generates one row in the output. All input rows having the same 
#       values in the group-by columns are combined (aggregated) into a 
#       single output row. 
#       If no group-by columns are specified, the entire input is
#       considered a single partition. The output consists of a single
#       row of (global) aggregates. (If no aggregations are specified,
#       the output is an empty table.)
#
#  -a <aggregation-specifier>
#       Specifies an aggregation of an input column, adding a column
#       to the output. <aggregation-specifier> has the form:
#       <func>:<arg>:<arg>:..., where <func> is one of the aggregation
#       functions listed below, and <arg>'s depend on the function.
#
#       Aggregation Functions:
#
#         sum:<column>  - sum of values
#         sumsq:<column>- sum of squared values
#         min:<column>  - minimum value
#         max:<column>  - minimum value
#         mean:<column> - mean value
#         avg:<column>  - same as mean:<column>
# XXXXX 
# Functions var and sd are temporarily disabled.
#
#         var:<column>  - variance of values
#         sd:<column>   - standard deviation of values
#             The specified input column must contain numeric values.
# XXXXX
#
#         count:<column> - counts number of distinct values in this
#            column in each partition
#         count - counts number of input rows in each partition
#
#         first:<column> - outputs column value for first member of partition
#         list:<column>[:<pss>] - concatenates input values into a string list
#               By default, items are separated by a comma and no prefix/suffix
#               is added. Optional <pss> explicitly specifies prefix, separator,
#               and suffix as single characters.
#
#               len(<pss>) :    Effect is:
#               ============    ==========
#                  1            separator = <pss>, prefix=suffix=''     
#                  2            prefix=pss[0], sep='', suffix=pss[1]
#                  3            prefix=pss[0], sep=pss[1], suffix=pss[2]
#               
#
#----------------------------------------------------------------------

#----------------------------------------------------------------------
#
# CONSTANTS for the various aggregation function names
#
COUNT   = "count"
FIRST   = "first"
LAST    = "last"
LIST    = "list"
SUM     = "sum"
SUMSQ   = "sumsq"
MIN     = "min"
MAX     = "max"
MEAN    = "mean"
AVG     = "avg"
VAR     = "var"
SD      = "sd"

#_STAT_FUNCS = [SUM,SUMSQ,MIN,MAX,MEAN,AVG,VAR,SD]
_STAT_FUNCS = [SUM,SUMSQ,MIN,MAX,MEAN,AVG]

_ALL_FUNCS = [COUNT,LIST,FIRST,LAST] + _STAT_FUNCS

#----------------------------------------------------------------------
class TAggregate( UnaryTableTool) :
    def __init__(self,argv):
        UnaryTableTool.__init__(self)
        self.maxColIndex = 0
        self.currentLine = None
        self.currentLineNum = 0

        self.gbColumns = []             # list of integer col indexes
        self.accumulatorClasses = []    # list of Accumulator classes
        self.accumulatorColumns = []    # corresp. list of columns to accum
        self.accumulatorXtraArg = []    # corresp extra arg to accum constructor
        self.col2stats = {}             # maps col# to Statistics accum
        self.outSpecifiers = []         # 

        self.partitions = {}

        self.parseCmdLine(argv)

    #---------------------------------------------------------
    # Parses the command line. Options and positional args
    # assigned to self.options and self.args, resp.
    #
    def initArgParser(self):
        UnaryTableTool.initArgParser(self)
        self.parser.add_option("-g", "--group-by", 
            metavar="COLUMN(S)",
            action="append", dest="groupByColumns", default=[], 
            help="Group-by column(s).")

        self.parser.add_option("-a", "--aggregate", 
            metavar="FCN:COLUMN",
            action="append", dest="aggSpecs", default=[], 
            help="Aggregation specifier. FCN is one of: " + ",".join(_ALL_FUNCS))

    #---------------------------------------------------------
    def processOptions(self, opts):
        # group-by columns
        #
        for g in opts.groupByColumns:
            self.addGroupByColumn(g)

        for a in opts.aggSpecs:
            self.addAggregation(a)

    #----------------------------------------------------------------------
    def addGroupByColumn(self,g):
        #split on any string of non-digits
        gcols = re.split('[^0-9]+', g)
        for gc in gcols:
            if gc=="":
                continue
            igc = int(gc)
            if igc not in self.gbColumns:
                self.gbColumns.append(igc)
                self.maxColIndex = max(self.maxColIndex, igc)


    #----------------------------------------------------------------------
    def addAggregation(self,arg):
        tokens = arg.split(COLON,2)
        func=tokens[0]
        colIndex = None
        if len(tokens) > 1:
            colIndex = int(tokens[1])
        #xtra = ''
        xtra = None
        if len(tokens) > 2:
            xtra = tokens[2]

        accClass = _FUNC2CLASS[func]
        if accClass is Statistics:
            if colIndex not in self.col2stats:
                self.col2stats[colIndex] = len(self.accumulatorClasses)
                self.accumulatorClasses.append(Statistics)
                self.accumulatorColumns.append(colIndex)
                self.accumulatorXtraArg.append(None)
            self.outSpecifiers.append( (self.col2stats[colIndex], func, xtra) )
        else:
            self.outSpecifiers.append( (len(self.accumulatorClasses),None,None) )
            self.accumulatorClasses.append(accClass)
            self.accumulatorColumns.append(colIndex)
            self.accumulatorXtraArg.append(xtra)

    #---------------------------------------------------------
    def readInput(self):
        row = self.t1.nextRow()
        while(row):
            self.processRow(row)
            row = self.t1.nextRow()

    #---------------------------------------------------------
    # Creates a new list of accumulator objects corresponding
    # to the command line specifications.
    #
    def newAccumulatorList(self):
        alist = []
        i=0
        for aclass in self.accumulatorClasses:
            alist.append(aclass(self.accumulatorColumns[i], \
                                self.accumulatorXtraArg[i]))
            i=i+1
        return alist

    #---------------------------------------------------------
    # Processes an input table row
    #
    def processRow(self, row):
        gbkey = self.makeKey(row,self.gbColumns)
        if gbkey not in self.partitions:
            self.partitions[gbkey]=self.newAccumulatorList()
        for a in self.partitions[gbkey]:
            a.nextRow(row)

    #---------------------------------------------------------
    def go(self):
        self.readInput()
        rownum=0
        for (part,aggs) in list(self.partitions.items()):
            rownum += 1
            aggrow = [rownum] + list(part)
            for (i,arg,xtra) in self.outSpecifiers:
                if arg is None:
                    apnd = aggs[i]
                else:
                    apnd = aggs[i].getResult(arg,xtra)

                aggrow.append(str(apnd))

            genrow = self.generateOutputRow(aggrow)
            if genrow is not None:
                self.writeOutput(genrow[1:])

#----------------------------------------------------------------------
# Abstract superclass. An accumulator is something that processes
# a sequence of values and produces an output value.
#
class Accumulator:
    def __init__(self, colIndex, xtra=''):
        self.colIndex = colIndex
        self.xtra = xtra
        #print "Created " + self.__class__.__name__ + ", Column " + `colIndex`

    def debug(self, s):
        sys.stderr.write(s)
        sys.stderr.write("\n")

    def nextRow(self, row):
        if self.colIndex is None:
            self.nextValue(None)
        else:
            self.nextValue(row[self.colIndex])

    def nextValue(self, value):
        raise RuntimeError("UnimplementedAbstractMethod: nextValue")

    def getResult(self,arg=None):
        raise RuntimeError("UnimplementedAbstractMethod: nextResult")

    def __str__(self):
        return str(self.getResult())

#----------------------------------------------------------------------
# If instantiated with a column index, counts number of
# distinct values in that column (within its partition).
# If instantiated with column index == None, simply counts
# the number of rows in its partition.
#
class Counter( Accumulator ):

    def __init__(self, ci, xtra=''):
        Accumulator.__init__(self, ci, xtra)
        self.countValues = (ci is not None)
        self.count = 0
        self.values = {}

    def nextValue(self, value):
        self.count = self.count + 1
        if self.countValues:
            self.values[value] = 1

    def getResult(self):
        if self.countValues:
            return len(self.values)
        else:
            return self.count


#----------------------------------------------------------------------
# Accumulates the values in a list.
#
class Concatenator( Accumulator ):

    def __init__(self, ci, xtra=''):
        Accumulator.__init__(self, ci, xtra)
        self.list = []
        self.separator = ','
        self.prefix = ''
        self.suffix = ''
        lx = -1
        if xtra != None:
            lx = len(xtra)

        if lx == 0:
            self.separator = ''
            self.prefix = ''
            self.suffix = ''
        elif lx==1:
            self.separator = xtra
            self.prefix = ''
            self.suffix = ''
        elif lx==2:
            self.separator = ''
            self.prefix = xtra[0]
            self.suffix = xtra[1]
        elif lx==3:
            self.separator = xtra[1]
            self.prefix = xtra[0]
            self.suffix = xtra[2]

    def nextValue(self, value):
        self.list.append(value)

    def getResult(self):
        return self.list

    def __str__(self):
        return self.prefix + \
            self.separator.join( map(str,self.list)) + self.suffix


#----------------------------------------------------------------------
# Returns the first value
#
class FirstValue( Accumulator ):

    def __init__(self, ci, xtra=''):
        Accumulator.__init__(self, ci, xtra)
        self.value = None
        self.first = True

    def nextValue(self, value):
        if self.first:
            self.value = value
            self.first = False

    def getResult(self):
        return self.value

    def __str__(self):
        return str(self.value)

#----------------------------------------------------------------------
# Returns the last value
#
class LastValue( Accumulator ):

    def __init__(self, ci, xtra=''):
        Accumulator.__init__(self, ci, xtra)
        self.value = None

    def nextValue(self, value):
        self.value = value

    def getResult(self):
        return self.value

    def __str__(self):
        return str(self.value)


#----------------------------------------------------------------------
#----------------------------------------------------------------------
# Computes statistics over the sequence of values.
#
class Statistics(Accumulator):

    def __init__(self, ci, xtra=''):
        Accumulator.__init__(self, ci, xtra)
        self.n = None
        self.sum = None
        self.sumsq = None
        self.min = None
        self.max = None

    def nextValue(self, value):
        value = float(value)
        if self.n is None:
            self.n = 1
            self.sum = value
            self.sumsq = value*value
            self.min = value
            self.max = value
        else:
            self.sum = self.sum + value
            self.sumsq = self.sumsq + value*value
            self.n = self.n + 1
            self.min = min(self.min, value)
            self.max = max(self.max, value)

    def getResult(self,field=None,xtra=''):
        rval = {}
        rval[COUNT] = self.n
        rval[SUM] = self.sum
        rval[SUMSQ] = self.sumsq
        rval[MIN] = self.min
        rval[MAX] = self.max
        if self.n == 0:
            rval[MEAN] = 0
        else:
            rval[MEAN] = float(self.sum) / self.n
        rval[AVG] = rval[MEAN]
        '''
        if self.n > 1 and self.min != self.max:
          try:
            rval[VAR] = (self.n*(self.sumsq) - self.sum*self.sum)/(self.n*(self.n-1))
            rval[SD] = rval[VAR] ** 0.5
          except:
            self.debug( "\n\n???????\n\n" )
            self.debug( "COUNT=%g"%rval[COUNT] )
            self.debug( "SUM=%g"%rval[SUM] )
            self.debug( "SUMSQ=%g"%rval[SUMSQ] )
            self.debug( "MIN=%g"%rval[MIN] )
            self.debug( "MAX=%g"%rval[MAX] )
            self.debug( "VAR=%g"%rval[VAR] )
            self.debug( "SD=%g"%rval[SD] )
        else:
            rval[VAR] = 0.0
            rval[SD] = 0.0
        '''

        if field is None:
            return rval
        else:
            return rval[field]

_FUNC2CLASS = {
}

_FUNC2CLASS[COUNT] = Counter
_FUNC2CLASS[LIST] = Concatenator
_FUNC2CLASS[FIRST] = FirstValue
_FUNC2CLASS[LAST] = LastValue
_FUNC2CLASS[SUM] = Statistics
_FUNC2CLASS[SUMSQ] = Statistics
_FUNC2CLASS[MIN] = Statistics
_FUNC2CLASS[MAX] = Statistics
_FUNC2CLASS[MEAN] = Statistics
_FUNC2CLASS[AVG] = Statistics
#_FUNC2CLASS[VAR] = Statistics
#_FUNC2CLASS[SD] = Statistics

#------------------------------------------------------------
#------------------------------------------------------------
#
# tb.py
#
# Table bucketize. Bucketizes a table containing a pair of ID columns.
# Each row represents an edge in a bipartite association graph.
# To represent unassociated IDs (i.e., those that end up in 1-0
# or 0-1 buckets), a null-value string can be declared, and appear
# in one ID column or the other. (Such as when performing an
# outer-join...see tj.)
#
#----------------------------------------------------------------------

BUCKETS = [
        "0-1",
        "1-0",
        "1-1",
        "n-1",
        "1-n",
        "n-m",
        ]
#----------------------------------------------------------------------
#
class TBucketize( UnaryTableTool ):
    def __init__(self,argv):
        UnaryTableTool.__init__(self,True)
        self.kcols1 = []
        self.kcols2 = []
        self.rows = []
        self.graph = None
        self.bucketFiles = {}
        self.parseCmdLine(argv)

    #---------------------------------------------------------
    def initArgParser(self):
        UnaryTableTool.initArgParser(self)

        self.parser.add_option("--k1", dest="k1", 
            action="append", default = [],
            metavar="COLUMN(S)",
            help="Specifies column(s) of first ID.")

        self.parser.add_option("--k2", dest="k2", 
            action="append", default = [],
            metavar="COLUMN(S)",
            help="Specifies column(s) of second ID.")

        self.parser.add_option("-n", "--null-string", dest="nullString", 
            action="store", default = "", metavar="NULLSTR",
            help="Specifies string for null values. (Default: empty string)")

        self.parser.add_option("-o", "--output-dir", dest="outDir", 
            action="store", default = "", metavar="DIR",
            help="Output directory. (Default: current directory)")

        self.parser.add_option("-t", "--template", dest="template", 
            action="store", default = None,  metavar="TMPLT",
            help="Template for generating file names. E.g., -tbucket_%s.txt " + \
                "The %s is replaced by the bucket id, e.g, bucket_1-n.txt. " + \
                "(Default: writes to stdout).")

    #---------------------------------------------------------
    def openFiles(self):
        UnaryTableTool.openFiles(self)
        if self.options.template is None:
            for b in BUCKETS:
                self.bucketFiles[b] = sys.stdout

        elif "%s" not in self.options.template:
            # no %s in the template. The template is a constant.
            # Write all to that file.
            bfname = os.path.join( self.options.outDir, self.options.template )
            fd = open( bfname, 'w')
            for b in BUCKETS:
                self.bucketFiles[b] = fd

        else:
            # open file for each bucket.
            for b in BUCKETS:
                bfname = os.path.join( self.options.outDir, self.options.template % b )
                self.bucketFiles[b] = open(bfname, 'w')

    #---------------------------------------------------------
    #
    def processOptions(self,opts):
        if len(opts.k1) > 0:
            self.kcols1 = self.parseIntList(opts.k1)
        if len(opts.k2) > 0:
            self.kcols2 = self.parseIntList(opts.k2)

        nkc1 = len(self.kcols1)
        nkc2 = len(self.kcols2)

        if nkc1 != nkc2:
            self.parser.error("Same number of key columns must " + \
                "be specified for both IDs.")

        
    #---------------------------------------------------------
    def makeKey(self, row, cols, prepend):
        key = [prepend]
        for c in cols:
            v = row[c]
            if v == self.options.nullString:
                #return (prepend,None)
                return None
            key.append( v )
        return tuple(key)

    #---------------------------------------------------------
    # Reads the input table and builds the corresponding
    # bipartite graph.
    #
    def buildGraph(self):
        inrow = self.t1.nextRow()
        g = BipartiteGraph()
        while inrow:
            k1 = self.makeKey(inrow, self.kcols1, "A")
            k2 = self.makeKey(inrow, self.kcols2, "B")
            g.add(k1,k2)
            if k1 is not None:
                self.rows.append((k1,inrow))
            else:
                self.rows.append((k2,inrow))
            inrow = self.t1.nextRow()
        self.graph = g

    #---------------------------------------------------------
    def computeCC(self):
        self.cca = CCA(self.graph)
        self.cca.go()

    #---------------------------------------------------------
    def getBid(self, bucket):
        counts = bucket.split("-")
        if counts[0] not in ["0","1"]:
                counts[0] = "n"
        if counts[1] not in ["0","1"]:
                if counts[0] == "n":
                    counts[1] = "m"
                else:
                    counts[1] = "n"
        bid = counts[0] + '-' + counts[1]
        return bid

    #---------------------------------------------------------
    def getBfd(self, bucket):
        return self.bucketFiles[self.getBid(bucket)]

    #---------------------------------------------------------
    def output(self):
        for (k,r) in self.rows:
            (cid,bucket) = self.cca.getCid(k)
            row = self.generateOutputRow(r[:1] + [cid,bucket,self.getBid(bucket)] + r[1:])
            if row is not None:
                self.writeOutput(row[1:], self.getBfd(bucket))

    #---------------------------------------------------------
    def go(self):
        self.buildGraph()
        self.computeCC()
        self.output()

#----------------------------------------------------------------------
# Class for representing a bipartite graph. The a/b distinction
# is encoded enforced by the a and b parameters to the add method.
#
class BipartiteGraph:
    def __init__(self):
        self.nodes = {}

    def __getneighbors__(self, n, dict):
        if n in dict:
            lst = dict[n]
        else:
            lst = []
            dict[n] = lst
        return lst

    def add(self, a, b):
        if a is not None:
            ns = self.__getneighbors__(a, self.nodes)
            if b is not None:
                if not b in ns:
                    ns.append(b)

        if b is not None:
            ns = self.__getneighbors__(b, self.nodes)
            if a is not None:
                if not a in ns:
                    ns.append(a)

    def __str__(self):
        return str(self.nodes)

#----------------------------------------------------------------------
# Class for doing connected component analysis on a bipartite graph.
#
class CCA:
    def __init__(self, bpg):
        self.graph = bpg
        self.visited = {}

        self.cc = {}
        self.cid = 0
        self.na = 0
        self.nb = 0

    def getCid(self, n):
        return self.visited[n]

    def reach(self, n):
        self.visited[n] = self.cid
        if n[1] is not None:
            if n[0] == "A":
                self.na += 1
            elif n[0] == "B":
                self.nb += 1
        self.cc[n] = n
        neighbors = self.graph.nodes[n]
        for n2 in neighbors:
            if n2 not in self.visited:
                self.reach(n2)

    def getCount(self, n):
        if n == 0:
            return "0"
        elif n == 1:
            return "1"
        else:
            return "n"

    def getBucket(self):
        return str(self.na) + "-" + str(self.nb)

    def go(self):
        for n in sorted(self.graph.nodes.keys()):
            if n not in self.visited:
                self.cc = {}
                self.na = 0
                self.nb = 0
                self.cid += 1
                self.reach(n) 
                for cn in sorted(self.cc.keys()):
                    self.visited[cn] = (self.visited[cn], self.getBucket())

#------------------------------------------------------------
#------------------------------------------------------------
# tdiu.py
#
# Table difference/intersection/union. 
#
# OPTIONS:
#
#   --file1 FILE
#   --file2 FILE
#       Specifies input files for T1 and T2, respectively.
#       If no --file1 (resp., --file2) is given, T1 (resp., T2)
#       is read from standard input. 
#
#   --ofile FILE
#       Specifies an output file. By default, result is written
#       to standard out.
#
#   --log-file FILE
#       Specifies a log file to receive diagnostic output. By
#       default, diagnostics are written to standard error.
#
#   --k1 COLUMNS
#   --k2 COLUMNS
#       Specifies the key column(s) for tables T1 and T2,
#       respectively.
#
# ----
#
# AUTHOR:
#   Joel Richardson, Ph.D.
#   Mouse Genome Informatics
#   The Jackson Laboratory
#   Bar Harbor, Maine 04609
#   jer@informatics.jax.org
#
# Date: April 2006
#
#----------------------------------------------------------------------

#----------------------------------------------------------------------
#
class TDiffIntUnion( BinaryTableTool ):
    def __init__(self,argv):
        BinaryTableTool.__init__(self)
        self.kcols1 = []
        self.kcols2 = []
        self.t2Keys = {}
        self.parseCmdLine(argv)

    #---------------------------------------------------------
    def initArgParser(self):
        BinaryTableTool.initArgParser(self)

        self.parser.add_option("--k1", dest="k1", 
            action="append", default = [],
            metavar="COLUMN(S)",
            help="Specifies key column(s) for table T1.")

        self.parser.add_option("--k2", dest="k2", 
            action="append", default = [],
            metavar="COLUMN(S)",
            help="Specifies key column(s) for table T2.")

    #---------------------------------------------------------
    #
    def processOptions(self,opts):
        if len(opts.k1) > 0:
            self.kcols1 = self.parseIntList(opts.k1)
        if len(opts.k2) > 0:
            self.kcols2 = self.parseIntList(opts.k2)

        nkc1 = len(self.kcols1)
        nkc2 = len(self.kcols2)

        if nkc1 != nkc2:
            self.parser.error("Same number of key columns must " + \
                "be specified for both IDs.")

        
    #---------------------------------------------------------
    def makeKey(self, row, cols):
        key = []
        for c in cols:
            v = row[c]
            key.append( v )
        return tuple(key)

    #---------------------------------------------------------
    def output(self, row):
        row = self.generateOutputRow(row,[])
        if row is not None:
                self.writeOutput(row[1:])

#----------------------------------------------------------------------
#----------------------------------------------------------------------
#
# td.py
#
# Table difference operator; outputs the rows of table 1
# that do not occur in table 2, based on keys.
#
# OPTIONS:
#
#   --file1 FILE
#   --file2 FILE
#       Specifies input files for T1 and T2, respectively.
#       If no --file1 (resp., --file2) is given, T1 (resp., T2)
#       is read from standard input. 
#
#   --ofile FILE
#       Specifies an output file. By default, result is written
#       to standard out.
#
#   --log-file FILE
#       Specifies a log file to receive diagnostic output. By
#       default, diagnostics are written to standard error.
#
#   --k1 COLUMNS
#   --k2 COLUMNS
#       Specifies the key column(s) for tables T1 and T2,
#       respectively.
#
#----------------------------------------------------------------------

#----------------------------------------------------------------------
class TDifference (TDiffIntUnion):
    def __init__(self,argv):
        TDiffIntUnion.__init__(self,argv)

    #---------------------------------------------------------
    def go(self):
        keys = {}
        row = self.t2.nextRow()
        while(row):
            key = self.makeKey(row, self.kcols2)
            keys[key] = 1
            row = self.t2.nextRow()

        row = self.t1.nextRow()
        while(row):
            key = self.makeKey(row, self.kcols1)
            if key not in keys:
                self.output(row)
            row = self.t1.nextRow()

#------------------------------------------------------------
#------------------------------------------------------------
# tfilt.py
#
# General table computation/selection/projection filter.
# I.e., allows you to: compute new columns; filter rows
# for those satisfying a condition; reorder and remove
# (and eventually, rename) input columns.
#
# Table filtering is an algebraic transformation.
# It takes a table as input and produces a table as output.
#
# GENERATORS AND FILTERS:
#
#  Each argument is a Python expression, optionally beginning
#  with a '?' character.
#  Expressions without a leading '?' generate a output columns.
#  We'll call these generators.
#  Expression with a leading '?' filter the input.
#  We'll call these filters.
#  In all cases, Python rules govern the expression syntax.
#
#  If no generators are specified on the command line, 
#  the generator "IN[1:]" is used. In other words, if you
#  don't specify any generators, you get all the columns.
#
# EVALUATION:
#
#  Each input row generates zero or one output row, as follows.
#
#  The argument expressions are evaluated in the order given.
#  If a given expression is a generator, its value sets the
#  next output column; if the value is a list of n items, 
#  it sets the next n output columns.
#  If an expression is a filter, it is evaluated and the
#  value interpreted as a Boolean. If True, processing on 
#  the current input row continues. Otherwise, the input 
#  row is screened out; further processing on the row is 
#  skipped, and tfilt proceeds to the next input row.
#
#  The following names are defined and can be used within
#  an expression:
#  
#       IN      the current input row. This is a list containing
#               the values from each column. The ith column's
#               value is written: IN[i]. Column numbers start
#               at 1. IN[0] contains the current row number (its
#               value is set automatically). 
#
#       OUT     the current output row. A list of column
#               values, like IN. OUT[0] is the current output
#               row number, and is set automatically. (OUT[0]
#               is _not_ written to the output, just as IN[0]
#               is not read from the input). 
#               
#       all the __builtin__ functions
#       string  the Python string ligrary
#       re      the Python regular expression library
#       math    the Python math library
#       
# EXAMPLES:
#       ... | tfilt ?IN[2] IN[1] IN[3]*IN[4] | ...
#
#       Reads table from stdin. For those rows where column[2] is
#       not 0/empty/null/False, it outputs a row containing
#       column 1 and the product of columns 3 and 4.
#
# INPUT/OUTPUT:
#  This is a filter. It reads from stdin and writes to stdout.
#  There is one row of output for each row of input.
#  The output columns are specified by command line args.
#
# FORMAT:
#  Currently supports only tab-delimited files without column
#  headers, comment lines, or anything else (TO BE FIXED SOON).
#
#----------------------------------------------------------------------
#
class TFilter ( UnaryTableTool ) :
    def __init__(self,argv):
        UnaryTableTool.__init__(self)
        self.parseCmdLine(argv)

    #---------------------------------------------------------
    def go(self):
        inrow = self.t1.nextRow()
        while(inrow):
            outrow = self.generateOutputRow(inrow)
            if outrow is not None:
                self.writeOutput(outrow[1:])
            inrow = self.t1.nextRow()


#----------------------------------------------------------------------
#----------------------------------------------------------------------
#
# ti.py
#
# Outputs the rows of table1 that also occur in table2,
# based on keys.
#
# OPTIONS:
#
#   --file1 FILE
#   --file2 FILE
#       Specifies input files for T1 and T2, respectively.
#       If no --file1 (resp., --file2) is given, T1 (resp., T2)
#       is read from standard input. 
#
#   --ofile FILE
#       Specifies an output file. By default, result is written
#       to standard out.
#
#   --log-file FILE
#       Specifies a log file to receive diagnostic output. By
#       default, diagnostics are written to standard error.
#
#   --k1 COLUMNS
#   --k2 COLUMNS
#       Specifies the key column(s) for tables T1 and T2,
#       respectively.
#
#----------------------------------------------------------------------

class TIntersection (TDiffIntUnion):
    def __init__(self,argv):
        TDiffIntUnion.__init__(self,argv)

    #---------------------------------------------------------
    def go(self):
        keys = {}
        row = self.t2.nextRow()
        while(row):
            key = self.makeKey(row, self.kcols2)
            keys[key] = 1
            row = self.t2.nextRow()

        row = self.t1.nextRow()
        while(row):
            key = self.makeKey(row, self.kcols1)
            if key in keys:
                self.output(row)
            row = self.t1.nextRow()

#------------------------------------------------------------
#------------------------------------------------------------
#
# tjoin.py
#
# Table joining is an algebraic transformation.
# It takes two tables as input and produces one 
# table as output.
#
# OPTIONS:
#
#
# EVALUATION:
#       
# INPUT/OUTPUT:
#
# FORMAT:
#  Currently supports only tab-delimited files without column
#  headers, comment lines, or anything else (TO BE FIXED SOON).
#
# OPTIONS:
#
#   --file1 FILE
#   --file2 FILE
#       Specifies input files for T1 and T2, respectively.
#       If no --file1 (resp., --file2) is given, T1 (resp., T2)
#       is read from standard input. If neither is given, T1
#       and T2 will be the same table.
#
#   --ofile FILE
#       Specifies an output file. By default, result is written
#       to standard out.
#
#   --log-file FILE
#       Specifies a log file to receive diagnostic output. By
#       default, diagnostics are written to standard error.
#
#   --j1 COLUMNS
#   --j2 COLUMNS
#       Specifies the column(s) for an equi-join. COLUMNS is a comma-separated
#       list of integer column indices (no spaces). --j1 specifies columns 
#       from T1, and --j2 specifies an equal number of columns from T2. 
#       In order for a pair of rows (r1, r2) to satisfy the join, they
#       must: (1) have equal values in corresponding columns named in
#       --j1/--j2, and (2) pass any additional command line filters.
#       
#       If neither --j1 nor --j2 is specified, tj will perform a
#       nested loops join, where the join condition is specified
#       by any command line filters. If no filters are specified,
#       tj generates the combinatorial cross-product of tuples
#       from the input tables.
#
#   expression
#       All positional command line arguments are Python expressions that
#       either generate output column values from a pair of input rows, 
#       or impose additional filtering on the joined pairs.
#       They work just like in tf, except that the defined names are
#       within the expression are:
#               IN1     - the input row from T1
#               IN2     - the input row from T2
#               OUT     - the output row
#       If no expressions are given, the expression "IN1[1:]+IN2[1:]" is
#       used. Thus, the default is to output all columns from both rows.
#
#       Filters (expressions beginning with a '?' character) can be included.
#
#       For more details, see tf documentation.
#
#----------------------------------------------------------------------
#
class TJoin( BinaryTableTool ):
    def __init__(self,argv):
        BinaryTableTool.__init__(self)

        self.jcols1 = []
        self.jcols2 = []

        self.doLeftOuter = False
        self.doRightOuter = False

        self.swappedInputs = False
        self.selfJoin = False
        self.inner = None
        self.parseCmdLine(argv)

    #---------------------------------------------------------
    def initArgParser(self):
        BinaryTableTool.initArgParser(self)

        self.parser.add_option("--k1", dest="j1", 
            action="append", default = [],
            metavar="COLUMN(S)",
            help="Specifies T1 join key columns.")

        self.parser.add_option("--k2", dest="j2", 
            action="append", default = [],
            metavar="COLUMN(S)",
            help="Specifies T2 join key columns.")

        self.parser.add_option("--left-outer", dest="dlo", 
            action="store_true", default = False,
            help="Performs 'left outer' join (default: No).")

        self.parser.add_option("--right-outer", dest="dro", 
            action="store_true", default = False,
            help="Performs 'right outer' join (default: No).")

        self.parser.add_option("-n", "--null-string", dest="nullString", 
            action="store", default = "", metavar="NULLSTR",
            help="Specifies string for null values. (Default: empty string)")

    #---------------------------------------------------------
    #
    def processOptions(self,opts):
        if len(opts.j1) > 0:
            self.jcols1 = self.parseIntList(opts.j1)
        if len(opts.j2) > 0:
            self.jcols2 = self.parseIntList(opts.j2)

        njc1 = len(self.jcols1)
        njc2 = len(self.jcols2)

        if njc1 != njc2:
            self.parser.error("Same number of join columns must " + \
                "be specified for both tables.")

        self.doLeftOuter = opts.dlo
        self.doRightOuter = opts.dro

    #---------------------------------------------------------
    # Decide who's inner and who's outer. The inner
    # table is the one that gets loaded, the outer
    # is then scanned to do the join. We want the
    # smaller table to be the inner, which in this
    # program is self.t2. The net effect of this
    # method is to possibly swap self.t1 and self.t2 (and
    # other stuff), and to record that we did so.
    #
    def pickInnerOuter(self):
        self.swappedInputs = False
        self.selfJoin = (self.t1.fileDesc == self.t2.fileDesc)
        if self.selfJoin:
            return 

        t1sz = self.t1.fileSize()
        t2sz = self.t2.fileSize()
        if t1sz != -1 and (t2sz == -1 or t1sz < t2sz):
            self.debug("Swapping input tables.")
            self.swappedInputs = True
            self.t1,self.t2 = self.t2,self.t1
            self.jcols1,self.jcols2 = self.jcols2,self.jcols1
            self.doLeftOuter,self.doRightOuter = self.doRightOuter,self.doLeftOuter

    #---------------------------------------------------------
    def processPair(self, r1, r2):
        if r1 is None:
            r1 = [self.options.nullString] * (self.t1.getNCols()+1)
        if r2 is None:
            r2 = [self.options.nullString] * (self.t2.getNCols()+1)
        if self.swappedInputs:
            row = self.generateOutputRow(r2,r1)
        else:
            row = self.generateOutputRow(r1,r2)
        if row is not None:
            self.writeOutput( row[1:] )

    #---------------------------------------------------------
    def loadInner(self):
        self.pickInnerOuter()
        # at this point, self.t2 is the inner, self.t1 is the outer
        self.inner = { }
        if self.doRightOuter:
            self.innerList=[]

        row = self.t2.nextRow()
        while(row):
            key = self.makeKey(row, self.jcols2)
            if key not in self.inner:
                self.inner[key] = [row]
            else:
                self.inner[key].append(row)

            if self.doRightOuter:
                self.innerList.append(row)

            row = self.t2.nextRow()

    #---------------------------------------------------------
    def scanOuter(self):
        if self.selfJoin:
            for rowlist in self.inner.values():
                for outerrow in rowlist:
                    for innerrow in rowlist:
                        self.processPair(outerrow,innerrow)
        else:
            outerrow = self.t1.nextRow()
            while outerrow is not None:
                key = self.makeKey(outerrow, self.jcols1)
                if key in self.inner:
                    innerList = self.inner[key]
                    for innerrow in innerList:
                        self.processPair(outerrow,innerrow)
                        if self.doRightOuter:
                            self.innerList[ innerrow[0]-1 ] = None
                elif self.doLeftOuter:
                    self.processPair(outerrow, None)
                outerrow = self.t1.nextRow()
            if self.doRightOuter:
                unseen = [x for x in self.innerList if x is not None]
                for r in unseen:
                    self.processPair(None, r)

    #---------------------------------------------------------
    # Do the join.
    #
    def go(self):
        self.loadInner()
        self.scanOuter()

#------------------------------------------------------------
#------------------------------------------------------------
#
# tp.py
#
# Table Partition. Routes each input row to one of n outputs.
# 
#----------------------------------------------------------------------
#
class TPartition( UnaryTableTool ):
    def __init__(self,argv):
        UnaryTableTool.__init__(self, True)
        self.pcols = []
        self.fname2ofd = {}
        self.pval2fname = {}
        self.parseCmdLine(argv)

    #---------------------------------------------------------
    def initArgParser(self):
        UnaryTableTool.initArgParser(self)

        self.parser.add_option("-p", dest="pcol", 
            action="store", default = None, type="int",
            metavar="COLUMN",
            help="Specifies column to partition on.")

        self.parser.add_option("-o", dest="ofile",
            action="store", default = "-",
            metavar="FILE",
            help= "Output file name or file name pattern. " + \
            "A pattern contains \"%s\"; output file names are generated " + \
            "by substituting values from the partition column. Each " + \
            "row is sent to the file associated with the partition value " + \
            "in that row")

    #---------------------------------------------------------
    #
    def processOptions(self,opts):
        pass

    #---------------------------------------------------------
    def getOutputFileName(self, pval):
        if pval in self.pval2fname:
            return self.pval2fname[pval]
        if "%s" in self.options.ofile:
             fn =  self.options.ofile % str(pval)
        else:
             fn =  self.options.ofile
        self.pval2fname[pval] = fn
        return fn

    #---------------------------------------------------------
    def getOutputFileNames(self):
        fns = list(self.pval2fname.values())
        fns.sort()
        return fns

    #---------------------------------------------------------
    def getOutputFile(self, pval):
        fname = self.getOutputFileName(pval)
        if fname == "-":
            fd = sys.stdout
        elif fname in self.fname2ofd:
            fd = self.fname2ofd[fname]
        else:
            fd = open(fname, 'w')
            self.fname2ofd[fname] = fd
        return fd

    #---------------------------------------------------------
    def processRow(self, r):
        pval = None
        if self.options.pcol is not None:
            pval = r[self.options.pcol]
        fd = self.getOutputFile(pval)
        orow = self.generateOutputRow(r)
        if orow is not None:
            self.writeOutput(orow[1:],fd)

    #---------------------------------------------------------
    def go(self):
        r = self.t1.nextRow()
        while r:
            self.processRow(r)
            r = self.t1.nextRow()
        for fd in list(self.fname2ofd.values()):
            fd.close()

#----------------------------------------------------------------------
#----------------------------------------------------------------------
#
# ts.py
#
# Table sort.
#
#----------------------------------------------------------------------
#
class TSort ( UnaryTableTool ) :
    def __init__(self,argv):
        UnaryTableTool.__init__(self)
        self.rows = []
        self.parseCmdLine(argv)

    #---------------------------------------------------------
    def initArgParser(self):
        UnaryTableTool.initArgParser(self)

        self.parser.add_option("-k", dest="sortKeys", 
            action="append", default = [],
            metavar="COL[:r]",
            help="Specifies column to sort on, with optional 'r' specifying " +\
                 "to reverse the sort order. Repeatible, for specifying multilevel sort.")

    #---------------------------------------------------------
    def processOptions(self,opts):
        nsk = []
        for skey in opts.sortKeys:
            reverse=False
            if skey.endswith(":r"):
                reverse=True
                skey = skey[:-2]
            elif skey.endswith("r"):
                reverse=True
                skey = skey[:-1]
            col=int(skey)
            nsk.append( (col, reverse) )
        opts.sortKeys = nsk
        #self.parser.error("...")

    #---------------------------------------------------------
    def doSort(self, rows, column, reverse):
        kfun = lambda row, c=column: row[c]
        rows.sort(key=kfun,reverse=True)

    #---------------------------------------------------------
    def go(self):
        self.rows = []
        row = self.t1.nextRow()
        while(row):
            self.rows.append(row)
            row = self.t1.nextRow()

        self.options.sortKeys.reverse()
        for (col,rev) in self.options.sortKeys:
            self.doSort(self.rows, col, rev)

        for row in self.rows:
            outrow = self.generateOutputRow(row)
            if outrow is not None:
                self.writeOutput(outrow[1:])

#----------------------------------------------------------------------
#----------------------------------------------------------------------
#
# tu.py
#
# Table union. Outputs all rows of table1 followed by
# all rows of table2 not in table 1, based on a key.
# No assumptions are made about union-compatability.
#
# OPTIONS:
#
#   --file1 FILE
#   --file2 FILE
#       Specifies input files for T1 and T2, respectively.
#       If no --file1 (resp., --file2) is given, T1 (resp., T2)
#       is read from standard input. 
#
#   --ofile FILE
#       Specifies an output file. By default, result is written
#       to standard out.
#
#   --log-file FILE
#       Specifies a log file to receive diagnostic output. By
#       default, diagnostics are written to standard error.
#
#   --k1 COLUMNS
#   --k2 COLUMNS
#       Specifies the key column(s) for tables T1 and T2,
#       respectively.
#
#----------------------------------------------------------------------
class TUnion (TDiffIntUnion):
    def __init__(self,argv):
        TDiffIntUnion.__init__(self,argv)

    #---------------------------------------------------------
    def go(self):
        row = self.t1.nextRow()
        keys = {}
        while(row):
            key = self.makeKey(row, self.kcols1)
            keys[key] = 1
            self.output(row)
            row = self.t1.nextRow()

        row = self.t2.nextRow()
        while(row):
            key = self.makeKey(row, self.kcols2)
            if key not in keys:
                self.output(row)
            row = self.t2.nextRow()

#------------------------------------------------------------
#------------------------------------------------------------
# txpand.py
#
# Expands list-valued columns in the input.
# Each input rows generates one or more output rows.
# The number of rows generated by an input row equals
# the number of elements in the list-valued column being
# expanded. Multiple columns may be expanded at once.
# In that case, they are expanded "in parallel". That
# is, for a given input row, the j-th output row 
# contains the j-th list element from each of the expanded
# columns. 
#
# OPTIONS:
#  -e ERR:action, --error-handler ERR:action
#       
#  -x COL:PSS, --expand COL:PSS
#       Expands input column COL. 
#
#----------------------------------------------------------------------

DEFAULT_PSS='[,]'

#----------------------------------------------------------------------
#
class TXpand ( UnaryTableTool ) :
    def __init__(self,argv):
        UnaryTableTool.__init__(self)
        self.xpColumns = [] # list (col,pref,sep,suff)
        self.parseCmdLine(argv)

    #---------------------------------------------------------
    def initArgParser(self):
        UnaryTableTool.initArgParser(self)
        self.parser.add_option("-x", "--expand", 
            action="append", dest="xpSpecs", default=[], 
            metavar="COL[:PSS]",
            help="Expand column COL. " + \
                "Use PSS as prefix/sep/suffix (Optional. Default=','). ")

    #---------------------------------------------------------
    def processXspec(self, spec):
        tokens = spec.split(':', 1)
        #
        col = int(tokens[0])
        pss = DEFAULT_PSS
        if len(tokens) == 2 and len(tokens[1]) > 0:
            pss = tokens[1]
        #
        self.separator = ','
        self.prefix = ''
        self.suffix = ''
        lx = -1
        if pss != None:
            lx = len(pss)

        if lx == 0:
            self.separator = ''
            self.prefix = ''
            self.suffix = ''
        elif lx==1:
            self.separator = pss
            self.prefix = ''
            self.suffix = ''
        elif lx==2:
            self.separator = ''
            self.prefix = pss[0]
            self.suffix = pss[1]
        elif lx==3:
            self.separator = pss[1]
            self.prefix = pss[0]
            self.suffix = pss[2]

        self.xpColumns.append( (col,self.prefix,self.separator,self.suffix) )

    #---------------------------------------------------------
    def processOptions(self, opts):
        for spec in opts.xpSpecs:
            self.processXspec(spec)

    #---------------------------------------------------------
    # Parses a string encoded list into an actual list.
    # 
    #
    def expandValue(self, value, prefix, sep, suffix, conv=None):
        if type(value) is not str:
            return None

        a=len(prefix)
        b=len(value) - len(suffix)

        valPrefix = value[0:a]
        if valPrefix != prefix:
            raise RuntimeError("SyntaxError")
        valSuffix = value[b:]
        if valSuffix != suffix:
            raise RuntimeError("SyntaxError")

        valItems = list(map(conv, re.split(sep, value[a:b])))
        return valItems

    #---------------------------------------------------------
    def expandRow(self, row):
        xvals = [] # list of (col, expanded-val-list)
        nxr = 1    # number of expanded rows generated by this row

        # expand all the specified columns.
        # determine number of expanded rows.
        #
        for (col,pfx,sep,sfx) in self.xpColumns:
            xvs = self.expandValue(row[col],pfx,sep,sfx)
            if xvs is not None:
                xvals.append( (col,xvs) )
                nxr = max( nxr, len(xvs) )

        xrows = []
        i=0
        while i < nxr:
            xrow = row[:]
            for (col, xvlist) in xvals:
                if i < len(xvlist):
                    xrow[col] = xvlist[i]
                else:
                    xrow[col] = ''
            xrows.append(xrow)
            i = i+1

        return xrows

    #---------------------------------------------------------
    def generateOutputRows(self, inrow):
        for xr in self.expandRow(inrow):
            r=self.generateOutputRow(xr)
            if r is not None:
                self.writeOutput(r[1:])

    #---------------------------------------------------------
    def go(self):
        inrow = self.t1.nextRow()
        while(inrow):
            self.generateOutputRows(inrow)
            inrow = self.t1.nextRow()

#------------------------------------------------------------
#------------------------------------------------------------
# Define these globals for backwards compatability.
# New code should use the real class names.

FJ = FJoin
TA = TAggregate
TB = TBucketize
TD = TDifference
TF = TFilter
TI = TIntersection
TJ = TJoin
TP = TPartition
TS = TSort
TU = TUnion
TX = TXpand

# Maps string to operator classes

OPERATION_MAP = {
        'fj' : FJ,
        'ta' : TA,
        'tb' : TB,
        'td' : TD,
        'tf' : TF,
        'ti' : TI,
        'tj' : TJ,
        'tp' : TP,
        'ts' : TS,
        'tu' : TU,
        'tx' : TX,
        }

#----------------------------------------------------------------------
#----------------------------------------------------------------------
#  Remainder of code handles initial command-line processing.
#  Mainly, decides what operator is specified and creating an
#  instance of that operator class.
#----------------------------------------------------------------------
#----------------------------------------------------------------------

def die(message = None, exitCode = -1):
        if message is not None:
            sys.stderr.write(message)
            sys.stderr.write(NL)
        sys.exit(exitCode)

def interpretCommandLine(args):
        op = None
        opClass = None
        if len(args) == 0:
            pass
        elif args[0] in OPERATION_MAP:
            op = args[0]
            opClass = OPERATION_MAP[op]
            args = args[1:]
        elif len(args) == 1:
            pass
        elif args[1] in OPERATION_MAP:
            op = args[1]
            opClass = OPERATION_MAP[op]
            args = args[2:]
        elif args[1] in ["-h", "--help"]:
            print(HELPTEXT)
            sys.exit(-1)

        if opClass is None:
            die("No operation specified or operation was unknown.")

        opClass(args).go()

#----------------------------------------------------------------------

if __name__ == "__main__":
        interpretCommandLine(sys.argv)
