import re
import regex

def isPattern(x):
	# Check if x is an instance of re.Pattern or regex.Pattern
	return isinstance(x, re.Pattern) or isinstance(x, regex.Pattern)
def isMatch(x):
	# Check if x is an instance of re.Match or regex.Match
	return isinstance(x, re.Match) or isinstance(x, regex.Match)
def isGenerator(x):
	# Temp solution
	# Used in RegexContainer.__getattr__(x) for when re.x/regex.x returns a generator
	# Or a list I guess
	# Basically str, bytes, re.Match, and regex.Match don't have a __next__ method
	return hasattr(x, "__next__")
