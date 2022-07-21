import argparse
from . import filesystem, argparseStuff, utils, processors

def main(args=None):
	#parsedArgs=argparseStuff.parser.parse_args(["bb", "--files", "a.mp4", "-E"])
	parsedArgs=argparseStuff.parser.parse_args(args)
	runtimeData=utils.RuntimeData()
	for file in filesystem.getFiles(parsedArgs.globs):
		try:
			for regexIndex, regex in enumerate(parsedArgs.regex):
				for match in regex.finditer(file.contents):
					try:
						for processorName, processorFunc in processors.processors.items():
							processorFunc(
								parsedArgs=parsedArgs,
								runtimeData=runtimeData,
								match=match,
								regexIndex=regexIndex
							)
					except utils.NextMatch:
						...
		except utils.NextFile:
			...

if __name__=="__main__":
	main()
