# Name: ignoreDeprecation.py
# Purpose: When imported, this module suppresses all deprecation warnings
#	from python.  To turn deprecation warnings back on (so they can
#	be identified and fixed), just comment out your
#	'import ignoreDeprecation' line.

# If we are running in Python 2.1 or later, we can suppress all deprecation
# warnings.  If this fails, we must be running in an earlier Python version,
# so just ignore it and go forward.

try:
	import warnings
	warnings.filterwarnings (action = 'ignore',
		category = DeprecationWarning)
except:
	pass
