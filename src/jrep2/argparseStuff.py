import argparse, sys, re, string, os, shutil
from . import glob, utils, containers

enhancedEngineDetector=re.compile(r"^-[a-zA-Z]*E|^--enhanced-engine$").match

def compileRegexes(regexes, namespace):
	return [containers.RegexContainer(pattern, namespace) for pattern in regexes]

def compileGlobs(globs, namespace):
	return compileRegexes([globs.translate(pattern, namespace) for pattern in globs], namespace)

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

class CustomStoreAction(argparse._StoreAction):
	def __init__(self, *args, **kwargs):
		if kwargs["nargs"] == 0:
			raise ValueError('nargs for store actions must be != 0; if you '
							 'have nothing to store, actions such as store '
							 'true or store const may be more appropriate')
		#if const is not None and nargs != OPTIONAL:
		#	raise ValueError('nargs must be %r to supply const' % OPTIONAL)
		super(argparse._StoreAction, self).__init__(*args, **kwargs)

	def __call__(self, parser, namespace, values, option_string=None):
		setattr(namespace, self.dest, values if values else self.const)

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

class RegexListAction(argparse.Action):
	"""
		For any paramater that's just a list of regexes
	"""
	def __call__(self, parser, namespace, values, option_string):
		setattr(namespace, self.dest, compileRegexes(values, namespace))

class TestsAction(argparse.Action):
	compileFunc  =None
	ruleSetSplit =None
	rulePartSplit=None
	def __call__(self, parser, namespace, values, option_string):
		ret=[]
		for rules in utils.listSplit(values, self.ruleSetSplit):
			splitRules=utils.listSplit(rules, self.rulePartSplit)
			if   len(splitRules)==1: splitRules=[splitRules[0], [],            []]
			elif len(splitRules)==2: splitRules=[splitRules[0], splitRules[1], []]
			ret.append({
				"tests"      : self.compileFunc(splitRules[0], namespace),
				"antiTests"  : self.compileFunc(splitRules[1], namespace),
				"ignoreTests": self.compileFunc(splitRules[2], namespace)
			})
		setattr(namespace, self.dest, ret)

class RegexTestsAction(TestsAction):
	compileFunc  =staticmethod(compileRegexes)
	rulePartSplit="?"
	ruleSetSplit ="*"

class GlobTestsAction(TestsAction):
	compileFunc  =staticmethod(compileGlobs)
	rulePartSplit=":"
	ruleSetSplit =None

class SubRegexAction(argparse.Action):
	"""
		Pre-processor for --sub stuff

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

parser=CustomParser(formatter_class=CustomHelpFormatter, description="""
	A modern GREP-like command line tool for processing files via regex
