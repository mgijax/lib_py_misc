# Name: symbolsort.py
# Purpose: provide a splitter() function that can be shared across Python products to
#    consistently split an alphanumeric string into a tuple of integers and strings for
#    sorting.

# global dictionaries used by splitter() for speedy lookups:

sdict = {       '' : ('')       }
digits = {      '1' : 1,        '2' : 1,        '3' : 1,        '4' : 1,
                '5' : 1,        '6' : 1,        '7' : 1,        '8' : 1,
                '9' : 1,        '0' : 1 }

def splitter (s):
        # Purpose: split string 's' into a tuple of strings and integers,
        #   representing the contents of 's' for sorting purposes
        # Returns: tuple containing a list of strings and integers
        # Assumes: s is a string or None
        # Effects: nothing
        # Throws: nothing
        # Notes: Because Python 3.7 does not allow strings to be compared with integers,
        #    we must ensure that all tuples have the same ordering of integers and strings.
        #    (So even for ones that would begin with a string, we'll prepend an integer to
        #    force it to appear after those beginning with integers.)
        # Examples:
        #       'Ren1' ==> (9999999, 'ren', 1)
        #       'abc123def' ==> (9999999, 'abc', 123, 'def')
        #       '789xyz32' ==> (789, 'xyz', 32)

        global sdict

        if s == None:
            return (99999999,)
        if s in sdict:
                return sdict[s]
        last = 0
        items = []
        sl = s.lower ()
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
                
        if type(items[0]) != int:
            items.insert(0, 9999999)

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

