# Name: top.py
# Purpose: provides functions to retrieve data regarding a program's memory
#	usage, processor utilization, and such.  No data is gathered auto-
#	matically; you must manually call the measure() method whenever you
#	want to add a data point to a Process object.

import os
import re
import subprocess
import platform
import gc

###--- Globals ---###

SOLARIS = 1	# used to identify that we are running on a Solaris box
LINUX = 2	# used to identify that we are running on a Linux box

MODE = None	# value from either SOLARIS or LINUX, above (set automatically)

# pulls a numeric group and a suffix group out of a RAM report (like 4.3M)
ramRegex = re.compile ('^([0-9.]+)([KkMmGgTt])$')

# looks for just an integer
intRegex = re.compile ('^([0-9]+)$')

# pulls a numeric group out of a CPU percentage (like 33.2%)
cpuRegex = re.compile ('^([0-9.]+)%?$')

KB = 1024	# bytes per kilobyte
MB = KB * KB	# bytes per megabyte
GB = MB * KB	# bytes per gigabyte
TB = MB * MB	# bytes per terabyte

# maps from a suffix (pulled out via ramRegex) to the multiplier to find the
# raw number of bytes represented
ramMultipliers = {
	'K' : KB,
	'k' : KB,
	'M' : MB,
	'm' : MB,
	'G' : GB,
	'g' : GB,
	'T' : TB,
	't' : TB,
	}

# count of number of subprocess executions, used to know when to run garbage
# collection
executionCount = 0

###--- Functions ---###

def execute (cmd):
	# Purpose: execute the given Unix command in a subprocess
	# Returns: tuple of (stdout, stderr, returncode)

	global executionCount

	p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
	p.wait()

	returncode = p.returncode
	stdout, stderr = p.communicate()

	# free up the memory for 'p' and run garbage collection for every
	# 100th execution

	del p

	executionCount = executionCount + 1
	if executionCount % 100 == 0:
		gc.collect()

	return stdout, stderr, returncode

###--- Classes ---###

class Process:
	# Is: an object representing a Unix process
	# Has: data about the process's memory and CPU usage
	# Does: collects measurements and reports average, maximum, and latest
	#	values for CPU and memory usage

	def __init__ (self, pid):
		self.pid = pid		# unix process ID

		# We could keep these as just a list of values and then do the
		# computations later, but it's space-inefficient.  So, we'll
		# only keep the bare minimum here.

		self.memorySum = 0	# total of memory in use at each point
		self.memoryCount = 0	# number of data points for memory
		self.memoryMax = 0	# maximum memory use in a single point
		self.memoryLatest = 0	# memory use at the latest data point

		self.procSum = 0	# total of processor % at each point
		self.procCount = 0	# number of data points for CPU
		self.procMax = 0	# maximum processor % in a single point
		self.procLatest = 0	# CPU % at the latest data point
		return

	def measure (self):
		# collect and add a new set of measurements to the accumulated
		# statistics for this process.  Note that this relies upon a
		# getData() method to be defined in a subclass that is specific
		# to the operating system.

		ram, cpu = self.getData()

		if ram != None:
			mem = convertMemory(ram)
			if mem != None:
				self.memoryLatest = mem
				self.memoryCount = self.memoryCount + 1
				self.memorySum = self.memorySum + mem
				self.memoryMax = max(self.memoryMax, mem)

		if cpu != None:
			proc = convertProcessor(cpu)
			if proc != None:
				self.procLatest = proc
				self.procCount = self.procCount + 1
				self.procSum = self.procSum + proc
				self.procMax = max(self.procMax, proc)
		return

	def getAverageProcessorPct (self):
		# return the average processor percentage used by this process
		# in the measurements so far

		if self.procCount == 0:
			return None
		return self.procSum * 1.0 / self.procCount

	def getLatestProcessorPct (self):
		# return the processor percentage from the most recent
		# measurement

		return self.procLatest

	def getMaxProcessorPct (self):
		# return the maximum processor percentage measured so far

		return self.procMax

	def getAverageMemoryUsed (self):
		# return the average number of bytes used by this process
		# across the measurements collected so far

		if self.memoryCount == 0:
			return None
		return self.memorySum * 1.0 / self.memoryCount

	def getLatestMemoryUsed (self):
		# return the number of bytes used by this process at its most
		# recent measurement

		return self.memoryLatest

	def getMaxMemoryUsed (self):
		# return the maximum number of bytes used by this process so
		# far, across all its measurements so far

		return self.memoryMax

