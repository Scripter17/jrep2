from . import utils, classchecking

class RegexContainer:
	"""
		Proxy class to abstract away the difference between str regexes and bytes regexes
	"""
	def __init__(self, regex, enhancedContext=False):
		compiler=utils.getRegexEngine(enhancedContext)
		self.str  =compiler.compile(utils.reEncode(regex, str))
		self.bytes=compiler.compile(utils.reEncode(regex, bytes))
		self.enhanced=utils.isEnhancedEngine(enhancedContext)
	def __getattr__(self, key):
		ret=getattr(self.bytes, key)
		if callable(ret):
			def func(*args, **kwargs):
				try:
					ret=getattr(self.bytes, key)(*args, **kwargs)
				except TypeError:
					ret=getattr(self.str, key)(*args, **kwargs)
				if classchecking.isMatch(ret):
					# RegexContainer.search, .match, etc.
					ret=MatchContainer(ret, self)
				elif classchecking.isGenerator(ret):
					# RegexContainer.finditer
					ret=(MatchContainer(x, self) for x in ret)
				return ret
			return func
		return ret

class MatchContainer:
	"""
		Proxy class to abstract away the difference between re.Pattern and regex.Pattern,
			as well as allowing me to modify the match in-place
	"""
	def __init__(self, match, re):
		self.match=match
		self.re=re
		self.dictOverride={}
	def __getattr__(self, key):
		return getattr(self.match, key)
	def __getitem__(self, key):
		if key in self.dictOverride:
			return self.dictOverride[key]
		return self.match[key]
	def __setitem__(self, key, value):
		self.dictOverride[key]=value
