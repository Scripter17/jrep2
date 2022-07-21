from . import utils

def replace(parsedArgs, match, regexIndex, **kwargs):
	if parsedArgs.replace is not None:
		match[0]=match.expand(parsedArgs.replace[regexIndex%len(parsedArgs.replace)])

def _subHelper(subRules, match, regexIndex, **kwargs):
	"""
		Handle --sub, --name-sub, and --dir-name-sub
		TYSM mCoding for explaining how zip works
		(zip([1,2,3], [4,5,6], [7,8,9]) -> [1,4,7], [2,5,8], [3,6,9])
	"""
	if subRules:
		regexIndex=regexIndex%len(subRules)
		if regexIndex<len(subRules):
			for group in subRules[regexIndex]:
				if utils.regexCheckerThing(match, group["tests"], group["antiTests"]):
					for pattern, repl in zip(group["patterns"], group["repls"]):
						match=pattern.sub(repl, match)
	return match

def sub(parsedArgs, match, regexIndex, **kwargs):
	if parsedArgs.sub is not None:
		match[0]=_subHelper(parsedArgs.sub, match[0], regexIndex)

def printMatch(match, **kwargs):
	print(match[0])

def matchRegex(parsedArgs, match, regexIndex, **kwargs):
	utils.regexCheckerThing(
		match[0],
		parsedArgs.match_pattern,
		parsedArgs.match_anti_pattern,
		parsedArgs.match_ignore_pattern
	)

processors={
	"replace":replace,
	"sub":sub,
	"print-match":printMatch,
}
