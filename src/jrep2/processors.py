import sys
from . import utils

def replace(parsedArgs, match, regexIndex, **kwargs):
	if parsedArgs.replace is not None:
		match[0]=match.expand(parsedArgs.replace[regexIndex%len(parsedArgs.replace)])

def _subHelper(subRules, match, regexIndex=0, **kwargs):
	"""
		Handle --sub and similar processors
	"""
	if subRules:
		regexIndex=regexIndex%len(subRules)
		if regexIndex<len(subRules):
			for group in subRules[regexIndex]:
				if utils.regexCheckerThing(match, group["tests"], group["antiTests"], []):
					if isinstance(match, str):
						repls=group["replsStr"]
					else:
						repls=group["replsBytes"]
					for pattern, repl in zip(group["patterns"], repls):
						match=pattern.sub(repl, match)
	return match

def sub(parsedArgs, match, regexIndex, **kwargs):
	match[0]=_subHelper(parsedArgs.sub, match[0], regexIndex)

def fullPathSub(parsedArgs, file, **kwargs):
	"""
		a/b/c.txt
		If --print-full-paths then C:/a/b/c.txt
	"""
	name=file.as_posix()
	name=_subHelper(parsedArgs.path_sub, name)
	del file._str # Uncaches the full path (needed because Path.as_posix checks for this)
	file._parts=name.split("/")

def dirPathSub(parsedArgs, file, **kwargs):
	"""
		a/b
	"""
	name=file.parents[0].as_posix()
	name=_subHelper(parsedArgs.dir_path_sub, name)
	del file._str # Uncaches the full path (needed because Path.as_posix checks for this)
	file._parts=name.split("/")+file._parts[-1]

def fileNameSub(parsedArgs, file, **kwargs):
	"""
		c.txt
	"""
	name=file._parts[-1]
	name=_subHelper(parsedArgs.file_name_sub, name)
	try:
		del file._str # Uncaches the full path (needed because Path.as_posix checks for this)
	except AttributeError:
		# Since file.as_posix isn't called there's no guarantee there's a cache to delete
		pass
	file._parts[-1]=name

def fullPathRegex(parsedArgs, file, **kwargs):
	"""
		a/b/c.txt
		If --print-full-paths then C:/a/b/c.txt
	"""
	name=file.as_posix()
	ret=utils.regexCheckerThing(
		match[0],
		parsedArgs.full_path_regex,
		parsedArgs.full_path_anti_regex,
		parsedArgs.full_path_ignore_regex
	)
	if ret is True : runtimeData.count("passed" , "match", regexIndex)
	if ret is None : runtimeData.count("ignored", "match", regexIndex)
	if ret is False: runtimeData.count("failed" , "match", regexIndex)

def dirPathRegex(parsedArgs, file, **kwargs):
	"""
		a/b
	"""
	name=file.parents[0].as_posix()
	ret=utils.regexCheckerThing(
		match[0],
		parsedArgs.dir_path_regex,
		parsedArgs.dir_path_anti_regex,
		parsedArgs.dir_path_ignore_regex
	)
	if ret is True : runtimeData.count("passed" , "match", regexIndex)
	if ret is None : runtimeData.count("ignored", "match", regexIndex)
	if ret is False: runtimeData.count("failed" , "match", regexIndex)

def fileNameRegex(parsedArgs, file, **kwargs):
	"""
		c.txt
	"""
	name=file._parts[-1]
	ret=utils.regexCheckerThing(
		match[0],
		parsedArgs.file_name_regex,
		parsedArgs.file_name_anti_regex,
		parsedArgs.file_name_ignore_regex
	)
	if ret is True : runtimeData.count("passed" , "match", regexIndex)
	if ret is None : runtimeData.count("ignored", "match", regexIndex)
	if ret is False: runtimeData.count("failed" , "match", regexIndex)

def matchRegex(parsedArgs, runtimeData, match, regexIndex, **kwargs):
	ret=utils.regexCheckerThing(
		match[0],
		parsedArgs.match_regex,
		parsedArgs.match_anti_regex,
		parsedArgs.match_ignore_regex
	)
	if ret is True : runtimeData.count("passed" , "match", regexIndex)
	if ret is None : runtimeData.count("ignored", "match", regexIndex)
	if ret is False: runtimeData.count("failed" , "match", regexIndex)

def printDirName(parsedArgs, runtimeData, file, **kwargs):
	if runtimeData["dir"]["printedName"]==False:
		runtimeData["dir"]["printedName"]=True
		print(file.parents[0].as_posix())

def printFileName(parsedArgs, runtimeData, file, **kwargs):
	if runtimeData["file"]["printedName"]==False:
		runtimeData["file"]["printedName"]=True
		print(file.as_posix())

def printMatch(parsedArgs, runtimeData, match, **kwargs):
	if parsedArgs.escape:
		sys.stdout.buffer.write(utils.escape(match[0]))
	else:
		sys.stdout.buffer.write(match[0])
	sys.stdout.buffer.write(b"\n")

# funcs={
# 	"replace"                 : funcReplace,
# 	"match-whole-lines"       : funcMatchWholeLines,
# 	"sub"                     : funcSub,
# 	"stdin-anti-match-strings":	funcStdinAntiMatchStrings,
# 	"match-regex"             : funcMatchRegex,
# 	"no-name-duplicates"      : funcNoNameDuplicates,
# 	"no-duplicates"           : funcNoDuplicates,
# 	"print-dir-name"          : funcPrintDirName,
# 	"print-name"              : funcPrintName,
# 	"print-match"             : funcPrintMatch,
# }

funcs={
	"file-name-sub"  : fileNameSub,
	"dir-path-sub"   : dirPathSub,
	"full-path-sub"  : fullPathSub,

	"file-name-regex": fileNameRegex,
	"dir-path-regex" : dirPathRegex,
	"full-path-regex": fullPathRegex,

	"replace"        : replace,
	"sub"            : sub,
	"match-regex"    : matchRegex,
	"print-dir-name" : printDirName,
	"print-file-name": printFileName,
	"print-match"    : printMatch,
}
