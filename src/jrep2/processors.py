
import sys, subprocess as sp, re
from . import utils, filtering

skipConditionParser=re.compile(r"(\w+):(.+)")
def skipConditions(parsedArgs, runtimeData, regexIndex=None, **kwargs):
	"""
		--skip-conditions <python expression 1> [<python expression 2> ...]
		Variables: totalProcessedDir  , totalPassedDir  , totalFailedDir  ,
		           totalProcessedFile , totalPassedFile , totalFailedFile ,
		           totalProcessedMatch, totalPassedMatch, totalFailedMatch,
		           dirProcessedFile   , dirPassedFile   , dirFailedFile   ,
		           dirProcessedMatch  , dirPassedMatch  , dirFailedMatch  ,
		           fileProcessedMatch , filePassedMatch , fileFailedMatch ,
		           printedFileName    , printedDirName
	"""
	for expr in parsedArgs.skip_conditions:
		name, expr=skipConditionParser.match(expr).groups()
		if not filtering.evaluateExpr(parsedArgs, expr, runtimeData.asFlatDict()):
			runtimeData.count("failed", name.lower(), regexIndex)



def fileValidatorExpr(parsedArgs, runtimeData, file, **kwargs):
	"""
		--file-validator-expr <python expression 1> [<python expression 2> ...]
		Variables: time (datetime.time), date (datetime.date), datetime (datetime.datetime),
		           path, abspath, normpath, filename, dir, absdir, normdir
		datetime classes have been modified to make comparing with ints/floats work
	"""
	if not all(map(lambda validator: filtering.evaluateExpr(parsedArgs, validator, filtering.getFileDict(file)), parsedArgs.file_validator_expr)):
		runtimeData.count("failed", "file")

def fileValidatorCmd(parsedArgs, runtimeData, file, **kwargs):
	"""
		--file-validator-cmd <command line command 1> [<command line command 2> ...]
		Variables: time (datetime.time), date (datetime.date), datetime (datetime.datetime),
		           path, abspath, normpath, filename, dir, absdir, normdir
		datetime classes have been modified to make comparing with ints/floats work
		Variables have to be written like {varname}
		{0} is {path}

		--file-validator-cmd-expr "<python expression 1>" ["<python expression 2>" ...]
		Variables: Same as above, returncode, stdout, stderr
	"""
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



def fileNameSub(parsedArgs, file, **kwargs):
	"""
		--file-name-sub <sub rules>
		Modifies the file.txt part of path/to/file.txt
		see _subHelper documentation
	"""
	name=_subHelper(parsedArgs.file_name_sub, file._parts[-1])
	try:
		del file._str # Uncaches the full path (needed because Path.as_posix checks for this)
	except AttributeError:
		# Since file.as_posix isn't called there's no guarantee there's a cache to delete
		pass
	file._parts[-1]=name

def dirPathSub(parsedArgs, file, **kwargs):
	"""
		--dir-path-sub <sub rules>
		Modifies the path/to part of path/to/file.txt
		see _subHelper documentation
	"""
	name=_subHelper(parsedArgs.dir_path_sub, file.parents[0].as_posix())
	del file._str # Uncaches the full path (needed because Path.as_posix checks for this)
	file._parts=name.split("/")+file._parts[-1]

def fullPathSub(parsedArgs, file, **kwargs):
	"""
		--path-sub <sub rules>
		Modifies the entirety of path/to/file.txt
		If --print-full-paths then it's C:/path/to/file.txt
		see _subHelper documentation
	"""
	name=_subHelper(parsedArgs.path_sub, file.as_posix())
	del file._str # Uncaches the full path (needed because Path.as_posix checks for this)
	file._parts=name.split("/")



def _testHelper(runtimeData, toTest, tests, subCategory, regexIndex=None):
	ret=utils.regexCheckerThing(
		toTest,
		tests["tests"      ],
		tests["antiTests"  ],
		tests["ignoreTests"]
	)
	if   ret is None : runtimeData.count("ignored", subCategory, regexIndex)
	elif ret is False: runtimeData.count("failed" , subCategory, regexIndex)



