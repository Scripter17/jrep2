import argparse, sys, re, string, os, shutil
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
		for value in values:
			if value[0:2] in ("*:", "?:"):
				for letter in string.ascii_uppercase:
					if os.path.exists(f"{letter}:/"):
						namespace.globs.append(letter+value[1:])
			else:
				namespace.globs.append(value)

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
				parsed={"tests":[], "antiTests":[], "patterns":[], "replsStr":[], "replsBytes":[]}
				thingParts=utils.listSplit(subSets, "?")
				if   len(thingParts)==1: thingParts=[[],            [], thingParts[0]]
				elif len(thingParts)==2: thingParts=[thingParts[0], [], thingParts[1]]
				parsed["tests"     ]=compileRegexes(thingParts[0]      , namespace)
				parsed["antiTests" ]=compileRegexes(thingParts[1]      , namespace)
				parsed["patterns"  ]=compileRegexes(thingParts[2][0::2], namespace) # Even elems
				parsed["replsStr"  ]=[utils.reEncode(x, str  ) for x in thingParts[2][1::2]] # Odd  elems
				parsed["replsBytes"]=[utils.reEncode(x, bytes) for x in thingParts[2][1::2]] # Odd  elems
				ret[-1].append(parsed)
		setattr(namespace, self.dest, ret)

class CustomParser(argparse.ArgumentParser):
	def parse_args(self, args=None, namespace=None):
		if args is None:
			args=sys.argv[1:]
		if namespace is None:
			namespace=argparse.Namespace()
		if any(map(enhancedEngineDetector, args)):
			namespace.enhanced_engine=True
		return super().parse_args(args, namespace)

class CustomHelpFormatter(argparse.HelpFormatter):
	"""
		Allows --help to better fit the console and adds support for blank lines
	"""
	def __init__(self, prog, indent_increment=2, max_help_position=24, width=None):
		argparse.HelpFormatter.__init__(self, prog, indent_increment, shutil.get_terminal_size().columns, width)

	def _split_lines(self, text, width):
		lines = super()._split_lines(text, width)
		if "\n" in text:
			lines += text.split("\n")[1:]
			text = text.split("\n")[0]
		return lines

	def _format_action_invocation(self, action):
		if not action.option_strings:
			default = self._get_default_metavar_for_positional(action)
			metavar, = self._metavar_formatter(action, default)(1)
			return metavar
		else:
			ret=", ".join(action.option_strings).ljust(30, " ")
			if action.nargs!=0:
				ret+=self._format_args(action, self._get_default_metavar_for_optional(action))
			return ret

parser=CustomParser(formatter_class=CustomHelpFormatter, description="""
	A modern GREP-like command line tool for processing files via regex
""")
parser.add_argument("regex"                   ,       nargs="*", action=RegexListAction            )
parser.add_argument("--enhanced-engine"       , "-E"           , action="store_true"               , help="Use the mrab-regex module instead of the bultin one (https://github.com/mrabarnett/mrab-regex)")

group=parser.add_argument_group("File selection", "`-f a.txt -g *.jpg -f b.txt` will handle the files in that order")
group .add_argument("--files"                 , "-f", nargs="+", action=FilesAction                )
group .add_argument("--globs"                 , "-g", nargs="+", action=GlobsAction                )

group=parser.add_argument_group("Output settings")
group .add_argument("--print-dir-names"       , "-d"           , action="store_true"               )
group .add_argument("--print-file-names"      , "-n"           , action="store_true"               )
group .add_argument("--print-full-paths"      , "-p"           , action="store_true"               , help="Affects --name-sub and co. too")
group .add_argument("--no-print-matches"      , "-N"           , action="store_true"               )
group .add_argument("--escape-match-output"   , "-e"           , action="store_true"               , help="Replace tabs, newlines, and carriage returns with \\t, \\n, and \\r. Also replace 0x00-0x1f and 0x80-0xff bytes with \\xHH")

group=parser.add_argument_group("Modify match")
group .add_argument("--replace"               , "-r", nargs="+"                                    , help="Reformat match using normal re.sub syntax (`jrep (.) -r \\1\\1` doubles each char)")
group .add_argument("--sub"                   , "-R", nargs="+", action=SubRegexAction             , help="Apply regex subsitutions to the match. See substitution syntax below")

group=parser.add_argument_group("File path subsitution")
group .add_argument("--file-name-sub"         ,       nargs="+", action=SubRegexAction             )
group .add_argument("--dir-path-sub"          ,       nargs="+", action=SubRegexAction             )
group .add_argument("--full-path-sub"         ,       nargs="+", action=SubRegexAction             )

group=parser.add_argument_group("File path validator regexes")
group .add_argument("--file-name-regex"       ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--file-name-anti-regex"  ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--file-name-ignore-regex",       nargs="+", action=RegexListAction, default=[])

group .add_argument("--dir-path-regex"        ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--dir-path-anti-regex"   ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--dir-path-ignore-regex" ,       nargs="+", action=RegexListAction, default=[])

group .add_argument("--full-path-regex"       ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--full-path-anti-regex"  ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--full-path-ignore-regex",       nargs="+", action=RegexListAction, default=[])

group=parser.add_argument_group("File path validator globs")
group .add_argument("--file-name-glob"        ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--file-name-anti-glob"   ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--file-name-ignore-glob" ,       nargs="+", action=RegexListAction, default=[])

group .add_argument("--dir-path-glob"         ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--dir-path-anti-glob"    ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--dir-path-ignore-glob"  ,       nargs="+", action=RegexListAction, default=[])

group .add_argument("--full-path-glob"        ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--full-path-anti-glob"   ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--full-path-ignore-glob" ,       nargs="+", action=RegexListAction, default=[])

group=parser.add_argument_group("Match validator regexes")
group .add_argument("--match-regex"           ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--match-anti-regex"      ,       nargs="+", action=RegexListAction, default=[])
group .add_argument("--match-ignore-regex"    ,       nargs="+", action=RegexListAction, default=[])

group=parser.add_argument_group("File path validator expressions")
group .add_argument("--file-validator"        ,       nargs="+"                        , default=[], help="Python expression(s); All must return truthy values for file to be processed")
