# Name: symbolsort.py
# Purpose: provide a nomenCompare() function to replace the byNumeric(),
#       bySymbol(), and byFilename() functions in the WI's version of
#       mgd_utils.py
# Notes:
#       At some point, this mgd_utils should be pulled out of the WI and CCR.
#       The code here should supercede that in the WI, as noted in the Purpose
#       above.  This remedies a bug in the WI whereby Ren1 == ren2 for sorting
#       purposes.
#       This file is now also used in the ratpages.  It should be pulled out
#       of there as well.

import string

# global dictionaries used by splitter() for speedy lookups:

sdict = {       '' : ('')       }
digits = {      '1' : 1,        '2' : 1,        '3' : 1,        '4' : 1,
                '5' : 1,        '6' : 1,        '7' : 1,        '8' : 1,
                '9' : 1,        '0' : 1 }

def splitter (s):
        # Purpose: split string 's' into a tuple of strings and integers,
        #       representing the contents of 's'
        # Returns: tuple containing a list of strings and integers
        # Assumes: s is a string
        # Effects: nothing
        # Throws: nothing
        # Examples:
        #       'Ren1' ==> ('Ren', 1)
        #       'abc123def' ==> ('abc', 123, 'def')

        global sdict
        if s in sdict:
                return sdict[s]
        last = 0
        items = []
        sl = string.lower (s)
        in_digits = sl[0] in digits
        for i in range(0, len(sl)):
                if (sl[i] in digits) != in_digits:
                        if in_digits:
                                items.append (int(sl[last:i]))
                        else:
                                items.append (sl[last:i])
                        last = i
                        in_digits = not in_digits
        if in_digits:
                items.append (int(sl[last:]))
        else:
                items.append (sl[last:])
        sdict[s] = tuple(items)
        return sdict[s]

def nomenCompare (s1, s2):
        # Purpose: compare strings s1 and s2
        # Returns: an integer;  negative if s1 < s2,
        #                       0 if s1 == s2,
        #                       positive if s1 > s2
        # Assumes: s1 and s2 are strings
        # Effects: nothing
        # Throws: nothing
        # Notes: considers numerics which may be included in s1 & s2, so that
        #       'Abc9' sorts before 'Abc10', for example

        return cmp(splitter(s1), splitter(s2))
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

