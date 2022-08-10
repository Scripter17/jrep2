import argparse, sys
from . import filesystem, argparseStuff, utils, processors

def main(args=None, stdout=sys.stdout.buffer, stderr=sys.stderr.buffer):

	parsedArgs=argparseStuff.parser.parse_args(args)
	runtimeData=utils.RuntimeData(parsedArgs)
	funcs=processors.getFuncs(parsedArgs)

	previousDir=None
	gotoNextDir=False
	for file in filesystem.getFiles(parsedArgs):
		runtimeData.new("file")

		if file.parents[0]!=previousDir:
			runtimeData.new("dir")
			runtimeData.count("passed", "dir")
		elif gotoNextDir:
			continue
		previousDir=file.parents[0]

		try:
			if not parsedArgs.regex:
				for func in funcs:
					func(
						parsedArgs=parsedArgs,
						runtimeData=runtimeData,
						file=file,
						stdout=stdout,
						stderr=stderr,
					)
			else:
				for regexIndex, regex in enumerate(parsedArgs.regex):
					for match in regex.finditer(file.contents):
						try:
							for func in funcs:
								func(
									parsedArgs=parsedArgs,
									runtimeData=runtimeData,
									file=file,
									match=match,
									regexIndex=regexIndex,
									stdout=stdout,
									stderr=stderr,
								)
						except utils.NextMatch:
							continue
						runtimeData.count("passed", "match", regexIndex)
		except utils.NextFile:
			continue
		except utils.NextDir:
			gotoNextDir=True
			continue
		runtimeData.count("passed", "file")

if __name__=="__main__":
	main()
