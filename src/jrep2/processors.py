import sys, subprocess as sp, re
from . import utils, filtering

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
	if   ret is True : runtimeData.count("passed" , "match", regexIndex)
	elif ret is None : runtimeData.count("ignored", "match", regexIndex)
	elif ret is False: runtimeData.count("failed" , "match", regexIndex)

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
	if   ret is True : runtimeData.count("passed" , "match", regexIndex)
	elif ret is None : runtimeData.count("ignored", "match", regexIndex)
	elif ret is False: runtimeData.count("failed" , "match", regexIndex)

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
	if   ret is True : runtimeData.count("passed" , "match", regexIndex)
	elif ret is None : runtimeData.count("ignored", "match", regexIndex)
	elif ret is False: runtimeData.count("failed" , "match", regexIndex)

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

def printDirName(parsedArgs, runtimeData, file, stdout, **kwargs):
	if runtimeData["dir"]["printedName"]==False:
		runtimeData["dir"]["printedName"]=True
		stdout.write(b"dir: ")
		stdout.write(file.parents[0].as_posix().encode())
		stdout.write(b"\n")

def printFileName(parsedArgs, runtimeData, file, stdout, **kwargs):
	if runtimeData["file"]["printedName"]==False:
		runtimeData["file"]["printedName"]=True
		stdout.write(b"file: ")
		stdout.write(file.as_posix().encode())
		stdout.write(b"\n")

def printMatch(parsedArgs, runtimeData, match, stdout, **kwargs):
	stdout.write(b"match: ")
	if parsedArgs.escape_match_output:
		stdout.write(utils.escape(match[0]))
	else:
		stdout.write(match[0])
	stdout.write(b"\n")

def fileValidator(parsedArgs, runtimeData, file, **kwargs):
	if not all(map(lambda validator: filtering.evaluateExpr(parsedArgs, validator, filtering.getFileDict(file)), parsedArgs.file_validator)):
		runtimeData.count("failed", "file")

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

def fileValidatorCmd(parsedArgs, runtimeData, file, **kwargs):
	fileDict=filtering.getFileDict(file)
	for cmd, expr in zip(parsedArgs.file_validator_cmd, parsedArgs.file_validator_cmd_expr):
		returnData=sp.run(
			cmd.format(
				file.as_posix(),
				**fileDict
			),
			stdout=sp.PIPE,
			stderr=sp.PIPE
		)

		if not filtering.evaluateExpr(parsedArgs, expr, {
					"returncode":returnData.returncode,
					"stdout":returnData.stdout,
					"stderr":returnData.stderr,
					**fileDict
				}):
			runtimeData.count("failed", "file")

def cmdHelper(cmds, file):
	fileDict=filtering.getFileDict(file)
	for cmd in cmds:
		sp.run(cmd.format(file.as_posix(), **fileDict))

def preDirNameCmd  (parsedArgs, file, **kwargs): cmdHelper(parsedArgs.pre_dir_name_cmd  , file)
def postDirNameCmd (parsedArgs, file, **kwargs): cmdHelper(parsedArgs.post_dir_name_cmd , file)
def preFileNameCmd (parsedArgs, file, **kwargs): cmdHelper(parsedArgs.pre_file_name_cmd , file)
def postFileNameCmd(parsedArgs, file, **kwargs): cmdHelper(parsedArgs.post_file_name_cmd, file)
def preMatchCmd    (parsedArgs, file, **kwargs): cmdHelper(parsedArgs.pre_match_cmd     , file)
def postMatchCmd   (parsedArgs, file, **kwargs): cmdHelper(parsedArgs.post_match_cmd    , file)

skipConditionParser=re.compile(r"(\w+)=(.+)")
def skipConditions(parsedArgs, runtimeData, regexIndex=None, **kwargs):
	for expr in parsedArgs.skip_conditions:
		name, expr=skipConditionParser.match(expr).groups()
		if not filtering.evaluateExpr(parsedArgs, expr, runtimeData.asFlatDict()):
			runtimeData.count("failed", name.lower(), regexIndex)

