# Makefile for lib_py_misc
#
# Usage: make PREFIXDIR=<directoryname>
# 
# The PREFIXDIR is the directory under which this product will 
# be installed. For example, if it is set to "/usr/local/mgi/depot/productname",
# the resulting installation would be in bin, lib, etc, man, and system_docs
# directories under /usr/local/mgi/depot/productname/.
#
# 

install:
	# check prefix 
	@ if \
        [ ! -d ${PREFIXDIR} ] ; \
	then \
		echo "${PREFIXDIR} is not a directory" ; \
		exit 1 ; \
	fi

	# create the 'lib' directory under the prefix dir, if necessary 
	@ if \
        [ ! -d ${PREFIXDIR}/lib ] ; \
	then \
		mkdir ${PREFIXDIR}/lib ; \
	fi

	# copy files
	cp -f mgdhtml.py     ${PREFIXDIR}/lib
	cp -f mgi_utils.py	 ${PREFIXDIR}/lib

	# set permissions 
	cd ${PREFIXDIR}/lib
	chmod 444 mgdhtml.py
	chmod 444 mgi_utils.py
