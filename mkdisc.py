#!/usr/bin/python

import tempfile
import fileinput
import re
import os
import sys
import subprocess

# DVD-5: 4.38 Gb
# DVD-9: 7.95 Gb

SI_GIGABYTE = 1000000000
DVD9_GB = 7.96 * SI_GIGABYTE
DVD5_GB = 4.37 * SI_GIGABYTE

DIR_EXCLUDES = [
	'.AppleDouble',
	'.DS_Store'
]

class IndexReader(object):

	RE_FOLDER = re.compile(r'^\[\s*(?:folder|directory|dir)\s+(.*)\s*\]$')
	RE_FILEENTRY = re.compile(r'^((?P<alias>[^=]*)\s*=\s*)?(?P<actual>.*)$')


	def __init__(self, filename):
		self.filename = filename

	def getlines(self):
		folder = None
		for line in fileinput.input(self.filename):
			filename = None
			if (len(line) == 0) or (line[0:1] == ';'): 
				continue # ignore comments and blank lines
			folder_match = self.RE_FOLDER.match(line)
			if folder_match is not None:
				folder = folder_match.group(1).strip()
				if folder[0:1] == '/':
					folder = '.' + folder
				continue
			file_match = self.RE_FILEENTRY.match(line)
			if file_match is not None:
				filename_actual = file_match.group('actual').strip()
				filename = file_match.group('alias')
				if filename is None or len(filename) == 0:
					filename = filename_actual
				if filename.endswith('/'):
					filename = filename[0:-1]
				filename = os.path.basename(filename).strip()
			if len(folder) and len(filename):
				yield folder, filename, filename_actual


class TreeLinker(object):
	def __init__(self, output_path, index_file):
		self.index = IndexReader(index_file)
		self.output = output_path

	def setup(self):
		size_total = 0
		if not os.path.isdir(self.output):
			os.makedirs(self.output)
		for folder, filename, actual in self.index.getlines():
			dest_folder = os.path.join(self.output, folder)
			dest_file = os.path.join(dest_folder, filename)
			if not os.path.isdir(dest_folder):
				os.makedirs(dest_folder)
			os.symlink(os.path.realpath(actual), dest_file)
			size_total = size_total + os.stat(actual).st_size
		return size_total
			

	def scan(self, followlinks = True):
		for root, dirs, files in os.walk(self.output, followlinks = followlinks):
			for e in DIR_EXCLUDES:
				if e in files: files.remove(e)
				if e in dirs: dirs.remove(e)
			for name in files:
				yield os.path.join(root, name)

	def wipeout(self):
		for root, dirs, files in os.walk(self.output, followlinks = False, topdown = False):
			for f in files:
				os.remove(os.path.join(root, f))
			for d in dirs:
				p = os.path.join(root, d)
				if os.path.isdir(p):
					os.rmdir(p)
				elif os.path.islink(p):
					os.remove(p)
	
					
class ImageBuilder(object):

	# TODO: MD5 generation
	# TODO: accommodate filenames with "#" in them, etc. (-no-bak ignores them)
	
	COMMAND = """genisoimage -f -cache-inodes -iso-level 4 -l
		-J -joliet-long -P NULL -p NULL -r
		-relaxed-filenames
		-o {1} {0}
	"""

	def __init__(self, output_path, *input_paths, **kwargs):
		self.input = input_paths
		self.output = output_path
		
	def run(self):
		command = self.COMMAND.format(' '.join(self.input), self.output)
		command = command.replace('\n', '')
		self.__call__(command)

	@classmethod
	def __call__(cls, command):
		return subprocess.Popen(command, shell = True, stdout = subprocess.PIPE).communicate()
	

# TODO: options to simply create the index tree + estimate size

def main(args):
	linker_temp = tempfile.mkdtemp()
	linker = TreeLinker(linker_temp, args[0])
	linker.setup()

	builder = ImageBuilder(args[1], linker_temp)

	size = sum(os.path.getsize(s) for s in linker.scan())

	print 'Path: {0}'.format(linker.output)
	print 'DVD-5: {0:.2f}% full ({1:d})'.format(100* size / DVD5_GB, size)
	print 'DVD-9: {0:.2f}% full ({1:d})'.format(100* size / DVD9_GB, size)

	print 'Preparing image... {0}'.format(args[1])
	builder.run()

	print 'Cleaning out... {0}'.format(linker_temp)
	linker.wipeout()
	os.rmdir(linker_temp)

	print 'Done'

if __name__ == '__main__':
	main(sys.argv[1:])	
