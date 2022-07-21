import argparse, re, dataclasses
try:
	import regex
except ModuleNotFoundError:
	regex=None
from . import classchecking

def isEnhancedEngine(context):
	ret=isinstance(context, argparse.Namespace) and context.enhanced_engine or\
		(regex is not None and isinstance(context, regex.Pattern)) or context is True
	if ret and regex is None:
		raise ModuleNotFoundError("mrab-regex module not installed; use `pip install regex` to use it")
	return ret

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

# WHY DID NOBODY TELL ME re.Match.expand WAS A THING
# def parseSubstitution(repl, matchRegex):
# 	# regex._compile_replacement_helper(regex.compile(r".(.)."), r"a\1b")
# 	# ['a', 1, 'b']
# 	# sre_parse.parse_template(r"a\1b", re.compile(".(.)."))
# 	# ([(1, 1)], ['a', None, 'b'])
# 	if isEnhancedEngine(matchRegex):
# 		return regex.regex._compile_replacement_helper(matchRegex, repl)
# 	maps, ret=sre_parse.parse_template(repl, matchRegex)
# 	for index, group in maps:
# 		ret[index]=group
# 	return ret

def regexCheckerThing(toCheck, passPatterns, failPatterns, ignorePatterns):
	"""
		True  = Passed
		False = Failed
		None  = Ignored
	"""
	if ignorePatterns and any(map(lambda x:x.search(toCheck), ignorePatterns)):
		return None
	if failPatterns and any(map(lambda x:x.search(toCheck), failPatterns)):
		return False
	if all(map(lambda x:x.search(toCheck), passPatterns)):
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

@dataclasses.dataclass
class RuntimeData:
	totalFileCount      : int=0
	totalPassedFileCount: int=0
	totalFailedFileCount: int=0
	totalIgnoredFileCount: int=0

class NextFile(Exception):
	pass
class NextMatch(Exception):
	pass