funcs={
	"skip-conditions"    : skipConditions  ,

	"file-validator"     : fileValidator   ,
	"file-validator-cmd" : fileValidatorCmd,

	"file-name-sub"      : fileNameSub     ,
	"dir-path-sub"       : dirPathSub      ,
	"full-path-sub"      : fullPathSub     ,

	"file-name-regex"    : fileNameRegex   ,
	"dir-path-regex"     : dirPathRegex    ,
	"full-path-regex"    : fullPathRegex   ,

	"replace"            : replace         ,
	"sub"                : sub             ,

	"match-regex"        : matchRegex      ,

	"pre-dir-name-cmd"   : preDirNameCmd   ,
	"print-dir-name"     : printDirName    ,
	"post-dir-name-cmd"  : postDirNameCmd  ,

	"pre-file-name-cmd"  : preFileNameCmd  ,
	"print-file-name"    : printFileName   ,
	"post-file-name-cmd" : postFileNameCmd ,

	"pre-match-cmd"      : preMatchCmd     ,
	"print-match"        : printMatch      ,
	"post-match-cmd"     : postMatchCmd    ,
}

def getFuncs(parsedArgs):
	ret={**funcs}

	if not parsedArgs.skip_conditions: del ret["skip-conditions"]

	if not parsedArgs.file_validator_expr: del ret["file-validator" ]
	if not parsedArgs.file_validator_cmd or\
			not parsedArgs.file_validator_cmd_expr or\
			parsedArgs.no_cmd or\
			parsedArgs.no_expr:
		del ret["file-validator-cmd"]

	if not parsedArgs.file_name_sub   : del ret["file-name-sub"  ]
	if not parsedArgs.dir_path_sub    : del ret["dir-path-sub"   ]
	if not parsedArgs.full_path_sub   : del ret["full-path-sub"  ]

	if not parsedArgs.file_name_glob and\
			not parsedArgs.file_name_anti_glob and\
			not parsedArgs.file_name_ignore_glob and\
			not parsedArgs.file_name_regex and\
			not parsedArgs.file_name_anti_regex and\
			not parsedArgs.file_name_ignore_regex:
		del ret["file-name-regex"]
	if not parsedArgs.dir_path_glob  and\
			not parsedArgs.dir_path_anti_glob  and\
			not parsedArgs.dir_path_ignore_glob  and\
			not parsedArgs.dir_path_regex  and\
			not parsedArgs.dir_path_anti_regex  and\
			not parsedArgs.dir_path_ignore_regex :
		del ret["dir-path-regex"]
	if not parsedArgs.full_path_glob and\
			not parsedArgs.full_path_anti_glob and\
			not parsedArgs.full_path_ignore_glob and\
			not parsedArgs.full_path_regex and\
			not parsedArgs.full_path_anti_regex and\
			not parsedArgs.full_path_ignore_regex:
		del ret["full-path-regex"]

	if not parsedArgs.replace     or not parsedArgs.regex: del ret["replace"]
	if not parsedArgs.sub         or not parsedArgs.regex: del ret["sub"    ]

	if not parsedArgs.match_regex or not parsedArgs.regex: del ret["match-regex"]

	if not parsedArgs.print_dir_names : del ret["print-dir-name" ]
	if not parsedArgs.print_file_names: del ret["print-file-name"]
	if     parsedArgs.no_print_matches or not parsedArgs.regex:
		del ret["print-match"]

	if not parsedArgs.pre_dir_name_cmd   or parsedArgs.no_cmd: del ret["pre-dir-name-cmd"  ]
	if not parsedArgs.post_dir_name_cmd  or parsedArgs.no_cmd: del ret["post-dir-name-cmd" ]
	if not parsedArgs.pre_file_name_cmd  or parsedArgs.no_cmd: del ret["pre-file-name-cmd" ]
	if not parsedArgs.post_file_name_cmd or parsedArgs.no_cmd: del ret["post-file-name-cmd"]
	if not parsedArgs.pre_match_cmd      or parsedArgs.no_cmd: del ret["pre-match-cmd"     ]
	if not parsedArgs.post_match_cmd     or parsedArgs.no_cmd: del ret["post-match-cmd"    ]

	return tuple(ret.values())