class LinuxProcess (Process):
	# Is: a Process object specific to the Linux operating system
	# Does: knows how to collect data about Linux processes

	def getData (self):
		# collect data about this process and return a 2-item tuple:
		# (ram, cpu) with each being a string; returns None for either
		# or both measurements when they are unavailable

		ram = None
		cpu = None

		# We use measrurements from 'top' as our Linux servers don't
		# have prstat.

		cmd = 'top -n 1 -b -p %s' % self.pid
		(stdout, stderr, exitcode) = execute(cmd)

		myLine = None
		lines = stdout.split('\n')
		pidStr = str(self.pid)

		for line in lines:
			if line.startswith(pidStr):
				myLine = line
				break

		if myLine:
			fields = myLine.split()
			if len(fields) >= 5:
				ram = fields[5]
				if len(fields) >= 8:
					cpu = fields[8]
		return ram, cpu

class SolarisProcess (Process):
	# Is: a Process object specific to the Solaris operating system
	# Does: knows how to collect data about Solaris processes

	def getData (self):
		# collect data about this process and return a 2-item tuple:
		# (ram, cpu) with each being a string; returns None for either
		# or both measurements when they are unavailable

		ram = None
		cpu = None

		# Solaris boxes have 'prstat', so we use that for the data
		# collection.

		cmd = 'prstat -p %s 1 1' % self.pid
		(stdout, stderr, exitcode) = execute(cmd)

		lines = stdout.split('\n')
		lastLine = lines[1]

		if lastLine:
			fields = lastLine.split()
			if len(fields) >= 3:
				ram = fields[3]
				if len(fields) >= 8:
					cpu = fields[8]
		return ram, cpu

###--- Public Functions ---###

def convertMemory(ram):
	# convert a memory measurement (as a string) to a float

	if not ram:
		return None

	match = ramRegex.match(ram)
	if not match:
		# Linux systems do not use a suffix for kilobytes, so if we
		# see just an integer, we can infer the measurement is in kb.

		match = intRegex.match(ram)
		if match:
			return int(match.group(1)) * KB

		return None

	num = float(match.group(1))
	suffix = match.group(2)

	if ramMultipliers.has_key(suffix):
		return num * ramMultipliers[suffix]
	return None 

def displayMemory(ram):
	# convert the memory amount (as a float) to be a string that is
	# convenient for human consumption (like 1.34G for 1.34 gigabytes)

	suffix = 'b'
	divisor = 1

	if ram >= TB:
		divisor = TB
		suffix = 't'
	elif ram >= GB:
		divisor = GB
		suffix = 'g'
	elif ram >= MB:
		divisor = MB
		suffix = 'm'
	elif ram >= KB:
		divisor = KB
		suffix = 'k'
	else:
		return str(round(ram))

	amount = (ram * 1.0) / divisor
	return '%0.3f%s' % (amount, suffix)

def displayProcessor(pct):
	# convert the processor percentage (as a float) to be a string that is
	# convenient for human consumption (like 1.25% for 1.2456456)

	return '%0.2f%%' % pct

def convertProcessor (cpu):
	# convert a processor measurement (as a string) to a float

	match = cpuRegex.match(cpu)
	if match:
		return float(match.group(1))
	return None

def getProcess(pid):
	# returns a Process object for the specified Unix pid
	if MODE == LINUX:
		return LinuxProcess(pid)
	return SolarisProcess(pid)

def getMyProcess():
	# returns a Process object for this script's Unix pid
	return getProcess(os.getpid())

###--- module initialization ---###

if platform.system().lower().find('linux') >= 0:
	MODE = LINUX
else:
	MODE = SOLARIS
