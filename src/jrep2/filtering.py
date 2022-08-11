import datetime as _datetime
import re, ast, functools, os

class NormalizationHelper:
	normalizer=None
	def __lt__(self, other): return super().__lt__(self.normalizer(other))
	def __le__(self, other): return super().__le__(self.normalizer(other))
	def __eq__(self, other): return super().__eq__(self.normalizer(other))
	def __ge__(self, other): return super().__ge__(self.normalizer(other))
	def __gt__(self, other): return super().__gt__(self.normalizer(other))
	def __ne__(self, other): return super().__ne__(self.normalizer(other))

class time(NormalizationHelper, _datetime.time):
	@staticmethod
	def normalizer(x):
		if isinstance(x, int) or isinstance(x, float):
			return _datetime.datetime.fromtimestamp(x).time()
		return x

class date(NormalizationHelper, _datetime.date):
	@staticmethod
	def normalizer(x):
		if isinstance(x, int) or isinstance(x, float):
			return _datetime.datetime.fromtimestamp(x).date()
		return x

class datetime(NormalizationHelper, _datetime.datetime):
	@staticmethod
	def normalizer(x):
		if isinstance(x, int) or isinstance(x, float):
			return _datetime.datetime.fromtimestamp(x)
		return x

attrGrabber=re.compile(r"\w+(?==)")
def getFileDict(file):
	stat=file.stat()
	ret={x.removeprefix("st_"):getattr(stat, x) for x in attrGrabber.findall(stat.__repr__())}
	ret["time"    ]=time
	ret["date"    ]=date
	ret["datetime"]=datetime
	ret["path"    ]=file.as_posix(),
	ret["abspath" ]=file.resolve(),
	ret["normpath"]=os.path.normpath(file),
	ret["filename"]=file.parts[-1],
	ret["dir"     ]=file.parents[0].as_posix(),
	ret["absdir"  ]=file.parents[0].resolve(),
	ret["normdir" ]=os.path.normpath(file.parents[0]),
	return ret

badVars=(r"_.*", "globals", "locals", "open", "eval", "exec", "exit", "quit", "compile")
exprFlagger=re.compile(rf"\b({'|'.join(badVars)})\b")
exprUnvalidator=lambda x: isinstance(x, ast.Name) and x.id in badVars
@functools.lru_cache(maxsize=None) # functools.cache isn't in 3.6
def validateExpr(expr):
	return not (exprFlagger.search(expr) and any(map(exprUnvalidator, ast.walk(ast.parse(expr)))))

def evaluateExpr(parsedArgs, expr, globalDict):
	if parsedArgs.unsafe_expr or validateExpr(expr):
		return eval(expr, globalDict)
	raise ValueError(f"Expression contains potentially unsafe code: {expr}")

if __name__=="__main__":
	import os
	print(time(5,0,0)<1659001478.8058286)
	print(time(5,0,0)<time(6,0,0))
	print(date(2020,1,1)<1659001478.8058286)
	print(os.stat("C:/"))
	print(evaluateFilter("ctime", os.stat("C:/")))
