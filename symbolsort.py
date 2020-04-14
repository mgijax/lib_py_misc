# Purpose: provide a nomenCompare() function to replace the byNumeric(),
#	bySymbol(), and byFilename() functions in the WI's version of
#	mgd_utils.py
# Notes:
#	At some point, this mgd_utils should be pulled out of the WI and CCR.
#	The code here should supercede that in the WI, as noted in the Purpose
#	above.  This remedies a bug in the WI whereby Ren1 == ren2 for sorting
#	purposes.
#	This file is now also used in the ratpages.  It should be pulled out
#	of there as well.

# global dictionaries used by splitter() for speedy lookups:

sdict = {	'' : ('')	}
digits = {	'1' : 1,	'2' : 1,	'3' : 1,	'4' : 1,
                '5' : 1,	'6' : 1,	'7' : 1,	'8' : 1,
                '9' : 1,	'0' : 1	}

def splitter (s):
        # Purpose: split str.'s' into a tuple of str. and integers,
        #	representing the contents of 's'
        # Returns: tuple containing a list of str. and integers
        # Assumes: s is a string
        # Effects: nothing
        # Throws: nothing
        # Examples:
        #	'Ren1' ==> ('Ren', 1)
        #	'abc123def' ==> ('abc', 123, 'def')

        global sdict
        if s in sdict:
                return sdict[s]
        last = 0
        items = []
        sl = str.lower (s)
        in_digits = sl[0] in digits
        for i in range(0, len(sl)):
                if (sl[i] in digits) != in_digits:
                        if in_digits:
                                items.append (str.atoi(sl[last:i]))
                        else:
                                items.append (sl[last:i])
                        last = i
                        in_digits = not in_digits
        if in_digits:
                items.append (str.atoi (sl[last:]))
        else:
                items.append (sl[last:])
        sdict[s] = tuple(items)
        return sdict[s]

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