def fileNameRegex(runtimeData, parsedArgs, file, **kwargs):
	"""
		--file-name-regex <regex match rules>
		Tests the file.txt part of path/to/file.txt against the match rules
	"""
	_testHelper(runtimeData, file._parts[-1], parsedArgs.file_name_regex[0], "file")

def dirPathRegex(runtimeData, parsedArgs, file, **kwargs):
	"""
		--file-name-regex <regex match rules>
		Tests the path/to part of path/to/file.txt against the match rules
		If --print-full-paths then it's C:/path/to/file.txt
	"""
	_testHelper(runtimeData, file.parents[0].as_posix(), parsedArgs.file_name_regex[0], "file")

def fullPathRegex(runtimeData, parsedArgs, file, **kwargs):
	"""
		--file-name-regex <regex match rules>
		Tests the entirety of path/to/file.txt against the match rules
		If --print-full-paths then it's C:/path/to/file.txt
	"""
	_testHelper(runtimeData, file.as_posix(), parsedArgs.file_name_regex[0], "file")



def fileNameGlob(runtimeData, parsedArgs, file, **kwargs):
	"""
		--file-name-regex <glob match rules>
		Tests the file.txt part of path/to/file.txt against the match rules
	"""
	_testHelper(runtimeData, file._parts[-1], parsedArgs.file_name_glob[0] , "file")

def dirPathGlob(runtimeData, parsedArgs, file, **kwargs):
	"""
		--file-name-regex <glob match rules>
		Tests the path/to part of path/to/file.txt against the match rules
		If --print-full-paths then it's C:/path/to/file.txt
	"""
	_testHelper(runtimeData, file.parents[0].as_posix(), parsedArgs.file_name_glob[0] , "file")

def fullPathGlob(runtimeData, parsedArgs, file, **kwargs):
	"""
		--file-name-regex <glob match rules>
		Tests the entirety of path/to/file.txt against the match rules
		If --print-full-paths then it's C:/path/to/file.txt
	"""
	_testHelper(runtimeData, file.as_posix(), parsedArgs.file_name_glob[0] , "file")



def replace(parsedArgs, match, regexIndex, **kwargs):
	"""
		--replace <replace string for get regex 1> [<replace string for get regex 2> ...]
		See re.sub documentation for details
	"""
	if parsedArgs.replace is not None:
		match[0]=match.expand(parsedArgs.replace[regexIndex%len(parsedArgs.replace)])

def _subHelper(subRules, match, regexIndex=0, **kwargs):
	"""
		Handle --sub and similar processors

		The easiest way to explain advanced uses of `--sub` is to give an example. So take `--sub a ? b ? c d e f + x ? y z * ? t ? e d * abc xyz` as an example.
		What it means is the following:

		- `a ? b ? c d e f`: If a match from get regex 0 matches `a` and not `b`, replace `c` with `d` and `e` with `f`
		- `+`: New conditions but stay on the same get regex
		- `x ? y z`: If a match from get regex 0 matches `x`, replace `y` with `z`
		- `*`: Move on to the next get regex
		- `? t ? e d`: If a match from get regex 1 does't match `t`, replace `e` with `d`
		- `*`: Move on to the next get regex
		- `abc xyz`: Replace `abc` with `xyz` without any conditions
	"""
	if subRules:
		regexIndex=regexIndex%len(subRules)
		if regexIndex<len(subRules):
			for group in subRules[regexIndex]:
				if utils.regexCheckerThing(match, group["tests"], group["antiTests"], []):
					repls=group["replsStr" if isinstance(match, str) else "replsBytes"]
					for pattern, repl in zip(group["patterns"], repls):
						match=pattern.sub(repl, match)
	return match

def sub(parsedArgs, match, regexIndex, **kwargs):
	"""
		--sub <sub rules 1> [<sub rules 2> ...]
		see _subHelper documentation
	"""
	match[0]=_subHelper(parsedArgs.sub, match[0], regexIndex)



