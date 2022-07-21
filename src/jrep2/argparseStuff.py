import argparse, sys, re
from . import glob, utils, containers

enhancedEngineDetector=re.compile(r"^-[a-zA-Z]*E|^--enhanced-engine$").match

class FilesAction(argparse.Action):
	"""
		For --files
	"""
	def __call__(self, parser, namespace, values, option_string):
		if not hasattr(namespace, "globs") or namespace.globs is None:
			namespace.globs=[]
		namespace.globs.extend(map(glob.escape, values))

class GlobsAction(argparse.Action):
	"""
		For --globs
	"""
	def __call__(self, parser, namespace, values, option_string):
		if not hasattr(namespace, "globs") or namespace.globs is None:
			namespace.globs=[]
		namespace.globs.extend(values)

def compileRegexes(regexes, namespace):
	return [containers.RegexContainer(pattern, namespace) for pattern in regexes]

# def compileGlobs(globs, namespace):
# 	return [globs.translate(pattern, namespace) for pattern in globs]

class RegexListAction(argparse.Action):
	"""
		For any paramater that's just a list of regexes
	"""
	def __call__(self, parser, namespace, values, option_string):
		setattr(namespace, self.dest, compileRegexes(values, namespace))

# class TestsAction(argparse.Action):
# 	compileFunc=None
# 	ruleSetSplit=None
# 	rulePartSplit=None
# 	def __call__(self, parser, namespace, values, option_string):
# 		ret=[]
# 		for rules in utils.listSplit(values, self.ruleSetSplit):
# 			splitRules=utils.listSplit(rules, self.rulePartSplit)
# 			if   len(splitRules)==1: splitRules=[splitRules[0], [],            []]
# 			elif len(splitRules)==2: splitRules=[splitRules[0], splitRules[1], []]
# 			ret.append({
# 				"tests"      : [self.compileFunc(x) for x in splitRules[0]],
# 				"antiTests"  : [self.compileFunc(x) for x in splitRules[1]],
# 				"ignoreTests": [self.compileFunc(x) for x in splitRules[2]]
# 			})
# 		setattr(namespace, self.dest, ret)

# class RegexTestsAction(TestsAction):
# 	ruleSetSplit="*"
# 	rulePartSplit="?"
# 	compileFunc=compileRegexes

# class GlobTestsAction(TestsAction):
# 	ruleSetSplit=None
# 	rulePartSplit=None
# 	compileFunc=compileGlobs

class SubRegexAction(argparse.Action):
	"""
		Pre-processor for --sub stuff
		These options take a list of arguments
		a ? b ? c d e f + x ? y z * ? t ? e d
		If a match from get regex 0 matches /a/ and not /b/, replace c with d and e with f
		If a match from get regex 0 matches /x/, replace y with z
		If a match from get regex 1 does't match /t/, replace e with d
	"""
	def __call__(self, parser, namespace, values, option_string):
		ret=[]
		for regexGroup in utils.listSplit(values, "*"):
			ret.append([])
			for subSets in utils.listSplit(regexGroup, "+"):
				parsed={"tests":[], "antiTests":[], "patterns":[], "repls":[]}
				thingParts=utils.listSplit(subSets, "?")
				if   len(thingParts)==1: thingParts=[[],            [], thingParts[0]]
				elif len(thingParts)==2: thingParts=[thingParts[0], [], thingParts[1]]
				parsed["tests"    ]=compileRegexes(thingParts[0]      , namespace)
				parsed["antiTests"]=compileRegexes(thingParts[1]      , namespace)
				parsed["patterns" ]=compileRegexes(thingParts[2][0::2], namespace) # Even elems
				parsed["repls"    ]=[utils.reEncode(x, bytes) for x in thingParts[2][1::2]] # Odd  elems
				ret[-1].append(parsed)
		setattr(namespace, self.dest, ret)

class DictableParser(argparse.ArgumentParser):
	def parse_args(self, args=None, namespace=None):
		if args is None:
			args=sys.argv[1:]
		if namespace is None:
			namespace=argparse.Namespace()
		if any(map(enhancedEngineDetector, args)):
			namespace.enhanced_engine=True
		return super().parse_args(args, namespace)

parser=DictableParser()
parser.add_argument("regex", nargs="+", action=RegexListAction)
parser.add_argument("--enhanced-engine", "-E", action="store_true")

parser.add_argument("--files", "-f", nargs="+", action=FilesAction)
parser.add_argument("--globs", "-g", nargs="+", action=GlobsAction)

parser.add_argument("--sub", "-R", nargs="+", action=SubRegexAction)
parser.add_argument("--replace", "-r", nargs="+")

parser.add_argument("--match-regex", nargs="+", action=RegexListAction, default=[])
parser.add_argument("--match-anti-regex", nargs="+", action=RegexListAction, default=[])
parser.add_argument("--match-ignore-regex", nargs="+", action=RegexListAction, default=[])
