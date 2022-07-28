import argparse
from . import filesystem, argparseStuff, utils, processors

def main(args=None):
	#parsedArgs=argparseStuff.parser.parse_args(["-g", "*", "-Enep", "--file-name-sub", "a", "b"])
	parsedArgs=argparseStuff.parser.parse_args(args)
	runtimeData=utils.RuntimeData(parsedArgs)

	funcs={**processors.funcs}
	if not parsedArgs.file_validator  : del funcs["file-validator" ]

	if not parsedArgs.file_name_sub   : del funcs["file-name-sub"  ]
	if not parsedArgs.dir_path_sub    : del funcs["dir-path-sub"   ]
	if not parsedArgs.full_path_sub   : del funcs["full-path-sub"  ]

	if not parsedArgs.file_name_glob and\
			not parsedArgs.file_name_anti_glob and\
			not parsedArgs.file_name_ignore_glob and\
			not parsedArgs.file_name_regex and\
			not parsedArgs.file_name_anti_regex and\
			not parsedArgs.file_name_ignore_regex:
		del funcs["file-name-regex"]
	if not parsedArgs.dir_path_glob  and\
			not parsedArgs.dir_path_anti_glob  and\
			not parsedArgs.dir_path_ignore_glob  and\
			not parsedArgs.dir_path_regex  and\
			not parsedArgs.dir_path_anti_regex  and\
			not parsedArgs.dir_path_ignore_regex :
		del funcs["dir-path-regex"]
	if not parsedArgs.full_path_glob and\
			not parsedArgs.full_path_anti_glob and\
			not parsedArgs.full_path_ignore_glob and\
			not parsedArgs.full_path_regex and\
			not parsedArgs.full_path_anti_regex and\
			not parsedArgs.full_path_ignore_regex:
		del funcs["full-path-regex"]

	if not parsedArgs.replace         : del funcs["replace"        ]
	if not parsedArgs.sub             : del funcs["sub"            ]

	if not parsedArgs.match_regex     : del funcs["match-regex"    ]

	if not parsedArgs.print_dir_names : del funcs["print-dir-name" ]
	if not parsedArgs.print_file_names: del funcs["print-file-name"]
	if     parsedArgs.no_print_matches or not parsedArgs.regex:
		del funcs["print-match"]

	previousDir=None
	for file in filesystem.getFiles(parsedArgs):
		runtimeData.new("file")

		if file.parents[0]!=previousDir:
			runtimeData.new("dir")
		previousDir=file.parents[0]

		try:
			if not parsedArgs.regex:
				for funcName, func in funcs.items():
					func(parsedArgs=parsedArgs, runtimeData=runtimeData, file=file)
			for regexIndex, regex in enumerate(parsedArgs.regex):
				for match in regex.finditer(file.contents):
					try:
						for func in funcs.values():
							func(
								parsedArgs=parsedArgs,
								runtimeData=runtimeData,
								file=file,
								match=match,
								regexIndex=regexIndex,
							)
					except utils.NextMatch:
						...
		except utils.NextFile:
			...
		except utils.NextDir:
			...

if __name__=="__main__":
	main()
