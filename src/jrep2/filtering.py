import datetime as _datetime
import re, ast, functools

class NormalizationHelper:
	normalizer=None
	def __lt__(self, other): return super().__lt__(self.__class__.normalizer(other))
	def __le__(self, other): return super().__le__(self.__class__.normalizer(other))
	def __eq__(self, other): return super().__eq__(self.__class__.normalizer(other))
	def __ge__(self, other): return super().__ge__(self.__class__.normalizer(other))
	def __gt__(self, other): return super().__gt__(self.__class__.normalizer(other))
	def __ne__(self, other): return super().__ne__(self.__class__.normalizer(other))

class time(NormalizationHelper, _datetime.time):
	def normalizer(x):
		if isinstance(x, int) or isinstance(x, float):
			return _datetime.datetime.fromtimestamp(x).time()
		return x

class date(NormalizationHelper, _datetime.date):
	def normalizer(x):
		if isinstance(x, int) or isinstance(x, float):
			return _datetime.datetime.fromtimestamp(x).date()
		return x

class datetime(NormalizationHelper, _datetime.datetime):
	def normalizer(x):
		if isinstance(x, int) or isinstance(x, float):
			return _datetime.datetime.fromtimestamp(x)
		return x

attrGrabber=re.compile(r"\w+(?==)")
def evaluateFilter(expr, stat):
	globalDict={x.removeprefix("st_"):getattr(stat, x) for x in attrGrabber.findall(stat.__repr__())}
	globalDict["time"    ]=time
	globalDict["date"    ]=date
	globalDict["datetime"]=datetime
	if validateExpr(expr):
		return eval(expr, globalDict)
	raise ValueError(f"Expression contains potentially unsafe code: {expr}")

exprUnvalidator=re.compile(r"\b(__builtins__|globals)\b")
exprProperUnvalidator=lambda x: isinstance(x, ast.Name) and (x.id=="__builtins__" or x.id=="globals")
@functools.lru_cache(maxsize=None)
def validateExpr(expr):
	return not (exprUnvalidator.search(expr) and any(map(exprProperUnvalidator, ast.walk(ast.parse(expr)))))

if __name__=="__main__":
	import os
	print(time(5,0,0)<1659001478.8058286)
	print(time(5,0,0)<time(6,0,0))
	print(date(2020,1,1)<1659001478.8058286)
	print(os.stat("C:/"))
	print(evaluateFilter("ctime", os.stat("C:/")))
