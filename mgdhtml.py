# htmllib.py
#
######################################################################
# Copyright (C) 1994 The Jackson Laboratory
#  
# Permission to use, copy, modify, distribute, and sell this software
# and its documentation for any purpose is hereby granted without fee,
# provided that the above copyright notice appear in all copies and
# that both that copyright notice and this permission notice appear
# in supporting documentation, that the fact that modifications have
# been made is clearly represented in any modified copies, and that
# the name of The Jackson Laboratory not be used in advertising or
# publicity pertaining to distribution of the software without
# specific, written prior permission.
#  
# THE JACKSON LABORATORY MAKES NO REPRESENTATIONS ABOUT THE
# SUITABILITY OF THIS SOFTWARE FOR ANY PURPOSE AND MAKES NO
# WARRANTIES, EITHER EXPRESS OR IMPLIED, INCLUDING WARRANTIES
# OF MERCHANTABILITY OR FITNESS OR THAT THE USE OF THIS
# SOFTWARE WILL NOT INFRINGE ANY THIRD PARTY PATENTS, COPYRIGHTS,
# TRADEMARKS OR OTHER RIGHTS.  IT IS PROVIDED "AS IS."
######################################################################
#

import sys
import wi_utils

def ht_title(content):
	sys.stdout.write('<TITLE>%s - %s</TITLE>' % \
		(wi_utils.mgiTitle (), content))
def ht_h1(content):
	sys.stdout.write('<H1>' + content + '</H1>')
def ht_hr():
	sys.stdout.write('<HR>')
def ht_anchor(link, content):
	sys.stdout.write('<A HREF="' + link + '">' + content + '</A>')

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
