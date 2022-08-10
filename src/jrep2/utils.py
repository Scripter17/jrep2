import argparse, re, fnmatch, functools
import regex
from . import classchecking

def isEnhancedEngine(context):
	return isinstance(context, argparse.Namespace) and context.enhanced_engine or\
		isinstance(context, regex.Pattern) or\
		context is True

def getRegexEngine(context):
	if isEnhancedEngine(context):
		return regex
	return re

def listSplit(arr, needle):
	"""
		str.split but for lists. I doubt I need to say much else
	"""
	ret=[[]]
	for x in arr:
		if x==needle:
			ret.append([])
		else:
			ret[-1].append(x)
	return ret

def reEncode(x, totype):
	if type(x)==totype:
		return x
	elif classchecking.isPattern(x):
		return reEncode(x.pattern, totype)
	elif type(x)==str:
		return x.encode()
	elif type(x)==bytes:
		return x.decode()

def regexCheckerThing(toCheck, passPatterns, failPatterns, ignorePatterns):
	"""
		True  = Passed
		False = Failed
		None  = Ignored
	"""
	if ignorePatterns and any(map(lambda x:x.search(toCheck), ignorePatterns)):
		return None
	elif failPatterns and any(map(lambda x:x.search(toCheck), failPatterns)):
		return False
	elif all(map(lambda x:x.search(toCheck), passPatterns)):
		return True
	return False

def globCheckerThing(partial, partialPass, partialFail, full="", fullPass=[], fullFail=[], partialIgnore=[], fullIgnore=[]):
	"""
		partial=Desktop/Whatever
		full   =C:/Users/You/Desktop/Whatever

		True  = Passed
		False = Failed
		None  = Ignored
	"""
	if any(map(lambda x:fnmatch.fnmatch(partial, x), partialIgnore)) or\
	   any(map(lambda x:fnmatch.fnmatch(full   , x), fullIgnore   )):
		return None
	if any(map(lambda x:fnmatch.fnmatch(partial, x), partialFail)) or\
	   any(map(lambda x:fnmatch.fnmatch(full   , x), fullFail   )):
		return False
	if all(map(lambda x:fnmatch.fnmatch(partial, x), partialPass)) and\
	   all(map(lambda x:fnmatch.fnmatch(full   , x), fullPass   )):
		return True
	return False

def escape(byteString):
	ret=byteString.replace(b"\\", b"\\\\")
	ret=ret.replace(b"\n", b"\\n")
	ret=ret.replace(b"\r", b"\\r")
	ret=ret.replace(b"\t", b"\\t")
	ret=re.sub(b"[\x00-\x1f\x80-\xff]", lambda x:f"\\x{ord(x[0]):02x}".encode(), ret)
	return ret

class RuntimeData(dict):
	categories={
		"total":["dir", "file", "match"],
		"dir"  :[       "file", "match"],
		"file" :[               "match"]
	}
	parentCategories={
		"dir"  :["total"               ],
		"file" :["total", "dir"        ],
		"match":["total", "dir", "file"]
	}
	filters=["processed", "passed", "failed"]

	def __init__(self, parsedArgs):
		self.regexCount=len(parsedArgs.regex)
		for category, subCategories in self.categories.items():
			self[category]={}
			for subCategory in subCategories:
				self[category][subCategory]={}
				for filter in self.filters:
					if subCategory=="match":
						self[category][subCategory][filter]=[0 for _ in range(self.regexCount)]
					else:
						self[category][subCategory][filter]=0
		self["file"]["printedName"]=False
		self["dir" ]["printedName"]=False

	@classmethod
	def flatDictKeys(cls):
		ret=[]
		for category, subCategories in cls.categories.items():
			for subCategory in subCategories:
				for filter in cls.filters:
					ret.append(f"{category}{filter.title()}{subCategory.title()}")
		ret.append("printedFileName")
		ret.append("printedDirName" )
		return ret

	def asFlatDict(self):
		ret={}
		for category, subCategories in self.categories.items():
			for subCategory in subCategories:
				for filter in self.filters:
					ret[f"{category}{filter.title()}{subCategory.title()}"]=self[category][subCategory][filter]
		ret["printedFileName"]=self["file"]["printedName"]
		ret["printedDirName" ]=self["dir" ]["printedName"]
		return ret

	def new(self, category):
		self[category]["printedName"]=False
		for subCategory in self.categories[category]:
			for filter in self.filters:
				if subCategory=="match":
					self[category][subCategory][filter]=[0 for _ in range(self.regexCount)]
				else:
					self[category][subCategory][filter]=0

	def count(self, filter, subCategory, regexIndex=None):
		filters=["processed"] if filter=="ignored" else ["processed", filter]
		for category in self.parentCategories[subCategory]:
			for filter in filters:
				if subCategory=="match":
					self[category][subCategory][filter][regexIndex]+=1
				else:
					self[category][subCategory][filter]+=1
		if filter=="failed" or filter=="ignored":
			raise nexts[subCategory]

class NextDir(Exception):
	pass
class NextFile(Exception):
	pass
class NextMatch(Exception):
	pass

nexts={
	"dir"  :NextDir  ,
	"file" :NextFile ,
	"match":NextMatch
}

def shouldOpenFiles(parsedArgs):
	return bool(parsedArgs.regex)