def matchRegex(parsedArgs, runtimeData, match, regexIndex, **kwargs):
	"""
		--match-regex 
	"""
	_testHelper(
		runtimeData,
		match[0],
		parsedArgs.match_regex[regexIndex%len(parsedArgs.match_regex)],
		"match",
		regexIndex
	)



def noDuplicateMatches(parsedArgs, runtimeData, match, regexIndex, **kwargs):
	# Short circuiting for the win
	dedupes=runtimeData["dedupe"]["match"]
	if "per-regex" in parsedArgs.no_duplicate_matches:
		dedupes=dedupes[regexIndex]
	if match[0] in dedupes:
		runtimeData.count("failed", "match", regexIndex)
	dedupes.append(match[0])



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

def printMatch(parsedArgs, runtimeData, match, stdout, regexIndex, **kwargs):
	stdout.write(f"match (R{regexIndex}): ".encode())
	if parsedArgs.escape_match_output:
		stdout.write(utils.escape(match[0]))
	else:
		stdout.write(match[0])
	stdout.write(b"\n")

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

funcs={
	"skip-conditions"     : skipConditions    ,

	"file-validator"      : fileValidatorExpr ,
	"file-validator-cmd"  : fileValidatorCmd  ,

	"file-name-sub"       : fileNameSub       ,
	"dir-path-sub"        : dirPathSub        ,
	"full-path-sub"       : fullPathSub       ,

	"file-name-regex"     : fileNameRegex     ,
	"dir-path-regex"      : dirPathRegex      ,
	"full-path-regex"     : fullPathRegex     ,

	"file-name-glob"      : fileNameGlob      ,
	"dir-path-glob"       : dirPathGlob       ,
	"full-path-glob"      : fullPathGlob      ,

	#"no-duplicate-file-names": funcNoDuplicateFileNames,

	"replace"             : replace           ,
	"sub"                 : sub               ,

	"match-regex"         : matchRegex        ,

	"no-duplicate-matches": noDuplicateMatches,

	"pre-dir-name-cmd"    : preDirNameCmd     ,
	"print-dir-name"      : printDirName      ,
	"post-dir-name-cmd"   : postDirNameCmd    ,

	"pre-file-name-cmd"   : preFileNameCmd    ,
	"print-file-name"     : printFileName     ,
	"post-file-name-cmd"  : postFileNameCmd   ,

	"pre-match-cmd"       : preMatchCmd       ,
	"print-match"         : printMatch        ,
	"post-match-cmd"      : postMatchCmd      ,
}

def getFuncs(parsedArgs):
	ret={**funcs}

	if not parsedArgs.skip_conditions: del ret["skip-conditions"]

	if not parsedArgs.file_validator_expr: del ret["file-validator"]
	if not parsedArgs.file_validator_cmd or\
			not parsedArgs.file_validator_cmd_expr or\
			parsedArgs.no_cmd or\
			parsedArgs.no_expr:
		del ret["file-validator-cmd"]

	if not parsedArgs.file_name_sub   : del ret["file-name-sub"]
	if not parsedArgs.dir_path_sub    : del ret["dir-path-sub" ]
	if not parsedArgs.full_path_sub   : del ret["full-path-sub"]

	if not parsedArgs.file_name_regex: del ret["file-name-regex"]
	if not parsedArgs.dir_path_regex : del ret["dir-path-regex" ]
	if not parsedArgs.full_path_regex: del ret["full-path-regex"]

	if not parsedArgs.file_name_glob: del ret["file-name-glob"]
	if not parsedArgs.dir_path_glob : del ret["dir-path-glob" ]
	if not parsedArgs.full_path_glob: del ret["full-path-glob"]
	
	if not parsedArgs.replace     or not parsedArgs.regex: del ret["replace"]
	if not parsedArgs.sub         or not parsedArgs.regex: del ret["sub"    ]

	if not parsedArgs.match_regex or not parsedArgs.regex: del ret["match-regex"]

	if not parsedArgs.no_duplicate_matches: del ret["no-duplicate-matches"]

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
