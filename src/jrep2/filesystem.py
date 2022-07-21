import pathlib, os, mmap
from . import glob

class OpenedPath(pathlib.Path):
	def __new__(cls, *args, **kwargs):
		if issubclass(cls, OpenedPath):
			cls=OpenedWindowsPath if os.name=="nt" else OpenedPosixPath
		self=cls._from_parts(args)
		if not self._flavour.is_supported:
			raise NotImplementedError(f"cannot instantiate {cls.__name__!r} on your system")
		return self
	def __init__(self, *args, **kwargs):
		fileHandler=open(self.as_posix(), "r")
		try:
			self.contents=mmap.mmap(fileHandler.fileno(), 0, access=mmap.ACCESS_READ)
		except OSError:
			# Windows cannot mmap an empty file
			self.contents=b""

class OpenedWindowsPath(OpenedPath, pathlib.WindowsPath):
	pass

class OpenedPosixPath(OpenedPath, pathlib.PosixPath):
	pass

def getFiles(globs):
	for pattern in globs:
		for filePath in glob.iglob(pattern):
			try:
				yield OpenedPath(filePath)
			except PermissionError:
				...
