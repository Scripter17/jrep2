import pathlib, os, mmap
from . import glob, utils

class OpenedPath(pathlib.Path):
	def __new__(cls, *args, **kwargs):
		if issubclass(cls, OpenedPath):
			cls=OpenedWindowsPath if os.name=="nt" else OpenedPosixPath
		self=cls._from_parts(args)
		if not self._flavour.is_supported:
			raise NotImplementedError(f"cannot instantiate {cls.__name__!r} on your system")
		return self
	def __init__(self, filePath, parsedArgs):
		fileHandler=open(filePath, "r")
		if utils.shouldOpenFiles(parsedArgs):
			try:
				self.contents=mmap.mmap(fileHandler.fileno(), 0, access=mmap.ACCESS_READ)
			except ValueError:
				# Windows cannot mmap an empty file
				self.contents=b""
		else:
			self.contents=b""

class OpenedWindowsPath(OpenedPath, pathlib.WindowsPath):
	pass

class OpenedPosixPath(OpenedPath, pathlib.PosixPath):
	pass

def getFiles(parsedArgs):
	for pattern in parsedArgs.globs:
		for filePath in glob.iglob(pattern, recursive=True):
			if os.path.isfile(filePath):
				try:
					if parsedArgs.print_full_paths:
						yield OpenedPath(filePath, parsedArgs=parsedArgs).absolute()
					else:
						yield OpenedPath(filePath, parsedArgs=parsedArgs)
				except PermissionError:
					...
