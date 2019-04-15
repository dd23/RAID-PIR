#!/usr/bin/env python3
"""
<Author>
	Daniel Demmler
	(inspired from upPIR by Justin Cappos)
	(inspired from a previous version by Geremy Condra)

<Date>
	January 2019

<Description>
	Creates a manifest from the files in a directory.   This takes a set of
	files that one wants to serve (rooted in 'vendorroot') and prepares the
	necessary metadata (manifest file) to serve them.   The client, mirror,
	and vendor all need this file in order for RAID-PIR to function.   Note that
	this file includes the host name of the vendor and so must be regenerated
	if the vendor's host name changes.

	The block size is the minimum number of bytes that must be downloaded from
	a mirror. A setting of 1MB will work well for most applications. However,
	for more information about tuning this, please see the website.



<Usage>
	$ python raidpir_create_manifest.py vendorroot blocksize vendorhostname


<Options>

See below

"""

# This file is laid out in two main parts.   First, we parse the command line
# options using parse_options(). Next, we generate the mainfest in the
# main part (not in a function).
#
# EXTENSION POINTS:
#
# The manifest file could be extended to support huge files (those that
# span multiple releases).   This would primarily require client changes, but
# it may be useful to add metadata to the manifest to further indicate
# information about how to stitch these files back together.


import sys

import raidpirlib as lib

import optparse

# Check the python version
if sys.version_info[0] != 3 or sys.version_info[1] < 5:
	print("Requires Python >= 3.5")
	sys.exit(1)

import msgpack


def parse_options():
	"""
	<Purpose>
		Parses command line arguments.

	<Arguments>
		None

	<Side Effects>
		None

	<Exceptions>
		These are handled by optparse internally.   I believe it will print / exit
		itself without raising exceptions further.   I do print an error and
		exit if there are extra args...

	<Returns>
		The command line options (includes the rootdir and blocksize)
	"""


	parser = optparse.OptionParser()

	parser.add_option("-m", "--manifestfile", dest="manifestfile", type="string",
				metavar="manifestfile", default="manifest.dat",
				help="Use this name for the manifest file (default manifest.dat)")

	parser.add_option("-p", "--vendorport", dest="vendorport", type="int",
				metavar="port", default=62293,
				help="The vendor will listen on this port (default 62293)")


	parser.add_option("-H", "--hashalgorithm", dest="hashalgorithm", type="string",
				metavar="algorithm", default="sha256-raw",
				help="Chooses which algorithm to use for the secure hash (default sha256-raw)")

	parser.add_option("-o", "--offsetalgorithm", dest="offsetalgorithm",
				type="string", metavar="algorithm", default="nogaps",
				help="Chooses how to put the files into blocks (default is 'nogaps'). Use 'eqdist' for uniform distribution of the data entries.")

	parser.add_option("-d", "--database", dest="database", metavar="filename", type="string", default=None, help="Create a single database file with this name and copy files into it.")


	# let's parse the args
	(commandlineoptions, remainingargs) = parser.parse_args()

	# check the arguments
	if len(remainingargs) != 3:
		print("Requires exactly three additional arguments: rootdir blocksize vendorhostname")
		sys.exit(1)

	# add these to the object to parse later...
	commandlineoptions.rootdir = remainingargs[0]

	commandlineoptions.blocksize = int(remainingargs[1])

	commandlineoptions.vendorhostname = remainingargs[2]

	if commandlineoptions.blocksize <= 0:
		print("Specified blocksize number is not positive")
		sys.exit(1)

	if commandlineoptions.blocksize % 64:
		print("Blocksize must be divisible by 64")
		sys.exit(1)

	if commandlineoptions.vendorport <= 0 or commandlineoptions.vendorport > 65535:
		print("Invalid vendorport")
		sys.exit(1)

	return commandlineoptions


if __name__ == '__main__':

	print("RAID-PIR create manifest", lib.pirversion)
	# parse user provided data
	commandlineoptions = parse_options()

	# create the dict
	manifestdict = lib.create_manifest(rootdir=commandlineoptions.rootdir,
		hashalgorithm=commandlineoptions.hashalgorithm,
		block_size=commandlineoptions.blocksize,
		datastore_layout=commandlineoptions.offsetalgorithm,
		vendorhostname=commandlineoptions.vendorhostname,
		vendorport=commandlineoptions.vendorport)

	# open the destination file
	manifestfo = open(commandlineoptions.manifestfile, 'wb')

	# and write it in a safely serialized format (msgpack).
	rawmanifest = msgpack.packb(manifestdict, use_bin_type=True)
	manifestfo.write(rawmanifest)

	manifestfo.close()

	if commandlineoptions.database != None:
		lib._write_db(commandlineoptions.rootdir, commandlineoptions.database)

	print("Generated manifest", commandlineoptions.manifestfile, "with", manifestdict['blockcount'], manifestdict['blocksize'], 'Byte blocks.')