""")
parser.add_argument("regex"                    ,       nargs="*", action=RegexListAction             )
parser.add_argument("--enhanced-engine"        , "-E"           , action="store_true"                , help="Use the mrab-regex module instead of the bultin one (https://github.com/mrabarnett/mrab-regex)")
parser.add_argument("--no-cmd"                 ,                  action="store_true"                , help="Disables all CMD functionality for safety")
parser.add_argument("--no-expr"                ,                  action="store_true"                , help="Disables all expr functionality for safety")
parser.add_argument("--unsafe-expr"            ,                  action="store_true"                , help="[NOT RECCOMMENDED] Allows usage of unsafe globals in expressions (open, exit, exec, etc.)")

group=parser.add_argument_group("File selection", "`-f a.txt -g *.jpg -f b.txt` will handle the files in that order")
group .add_argument("--files"                  , "-f", nargs="+", action=FilesAction                 )
group .add_argument("--globs"                  , "-g", nargs="+", action=GlobsAction     , default=[])

group=parser.add_argument_group("Output settings")
group .add_argument("--print-dir-names"        , "-d"           , action="store_true"                )
group .add_argument("--print-file-names"       , "-n"           , action="store_true"                )
group .add_argument("--print-full-paths"       , "-p"           , action="store_true"                , help="Affects --name-sub and co. too")
group .add_argument("--no-print-matches"       , "-N"           , action="store_true"                )
group .add_argument("--escape-match-output"    , "-e"           , action="store_true"                , help="Replace tabs, newlines, and carriage returns with \\t, \\n, and \\r. Also replace 0x00-0x1f and 0x80-0xff bytes with \\xHH")

group=parser.add_argument_group("Modify match")
group .add_argument("--replace"                , "-r", nargs="+"                                     , help="Reformat match using normal re.sub syntax (`jrep (.) -r \\1\\1` doubles each char)")
group .add_argument("--sub"                    , "-R", nargs="+", action=SubRegexAction              , help="Apply regex subsitutions to the match. See substitution syntax below")

group=parser.add_argument_group("File path subsitution")
group .add_argument("--file-name-sub"          ,       nargs="+", action=SubRegexAction              )
group .add_argument("--dir-path-sub"           ,       nargs="+", action=SubRegexAction              )
group .add_argument("--full-path-sub"          ,       nargs="+", action=SubRegexAction              )

group=parser.add_argument_group("Validator regexes/globs")
group .add_argument("--file-name-regex"        ,       nargs="+", action=RegexTestsAction, default=[])
group .add_argument("--dir-path-regex"         ,       nargs="+", action=RegexTestsAction, default=[])
group .add_argument("--full-path-regex"        ,       nargs="+", action=RegexTestsAction, default=[])
group .add_argument("--file-name-glob"         ,       nargs="+", action=GlobTestsAction , default=[])
group .add_argument("--dir-path-glob"          ,       nargs="+", action=GlobTestsAction , default=[])
group .add_argument("--full-path-glob"         ,       nargs="+", action=GlobTestsAction , default=[])
group .add_argument("--match-regex"            ,       nargs="+", action=RegexTestsAction, default=[])

group=parser.add_argument_group("File validator expressions")
group .add_argument("--file-validator-expr"    ,       nargs="+"                                     , help="Python expression that must return truthy for the file to be processed. Uses os.stat(file) results as well as time, date, and datetime from the datetime builtin library modded to support comparing with ints/floats. Example: `ctime<date(2020,01,01)`")
group .add_argument("--file-validator-cmd"     ,       nargs="+"                                     , help="Command line command(s) whose stdout, stderr, and return code are passed to --file-validator-expr. Use {path} {abspath} {normpath} {filename} {dir} {absdir} and {normdir} to substitute the respective values")
group .add_argument("--file-validator-cmd-expr",       nargs="+"                                     , help="--file-validator but the nth expression uses the output of the nth --file-validator-cmd. Uses command stdout, stderr, and returncode. Examples: `returncode==0`, `returncode!=0`, `stderr==''`")

group=parser.add_argument_group("Pre/Post printing cmds")
group .add_argument("--pre-dir-name-cmd"       ,       nargs="+"                                     , help="Execute each command before printing dir names")
group .add_argument("--post-dir-name-cmd"      ,       nargs="+"                                     , help="Execute each command after  printing dir names")
group .add_argument("--pre-file-name-cmd"      ,       nargs="+"                                     , help="Execute each command before printing file names")
group .add_argument("--post-file-name-cmd"     ,       nargs="+"                                     , help="Execute each command after  printing file names")
group .add_argument("--pre-match-cmd"          ,       nargs="+"                                     , help="Execute each command before printing matches")
group .add_argument("--post-match-cmd"         ,       nargs="+"                                     , help="Execute each command after  printing matches")

group=parser.add_argument_group("Miscellaneous")
group .add_argument("--skip-conditions"        ,       nargs="+"                                     , help=f"`file:{{python expression}}` skips the file when the expression is truthy. Same with `dir:` and `match:`. Variables are {', '.join(utils.RuntimeData.flatDictKeys())}")
group .add_argument("--no-duplicate-matches"   , "-D", nargs="*", action=CustomStoreAction, choices=["global", "per-regex", "per-file", "per-dir"], const=["global"], default=[])
#group .add_argument("--no-duplicate-file-names",                  action="store_true"               )
